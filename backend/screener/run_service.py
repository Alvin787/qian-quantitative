"""In-process screener run management, history, and CSV normalization."""

from __future__ import annotations

import json
import math
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from backend.marketdata.calendar import breakout_run_allowed
from backend.screener.hybrid_screener import (
    DEFAULT_OUTPUT_DIR,
    LEGACY_ALL_RESULTS,
    LEGACY_CANDIDATES,
    allocate_run_id,
)
from backend.screener.strategies import StrategyDefinition, get_strategy, list_strategies
from backend.screener.strategies.base import RunCallable

LEGACY_RUN_ID = "legacy"
HISTORY_DAYS = 14


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def normalize_cell(value: Any) -> Any:
    """Convert a pandas/numpy CSV cell into JSON-safe Python values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    return str(value)


def dataframe_to_records(df: pd.DataFrame) -> tuple[list[str], list[dict[str, Any]]]:
    columns = [str(c) for c in df.columns.tolist()]
    rows: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        rows.append({k: normalize_cell(v) for k, v in record.items()})
    return columns, rows


class ScreenerRunService:
    """Manage screener runs with one-at-a-time background execution."""

    def __init__(
        self,
        output_dir: Path | None = None,
        *,
        legacy_all: Path | None = None,
        legacy_candidates: Path | None = None,
        run_overrides: Mapping[str, RunCallable] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.legacy_all = Path(legacy_all) if legacy_all else LEGACY_ALL_RESULTS
        self.legacy_candidates = (
            Path(legacy_candidates) if legacy_candidates else LEGACY_CANDIDATES
        )
        self._run_overrides: dict[str, RunCallable] = dict(run_overrides or {})
        self._lock = threading.Lock()
        self._active_run_id: str | None = None
        self._active_strategy_id: str | None = None
        self._thread: threading.Thread | None = None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reconcile_stale_runs()

    def _resolve_run(self, definition: StrategyDefinition) -> RunCallable:
        return self._run_overrides.get(definition.id, definition.run)

    def meta_path(self, strategy_id: str, run_id: str) -> Path:
        return self.output_dir / get_strategy(strategy_id).meta_file.format(run_id=run_id)

    def view_path(self, strategy_id: str, run_id: str, view: str) -> Path:
        return self.output_dir / get_strategy(strategy_id).view_files[view].format(
            run_id=run_id
        )

    def write_metadata(self, meta: dict[str, Any]) -> None:
        run_id = meta["run_id"]
        strategy_id = meta["strategy_id"]
        path = self.meta_path(strategy_id, run_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def read_metadata(self, strategy_id: str, run_id: str) -> dict[str, Any] | None:
        path = self.meta_path(strategy_id, run_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def reconcile_stale_runs(self) -> None:
        """Mark orphaned 'running' metadata as failed after process restart."""
        for definition in list_strategies():
            pattern = definition.meta_file.format(run_id="*")
            for path in self.output_dir.glob(pattern):
                try:
                    meta = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                if meta.get("status") != "running":
                    continue
                if (
                    meta.get("run_id") == self._active_run_id
                    and meta.get("strategy_id") == self._active_strategy_id
                ):
                    continue
                meta["status"] = "failed"
                meta["error"] = meta.get("error") or "interrupted by restart"
                meta["finished_at"] = _iso(_utc_now())
                path.write_text(
                    json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
                )

    def has_active_run(self) -> bool:
        with self._lock:
            return self._active_run_id is not None

    def active_run_id(self) -> str | None:
        with self._lock:
            return self._active_run_id

    def start_run(
        self, strategy_id: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Start a background screener run. Raises RuntimeError if busy."""
        definition = get_strategy(strategy_id)
        opts = options or {}
        if strategy_id == "breakout" and not breakout_run_allowed():
            raise ValueError(
                "Breakout runs are accepted only 15 minutes after the official XNYS close"
            )
        with self._lock:
            if self._active_run_id is not None:
                raise RuntimeError(
                    f"Run already in progress: {self._active_strategy_id}/{self._active_run_id}"
                )
            run_id = allocate_run_id(
                self.output_dir,
                filenames=(definition.meta_file, *definition.view_files.values()),
            )
            started = _utc_now()
            files = {
                view: template.format(run_id=run_id)
                for view, template in definition.view_files.items()
            }
            meta: dict[str, Any] = {
                "run_id": run_id,
                "strategy_id": strategy_id,
                "status": "running",
                "started_at": _iso(started),
                "finished_at": None,
                "scored": None,
                "passed": None,
                "skipped": None,
                "files": files,
                "views": list(definition.views),
                "notes": None,
                "regime_ok": None,
                "error": None,
                "legacy": False,
                "as_of_session": None,
                "screen_manifest": None,
            }
            self.write_metadata(meta)
            self._active_run_id = run_id
            self._active_strategy_id = strategy_id
            thread = threading.Thread(
                target=self._run_worker,
                args=(definition, run_id, opts),
                name=f"screener-{strategy_id}-{run_id}",
                daemon=True,
            )
            self._thread = thread
            thread.start()
            return dict(meta)

    def _run_worker(
        self, definition: StrategyDefinition, run_id: str, options: dict[str, Any]
    ) -> None:
        meta = self.read_metadata(definition.id, run_id) or {
            "run_id": run_id,
            "strategy_id": definition.id,
            "status": "running",
        }
        try:
            result = self._resolve_run(definition)(
                outdir=self.output_dir,
                run_id=run_id,
                options=options,
            )
            meta.update(
                {
                    "status": "completed",
                    "finished_at": _iso(_utc_now()),
                    "scored": result.scored,
                    "passed": result.passed,
                    "skipped": result.skipped,
                    "files": {view: path.name for view, path in result.paths.items()},
                    "notes": result.notes,
                    "regime_ok": result.regime_ok,
                    "error": None,
                    "as_of_session": result.as_of_session,
                    "screen_manifest": getattr(result, "screen_manifest", None),
                }
            )
        except Exception as exc:  # noqa: BLE001 — persist any worker failure
            meta.update(
                {
                    "status": "failed",
                    "finished_at": _iso(_utc_now()),
                    "error": str(exc),
                }
            )
        finally:
            self.write_metadata(meta)
            with self._lock:
                self._active_run_id = None
                self._active_strategy_id = None
                self._thread = None

    def legacy_metadata(self, strategy_id: str) -> dict[str, Any] | None:
        definition = get_strategy(strategy_id)
        if not definition.supports_legacy:
            return None
        if not self.legacy_all.exists():
            return None
        mtime = datetime.fromtimestamp(self.legacy_all.stat().st_mtime, tz=timezone.utc)
        passed = None
        scored = None
        try:
            all_df = pd.read_csv(self.legacy_all)
            scored = int(len(all_df))
            if "pass_all" in all_df.columns:
                passed = int(
                    all_df["pass_all"]
                    .astype(str)
                    .str.lower()
                    .isin(("true", "1", "yes"))
                    .sum()
                )
            elif self.legacy_candidates.exists():
                passed = int(len(pd.read_csv(self.legacy_candidates)))
        except Exception:  # noqa: BLE001
            scored = None
            passed = None
        files: dict[str, str] = {"all": self.legacy_all.name}
        if self.legacy_candidates.exists():
            files["candidates"] = self.legacy_candidates.name
        return {
            "run_id": LEGACY_RUN_ID,
            "strategy_id": strategy_id,
            "status": "completed",
            "started_at": _iso(mtime),
            "finished_at": _iso(mtime),
            "scored": scored,
            "passed": passed,
            "skipped": None,
            "files": files,
            "views": list(definition.views),
            "notes": None,
            "regime_ok": None,
            "error": None,
            "legacy": True,
        }

    def _parse_started_at(self, meta: dict[str, Any]) -> datetime | None:
        raw = meta.get("started_at") or meta.get("finished_at")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

    def list_runs(
        self, strategy_id: str, *, days: int = HISTORY_DAYS
    ) -> list[dict[str, Any]]:
        definition = get_strategy(strategy_id)
        cutoff = _utc_now() - timedelta(days=days)
        runs: list[dict[str, Any]] = []
        pattern = definition.meta_file.format(run_id="*")
        for path in self.output_dir.glob(pattern):
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if meta.get("strategy_id") not in (None, strategy_id):
                continue
            started = self._parse_started_at(meta)
            if started is not None and started < cutoff:
                continue
            meta.setdefault("legacy", False)
            meta.setdefault("strategy_id", strategy_id)
            runs.append(meta)

        if not runs and definition.supports_legacy:
            legacy = self.legacy_metadata(strategy_id)
            if legacy is not None:
                runs.append(legacy)

        def sort_key(item: dict[str, Any]) -> datetime:
            return self._parse_started_at(item) or datetime.min.replace(
                tzinfo=timezone.utc
            )

        runs.sort(key=sort_key, reverse=True)
        return runs

    def get_run(self, strategy_id: str, run_id: str) -> dict[str, Any] | None:
        if run_id == LEGACY_RUN_ID:
            return self.legacy_metadata(strategy_id)
        meta = self.read_metadata(strategy_id, run_id)
        if meta is None:
            return None
        # Pre-strategy metadata may omit strategy_id; backfill for API responses.
        meta.setdefault("strategy_id", strategy_id)
        meta.setdefault("legacy", False)
        return meta

    def resolve_csv(self, strategy_id: str, run_id: str, view: str) -> Path | None:
        if run_id == LEGACY_RUN_ID:
            if not get_strategy(strategy_id).supports_legacy:
                return None
            path = self.legacy_all if view == "all" else self.legacy_candidates
            return path if path.exists() else None

        meta = self.read_metadata(strategy_id, run_id)
        if meta is None:
            return None
        files = meta.get("files") or {}
        name = files.get(view)
        if name:
            path = self.output_dir / name
        else:
            path = self.view_path(strategy_id, run_id, view)
        return path if path.exists() else None

    def load_results(
        self, strategy_id: str, run_id: str, view: str
    ) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
        meta = self.get_run(strategy_id, run_id)
        if meta is None:
            raise FileNotFoundError(f"Run not found: {run_id}")
        status = meta.get("status")
        if status == "running":
            raise RuntimeError(f"Run {run_id} is still running")
        if status == "failed" and self.resolve_csv(strategy_id, run_id, view) is None:
            raise LookupError(meta.get("error") or f"Run {run_id} failed")

        path = self.resolve_csv(strategy_id, run_id, view)
        if path is None:
            raise FileNotFoundError(f"Results not found for run {run_id} view={view}")

        df = pd.read_csv(path)
        columns, rows = dataframe_to_records(df)
        return meta, columns, rows


# Process-wide singleton for the FastAPI app.
screener_run_service = ScreenerRunService()

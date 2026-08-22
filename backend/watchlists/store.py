from __future__ import annotations

import json
import shutil
import threading
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime, timezone
from pathlib import Path

LISTS: tuple[str, ...] = ("master", "stalk", "focus", "back")
DATA_DIR = Path(__file__).resolve().parent / "watchlist_data"
SCHEMA_VERSION = 4


@dataclass
class Gates:
    adr_pct: float | None = None
    adr_ok: bool | None = None
    avg_dollar_vol: float | None = None
    liq_ok: bool | None = None
    close: float | None = None
    sma10: float | None = None
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    above_10: bool | None = None
    above_20: bool | None = None
    rising_10: bool | None = None
    rising_20: bool | None = None
    extension_x: float | None = None
    ext_ok: bool | None = None
    rs_3m_pp: float | None = None
    rs_ok: bool | None = None
    earnings_date: str | None = None
    days_to_earnings: int | None = None
    earn_ok: str | None = None
    biotech: bool | None = None
    declining_200: bool | None = None
    room_to_200_adr: float | None = None
    room_to_200_ok: bool | None = None
    volume_dryup: bool | None = None
    range_compress: bool | None = None
    near_10_20: bool | None = None
    atr_pct: float | None = None
    extension_basis: str | None = None
    rs_sessions: int | None = None
    price_as_of: str | None = None
    data_fresh: bool | None = None


@dataclass
class ChartChecklist:
    catalyst: bool | None = None
    vcp: bool | None = None
    linearity: bool | None = None
    pivot: bool | None = None
    group_leader: bool | None = None
    gap_resistance_ok: bool | None = None
    stop_planned: bool | None = None
    alert_set: bool | None = None
    earnings_verified: bool | None = None


@dataclass
class Name:
    ticker: str
    list: str
    added_at: str
    source_screens: list[str] = field(default_factory=list)
    historical_source_screens: list[str] = field(default_factory=list)
    screen_count: int | None = None
    screen_family_count: int | None = None
    industry: str = ""
    note: str = ""
    group: str = ""
    readiness: str = "unscored"
    queue_reason: str | None = None
    fail_reasons: str = ""
    gates: Gates = field(default_factory=Gates)
    chart_checklist: ChartChecklist = field(default_factory=ChartChecklist)
    manual_focus_approved_at: str | None = None
    last_scored_at: str | None = None


@dataclass
class ReviewMeta:
    review_id: str | None = None
    status: str = "idle"
    started_at: str | None = None
    finished_at: str | None = None
    ingested: int | None = None
    scored: int | None = None
    unknown: int | None = None
    error: str | None = None
    notes: str | None = None
    breakout_run_id: str | None = None


@dataclass
class FunnelState:
    updated_at: str
    schema_version: int = SCHEMA_VERSION
    review: ReviewMeta = field(default_factory=ReviewMeta)
    names: list[Name] = field(default_factory=list)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_gates(raw: object) -> Gates:
    if not isinstance(raw, dict):
        raise TypeError("gates must be an object")
    allowed = {item.name for item in fields(Gates)}
    return Gates(**{key: value for key, value in raw.items() if key in allowed})


def _parse_checklist(raw: object) -> ChartChecklist:
    if isinstance(raw, ChartChecklist):
        return raw
    if not isinstance(raw, dict):
        raise TypeError("chart_checklist must be an object")
    allowed = {item.name for item in fields(ChartChecklist)}
    return ChartChecklist(**{key: value for key, value in raw.items() if key in allowed})


def _apply_checklist_update(target: ChartChecklist, patch: dict | ChartChecklist) -> None:
    if isinstance(patch, ChartChecklist):
        patch_dict = asdict(patch)
    elif isinstance(patch, dict):
        patch_dict = patch
    else:
        raise TypeError("checklist must be a dict or ChartChecklist")
    allowed = {item.name for item in fields(ChartChecklist)}
    for key, value in patch_dict.items():
        if key in allowed:
            setattr(target, key, value)


def _parse_name(item: object) -> Name:
    if not isinstance(item, dict):
        raise TypeError("name must be an object")
    allowed = {item_field.name for item_field in fields(Name)}
    payload = {
        key: value
        for key, value in item.items()
        if key in allowed and key not in {"gates", "chart_checklist", "source_screens", "historical_source_screens"}
    }
    payload["gates"] = _parse_gates(item.get("gates") or {})
    payload["chart_checklist"] = _parse_checklist(item.get("chart_checklist") or {})
    payload["source_screens"] = list(item.get("source_screens") or [])
    payload["historical_source_screens"] = list(item.get("historical_source_screens") or [])
    if payload.get("readiness") == "focus_ready":
        payload["readiness"] = "chart_review_ready"
    return Name(**payload)


def _parse_review(raw: object) -> ReviewMeta:
    if not isinstance(raw, dict):
        raise TypeError("review must be an object")
    allowed = {item.name for item in fields(ReviewMeta)}
    return ReviewMeta(**{key: value for key, value in raw.items() if key in allowed})


def _state_from_data(data: object) -> FunnelState:
    if not isinstance(data, dict):
        raise TypeError("funnel root must be an object")
    review_raw = data.get("review") or {}
    if not isinstance(review_raw, dict):
        raise TypeError("review must be an object")
    names_raw = data.get("names") or []
    if not isinstance(names_raw, list):
        raise TypeError("names must be a list")
    schema_version = data["schema_version"] if "schema_version" in data else 3
    return FunnelState(
        updated_at=data["updated_at"],
        schema_version=schema_version,
        review=_parse_review(review_raw),
        names=_unique_names([_parse_name(item) for item in names_raw]),
    )


def _unique_names(names: list[Name]) -> list[Name]:
    by_ticker: dict[str, Name] = {}
    for name in names:
        ticker = str(name.ticker).strip().upper()
        name.ticker = ticker
        by_ticker[ticker] = name
    return list(by_ticker.values())


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise ValueError("empty ticker")
    return normalized


def _require_list(list_name: str) -> str:
    if list_name not in LISTS:
        raise ValueError(f"invalid list: {list_name}")
    return list_name


class WatchlistStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else DATA_DIR
        self._lock = threading.Lock()

    def _path(self) -> Path:
        return self.root / "funnel.json"

    def get(self) -> FunnelState:
        with self._lock:
            return self._get_unlocked()

    def put(self, state: FunnelState) -> FunnelState:
        with self._lock:
            return self._put_unlocked(state)

    def upsert(
        self,
        ticker: str,
        list_name: str,
        *,
        note: str | None = None,
        group: str | None = None,
        chart_checklist: dict | ChartChecklist | None = None,
        added_at: str,
    ) -> Name:
        ticker = _normalize_ticker(ticker)
        list_name = _require_list(list_name)
        with self._lock:
            state = self._get_unlocked()
            existing = next((name for name in state.names if name.ticker == ticker), None)
            if existing is not None:
                existing.list = list_name
                if note is not None:
                    existing.note = note
                if group is not None:
                    existing.group = group
                if list_name == "focus" and existing.manual_focus_approved_at is None:
                    existing.manual_focus_approved_at = _now_utc()
                if chart_checklist is not None:
                    _apply_checklist_update(existing.chart_checklist, chart_checklist)
                self._put_unlocked(state)
                return existing
            chk = ChartChecklist()
            if chart_checklist is not None:
                _apply_checklist_update(chk, chart_checklist)
            focus_approved_at = _now_utc() if list_name == "focus" else None
            name = Name(
                ticker,
                list_name,
                added_at,
                readiness="unscored",
                chart_checklist=chk,
                manual_focus_approved_at=focus_approved_at,
            )
            state.names.append(name)
            self._put_unlocked(state)
            return name

    def move(self, ticker: str, list_name: str) -> Name:
        ticker = _normalize_ticker(ticker)
        list_name = _require_list(list_name)
        with self._lock:
            state = self._get_unlocked()
            for name in state.names:
                if name.ticker == ticker:
                    name.list = list_name
                    if list_name == "focus" and name.manual_focus_approved_at is None:
                        name.manual_focus_approved_at = _now_utc()
                    self._put_unlocked(state)
                    return name
            raise KeyError(ticker)

    def update_checklist(self, ticker: str, checklist: dict | ChartChecklist) -> Name:
        ticker = _normalize_ticker(ticker)
        with self._lock:
            state = self._get_unlocked()
            for name in state.names:
                if name.ticker == ticker:
                    _apply_checklist_update(name.chart_checklist, checklist)
                    self._put_unlocked(state)
                    return name
            raise KeyError(ticker)

    def delete(self, ticker: str) -> None:
        ticker = ticker.strip().upper()
        with self._lock:
            state = self._get_unlocked()
            kept = [name for name in state.names if name.ticker != ticker]
            if len(kept) == len(state.names):
                raise KeyError(ticker)
            state.names = kept
            self._put_unlocked(state)

    def apply_review(self, scored: list[Name], *, review: ReviewMeta) -> FunnelState:
        from backend.watchlists.review import queue_reason

        scored_by_ticker = {name.ticker: name for name in scored}
        with self._lock:
            current = self._get_unlocked()
            merged: list[Name] = []
            for name in current.names:
                scored_name = scored_by_ticker.get(name.ticker)
                if scored_name is None:
                    merged.append(name)
                    continue
                merged.append(
                    replace(
                        scored_name,
                        list=name.list,
                        note=name.note,
                        group=name.group,
                        added_at=name.added_at,
                        chart_checklist=name.chart_checklist,
                        manual_focus_approved_at=name.manual_focus_approved_at,
                        queue_reason=queue_reason(
                            readiness=scored_name.readiness,
                            list_name=name.list,
                            newly_ingested=scored_name.queue_reason == "new_ingest",
                            source_screens=scored_name.source_screens,
                            historical_source_screens=scored_name.historical_source_screens,
                        ),
                    )
                )
            current.names = merged
            current.review = review
            return self._put_unlocked(current)

    def _get_unlocked(self) -> FunnelState:
        path = self._path()
        if not path.is_file():
            return FunnelState(
                updated_at=_now_utc(),
                review=ReviewMeta(),
                names=[],
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _state_from_data(data)
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"corrupt funnel.json: {exc}") from exc

    def _put_unlocked(self, state: FunnelState) -> FunnelState:
        self.root.mkdir(parents=True, exist_ok=True)
        state.updated_at = _now_utc()
        state.schema_version = SCHEMA_VERSION
        state.names = _unique_names(state.names)
        path = self._path()
        if path.is_file():
            shutil.copy2(path, self.root / "funnel.json.bak")
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        return state

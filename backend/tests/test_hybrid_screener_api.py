"""Practical hybrid screener backend tests (no live Finviz/yfinance)."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.screener.hybrid_run_service import (
    HybridRunService,
    LEGACY_RUN_ID,
    dataframe_to_records,
    normalize_cell,
)
from backend.screener.hybrid_screener import ScreenerRunResult, allocate_run_id
from backend.screener import router as screener_router
from backend.main import app


@pytest.fixture
def tmp_paths(tmp_path: Path):
    out = tmp_path / "screener_output"
    out.mkdir()
    legacy_all = tmp_path / "hybrid_all_results.csv"
    legacy_cand = tmp_path / "hybrid_candidates.csv"
    return out, legacy_all, legacy_cand


def _write_pair(outdir: Path, run_id: str, rows: list[dict]) -> tuple[Path, Path]:
    all_df = pd.DataFrame(rows)
    cand_df = all_df[all_df["pass_all"]] if "pass_all" in all_df.columns else all_df
    all_path = outdir / f"hybrid_all_results_{run_id}.csv"
    cand_path = outdir / f"hybrid_candidates_{run_id}.csv"
    all_df.to_csv(all_path, index=False)
    cand_df.to_csv(cand_path, index=False)
    return all_path, cand_path


def _fake_executor_factory(outdir: Path, *, fail: bool = False, delay: float = 0.0):
    def _executor(*, run_id: str, outdir: Path, **kwargs) -> ScreenerRunResult:
        if delay:
            time.sleep(delay)
        if fail:
            raise RuntimeError("boom")
        rows = [
            {
                "ticker": "AAA",
                "pass_all": True,
                "close": 10.5,
                "adr_pct": 2.1,
                "fail_reasons": "",
            },
            {
                "ticker": "BBB",
                "pass_all": False,
                "close": 8.0,
                "adr_pct": 6.0,
                "fail_reasons": "adr",
            },
        ]
        all_path, cand_path = _write_pair(outdir, run_id, rows)
        return ScreenerRunResult(
            run_id=run_id,
            all_results_path=all_path,
            candidates_path=cand_path,
            scored=2,
            passed=1,
            skipped=0,
            regime_ok=True,
            regime_note="ok",
        )

    return _executor


class TestAllocateAndNormalize:
    def test_allocate_run_id_collision_safe(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        when = datetime(2026, 7, 30, 16, 30, 45)
        first = allocate_run_id(out, when=when)
        assert first == "2026-07-30_163045"
        (out / f"hybrid_all_results_{first}.csv").write_text("x", encoding="utf-8")
        second = allocate_run_id(out, when=when)
        assert second == "2026-07-30_163046"

    def test_normalize_cell_json_safe(self):
        assert normalize_cell(np.nan) is None
        assert normalize_cell(float("nan")) is None
        assert normalize_cell(np.bool_(True)) is True
        assert normalize_cell(np.int64(3)) == 3
        assert normalize_cell(np.float64(1.5)) == 1.5
        assert normalize_cell(pd.NaT) is None
        assert normalize_cell(pd.Timestamp("2026-07-30")) == "2026-07-30T00:00:00"

    def test_dataframe_to_records(self):
        df = pd.DataFrame(
            {
                "ticker": ["AAA"],
                "pass_all": [True],
                "close": [np.float64(1.25)],
                "missing": [np.nan],
            }
        )
        columns, rows = dataframe_to_records(df)
        assert columns == ["ticker", "pass_all", "close", "missing"]
        assert rows == [
            {"ticker": "AAA", "pass_all": True, "close": 1.25, "missing": None}
        ]


class TestHybridRunService:
    def test_list_runs_newest_first_within_14_days(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        service = HybridRunService(
            out, legacy_all=legacy_all, legacy_candidates=legacy_cand
        )

        older = datetime.now(timezone.utc) - timedelta(days=2)
        newer = datetime.now(timezone.utc) - timedelta(hours=1)
        stale = datetime.now(timezone.utc) - timedelta(days=20)

        for run_id, started in (
            ("2026-07-28_100000", older),
            ("2026-07-30_120000", newer),
            ("2026-07-01_090000", stale),
        ):
            service.write_metadata(
                {
                    "run_id": run_id,
                    "status": "completed",
                    "started_at": started.isoformat(),
                    "finished_at": started.isoformat(),
                    "scored": 1,
                    "passed": 0,
                    "skipped": 0,
                    "all_results_file": f"hybrid_all_results_{run_id}.csv",
                    "candidates_file": f"hybrid_candidates_{run_id}.csv",
                    "error": None,
                    "legacy": False,
                }
            )

        runs = service.list_runs(days=14)
        ids = [r["run_id"] for r in runs]
        assert ids == ["2026-07-30_120000", "2026-07-28_100000"]

    def test_legacy_fallback_when_no_timestamped_runs(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        pd.DataFrame(
            [{"ticker": "AAA", "pass_all": True}, {"ticker": "BBB", "pass_all": False}]
        ).to_csv(legacy_all, index=False)
        pd.DataFrame([{"ticker": "AAA", "pass_all": True}]).to_csv(
            legacy_cand, index=False
        )
        service = HybridRunService(
            out, legacy_all=legacy_all, legacy_candidates=legacy_cand
        )
        runs = service.list_runs()
        assert len(runs) == 1
        assert runs[0]["run_id"] == LEGACY_RUN_ID
        assert runs[0]["legacy"] is True
        assert runs[0]["scored"] == 2
        assert runs[0]["passed"] == 1

    def test_active_run_protection_and_failure_status(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        gate = threading.Event()

        def slow_executor(*, run_id: str, outdir: Path, **kwargs):
            gate.wait(timeout=5)
            raise RuntimeError("forced failure")

        service = HybridRunService(
            out,
            legacy_all=legacy_all,
            legacy_candidates=legacy_cand,
            executor=slow_executor,
        )
        first = service.start_run()
        assert first["status"] == "running"

        with pytest.raises(RuntimeError, match="already in progress"):
            service.start_run()

        gate.set()
        deadline = time.time() + 5
        while service.has_active_run() and time.time() < deadline:
            time.sleep(0.01)

        meta = service.get_run(first["run_id"])
        assert meta is not None
        assert meta["status"] == "failed"
        assert "forced failure" in meta["error"]

    def test_reconcile_stale_running_on_init(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        run_id = "2026-07-30_111111"
        (out / f"hybrid_run_{run_id}.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "error": None,
                }
            ),
            encoding="utf-8",
        )
        service = HybridRunService(
            out, legacy_all=legacy_all, legacy_candidates=legacy_cand
        )
        meta = service.get_run(run_id)
        assert meta["status"] == "failed"
        assert "interrupted" in meta["error"]


class TestHybridApi:
    @pytest.fixture
    def api_client(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        pd.DataFrame(
            [{"ticker": "LEG", "pass_all": True, "close": 1.0}]
        ).to_csv(legacy_all, index=False)
        pd.DataFrame(
            [{"ticker": "LEG", "pass_all": True, "close": 1.0}]
        ).to_csv(legacy_cand, index=False)

        service = HybridRunService(
            out,
            legacy_all=legacy_all,
            legacy_candidates=legacy_cand,
            executor=_fake_executor_factory(out),
        )
        previous = screener_router.get_service()
        screener_router.set_service(service)
        client = TestClient(app)
        try:
            yield client, service
        finally:
            screener_router.set_service(previous)

    def test_post_returns_202_and_results_flow(self, api_client):
        client, service = api_client
        resp = client.post("/api/screener/hybrid/runs", json={})
        assert resp.status_code == 202
        body = resp.json()
        run_id = body["run_id"]
        assert body["status"] == "running"

        deadline = time.time() + 5
        while time.time() < deadline:
            status = client.get(f"/api/screener/hybrid/runs/{run_id}")
            assert status.status_code == 200
            if status.json()["status"] == "completed":
                break
            time.sleep(0.02)
        else:
            pytest.fail("run did not complete")

        listed = client.get("/api/screener/hybrid/runs")
        assert listed.status_code == 200
        ids = [r["run_id"] for r in listed.json()["runs"]]
        assert run_id in ids
        assert LEGACY_RUN_ID not in ids  # timestamped history supersedes legacy

        results = client.get(
            f"/api/screener/hybrid/runs/{run_id}/results", params={"view": "all"}
        )
        assert results.status_code == 200
        payload = results.json()
        assert payload["row_count"] == 2
        assert payload["rows"][0]["ticker"] == "AAA"
        assert payload["rows"][0]["pass_all"] is True

        cands = client.get(
            f"/api/screener/hybrid/runs/{run_id}/results",
            params={"view": "candidates"},
        )
        assert cands.status_code == 200
        assert cands.json()["row_count"] == 1

        download = client.get(
            f"/api/screener/hybrid/runs/{run_id}/download",
            params={"view": "candidates"},
        )
        assert download.status_code == 200
        assert "text/csv" in download.headers["content-type"]
        assert b"AAA" in download.content

    def test_conflict_when_active(self, tmp_paths):
        out, legacy_all, legacy_cand = tmp_paths
        gate = threading.Event()

        def slow(*, run_id: str, outdir: Path, **kwargs):
            gate.wait(timeout=5)
            return _fake_executor_factory(outdir)(run_id=run_id, outdir=outdir)

        service = HybridRunService(
            out,
            legacy_all=legacy_all,
            legacy_candidates=legacy_cand,
            executor=slow,
        )
        previous = screener_router.get_service()
        screener_router.set_service(service)
        client = TestClient(app)
        try:
            first = client.post("/api/screener/hybrid/runs")
            assert first.status_code == 202
            second = client.post("/api/screener/hybrid/runs")
            assert second.status_code == 409
        finally:
            gate.set()
            deadline = time.time() + 5
            while service.has_active_run() and time.time() < deadline:
                time.sleep(0.01)
            screener_router.set_service(previous)

    def test_http_errors(self, api_client):
        client, _service = api_client
        missing = client.get("/api/screener/hybrid/runs/does-not-exist")
        assert missing.status_code == 404

        bad_view = client.get(
            "/api/screener/hybrid/runs/legacy/results", params={"view": "nope"}
        )
        assert bad_view.status_code == 400

        legacy = client.get(
            "/api/screener/hybrid/runs/legacy/results", params={"view": "all"}
        )
        assert legacy.status_code == 200
        assert legacy.json()["rows"][0]["ticker"] == "LEG"

from __future__ import annotations

import threading
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backend.screener.strategies.breakout import BREAKOUT_SCREEN_IDS
from backend.watchlists.review import WatchlistReviewService, queue_reason
from backend.watchlists.store import FunnelState, Name, WatchlistStore

FROZEN = date(2026, 8, 14)


def make_ohlcv(
    n: int,
    *,
    start_close: float = 100.0,
    close_step: float = 0.5,
    volume: float = 1_000_000.0,
    end: str | None = None,
) -> pd.DataFrame:
    idx = pd.bdate_range(end=end, periods=n) if end is not None else pd.bdate_range("2026-01-02", periods=n)
    close = start_close + close_step * np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.04,
            "Low": close / 1.04,
            "Close": close,
            "Volume": np.full(n, volume),
        },
        index=idx,
    )


HISTORY = make_ohlcv(70)
SPY = make_ohlcv(70, start_close=400.0, close_step=0.01)
CHART_HISTORY = make_ohlcv(220, end="2026-08-14")
CHART_SPY = make_ohlcv(220, end="2026-08-14", start_close=400.0, close_step=0.01)
EARNINGS = date(2026, 8, 28)


class StubScreener:
    def __init__(self, rows=None, runs=None, as_of_session="2026-08-14") -> None:
        self.rows = list(rows or [])
        self.runs = list(runs) if runs is not None else [
            {"run_id": "r1", "status": "completed"}
        ]
        self.as_of_session = as_of_session

    def list_runs(self, strategy_id: str, *, days: int = 14) -> list[dict]:
        return list(self.runs)

    def load_results(self, strategy_id, run_id, view) -> tuple[dict, list[str], list[dict]]:
        return (
            {
                "run_id": run_id,
                "status": "completed",
                "as_of_session": self.as_of_session,
                "scored": len(self.rows),
            },
            ["ticker", "industry", "source_screens"],
            self.rows,
        )


def wait_review(service: WatchlistReviewService, review_id: str, timeout: float = 2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        meta = service.get_review(review_id)
        if meta is not None and meta.status in ("completed", "failed"):
            return meta
        time.sleep(0.02)
    raise AssertionError(f"review {review_id} did not finish")


def _service(
    tmp_path: Path,
    *,
    rows=None,
    runs=None,
    as_of_session="2026-08-14",
    load_history=None,
    load_spy=None,
    load_earnings=None,
    load_history_batch=None,
    today=None,
    expected_session=None,
    cache_root: Path | None = None,
) -> tuple[WatchlistStore, WatchlistReviewService]:
    store = WatchlistStore(root=tmp_path)
    service = WatchlistReviewService(
        store,
        screener=StubScreener(rows=rows, runs=runs, as_of_session=as_of_session),
        load_history=load_history or (lambda ticker: HISTORY),
        load_spy=load_spy or (lambda: SPY),
        load_earnings=load_earnings or (lambda ticker: EARNINGS),
        load_history_batch=load_history_batch,
        today=today if today is not None else FROZEN,
        expected_session=expected_session if expected_session is not None else FROZEN,
        cache_root=cache_root or (tmp_path / "eod_cache"),
    )
    return store, service


def test_review_ingest_new_on_master_old_stays_stalk(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[
            {"ticker": "OLD", "industry": "Software", "source_screens": "canslim_calibrated"},
            {"ticker": "NEW", "industry": "Software", "source_screens": "high_adr_hottest"},
        ],
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="OLD",
                    list="stalk",
                    added_at="2026-01-01",
                    source_screens=["ipo_this_year"],
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    by_ticker = {name.ticker: name for name in store.get().names}
    assert by_ticker["NEW"].list == "master"
    assert by_ticker["OLD"].list == "stalk"
    assert by_ticker["NEW"].queue_reason == "new_ingest"
    assert by_ticker["OLD"].source_screens == ["canslim_calibrated"]
    hist = by_ticker["OLD"].historical_source_screens
    assert "canslim_calibrated" in hist
    assert "ipo_this_year" in hist
    ordered = [sid for sid in BREAKOUT_SCREEN_IDS if sid in hist]
    leftovers = [sid for sid in hist if sid not in BREAKOUT_SCREEN_IDS]
    assert hist == ordered + leftovers


def test_queue_reason_first_match():
    assert queue_reason(
        readiness="disrupted", list_name="back", newly_ingested=True
    ) == "new_ingest"
    assert queue_reason(
        readiness="disrupted",
        list_name="master",
        newly_ingested=False,
        source_screens=[],
        historical_source_screens=["ipo_this_year"],
    ) == "dropped"
    assert queue_reason(
        readiness="disrupted",
        list_name="back",
        newly_ingested=False,
        source_screens=[],
        historical_source_screens=["ipo_this_year"],
    ) is None
    assert queue_reason(
        readiness="disrupted", list_name="back", newly_ingested=False
    ) is None
    assert queue_reason(
        readiness="disrupted", list_name="master", newly_ingested=False
    ) == "disrupted"
    assert queue_reason(
        readiness="excluded", list_name="master", newly_ingested=False
    ) == "excluded"
    assert queue_reason(
        readiness="excluded", list_name="back", newly_ingested=False
    ) is None
    assert queue_reason(
        readiness="unknown", list_name="master", newly_ingested=False
    ) == "score_failed"
    assert queue_reason(
        readiness="data_incomplete", list_name="master", newly_ingested=False
    ) == "data_incomplete"
    assert queue_reason(
        readiness="data_incomplete", list_name="back", newly_ingested=False
    ) is None
    assert queue_reason(
        readiness="chart_review_ready", list_name="focus", newly_ingested=False
    ) is None
    assert queue_reason(
        readiness="chart_review_ready", list_name="master", newly_ingested=False
    ) == "chart_review_ready"
    assert queue_reason(
        readiness="earnings_blocked", list_name="stalk", newly_ingested=False
    ) == "earnings_blocked"
    assert queue_reason(
        readiness="stalk_ready", list_name="master", newly_ingested=False
    ) == "stalk_ready"
    assert queue_reason(
        readiness="stalk_ready", list_name="stalk", newly_ingested=False
    ) is None


def test_review_move_during_score_keeps_list(tmp_path: Path):
    entered = threading.Event()
    release = threading.Event()

    def load_history(ticker: str):
        entered.set()
        release.wait(timeout=5)
        return CHART_HISTORY

    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history=load_history,
        load_spy=lambda: CHART_SPY,
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAA",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                )
            ],
        )
    )
    meta = service.start_review()
    assert entered.wait(timeout=2)
    store.move("AAA", "focus")
    release.set()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    aaa = next(name for name in store.get().names if name.ticker == "AAA")
    assert aaa.list == "focus"
    assert aaa.queue_reason is None
    assert aaa.last_scored_at is not None


def test_review_delete_during_score_drops_name(tmp_path: Path):
    entered = threading.Event()
    release = threading.Event()

    def load_history(ticker: str):
        entered.set()
        release.wait(timeout=5)
        return HISTORY

    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history=load_history,
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[Name(ticker="BBB", list="master", added_at="2026-01-01")],
        )
    )
    meta = service.start_review()
    assert entered.wait(timeout=2)
    assert any(name.ticker == "BBB" for name in store.get().names)
    store.delete("BBB")
    release.set()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    assert all(name.ticker != "BBB" for name in store.get().names)

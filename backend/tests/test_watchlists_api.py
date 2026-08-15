from __future__ import annotations

import threading
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.diary import router as diary_router
from backend.diary.store import DiaryStore
from backend.main import app
from backend.watchlists import router as watchlists_router
from backend.watchlists.review import WatchlistReviewService
from backend.watchlists.store import FunnelState, Name, WatchlistStore


def test_put_move_delete_round_trip(tmp_path: Path):
    previous = watchlists_router.get_store()
    watchlists_router.set_store(WatchlistStore(root=tmp_path))
    client = TestClient(app)
    try:
        put = client.put(
            "/api/watchlists/names",
            json={"ticker": "aapl", "list": "master"},
        )
        assert put.status_code == 200
        assert put.json()["ticker"] == "AAPL"

        get = client.get("/api/watchlists/")
        assert get.status_code == 200
        assert any(name["ticker"] == "AAPL" for name in get.json()["names"])

        moved = client.post(
            "/api/watchlists/names/AAPL/move",
            json={"list": "stalk"},
        )
        assert moved.status_code == 200
        assert moved.json()["list"] == "stalk"

        deleted = client.delete("/api/watchlists/names/AAPL")
        assert deleted.status_code == 204

        after = client.get("/api/watchlists/")
        assert after.status_code == 200
        assert after.json()["names"] == []
    finally:
        watchlists_router.set_store(previous)


def test_put_unknown_list_returns_400(tmp_path: Path):
    previous = watchlists_router.get_store()
    watchlists_router.set_store(WatchlistStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.put(
            "/api/watchlists/names",
            json={"ticker": "AAPL", "list": "nope"},
        )
        assert resp.status_code == 400
    finally:
        watchlists_router.set_store(previous)


def test_put_empty_ticker_returns_400(tmp_path: Path):
    previous = watchlists_router.get_store()
    watchlists_router.set_store(WatchlistStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.put(
            "/api/watchlists/names",
            json={"ticker": "  ", "list": "master"},
        )
        assert resp.status_code == 400
    finally:
        watchlists_router.set_store(previous)


def test_get_corrupt_returns_500(tmp_path: Path):
    previous = watchlists_router.get_store()
    watchlists_router.set_store(WatchlistStore(root=tmp_path))
    (tmp_path / "funnel.json").write_text("{not-json", encoding="utf-8")
    client = TestClient(app)
    try:
        resp = client.get("/api/watchlists/")
        assert resp.status_code == 500
        assert "corrupt funnel.json" in resp.json()["detail"]
    finally:
        watchlists_router.set_store(previous)


def test_diary_watchlists_still_empty_on_fresh_store(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/watchlists")
        assert resp.status_code == 200
        body = resp.json()
        assert body["focus"] == []
        assert body["stalk"] == []
    finally:
        diary_router.set_store(previous)


def _ohlcv(n: int = 70) -> pd.DataFrame:
    idx = pd.bdate_range("2026-01-02", periods=n)
    close = 100.0 + 0.5 * np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.04,
            "Low": close / 1.04,
            "Close": close,
            "Volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


class StubScreener:
    def __init__(self, rows=None, runs=None) -> None:
        self.rows = list(rows or [])
        self.runs = list(runs) if runs is not None else []

    def list_runs(self, strategy_id: str, *, days: int = 14) -> list[dict]:
        return list(self.runs)

    def load_results(self, strategy_id, run_id, view) -> tuple[dict, list[str], list[dict]]:
        return (
            {"run_id": run_id, "status": "completed"},
            ["ticker", "industry", "source_screens"],
            self.rows,
        )


def wait_review_api(client: TestClient, review_id: str, timeout: float = 2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/watchlists/reviews/{review_id}")
        if resp.status_code == 200 and resp.json()["status"] in ("completed", "failed"):
            return resp.json()
        time.sleep(0.02)
    raise AssertionError(f"review {review_id} did not finish")


def _install_review(tmp_path: Path, *, screener, load_history, load_spy, load_earnings):
    previous_store = watchlists_router.get_store()
    previous_review = watchlists_router.get_review_service()
    store = WatchlistStore(root=tmp_path)
    watchlists_router.set_store(store)
    watchlists_router.set_review_service(
        WatchlistReviewService(
            store,
            screener=screener,
            load_history=load_history,
            load_spy=load_spy,
            load_earnings=load_earnings,
        )
    )
    return previous_store, previous_review, store


def test_post_reviews_while_running_returns_409(tmp_path: Path):
    entered = threading.Event()
    release = threading.Event()

    def load_history(ticker: str):
        entered.set()
        release.wait(timeout=5)
        return _ohlcv()

    previous_store, previous_review, store = _install_review(
        tmp_path,
        screener=StubScreener(),
        load_history=load_history,
        load_spy=lambda: _ohlcv(),
        load_earnings=lambda ticker: date(2026, 8, 28),
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[Name(ticker="AAA", list="master", added_at="2026-01-01")],
        )
    )
    client = TestClient(app)
    try:
        first = client.post("/api/watchlists/reviews")
        assert first.status_code == 202
        assert entered.wait(timeout=2)
        second = client.post("/api/watchlists/reviews")
        assert second.status_code == 409
        release.set()
        wait_review_api(client, first.json()["review_id"])
    finally:
        release.set()
        watchlists_router.set_store(previous_store)
        watchlists_router.set_review_service(previous_review)


def test_post_reviews_no_completed_breakout_run(tmp_path: Path):
    history = _ohlcv()
    previous_store, previous_review, store = _install_review(
        tmp_path,
        screener=StubScreener(runs=[]),
        load_history=lambda ticker: history,
        load_spy=lambda: history,
        load_earnings=lambda ticker: date(2026, 8, 28),
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[Name(ticker="AAA", list="master", added_at="2026-01-01")],
        )
    )
    client = TestClient(app)
    try:
        started = client.post("/api/watchlists/reviews")
        assert started.status_code == 202
        done = wait_review_api(client, started.json()["review_id"])
        assert done["status"] == "completed"
        assert done["notes"] is not None and "no completed breakout run" in done["notes"]
        names = store.get().names
        assert len(names) == 1
        assert names[0].ticker == "AAA"
        assert names[0].list == "master"
        assert names[0].last_scored_at is not None
    finally:
        watchlists_router.set_store(previous_store)
        watchlists_router.set_review_service(previous_review)


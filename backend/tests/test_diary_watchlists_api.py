"""Watchlists API tests with network mocked."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.diary import router as diary_router
from backend.diary.store import DiaryStore
from backend.main import app


def _history(close: float = 100.0, prev: float = 98.0, low: float = 80.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [prev, close],
            "High": [close + 1, close + 2],
            "Low": [low, low + 1],
            "Close": [prev, close],
            "Volume": [1_000_000, 1_200_000],
        },
        index=pd.DatetimeIndex(["2026-08-07", "2026-08-08"]),
    )


def test_put_then_get_watchlists_round_trip(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        payload = {
            "focus": [{"ticker": "NVDA", "group": "semis", "note": "leader"}],
            "stalk": ["SMCI", "ARM"],
            "themes": [{"name": "AI", "tickers": ["NVDA", "MSFT"]}],
            "leadership": [{"name": "Mag7", "tickers": ["AAPL", "MSFT"]}],
        }
        put = client.put("/api/diary/watchlists", json=payload)
        assert put.status_code == 200
        put_body = put.json()
        assert put_body["focus"][0]["ticker"] == "NVDA"
        assert put_body["stalk"] == ["SMCI", "ARM"]
        assert put_body["themes"][0]["name"] == "AI"
        assert put_body["leadership"][0]["tickers"] == ["AAPL", "MSFT"]

        get = client.get("/api/diary/watchlists")
        assert get.status_code == 200
        assert get.json() == put_body
    finally:
        diary_router.set_store(previous)


def test_get_watchlists_empty_when_missing(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/watchlists")
        assert resp.status_code == 200
        body = resp.json()
        assert body["focus"] == []
        assert body["stalk"] == []
        assert body["themes"] == []
        assert body["leadership"] == []
    finally:
        diary_router.set_store(previous)


def test_enrich_watchlists_monkeypatched(tmp_path: Path, monkeypatch):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)

    def fake_load_history(symbol: str):
        if symbol == "BAD":
            raise ValueError("No data found for ticker: BAD")
        if symbol == "AAPL":
            return _history(close=110.0, prev=100.0, low=100.0)
        return _history(close=100.0, prev=98.0, low=80.0)

    monkeypatch.setattr(diary_router, "load_history", fake_load_history)
    try:
        resp = client.post(
            "/api/diary/watchlists/enrich",
            json={"tickers": ["aapl", "AAPL", "msft", "bad", "  "]},
        )
        assert resp.status_code == 200
        rows = resp.json()["rows"]
        assert [row["ticker"] for row in rows] == ["AAPL", "MSFT", "BAD"]
        assert rows[0]["error"] is None
        assert rows[0]["daily_change_pct"] == 10.0
        assert rows[0]["pct_from_52w_low"] == 10.0
        # mean of Close*Volume over available sessions: (100*1e6 + 110*1.2e6) / 2
        assert abs(rows[0]["avg_dollar_volume_20"] - 116_000_000.0) < 1e-6
        assert rows[1]["error"] is None
        assert rows[2]["error"] is not None
        assert "BAD" in rows[2]["error"]
        assert rows[2]["daily_change_pct"] is None
        assert rows[2]["pct_from_52w_low"] is None
        assert rows[2]["avg_dollar_volume_20"] is None
    finally:
        diary_router.set_store(previous)


def test_enrich_caps_at_50(tmp_path: Path, monkeypatch):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    calls: list[str] = []

    def fake_load_history(symbol: str):
        calls.append(symbol)
        return _history()

    monkeypatch.setattr(diary_router, "load_history", fake_load_history)
    try:
        tickers = [f"t{i}" for i in range(60)]
        resp = client.post(
            "/api/diary/watchlists/enrich",
            json={"tickers": tickers},
        )
        assert resp.status_code == 200
        rows = resp.json()["rows"]
        assert len(rows) == 50
        assert len(calls) == 50
        assert rows[0]["ticker"] == "T0"
        assert rows[-1]["ticker"] == "T49"
    finally:
        diary_router.set_store(previous)


def test_get_watchlists_corrupt_returns_500(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    (tmp_path / "watchlists.json").write_text("{not-json", encoding="utf-8")
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/watchlists")
        assert resp.status_code == 500
        assert "corrupt watchlists" in resp.json()["detail"]
    finally:
        diary_router.set_store(previous)

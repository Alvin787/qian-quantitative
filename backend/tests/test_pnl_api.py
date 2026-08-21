from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.pnl import router as pnl_router
from backend.pnl.store import PnlStore


def _client(tmp_path: Path) -> TestClient:
    pnl_router.set_store(PnlStore(root=tmp_path))
    return TestClient(app)


def test_create_get_update_delete_round_trip(tmp_path: Path):
    previous = pnl_router.get_store()
    client = _client(tmp_path)
    try:
        created = client.post(
            "/api/pnl/trades",
            json={
                "ticker": "rblx",
                "entry_date": "2026-07-29",
                "entry_price": 34.56,
                "shares": 100,
                "exit_date": "2026-08-04",
                "exit_price": 38.15,
                "account": "401k",
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert body["ticker"] == "RBLX"
        assert body["value"] == 3456.0
        assert body["pnl"] == 359.0
        assert body["percent"] == 10.39

        listing = client.get("/api/pnl/")
        assert listing.status_code == 200
        assert listing.json()["total_pnl"] == 359.0
        assert listing.json()["closed_count"] == 1

        trade_id = body["id"]
        updated = client.put(
            f"/api/pnl/trades/{trade_id}",
            json={
                "ticker": "RBLX",
                "entry_date": "2026-07-29",
                "entry_price": 34.56,
                "shares": 100,
                "notes": "closed early",
                "account": "401k",
            },
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "open"
        assert updated.json()["pnl"] is None

        deleted = client.delete(f"/api/pnl/trades/{trade_id}")
        assert deleted.status_code == 204
        after = client.get("/api/pnl/")
        assert after.json()["trades"] == []
    finally:
        pnl_router.set_store(previous)


def test_create_empty_ticker_returns_400(tmp_path: Path):
    previous = pnl_router.get_store()
    client = _client(tmp_path)
    try:
        resp = client.post(
            "/api/pnl/trades",
            json={
                "ticker": "  ",
                "entry_date": "2026-07-29",
                "entry_price": 10,
                "shares": 1,
            },
        )
        assert resp.status_code == 400
    finally:
        pnl_router.set_store(previous)


def test_update_missing_returns_404(tmp_path: Path):
    previous = pnl_router.get_store()
    client = _client(tmp_path)
    try:
        resp = client.put(
            "/api/pnl/trades/missing",
            json={
                "ticker": "AAPL",
                "entry_date": "2026-07-29",
                "entry_price": 10,
                "shares": 1,
            },
        )
        assert resp.status_code == 404
    finally:
        pnl_router.set_store(previous)


def test_get_corrupt_returns_500(tmp_path: Path):
    previous = pnl_router.get_store()
    client = _client(tmp_path)
    (tmp_path / "trades.json").write_text("{not-json", encoding="utf-8")
    try:
        resp = client.get("/api/pnl/")
        assert resp.status_code == 500
        assert "corrupt trades.json" in resp.json()["detail"]
    finally:
        pnl_router.set_store(previous)

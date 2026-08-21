from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.pnl.store import PnlStore


def test_missing_file_returns_empty_ledger(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    snapshot = store.snapshot()
    assert snapshot["trades"] == []
    assert snapshot["total_pnl"] == 0
    assert snapshot["open_count"] == 0
    assert snapshot["closed_count"] == 0
    assert snapshot["open_value"] == 0


def test_create_get_round_trip_persists_to_disk(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    created = store.create(
        ticker="rblx",
        entry_date="2026-07-29",
        entry_price=34.56,
        shares=100,
        exit_date="2026-08-04",
        exit_price=38.15,
        notes="took profits",
        account="401k",
    )
    assert created["ticker"] == "RBLX"
    assert created["pnl"] == 359.0
    assert created["percent"] == 10.39
    assert created["status"] == "closed"

    snapshot = store.snapshot()
    assert len(snapshot["trades"]) == 1
    assert snapshot["total_pnl"] == 359.0
    data = json.loads((tmp_path / "trades.json").read_text(encoding="utf-8"))
    assert data["trades"][0]["ticker"] == "RBLX"
    assert "pnl" not in data["trades"][0]


def test_same_ticker_can_appear_twice(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    first = store.create(
        ticker="AAPL",
        entry_date="2026-01-02",
        entry_price=100,
        shares=10,
    )
    second = store.create(
        ticker="AAPL",
        entry_date="2026-02-02",
        entry_price=110,
        shares=5,
    )
    assert first["id"] != second["id"]
    assert len(store.snapshot()["trades"]) == 2


def test_update_and_delete(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    created = store.create(
        ticker="LXEO",
        entry_date="2026-07-29",
        entry_price=4.24,
        shares=200,
        account="401k",
    )
    updated = store.update(
        created["id"],
        ticker="LXEO",
        entry_date="2026-07-29",
        entry_price=4.24,
        shares=200,
        exit_date="2026-08-15",
        exit_price=5.00,
        notes="closed",
        account="401k",
    )
    assert updated["status"] == "closed"
    assert updated["pnl"] == 152.0

    store.delete(created["id"])
    assert store.snapshot()["trades"] == []


def test_delete_missing_raises_keyerror(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.delete("missing")


def test_update_missing_raises_keyerror(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.update(
            "missing",
            ticker="AAPL",
            entry_date="2026-01-02",
            entry_price=10,
            shares=1,
        )


def test_empty_ticker_raises(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    with pytest.raises(ValueError, match="empty ticker"):
        store.create(
            ticker="  ",
            entry_date="2026-01-02",
            entry_price=10,
            shares=1,
        )


def test_exit_before_entry_raises(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    with pytest.raises(ValueError, match="exit_date"):
        store.create(
            ticker="AAPL",
            entry_date="2026-08-04",
            entry_price=10,
            shares=1,
            exit_date="2026-08-01",
            exit_price=11,
        )


def test_open_sorts_before_closed(tmp_path: Path):
    store = PnlStore(root=tmp_path)
    store.create(
        ticker="RBLX",
        entry_date="2026-07-29",
        entry_price=34.56,
        shares=100,
        exit_date="2026-08-04",
        exit_price=38.15,
    )
    store.create(
        ticker="LXEO",
        entry_date="2026-07-20",
        entry_price=4.24,
        shares=200,
    )
    tickers = [trade["ticker"] for trade in store.snapshot()["trades"]]
    assert tickers[0] == "LXEO"
    assert tickers[1] == "RBLX"


def test_corrupt_file_raises_valueerror(tmp_path: Path):
    (tmp_path / "trades.json").write_text("{not-json", encoding="utf-8")
    store = PnlStore(root=tmp_path)
    with pytest.raises(ValueError, match="corrupt trades.json"):
        store.snapshot()

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.watchlists.store import FunnelState, Name, WatchlistStore


def test_missing_file_returns_empty_names(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    state = store.get()
    assert state.names == []


def test_put_get_round_trip_persists_to_disk(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[Name(ticker="AAPL", list="master", added_at="2026-01-01")],
        )
    )
    loaded = store.get()
    assert loaded.names[0].ticker == "AAPL"
    assert loaded.names[0].list == "master"
    data = json.loads((tmp_path / "funnel.json").read_text(encoding="utf-8"))
    assert data["names"][0]["ticker"] == "AAPL"
    assert data["names"][0]["list"] == "master"


def test_upsert_existing_keeps_readiness(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAPL",
                    list="master",
                    added_at="2026-01-01",
                    readiness="watch",
                )
            ],
        )
    )
    updated = store.upsert("AAPL", "stalk", added_at="2026-08-14")
    assert updated.list == "stalk"
    assert updated.readiness == "watch"


def test_move_missing_raises_keyerror(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.move("AAPL", "stalk")


def test_delete_missing_raises_keyerror(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    with pytest.raises(KeyError):
        store.delete("AAPL")


def test_corrupt_file_raises_valueerror(tmp_path: Path):
    (tmp_path / "funnel.json").write_text("{not-json", encoding="utf-8")
    store = WatchlistStore(root=tmp_path)
    with pytest.raises(ValueError, match="corrupt funnel.json"):
        store.get()


def test_duplicate_tickers_last_wins_on_load(tmp_path: Path):
    (tmp_path / "funnel.json").write_text(
        json.dumps(
            {
                "updated_at": "2026-01-01T00:00:00+00:00",
                "names": [
                    {
                        "ticker": "AAPL",
                        "list": "master",
                        "added_at": "2026-01-01",
                        "note": "first",
                    },
                    {
                        "ticker": "AAPL",
                        "list": "stalk",
                        "added_at": "2026-01-02",
                        "note": "second",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    store = WatchlistStore(root=tmp_path)
    loaded = store.get()
    aapls = [name for name in loaded.names if name.ticker == "AAPL"]
    assert len(loaded.names) == 1
    assert len(aapls) == 1
    assert aapls[0].list == "stalk"
    assert aapls[0].note == "second"

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.watchlists.store import SCHEMA_VERSION, FunnelState, Name, WatchlistStore


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


def test_v3_focus_ready_upgrades_and_put_writes_v4_bak(tmp_path: Path):
    (tmp_path / "funnel.json").write_text(
        json.dumps(
            {
                "updated_at": "2026-01-01T00:00:00+00:00",
                "names": [
                    {
                        "ticker": "AAPL",
                        "list": "master",
                        "added_at": "2026-01-01",
                        "readiness": "focus_ready",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    store = WatchlistStore(root=tmp_path)
    loaded = store.get()
    assert loaded.names[0].readiness == "chart_review_ready"
    assert loaded.schema_version == 3
    store.put(loaded)
    data = json.loads((tmp_path / "funnel.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert SCHEMA_VERSION == 4
    assert (tmp_path / "funnel.json.bak").is_file()
    bak = json.loads((tmp_path / "funnel.json.bak").read_text(encoding="utf-8"))
    assert "schema_version" not in bak


def test_unknown_gate_key_ignored(tmp_path: Path):
    (tmp_path / "funnel.json").write_text(
        json.dumps(
            {
                "updated_at": "2026-01-01T00:00:00+00:00",
                "names": [
                    {
                        "ticker": "AAPL",
                        "list": "master",
                        "added_at": "2026-01-01",
                        "gates": {"adr_pct": 5.0, "not_a_real_gate": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    store = WatchlistStore(root=tmp_path)
    loaded = store.get()
    assert loaded.names[0].gates.adr_pct == 5.0


def test_move_to_focus_sets_and_preserves_manual_focus_approved_at(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    store.upsert("AAPL", "master", added_at="2026-01-01")
    name = store.get().names[0]
    assert name.manual_focus_approved_at is None

    moved = store.move("AAPL", "focus")
    assert moved.list == "focus"
    assert moved.manual_focus_approved_at is not None
    approved_time = moved.manual_focus_approved_at

    demoted = store.move("AAPL", "stalk")
    assert demoted.list == "stalk"
    assert demoted.manual_focus_approved_at == approved_time

    refocused = store.move("AAPL", "focus")
    assert refocused.list == "focus"
    assert refocused.manual_focus_approved_at == approved_time


def test_upsert_to_focus_sets_manual_focus_approved_at_and_checklist(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    created = store.upsert(
        "NVDA",
        "focus",
        added_at="2026-01-01",
        chart_checklist={"catalyst": True, "vcp": True},
    )
    assert created.list == "focus"
    assert created.manual_focus_approved_at is not None
    assert created.chart_checklist.catalyst is True
    assert created.chart_checklist.vcp is True
    assert created.chart_checklist.linearity is None


def test_update_checklist_updates_fields_and_raises_for_missing(tmp_path: Path):
    store = WatchlistStore(root=tmp_path)
    store.upsert("MSFT", "stalk", added_at="2026-01-01")

    updated = store.update_checklist("MSFT", {"pivot": True, "group_leader": False})
    assert updated.chart_checklist.pivot is True
    assert updated.chart_checklist.group_leader is False
    assert updated.chart_checklist.catalyst is None

    updated2 = store.update_checklist("MSFT", {"alert_set": True})
    assert updated2.chart_checklist.pivot is True
    assert updated2.chart_checklist.group_leader is False
    assert updated2.chart_checklist.alert_set is True

    with pytest.raises(KeyError):
        store.update_checklist("UNKNOWN", {"pivot": True})


def test_apply_review_preserves_checklist_and_focus_approved_at(tmp_path: Path):
    from backend.watchlists.store import ChartChecklist, ReviewMeta

    store = WatchlistStore(root=tmp_path)
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAPL",
                    list="focus",
                    added_at="2026-01-01",
                    readiness="watch",
                    chart_checklist=ChartChecklist(catalyst=True, vcp=True),
                    manual_focus_approved_at="2026-01-01T12:00:00+00:00",
                )
            ],
        )
    )

    scored_name = Name(
        ticker="AAPL",
        list="master",
        added_at="2026-01-01",
        readiness="chart_review_ready",
        note="from screener",
    )
    res = store.apply_review([scored_name], review=ReviewMeta(status="completed"))
    res_name = res.names[0]
    assert res_name.ticker == "AAPL"
    assert res_name.list == "focus"
    assert res_name.readiness == "chart_review_ready"
    assert res_name.chart_checklist.catalyst is True
    assert res_name.chart_checklist.vcp is True
    assert res_name.manual_focus_approved_at == "2026-01-01T12:00:00+00:00"


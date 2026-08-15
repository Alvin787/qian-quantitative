"""Unit tests for DiaryStore narrative persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.diary.store import (
    DiaryStore,
    FocusItem,
    NamedGroup,
    Watchlists,
)


def test_get_narrative_missing_returns_none(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    assert store.get_narrative("2026-08-08") is None


def test_put_then_get_round_trip(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    saved = store.put_narrative("2026-08-08", "Market looked mixed.")
    assert saved.date == "2026-08-08"
    assert saved.body == "Market looked mixed."
    assert saved.updated_at

    loaded = store.get_narrative("2026-08-08")
    assert loaded is not None
    assert loaded.date == saved.date
    assert loaded.body == saved.body
    assert loaded.updated_at == saved.updated_at

    path = tmp_path / "narrative_2026-08-08.json"
    assert path.is_file()


def test_put_overwrites_existing(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    store.put_narrative("2026-08-08", "first")
    second = store.put_narrative("2026-08-08", "second")
    loaded = store.get_narrative("2026-08-08")
    assert loaded is not None
    assert loaded.body == "second"
    assert loaded.updated_at == second.updated_at


def test_get_watchlists_missing_returns_empty(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    loaded = store.get_watchlists()
    assert loaded.focus == []
    assert loaded.stalk == []
    assert loaded.themes == []
    assert loaded.leadership == []


def test_put_then_get_watchlists_round_trip(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    payload = Watchlists(
        focus=[FocusItem(ticker="NVDA", group="semis", note="leader")],
        stalk=["SMCI", "ARM"],
        themes=[NamedGroup(name="AI", tickers=["NVDA", "MSFT"])],
        leadership=[NamedGroup(name="Mag7", tickers=["AAPL", "MSFT"])],
    )
    saved = store.put_watchlists(payload)
    assert saved.focus[0].ticker == "NVDA"
    assert saved.stalk == ["SMCI", "ARM"]

    loaded = store.get_watchlists()
    assert loaded.focus[0].ticker == "NVDA"
    assert loaded.focus[0].group == "semis"
    assert loaded.focus[0].note == "leader"
    assert loaded.stalk == ["SMCI", "ARM"]
    assert loaded.themes[0].name == "AI"
    assert loaded.themes[0].tickers == ["NVDA", "MSFT"]
    assert loaded.leadership[0].name == "Mag7"
    assert loaded.leadership[0].tickers == ["AAPL", "MSFT"]
    assert (tmp_path / "watchlists.json").is_file()


def test_corrupt_narrative_raises_value_error(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    path = tmp_path / "narrative_2026-08-08.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt narrative for 2026-08-08"):
        store.get_narrative("2026-08-08")


def test_corrupt_narrative_missing_fields_raises_value_error(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    path = tmp_path / "narrative_2026-08-08.json"
    path.write_text('{"date": "2026-08-08"}', encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt narrative for 2026-08-08"):
        store.get_narrative("2026-08-08")


def test_corrupt_watchlists_raises_value_error(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    (tmp_path / "watchlists.json").write_text('{"focus": "bad"}', encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt watchlists.json"):
        store.get_watchlists()


def test_corrupt_watchlists_non_object_raises_value_error(tmp_path: Path):
    store = DiaryStore(root=tmp_path)
    (tmp_path / "watchlists.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt watchlists.json"):
        store.get_watchlists()

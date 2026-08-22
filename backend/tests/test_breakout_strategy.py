"""Unit tests for the breakout universe strategy."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from backend.screener.finviz import ScrapeResult
from backend.screener.screens import get_screen
from backend.screener.strategies import list_strategies
from backend.screener.strategies.breakout import (
    run_breakout,
)

AS_OF = date(2026, 8, 14)


def _result(tickers: list[str], industries: dict[str, str] | None = None) -> ScrapeResult:
    unique = list(dict.fromkeys(tickers))
    return ScrapeResult(
        tickers=tickers,
        industries=industries or {},
        reported_total=len(unique),
        pages=1,
    )


def _patch_breakout(
    monkeypatch: pytest.MonkeyPatch,
    fake_scrape,
) -> None:
    monkeypatch.setattr(
        "backend.screener.strategies.breakout.scrape_finviz", fake_scrape
    )
    monkeypatch.setattr(
        "backend.screener.strategies.breakout.latest_completed_session",
        lambda: AS_OF,
    )


def test_breakout_first_in_registry():
    assert list_strategies()[0].id == "breakout"


def test_run_breakout_fails_closed_on_screen_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    failing = "high_adr_hottest"

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del max_pages, sleep_s, retries
        if url == get_screen(failing).url:
            raise RuntimeError("finviz down")
        return _result(["AAA"], {"AAA": "Software"})

    _patch_breakout(monkeypatch, fake_scrape)

    with pytest.raises(RuntimeError, match=failing):
        run_breakout(outdir=tmp_path, run_id="test-run", options={})

    assert not (tmp_path / "breakout_all_results_test-run.csv").exists()


def test_run_breakout_all_screens_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def always_fail(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del url, max_pages, sleep_s, retries
        raise RuntimeError("offline")

    _patch_breakout(monkeypatch, always_fail)
    with pytest.raises(RuntimeError, match="canslim_calibrated"):
        run_breakout(outdir=tmp_path, run_id="fail-run", options={})
    assert not (tmp_path / "breakout_all_results_fail-run.csv").exists()


def test_run_breakout_adaptive_1m_substitutes_when_broad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    baseline_1m = [f"T{i:03d}" for i in range(60)]
    tight_1m = [f"U{i:03d}" for i in range(10)]
    by_url = {
        get_screen("strongest_mover_1m").url: _result(baseline_1m),
        get_screen("strongest_mover_1m_strong_market").url: _result(tight_1m),
        get_screen("strongest_mover_1w").url: _result(["WEE"]),
    }

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del max_pages, sleep_s, retries
        if url in by_url:
            return by_url[url]
        return _result([])

    _patch_breakout(monkeypatch, fake_scrape)

    result = run_breakout(outdir=tmp_path, run_id="adapt-run", options={})
    path = tmp_path / "breakout_all_results_adapt-run.csv"
    assert path.exists()
    assert result.as_of_session == "2026-08-14"
    assert result.screen_manifest is not None
    assert isinstance(result.screen_manifest, list)
    expected_keys = {
        "screen_id",
        "url",
        "selected",
        "row_count",
        "reported_total",
        "pages",
        "error",
    }
    for entry in result.screen_manifest:
        assert set(entry.keys()) == expected_keys
        assert entry["error"] is None
        assert entry["url"].startswith("http")
        assert isinstance(entry["pages"], int)
        assert isinstance(entry["row_count"], int)
        assert isinstance(entry["reported_total"], int)

    by_id = {entry["screen_id"]: entry for entry in result.screen_manifest}
    assert by_id["strongest_mover_1m"]["selected"] is False
    assert by_id["strongest_mover_1m"]["row_count"] == 60
    assert by_id["strongest_mover_1m_strong_market"]["selected"] is True
    assert by_id["strongest_mover_1m_strong_market"]["row_count"] == 10
    assert by_id["strongest_mover_1w"]["selected"] is True
    assert "strongest_mover_1w_tight" not in by_id

    df = pd.read_csv(path)
    membership = df["source_screens"].fillna("").map(lambda s: str(s).split(";"))
    assert membership.map(lambda ids: "strongest_mover_1m_strong_market" in ids).any()
    assert not membership.map(lambda ids: "strongest_mover_1m" in ids).any()
    assert set(tight_1m).issubset(set(df["ticker"]))
    assert not set(baseline_1m).intersection(set(df["ticker"]))


def test_run_breakout_manifest_baseline_selected_omits_tight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    by_url = {
        get_screen("canslim_calibrated").url: _result(["AAA"], {"AAA": "Tech"}),
        get_screen("strongest_mover_1w").url: _result(["BBB"]),
        get_screen("strongest_mover_1m").url: _result(["CCC"]),
    }

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del max_pages, sleep_s, retries
        if url in by_url:
            return by_url[url]
        return _result([])

    _patch_breakout(monkeypatch, fake_scrape)

    result = run_breakout(outdir=tmp_path, run_id="clean-run", options={})
    assert result.screen_manifest is not None
    assert len(result.screen_manifest) == 11  # 9 always + 2 adaptive baselines

    by_id = {entry["screen_id"]: entry for entry in result.screen_manifest}
    assert "strongest_mover_1w_tight" not in by_id
    assert "strongest_mover_1m_strong_market" not in by_id
    assert by_id["strongest_mover_1w"]["selected"] is True
    assert by_id["strongest_mover_1w"]["row_count"] == 1
    assert by_id["strongest_mover_1m"]["selected"] is True
    assert by_id["canslim_calibrated"]["selected"] is True
    assert by_id["canslim_calibrated"]["row_count"] == 1


def test_momentum_family_count_is_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    by_url = {
        get_screen("strongest_mover_1w").url: _result(["MOM"]),
        get_screen("strongest_mover_1m").url: _result(["MOM"]),
        get_screen("strongest_mover_3m").url: _result(["MOM"]),
        get_screen("strongest_mover_6m").url: _result(["MOM"]),
    }

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del max_pages, sleep_s, retries
        if url in by_url:
            return by_url[url]
        return _result([])

    _patch_breakout(monkeypatch, fake_scrape)

    result = run_breakout(outdir=tmp_path, run_id="mom-run", options={})
    df = pd.read_csv(result.paths["all"])
    row = df[df["ticker"] == "MOM"].iloc[0]
    assert int(row["screen_family_count"]) == 1
    assert int(row["screen_count"]) == 4
    assert row["source_screens"] == (
        "strongest_mover_1w;strongest_mover_1m;strongest_mover_3m;strongest_mover_6m"
    )


def test_base_plus_momentum_family_count_is_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    by_url = {
        get_screen("extended_base_above_sma200").url: _result(["MIX"]),
        get_screen("strongest_mover_3m").url: _result(["MIX"]),
    }

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del max_pages, sleep_s, retries
        if url in by_url:
            return by_url[url]
        return _result([])

    _patch_breakout(monkeypatch, fake_scrape)

    result = run_breakout(outdir=tmp_path, run_id="mix-run", options={})
    df = pd.read_csv(result.paths["all"])
    row = df[df["ticker"] == "MIX"].iloc[0]
    assert int(row["screen_family_count"]) == 2
    assert int(row["screen_count"]) == 2
    assert row["source_screens"] == "extended_base_above_sma200;strongest_mover_3m"


def test_run_breakout_includes_leveraged_etfs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35, retries: int = 3):
        del url, max_pages, sleep_s, retries
        return _result([])

    _patch_breakout(monkeypatch, fake_scrape)

    result = run_breakout(outdir=tmp_path, run_id="etf-run", options={})
    df = pd.read_csv(result.paths["all"])
    assert "TQQQ" in set(df["ticker"])
    tqqq = df[df["ticker"] == "TQQQ"].iloc[0]
    assert "liquid_leveraged_etf" in str(tqqq["source_screens"]).split(";")
    assert tqqq["industry"] == "Exchange Traded Fund"
    assert int(tqqq["screen_family_count"]) == 1


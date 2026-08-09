"""Unit tests for the breakout universe strategy."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from backend.screener.finviz import ScrapeResult
from backend.screener.screens import get_screen
from backend.screener.strategies import list_strategies
from backend.screener.strategies.breakout import (
    BREAKOUT_SCREEN_IDS,
    run_breakout,
)


def test_breakout_first_in_registry():
    assert list_strategies()[0].id == "breakout"


def test_run_breakout_unions_dedupes_and_tolerates_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Overlapping tickers across screens; one empty industries; one raises.
    # AAA in screens 0, 1, 2  -> count 3
    # BBB in screens 0, 0(dup), 1 -> count 2 (dup within screen once)
    # CCC only in screen 1 with empty industries
    screen0 = BREAKOUT_SCREEN_IDS[0]
    screen1 = BREAKOUT_SCREEN_IDS[1]
    screen2 = BREAKOUT_SCREEN_IDS[2]
    failing = BREAKOUT_SCREEN_IDS[3]

    by_url: dict[str, ScrapeResult] = {
        get_screen(screen0).url: ScrapeResult(
            tickers=["AAA", "BBB", "BBB"],
            industries={"AAA": "Software", "BBB": "Biotech"},
        ),
        get_screen(screen1).url: ScrapeResult(
            tickers=["AAA", "BBB", "CCC"],
            industries={},  # empty industries map
        ),
        get_screen(screen2).url: ScrapeResult(
            tickers=["AAA"],
            industries={"AAA": "IgnoredSecond"},
        ),
    }

    def fake_scrape(url: str, *, max_pages: int = 20, sleep_s: float = 0.35):
        del max_pages, sleep_s
        if url == get_screen(failing).url:
            raise RuntimeError("finviz down")
        if url in by_url:
            return by_url[url]
        return ScrapeResult(tickers=[], industries={})

    monkeypatch.setattr(
        "backend.screener.strategies.breakout.scrape_finviz", fake_scrape
    )

    result = run_breakout(outdir=tmp_path, run_id="test-run", options={})

    path = tmp_path / "breakout_all_results_test-run.csv"
    assert path.exists()
    assert result.paths["all"] == path
    assert result.passed is None
    assert result.scored == 3
    assert failing in (result.notes or "")
    assert "finviz down" in (result.notes or "")

    df = pd.read_csv(path)
    assert list(df.columns) == [
        "ticker",
        "industry",
        "screen_count",
        "source_screens",
    ]

    aaa = df[df["ticker"] == "AAA"].iloc[0]
    assert int(aaa["screen_count"]) == 3
    assert aaa["source_screens"] == f"{screen0};{screen1};{screen2}"
    assert aaa["industry"] == "Software"  # first non-empty wins

    bbb = df[df["ticker"] == "BBB"].iloc[0]
    assert int(bbb["screen_count"]) == 2
    assert bbb["source_screens"] == f"{screen0};{screen1}"

    ccc = df[df["ticker"] == "CCC"].iloc[0]
    assert int(ccc["screen_count"]) == 1
    assert ccc["source_screens"] == screen1
    assert ccc["industry"] == "" or pd.isna(ccc["industry"])

    # sorted by screen_count desc, then ticker asc
    assert list(df["ticker"]) == ["AAA", "BBB", "CCC"]
    assert list(df["screen_count"]) == [3, 2, 1]


def test_run_breakout_all_screens_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def always_fail(url: str, *, max_pages: int = 20, sleep_s: float = 0.35):
        del url, max_pages, sleep_s
        raise RuntimeError("offline")

    monkeypatch.setattr(
        "backend.screener.strategies.breakout.scrape_finviz", always_fail
    )
    with pytest.raises(RuntimeError, match="All breakout screens failed"):
        run_breakout(outdir=tmp_path, run_id="fail-run", options={})

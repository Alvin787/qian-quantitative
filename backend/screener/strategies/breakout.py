"""Breakout universe strategy: union of Finviz breakout screens.

A full run scrapes 12 screens × up to 20 paged requests with the scraper's
built-in delay, so it typically takes roughly one to two minutes. That is why
runs are background jobs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.screener.finviz import scrape_finviz
from backend.screener.screens import get_screen
from backend.screener.strategies.base import StrategyDefinition, StrategyRunResult

BREAKOUT_SCREEN_IDS: tuple[str, ...] = (
    "canslim_calibrated",
    "high_adr_hottest",
    "high_adr_short_squeeze",
    "extended_base_above_sma200",
    "extended_base_below_sma200",
    "strongest_mover_1w",
    "strongest_mover_1m",
    "strongest_mover_1m_strong_market",
    "strongest_mover_3m",
    "strongest_mover_6m",
    "ipo_this_year",
    "high_short_float",
)


def run_breakout(*, outdir: Path, run_id: str, options: dict[str, Any]) -> StrategyRunResult:
    del options  # allowed_options is empty; router rejects unknown keys before this runs

    ticker_screens: dict[str, list[str]] = {}
    ticker_industry: dict[str, str] = {}
    failures: list[str] = []
    ok_count = 0

    for screen_id in BREAKOUT_SCREEN_IDS:
        screen = get_screen(screen_id)
        try:
            result = scrape_finviz(screen.url, max_pages=screen.max_pages)
        except Exception as exc:
            failures.append(f"{screen_id}: {exc}")
            continue

        ok_count += 1
        for ticker in result.tickers:
            screens = ticker_screens.setdefault(ticker, [])
            if screen_id not in screens:
                screens.append(screen_id)
            industry = result.industries.get(ticker, "")
            if ticker not in ticker_industry and industry:
                ticker_industry[ticker] = industry

    if ok_count == 0:
        raise RuntimeError(
            "All breakout screens failed: " + "; ".join(failures)
        )

    rows = []
    for ticker, source_ids in ticker_screens.items():
        ordered = [sid for sid in BREAKOUT_SCREEN_IDS if sid in source_ids]
        rows.append(
            {
                "ticker": ticker,
                "industry": ticker_industry.get(ticker, ""),
                "screen_count": len(ordered),
                "source_screens": ";".join(ordered),
            }
        )

    df = pd.DataFrame(
        rows, columns=["ticker", "industry", "screen_count", "source_screens"]
    )
    if not df.empty:
        df = df.sort_values(
            by=["screen_count", "ticker"], ascending=[False, True]
        ).reset_index(drop=True)

    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"breakout_all_results_{run_id}.csv"
    df.to_csv(path, index=False)

    notes = f"{ok_count}/{len(BREAKOUT_SCREEN_IDS)} screens scraped; {len(rows)} unique tickers"
    if failures:
        notes += f" | failed: {'; '.join(failures)}"

    return StrategyRunResult(
        run_id=run_id,
        paths={"all": path},
        scored=len(rows),
        passed=None,
        skipped=0,
        skipped_tickers=[],
        notes=notes,
        regime_ok=None,
    )


BREAKOUT = StrategyDefinition(
    id="breakout",
    label="Breakout",
    description="Union of the breakout Finviz screens. No scoring criteria yet — raw universe only.",
    screen_ids=BREAKOUT_SCREEN_IDS,
    views=("all",),
    view_files={"all": "breakout_all_results_{run_id}.csv"},
    meta_file="breakout_run_{run_id}.json",
    allowed_options=(),
    run=run_breakout,
    supports_legacy=False,
)

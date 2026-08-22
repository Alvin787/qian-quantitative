"""Breakout universe strategy: union of Finviz breakout screens.

A full run scrapes 12 screens × up to 20 paged requests with the scraper's
built-in delay, so it typically takes roughly one to two minutes. That is why
runs are background jobs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.marketdata.calendar import latest_completed_session
from backend.screener.finviz import ScrapeResult, scrape_finviz
from backend.screener.leveraged_etfs import LIQUID_LEVERAGED_ETFS
from backend.screener.screens import get_screen, screen_family_count
from backend.screener.strategies.base import StrategyDefinition, StrategyRunResult

BREADTH_CEILING = 60  # selected adaptive variant must have len(tickers) < 60

BREAKOUT_SCREEN_IDS: tuple[str, ...] = (
    "canslim_calibrated",
    "high_adr_hottest",
    "high_adr_short_squeeze",
    "extended_base_above_sma200",
    "extended_base_below_sma200",
    "strongest_mover_1w",
    "strongest_mover_1w_tight",
    "strongest_mover_1m",
    "strongest_mover_1m_strong_market",
    "strongest_mover_3m",
    "strongest_mover_6m",
    "ipo_this_year",
    "high_short_float",
    "liquid_leveraged_etf",
)

ALWAYS_SCREEN_IDS: tuple[str, ...] = (
    "canslim_calibrated",
    "high_adr_hottest",
    "high_adr_short_squeeze",
    "extended_base_above_sma200",
    "extended_base_below_sma200",
    "strongest_mover_3m",
    "strongest_mover_6m",
    "ipo_this_year",
    "high_short_float",
)

ADAPTIVE_PAIRS: tuple[tuple[str, str], ...] = (
    ("strongest_mover_1w", "strongest_mover_1w_tight"),
    ("strongest_mover_1m", "strongest_mover_1m_strong_market"),
)


def _record_membership(
    ticker_screens: dict[str, list[str]],
    ticker_industry: dict[str, str],
    screen_id: str,
    result: ScrapeResult,
) -> None:
    for ticker in result.tickers:
        screens = ticker_screens.setdefault(ticker, [])
        if screen_id not in screens:
            screens.append(screen_id)
        industry = result.industries.get(ticker, "")
        if ticker not in ticker_industry and industry:
            ticker_industry[ticker] = industry


def _scrape_screen(screen_id: str) -> ScrapeResult:
    screen = get_screen(screen_id)
    try:
        return scrape_finviz(screen.url, max_pages=screen.max_pages)
    except Exception as exc:
        raise RuntimeError(f"{screen_id}: {exc}") from exc


def run_breakout(*, outdir: Path, run_id: str, options: dict[str, Any]) -> StrategyRunResult:
    del options  # allowed_options is empty; router rejects unknown keys before this runs

    as_of = latest_completed_session()
    ticker_screens: dict[str, list[str]] = {}
    ticker_industry: dict[str, str] = {}
    selected: list[str] = []
    manifest: list[dict[str, Any]] = []

    for screen_id in ALWAYS_SCREEN_IDS:
        result = _scrape_screen(screen_id)
        _record_membership(ticker_screens, ticker_industry, screen_id, result)
        selected.append(screen_id)
        manifest.append(
            {
                "screen_id": screen_id,
                "url": get_screen(screen_id).url,
                "selected": True,
                "row_count": len(result.tickers),
                "reported_total": result.reported_total or len(result.tickers),
                "pages": result.pages,
                "error": None,
            }
        )

    for baseline, tight in ADAPTIVE_PAIRS:
        baseline_result = _scrape_screen(baseline)
        if len(baseline_result.tickers) < BREADTH_CEILING:
            _record_membership(ticker_screens, ticker_industry, baseline, baseline_result)
            selected.append(baseline)
            manifest.append(
                {
                    "screen_id": baseline,
                    "url": get_screen(baseline).url,
                    "selected": True,
                    "row_count": len(baseline_result.tickers),
                    "reported_total": baseline_result.reported_total or len(baseline_result.tickers),
                    "pages": baseline_result.pages,
                    "error": None,
                }
            )
        else:
            manifest.append(
                {
                    "screen_id": baseline,
                    "url": get_screen(baseline).url,
                    "selected": False,
                    "row_count": len(baseline_result.tickers),
                    "reported_total": baseline_result.reported_total or len(baseline_result.tickers),
                    "pages": baseline_result.pages,
                    "error": None,
                }
            )
            tight_result = _scrape_screen(tight)
            if len(tight_result.tickers) < BREADTH_CEILING:
                _record_membership(ticker_screens, ticker_industry, tight, tight_result)
                selected.append(tight)
                manifest.append(
                    {
                        "screen_id": tight,
                        "url": get_screen(tight).url,
                        "selected": True,
                        "row_count": len(tight_result.tickers),
                        "reported_total": tight_result.reported_total or len(tight_result.tickers),
                        "pages": tight_result.pages,
                        "error": None,
                    }
                )
            else:
                raise RuntimeError(
                    f"{baseline}/{tight} exceed breadth ceiling: "
                    f"{len(baseline_result.tickers)}/{len(tight_result.tickers)}"
                )

    for ticker in LIQUID_LEVERAGED_ETFS:
        screens = ticker_screens.setdefault(ticker, [])
        if "liquid_leveraged_etf" not in screens:
            screens.append("liquid_leveraged_etf")
        if ticker not in ticker_industry or not ticker_industry[ticker]:
            ticker_industry[ticker] = "Exchange Traded Fund"

    if not ticker_screens:
        raise RuntimeError("Breakout universe is empty")

    rows = []
    for ticker, source_ids in ticker_screens.items():
        ordered = [sid for sid in BREAKOUT_SCREEN_IDS if sid in source_ids]
        rows.append(
            {
                "ticker": ticker,
                "industry": ticker_industry.get(ticker, ""),
                "screen_count": len(ordered),
                "screen_family_count": screen_family_count(ordered),
                "source_screens": ";".join(ordered),
            }
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "ticker",
            "industry",
            "screen_count",
            "screen_family_count",
            "source_screens",
        ],
    )
    df = df.sort_values(
        by=["screen_family_count", "screen_count", "ticker"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"breakout_all_results_{run_id}.csv"
    df.to_csv(path, index=False)

    notes = f"{len(selected)} screens scraped; {len(rows)} unique tickers"

    return StrategyRunResult(
        run_id=run_id,
        paths={"all": path},
        scored=len(rows),
        passed=None,
        skipped=0,
        skipped_tickers=[],
        notes=notes,
        regime_ok=None,
        as_of_session=as_of.isoformat(),
        screen_manifest=manifest,
    )


BREAKOUT = StrategyDefinition(
    id="breakout",
    label="Breakout",
    description="Post-close Finviz universe with adaptive strong-movers, independent screen families, and fail-closed snapshots.",
    screen_ids=BREAKOUT_SCREEN_IDS,
    views=("all",),
    view_files={"all": "breakout_all_results_{run_id}.csv"},
    meta_file="breakout_run_{run_id}.json",
    allowed_options=(),
    run=run_breakout,
    supports_legacy=False,
)

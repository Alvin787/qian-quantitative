"""Finviz new-high / new-low count helpers for diary breadth."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.screener.finviz import fetch_html

_TOTAL_RE = re.compile(r"#(\d+)\s*/\s*(\d+)")

_NEWHIGH_URL = "https://finviz.com/screener.ashx?v=111&s=ta_newhigh"
_NEWLOW_URL = "https://finviz.com/screener.ashx?v=111&s=ta_newlow"


@dataclass(frozen=True)
class FinvizCount:
    label: str
    count: int
    url: str


def screener_total(url: str) -> int:
    """
    fetch_html from backend.screener.finviz; parse first (#a / #b) with the same
    total_re as scrape_finviz; return int(b). Raise RuntimeError if none.
    """
    html = fetch_html(url)
    match = _TOTAL_RE.search(html)
    if not match:
        raise RuntimeError(f"finviz screener total not found for {url}")
    return int(match.group(2))


def new_high_low_counts() -> tuple[FinvizCount, FinvizCount]:
    """
    Highs: https://finviz.com/screener.ashx?v=111&s=ta_newhigh
    Lows:  https://finviz.com/screener.ashx?v=111&s=ta_newlow
    """
    highs = screener_total(_NEWHIGH_URL)
    lows = screener_total(_NEWLOW_URL)
    return (
        FinvizCount(label="new_highs", count=highs, url=_NEWHIGH_URL),
        FinvizCount(label="new_lows", count=lows, url=_NEWLOW_URL),
    )

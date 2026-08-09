from __future__ import annotations

import html as html_lib
import re
import time
import urllib.request
from dataclasses import dataclass

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class ScrapeResult:
    tickers: list[str]                 # de-duplicated, in Finviz order
    industries: dict[str, str]         # ticker -> industry string; may be empty


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def scrape_finviz(
    url: str,
    *,
    sleep_s: float = 0.35,
    max_pages: int = 20,
) -> ScrapeResult:
    """Paginate Finviz screener (&r=1,21,41,...) and return unique tickers."""
    base = re.sub(r"&r=\d+", "", url)
    ticker_re = re.compile(r'data-boxover-ticker="([A-Z0-9.\-]+)"')
    industry_re = re.compile(
        r'data-boxover-ticker="([A-Z0-9.\-]+)"[^>]*data-boxover-industry="([^"]*)"',
        re.I,
    )
    total_re = re.compile(r"#(\d+)\s*/\s*(\d+)")

    tickers: list[str] = []
    industries: dict[str, str] = {}
    reported_total: int | None = None

    for start in range(1, max_pages * 20 + 1, 20):
        page_url = f"{base}&r={start}"
        html = fetch_html(page_url)

        page = ticker_re.findall(html)
        seen_page: set[str] = set()
        unique_page: list[str] = []
        for t in page:
            if t not in seen_page:
                seen_page.add(t)
                unique_page.append(t)

        for m in industry_re.finditer(html):
            industries[m.group(1)] = html_lib.unescape(m.group(2))

        totals = total_re.findall(html)
        if totals:
            reported_total = max(int(b) for _, b in totals)

        if not unique_page:
            break

        for t in unique_page:
            if t not in tickers:
                tickers.append(t)

        print(f"  Finviz page r={start}: {len(unique_page)} names "
              f"(running total {len(tickers)}"
              + (f" / {reported_total}" if reported_total else "")
              + ")")

        if reported_total and len(tickers) >= reported_total:
            break
        time.sleep(sleep_s)

    return ScrapeResult(tickers=tickers, industries=industries)

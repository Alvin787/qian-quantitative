from __future__ import annotations

import html as html_lib
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class FinvizScrapeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScrapeResult:
    tickers: list[str]                 # de-duplicated, in Finviz order
    industries: dict[str, str]         # ticker -> industry string; may be empty
    reported_total: int | None = None
    pages: int = 0


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
    retries: int = 3,
) -> ScrapeResult:
    """Paginate Finviz screener (&r=1,21,41,...) and return unique tickers."""
    base = re.sub(r"&r=\d+", "", url)
    ticker_re = re.compile(r"""data-boxover-ticker=['"]([A-Z0-9.\-]+)['"]""")
    industry_re = re.compile(r"""data-boxover-industry=['"]([^'"]*)['"]""", re.I)
    tag_re = re.compile(r"<[^>]+>")
    total_re = re.compile(r"#(\d+)\s*/\s*(\d+)")

    tickers: list[str] = []
    industries: dict[str, str] = {}
    reported_total: int | None = None
    pages = 0

    def fetch_page(page_url: str) -> str:
        last_exc: BaseException | None = None
        for attempt in range(retries):
            try:
                return fetch_html(page_url)
            except (OSError, urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                if attempt >= retries - 1:
                    raise
                time.sleep(0.5 * (2 ** attempt))
        raise last_exc  # pragma: no cover

    for start in range(1, max_pages * 20 + 1, 20):
        page_url = f"{base}&r={start}"
        html = fetch_page(page_url)
        pages += 1

        page = ticker_re.findall(html)
        seen_page: set[str] = set()
        unique_page: list[str] = []
        for t in page:
            if t not in seen_page:
                seen_page.add(t)
                unique_page.append(t)

        for tag in tag_re.findall(html):
            ticker_m = ticker_re.search(tag)
            industry_m = industry_re.search(tag)
            if ticker_m and industry_m:
                industries[ticker_m.group(1)] = html_lib.unescape(industry_m.group(1))

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
        if sleep_s:
            time.sleep(sleep_s)

    if reported_total is None:
        raise FinvizScrapeError("missing Finviz result total")
    if reported_total == 0:
        return ScrapeResult(
            tickers=[],
            industries={},
            reported_total=0,
            pages=pages,
        )
    if len(tickers) != reported_total:
        raise FinvizScrapeError("Finviz total mismatch")

    return ScrapeResult(
        tickers=tickers,
        industries=industries,
        reported_total=reported_total,
        pages=pages,
    )

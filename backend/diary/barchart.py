"""Barchart quote and history helpers for diary breadth."""

from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from backend.screener.finviz import USER_AGENT

_QUOTE_PAGE = "https://www.barchart.com/stocks/quotes/$MMTW"
_QUOTES_URL = "https://www.barchart.com/proxies/core-api/v1/quotes/get"
_HISTORY_URL = "https://www.barchart.com/proxies/core-api/v1/historical/get"


@dataclass(frozen=True)
class BarchartQuote:
    symbol: str
    last: float


@dataclass(frozen=True)
class BarchartHistoryPoint:
    date: str  # YYYY-MM-DD
    last: float


def _open_session() -> tuple[urllib.request.OpenerDirector, str]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        _QUOTE_PAGE,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with opener.open(req, timeout=30) as resp:
            resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"barchart session failed: {exc}") from exc

    xsrf: str | None = None
    for cookie in jar:
        if cookie.name == "XSRF-TOKEN":
            xsrf = urllib.parse.unquote(urllib.parse.unquote(cookie.value))
            break
    if not xsrf:
        raise RuntimeError("barchart session missing XSRF-TOKEN cookie")
    return opener, xsrf


def _api_get(
    opener: urllib.request.OpenerDirector,
    xsrf: str,
    url: str,
    params: dict[str, str],
) -> dict:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        full,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "X-XSRF-TOKEN": xsrf,
        },
    )
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"barchart request failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"barchart parse failed: {exc}") from exc


def fetch_quotes(symbols: list[str]) -> dict[str, BarchartQuote]:
    """
    Session: GET https://www.barchart.com/stocks/quotes/$MMTW with USER_AGENT
    (reuse backend.screener.finviz.USER_AGENT), collect cookies, set header
    X-XSRF-TOKEN to urllib.parse.unquote(unquote(cookie XSRF-TOKEN)).
    Then GET https://www.barchart.com/proxies/core-api/v1/quotes/get
    with symbols joined by comma and fields=symbol,lastPrice.
    Missing/invalid symbols omitted. On HTTP/parse failure raise RuntimeError.
    """
    if not symbols:
        return {}
    opener, xsrf = _open_session()
    payload = _api_get(
        opener,
        xsrf,
        _QUOTES_URL,
        {
            "symbols": ",".join(symbols),
            "fields": "symbol,lastPrice",
        },
    )
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("barchart quotes missing data list")

    out: dict[str, BarchartQuote] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = row.get("symbol")
        last_raw = row.get("lastPrice")
        if not isinstance(symbol, str) or symbol == "":
            continue
        try:
            last = float(last_raw)
        except (TypeError, ValueError):
            continue
        out[symbol] = BarchartQuote(symbol=symbol, last=last)
    return out


def _to_iso_date(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Unix epoch seconds (or ms)
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[: len(fmt) + 2], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Truncate ISO-like prefixes
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return None


def fetch_history(symbol: str, *, limit: int = 5) -> list[BarchartHistoryPoint]:
    """
    Same cookie session pattern. GET
    https://www.barchart.com/proxies/core-api/v1/historical/get
    with symbol, fields=tradeTime.format(m/d/Y),lastPrice, type=eod,
    orderBy=tradeTime, orderDir=desc, limit, raw=1.
    Prefer raw.tradeTime / raw.lastPrice when present.
    Return chronological ascending (oldest first) of length <= limit.
    """
    opener, xsrf = _open_session()
    payload = _api_get(
        opener,
        xsrf,
        _HISTORY_URL,
        {
            "symbol": symbol,
            "fields": "tradeTime.format(m/d/Y),lastPrice",
            "type": "eod",
            "orderBy": "tradeTime",
            "orderDir": "desc",
            "limit": str(limit),
            "raw": "1",
        },
    )
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("barchart history missing data list")

    points: list[BarchartHistoryPoint] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        trade_time = raw.get("tradeTime") if "tradeTime" in raw else row.get("tradeTime")
        last_raw = raw.get("lastPrice") if "lastPrice" in raw else row.get("lastPrice")
        date = _to_iso_date(trade_time)
        if date is None:
            continue
        try:
            last = float(last_raw)
        except (TypeError, ValueError):
            continue
        points.append(BarchartHistoryPoint(date=date, last=last))
        if len(points) >= limit:
            break

    points.reverse()  # API returns desc; return ascending
    return points

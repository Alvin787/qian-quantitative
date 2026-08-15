from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf


@dataclass(frozen=True)
class EtfRow:
    symbol: str
    last: float
    daily_change_pct: float
    pct_from_52w_low: float
    pct_from_52w_high: float
    short_term_trend: str  # deterministic label from MA rules below
    priority: bool = False
    ratio_to: str | None = None
    ratio_value: float | None = None


def short_term_trend_label(close: float, sma20: float, sma50: float, sma200: float) -> str:
    """
    Precedence (first match wins):
    1. close >= sma20 and sma20 >= sma50 and sma50 >= sma200 -> "Up, Above All MA"
    2. close >= sma20 and close >= sma50 -> "Up, Above 20 & 50-MA"
    3. close >= sma20 -> "Up, Above 20-MA"
    4. close < sma20 and close >= sma50 -> "Down, Above 50-MA"
    5. else -> "Down, Below 20-MA"
    """
    if close >= sma20 and sma20 >= sma50 and sma50 >= sma200:
        return "Up, Above All MA"
    if close >= sma20 and close >= sma50:
        return "Up, Above 20 & 50-MA"
    if close >= sma20:
        return "Up, Above 20-MA"
    if close < sma20 and close >= sma50:
        return "Down, Above 50-MA"
    return "Down, Below 20-MA"


def build_etf_row(symbol: str, history, *, priority: bool = False) -> EtfRow:
    """
    `history` is a pandas.DataFrame with columns Open/High/Low/Close/Volume and
    DatetimeIndex, newest last, covering >= 252 sessions when available.
    Uses last two Close for daily_change_pct.
    52w low/high = min(Low)/max(High) over available history capped at last 252 rows.
    SMAs = trailing means of Close for 20/50/200 (if len insufficient for 200, still
    compute shorter MAs; if sma200 cannot be computed, treat sma200 as sma50 for labeling only).
    """
    window = history.tail(252)
    closes = window["Close"]
    lows = window["Low"]
    highs = window["High"]

    last = float(closes.iloc[-1])
    if len(closes) >= 2:
        prev = float(closes.iloc[-2])
        daily_change_pct = ((last - prev) / prev) * 100.0 if prev != 0 else 0.0
    else:
        daily_change_pct = 0.0

    low_52w = float(lows.min())
    high_52w = float(highs.max())
    pct_from_52w_low = ((last - low_52w) / low_52w) * 100.0 if low_52w != 0 else 0.0
    pct_from_52w_high = ((last - high_52w) / high_52w) * 100.0 if high_52w != 0 else 0.0

    n = len(closes)
    sma20 = float(closes.tail(20).mean()) if n >= 20 else last
    sma50 = float(closes.tail(50).mean()) if n >= 50 else sma20
    if n >= 200:
        sma200 = float(closes.tail(200).mean())
    else:
        sma200 = sma50

    trend = short_term_trend_label(last, sma20, sma50, sma200)

    return EtfRow(
        symbol=symbol,
        last=last,
        daily_change_pct=daily_change_pct,
        pct_from_52w_low=pct_from_52w_low,
        pct_from_52w_high=pct_from_52w_high,
        short_term_trend=trend,
        priority=priority,
    )


def avg_dollar_volume_20(history) -> float:
    """Mean of (Close * Volume) over the last 20 sessions (or fewer if shorter)."""
    window = history.tail(20)
    dollar_volume = window["Close"] * window["Volume"]
    return float(dollar_volume.mean())


def load_history(symbol: str):
    """yfinance download; raise ValueError if empty."""
    df = yf.Ticker(symbol).history(period="1y")
    if df.empty:
        raise ValueError(f"No data found for ticker: {symbol}")
    return df

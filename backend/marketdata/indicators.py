from __future__ import annotations

import pandas as pd

ADR_WINDOW = 20
ATR_PERIOD = 14


def adr_pct(high: pd.Series, low: pd.Series, close: pd.Series, *, window: int = ADR_WINDOW) -> float | None:
    """(mean(high[-window:]) - mean(low[-window:])) / close[-1] * 100. None if < window bars or close<=0."""
    if len(high) < window or len(low) < window or len(close) < window:
        return None
    last_close = float(close.iloc[-1])
    if last_close <= 0:
        return None
    return (float(high.iloc[-window:].mean()) - float(low.iloc[-window:].mean())) / last_close * 100.0


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """TR[0] = high[0]-low[0]; else max(h-l, abs(h-prev_c), abs(l-prev_c)). Aligned to close.index."""
    high_a = high.reindex(close.index).astype(float)
    low_a = low.reindex(close.index).astype(float)
    close_a = close.astype(float)
    prev_close = close_a.shift(1)
    tr = pd.concat(
        [
            high_a - low_a,
            (high_a - prev_close).abs(),
            (low_a - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    if len(tr) > 0:
        tr.iloc[0] = float(high_a.iloc[0] - low_a.iloc[0])
    tr.index = close.index
    return tr


def wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series, *, period: int = ATR_PERIOD) -> pd.Series:
    """Seed ATR at iloc[period-1] = mean(TR.iloc[:period]); then (prev*(period-1)+TR)/period. Earlier rows NaN."""
    tr = true_range(high, low, close)
    atr = pd.Series(float("nan"), index=close.index, dtype=float)
    if len(tr) < period:
        return atr
    atr.iloc[period - 1] = float(tr.iloc[:period].mean())
    for i in range(period, len(tr)):
        atr.iloc[i] = (float(atr.iloc[i - 1]) * (period - 1) + float(tr.iloc[i])) / period
    return atr


def atr_pct(high: pd.Series, low: pd.Series, close: pd.Series, *, period: int = ATR_PERIOD) -> float | None:
    """Last Wilder ATR / last close * 100. None if ATR or close missing/<=0."""
    if close.empty:
        return None
    last_close = float(close.iloc[-1])
    if last_close <= 0:
        return None
    atr = wilder_atr(high, low, close, period=period)
    if atr.empty:
        return None
    last_atr = atr.iloc[-1]
    if last_atr is None or bool(pd.isna(last_atr)):
        return None
    last_atr_f = float(last_atr)
    if last_atr_f <= 0:
        return None
    return last_atr_f / last_close * 100.0


def ma_extension_x(*, close: float, sma: float, atr_pct_value: float) -> float | None:
    """((close/sma - 1)*100) / atr_pct_value. None if sma<=0 or atr_pct_value<=0."""
    if sma <= 0 or atr_pct_value <= 0:
        return None
    return ((close / sma - 1.0) * 100.0) / atr_pct_value

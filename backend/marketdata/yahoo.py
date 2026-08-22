from __future__ import annotations

import pandas as pd

_OHLCV = ("Open", "High", "Low", "Close", "Volume")


def yahoo_symbol(ticker: str) -> str:
    """Uppercase stripped; replace '.' with '-' (BRK.B -> BRK-B). Do not change other characters."""
    return ticker.strip().upper().replace(".", "-")


def _ohlcv_frame(frame: pd.DataFrame) -> pd.DataFrame | None:
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    if any(col not in frame.columns for col in _OHLCV):
        return None
    out = frame.loc[:, list(_OHLCV)].copy()
    if out.empty or out.isna().all().all() or any(out[col].isna().all() for col in _OHLCV):
        return None
    return out


def frames_from_yf_download(data: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    """
    Split a yf.download result into ticker -> OHLCV (Open,High,Low,Close,Volume).
    Missing ticker or empty/NaN frame: omit the key (caller fail-closes).
    Do not call yfinance here.
    """
    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        return {}
    out: dict[str, pd.DataFrame] = {}
    if isinstance(data.columns, pd.MultiIndex):
        level0 = set(data.columns.get_level_values(0))
        for ticker in tickers:
            if ticker not in level0:
                continue
            extracted = _ohlcv_frame(data[ticker])
            if extracted is not None:
                out[ticker] = extracted
        return out
    if len(tickers) == 1:
        extracted = _ohlcv_frame(data)
        if extracted is not None:
            out[tickers[0]] = extracted
    return out

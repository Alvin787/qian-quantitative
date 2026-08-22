from __future__ import annotations

import pandas as pd

from backend.marketdata.indicators import adr_pct, atr_pct, ma_extension_x, wilder_atr


def test_adr_pct_swing_data_formula():
    high = pd.Series([12.0] * 20)
    low = pd.Series([10.0] * 20)
    close = pd.Series([20.0] * 20)
    assert adr_pct(high, low, close) == 10.0


def test_ma_extension_uses_atr_not_adr():
    n = 30
    close = pd.Series(100.0 + 10.0 * pd.RangeIndex(n).astype(float))
    high = close + 1.0
    low = close - 1.0
    adr_value = adr_pct(high, low, close)
    atr_value = atr_pct(high, low, close)
    assert adr_value is not None
    assert atr_value is not None
    assert adr_value != atr_value
    close_last = float(close.iloc[-1])
    sma = 100.0
    ext = ma_extension_x(close=close_last, sma=sma, atr_pct_value=atr_value)
    pct_above = (close_last / sma - 1.0) * 100.0
    assert ext == pct_above / atr_value
    assert ext != pct_above / adr_value


def test_wilder_atr_seed_identical_trs():
    rows = [{"High": 2.0, "Low": 1.0, "Close": 1.5}]
    close_px = 1.5
    for _ in range(14):
        rows.append({"High": close_px + 0.5, "Low": close_px - 0.5, "Close": close_px})
    frame = pd.DataFrame(rows)
    atr = wilder_atr(frame["High"], frame["Low"], frame["Close"])
    assert float(atr.iloc[-1]) == 1.0

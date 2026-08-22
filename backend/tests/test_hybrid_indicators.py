from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from backend.marketdata.calendar import latest_completed_session, sessions_before_earnings
from backend.marketdata.indicators import adr_pct, atr_pct, ma_extension_x
from backend.screener.hybrid_screener import (
    Row,
    annotate_earnings,
    compute_regime,
    compute_row,
)


def _make_synth_bars(n: int = 260) -> pd.DataFrame:
    """Build a steady upward trending DataFrame where ADR% != ATR%."""
    dates = pd.date_range(end="2026-08-21", periods=n, freq="B")
    # Base price rising steadily
    t = np.arange(n)
    # Slow compounding trend
    close_vals = 50.0 * (1.0025 ** t)
    # Add a slight dip at the very end so price is close to SMA20 (within 2%)
    close_vals[-1] = close_vals[-2] * 0.995

    close = pd.Series(close_vals, index=dates)
    # Give high and low daily ranges around ~3%
    # Introduce small gaps on some days so True Range differs from High - Low
    high = close * 1.018
    low = close * 0.982
    open_p = close * 0.995
    volume = pd.Series(1_000_000.0, index=dates)

    # Introduce a gap on bar -10 to create a notable difference between ADR and ATR
    high.iloc[-10] = close.iloc[-11] * 1.04
    low.iloc[-10] = close.iloc[-11] * 1.01
    close.iloc[-10] = close.iloc[-11] * 1.03

    df = pd.DataFrame(
        {
            "Open": open_p,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
    return df


def test_compute_row_extension_uses_atr_and_differs_from_adr():
    df = _make_synth_bars(260)
    c = float(df["Close"].iloc[-1])
    s50 = float(df["Close"].rolling(50).mean().iloc[-1])
    s20 = float(df["Close"].rolling(20).mean().iloc[-1])

    adr_val = adr_pct(high=df["High"], low=df["Low"], close=df["Close"])
    atr_val = atr_pct(high=df["High"], low=df["Low"], close=df["Close"])

    assert adr_val is not None
    assert atr_val is not None
    # Ensure our synthetic data satisfies ADR% != ATR%
    assert abs(adr_val - atr_val) > 1e-4

    expected_ext_atr = ma_extension_x(close=c, sma=s50, atr_pct_value=atr_val)
    old_ext_adr = ((c / s50 - 1.0) * 100.0) / adr_val

    # Stock is beating SPY on both 3m and 6m windows
    spy_r3 = -0.05
    spy_r6 = -0.05

    row = compute_row("SYNTH", df, spy_r3, spy_r6)
    assert row is not None
    assert row.adr_ok is True
    assert row.pullback_ok is True
    # Price is within 4% of SMA20
    assert abs(c / s20 - 1.0) * 100.0 <= 4.0

    # Observable: row.extension_x matches ATR-based ma_extension_x and differs from ADR-based
    assert row.extension_x == pytest.approx(expected_ext_atr, rel=1e-6)
    assert row.extension_x != pytest.approx(old_ext_adr, rel=1e-4)
    assert row.ext_ok is True
    assert row.pass_all is True


def test_compute_regime_extension_uses_atr():
    df = _make_synth_bars(260)
    c = float(df["Close"].iloc[-1])
    sma50 = float(df["Close"].rolling(50).mean().iloc[-1])

    atr_val = atr_pct(high=df["High"], low=df["Low"], close=df["Close"])
    assert atr_val is not None
    expected_ext = ma_extension_x(close=c, sma=sma50, atr_pct_value=atr_val)

    old_adr = float(((df["High"] / df["Low"] - 1.0) * 100.0).tail(20).mean())
    old_ext = ((c / sma50 - 1.0) * 100.0) / old_adr

    regime = compute_regime(df)
    assert regime is not None
    assert regime.extension_x == pytest.approx(expected_ext, rel=1e-6)
    assert regime.extension_x != pytest.approx(old_ext, rel=1e-4)


def test_annotate_earnings_with_as_of_session():
    as_of = date(2026, 8, 21)
    earnings_ok = date(2026, 9, 15)  # Many sessions away (> 6)

    expected_sessions = sessions_before_earnings(as_of_session=as_of, earnings_date=earnings_ok)
    assert expected_sessions >= 6

    row = Row(ticker="TEST", pass_all=True)
    annotate_earnings(row, earnings_ok, as_of=as_of)

    assert row.earnings_date == "2026-09-15"
    assert row.days_to_earnings == float(expected_sessions)
    assert row.earn_ok == "ok"
    assert row.pass_all is True

    # Test earnings too soon (< 6 sessions)
    earnings_soon = date(2026, 8, 25)
    sessions_soon = sessions_before_earnings(as_of_session=as_of, earnings_date=earnings_soon)
    assert sessions_soon < 6

    row_soon = Row(ticker="SOON", pass_all=True)
    annotate_earnings(row_soon, earnings_soon, as_of=as_of)

    assert row_soon.days_to_earnings == float(sessions_soon)
    assert row_soon.earn_ok == "FAIL"
    assert row_soon.pass_all is False
    assert f"earnings_in_{sessions_soon}d" in row_soon.fail_reasons

    # Test unknown earnings
    row_unk = Row(ticker="UNK", pass_all=True)
    annotate_earnings(row_unk, None, as_of=as_of)
    assert row_unk.earn_ok == "unknown"
    assert "earnings_unknown_VERIFY" in row_unk.warnings
    assert row_unk.pass_all is True

    # Test default as_of (uses latest_completed_session())
    row_def = Row(ticker="DEF", pass_all=True)
    future_date = latest_completed_session() + timedelta(days=30)
    annotate_earnings(row_def, future_date)
    assert row_def.earn_ok == "ok"
    assert row_def.earnings_date == future_date.isoformat()

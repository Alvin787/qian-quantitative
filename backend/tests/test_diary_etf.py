"""Unit tests for diary ETF row builders (no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.diary.etf import avg_dollar_volume_20, build_etf_row, short_term_trend_label


class TestShortTermTrendLabel:
    def test_up_above_all_ma(self):
        assert (
            short_term_trend_label(100.0, 90.0, 80.0, 70.0)
            == "Up, Above All MA"
        )

    def test_up_above_20_and_50(self):
        # close >= sma20 and close >= sma50, but sma20 < sma50 so not all-MA
        assert (
            short_term_trend_label(100.0, 95.0, 98.0, 110.0)
            == "Up, Above 20 & 50-MA"
        )

    def test_up_above_20_only(self):
        # close >= sma20 but close < sma50
        assert (
            short_term_trend_label(100.0, 95.0, 105.0, 110.0)
            == "Up, Above 20-MA"
        )

    def test_down_above_50(self):
        # close < sma20 and close >= sma50
        assert (
            short_term_trend_label(100.0, 105.0, 95.0, 90.0)
            == "Down, Above 50-MA"
        )

    def test_down_below_20(self):
        assert (
            short_term_trend_label(80.0, 100.0, 110.0, 120.0)
            == "Down, Below 20-MA"
        )


def _synthetic_history(
    n: int = 252,
    *,
    start_close: float = 100.0,
    drift: float = 0.1,
) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    closes = start_close + np.arange(n, dtype=float) * drift
    highs = closes + 1.0
    lows = closes - 1.0
    opens = closes.copy()
    volume = np.full(n, 1_000_000.0)
    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volume,
        },
        index=idx,
    )


class TestBuildEtfRow:
    def test_build_etf_row_metrics(self):
        history = _synthetic_history(252, start_close=100.0, drift=0.1)
        row = build_etf_row("RSP", history, priority=False)

        last = float(history["Close"].iloc[-1])
        prev = float(history["Close"].iloc[-2])
        expected_daily = ((last - prev) / prev) * 100.0
        low_52w = float(history["Low"].min())
        high_52w = float(history["High"].max())
        expected_from_low = ((last - low_52w) / low_52w) * 100.0
        expected_from_high = ((last - high_52w) / high_52w) * 100.0

        assert row.symbol == "RSP"
        assert row.last == last
        assert abs(row.daily_change_pct - expected_daily) < 1e-9
        assert abs(row.pct_from_52w_low - expected_from_low) < 1e-9
        assert abs(row.pct_from_52w_high - expected_from_high) < 1e-9
        assert row.priority is False
        assert row.short_term_trend in {
            "Up, Above All MA",
            "Up, Above 20 & 50-MA",
            "Up, Above 20-MA",
            "Down, Above 50-MA",
            "Down, Below 20-MA",
        }

    def test_build_etf_row_priority_and_short_history(self):
        history = _synthetic_history(60, start_close=50.0, drift=0.2)
        row = build_etf_row("XLE", history, priority=True)
        assert row.priority is True
        assert row.symbol == "XLE"
        assert row.last == float(history["Close"].iloc[-1])


class TestAvgDollarVolume20:
    def test_avg_dollar_volume_20_mean_of_close_times_volume(self):
        history = pd.DataFrame(
            {
                "Open": [10.0, 11.0, 12.0],
                "High": [11.0, 12.0, 13.0],
                "Low": [9.0, 10.0, 11.0],
                "Close": [10.0, 20.0, 30.0],
                "Volume": [100.0, 200.0, 300.0],
            },
            index=pd.DatetimeIndex(["2026-08-06", "2026-08-07", "2026-08-08"]),
        )
        # (10*100 + 20*200 + 30*300) / 3 = 4666.666...
        assert abs(avg_dollar_volume_20(history) - (1000.0 + 4000.0 + 9000.0) / 3.0) < 1e-9

    def test_avg_dollar_volume_20_uses_last_20_sessions(self):
        n = 25
        closes = np.arange(1.0, n + 1.0)
        volumes = np.full(n, 10.0)
        history = pd.DataFrame(
            {
                "Open": closes,
                "High": closes,
                "Low": closes,
                "Close": closes,
                "Volume": volumes,
            },
            index=pd.date_range("2026-01-01", periods=n, freq="B"),
        )
        expected = float((closes[-20:] * volumes[-20:]).mean())
        assert abs(avg_dollar_volume_20(history) - expected) < 1e-9

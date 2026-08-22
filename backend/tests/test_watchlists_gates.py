from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backend.watchlists.gates import score_history


def make_ohlcv(
    n: int,
    *,
    start_close: float = 100.0,
    close_step: float = 0.5,
    volume: float = 1_000_000.0,
) -> pd.DataFrame:
    idx = pd.bdate_range("2026-01-02", periods=n)
    close = start_close + close_step * np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.04,
            "Low": close / 1.04,
            "Close": close,
            "Volume": np.full(n, volume),
        },
        index=idx,
    )


TODAY = date(2026, 8, 14)
EARNINGS_OK = date(2026, 8, 28)
EARNINGS_SOON = date(2026, 8, 18)


def _focus_inputs(*, industry: str = "Software", earnings_date: date = EARNINGS_OK):
    return dict(
        industry=industry,
        history=make_ohlcv(220),
        spy_history=make_ohlcv(220, start_close=400.0, close_step=0.01),
        earnings_date=earnings_date,
        today=TODAY,
    )


def test_score_history_chart_review_ready():
    result = score_history(**_focus_inputs())
    assert result.readiness == "chart_review_ready"
    assert result.unknown is False
    assert result.fail_reasons == ""
    assert result.gates.adr_ok is True
    assert result.gates.liq_ok is True
    assert result.gates.ext_ok is True
    assert result.gates.rs_ok is True
    assert result.gates.earn_ok == "ok"
    assert result.gates.room_to_200_ok is True
    assert result.gates.extension_basis == "sma50"
    assert result.gates.atr_pct is not None


def test_score_history_biotech_excluded():
    result = score_history(**_focus_inputs(industry="Biotechnology"))
    assert result.readiness == "excluded"
    assert "biotech" in result.fail_reasons.split(";")


def test_score_history_gap_down_high_vol_sell_disrupted():
    inputs = _focus_inputs()
    history = inputs["history"]
    prev_close = float(history["Close"].iloc[-2])
    vol_mean_50 = float(history["Volume"].iloc[-50:].mean())
    last = history.index[-1]
    history.loc[last, "Open"] = prev_close * 0.96
    history.loc[last, "Close"] = prev_close * 0.99
    history.loc[last, "Volume"] = 2.0 * vol_mean_50
    result = score_history(**inputs)
    assert result.readiness == "disrupted"
    assert "disrupted" in result.fail_reasons.split(";")


def test_score_history_earnings_blocked():
    result = score_history(**_focus_inputs(earnings_date=EARNINGS_SOON))
    assert result.readiness != "chart_review_ready"
    assert result.readiness == "earnings_blocked"


def test_score_history_short_history_unknown():
    result = score_history(
        industry="Software",
        history=make_ohlcv(19),
        spy_history=make_ohlcv(70, start_close=400.0, close_step=0.01),
        earnings_date=EARNINGS_OK,
        today=TODAY,
    )
    assert result.readiness == "unknown"
    assert result.fail_reasons == "fetch"
    assert result.unknown is True


def test_score_history_established_missing_sma200():
    result = score_history(
        industry="Software",
        history=make_ohlcv(70),
        spy_history=make_ohlcv(70, start_close=400.0, close_step=0.01),
        earnings_date=EARNINGS_OK,
        today=TODAY,
    )
    assert result.readiness == "data_incomplete"
    assert "sma200" in result.fail_reasons.split(";")


def test_score_history_ipo_uses_sma20_fallback():
    result = score_history(
        industry="Software",
        history=make_ohlcv(40),
        spy_history=make_ohlcv(40, start_close=400.0, close_step=0.01),
        earnings_date=EARNINGS_OK,
        today=TODAY,
        source_screens=["ipo_this_year"],
    )
    assert result.gates.extension_basis == "sma20_ipo_fallback"
    assert result.readiness != "data_incomplete"
    assert "sma200" not in result.fail_reasons.split(";")


def test_score_history_empty_industry_data_incomplete():
    result = score_history(**_focus_inputs(industry=""))
    assert result.readiness == "data_incomplete"
    assert "industry" in result.fail_reasons.split(";")


def test_score_history_gap_down_without_high_vol_sell_disrupted():
    inputs = _focus_inputs()
    history = inputs["history"]
    prev_close = float(history["Close"].iloc[-2])
    last = history.index[-1]
    history.loc[last, "Open"] = prev_close * 0.96
    result = score_history(**inputs)
    assert result.readiness == "disrupted"
    assert "disrupted" in result.fail_reasons.split(";")


def test_score_history_range_compress_false_still_chart_review_ready():
    result = score_history(**_focus_inputs())
    assert result.gates.range_compress is False
    assert result.readiness == "chart_review_ready"


def test_score_history_room_to_200_uses_adr_denominator():
    history = make_ohlcv(220, start_close=200.0, close_step=-0.5)
    spy_history = make_ohlcv(220, start_close=400.0, close_step=0.01)
    result = score_history(
        industry="Software",
        history=history,
        spy_history=spy_history,
        earnings_date=EARNINGS_OK,
        today=TODAY,
    )
    close_last = float(history["Close"].iloc[-1])
    s200 = result.gates.sma200
    adr_pct = result.gates.adr_pct
    assert s200 is not None
    assert adr_pct is not None and adr_pct > 0
    assert close_last < s200
    assert result.gates.declining_200 is True
    room = ((s200 / close_last - 1.0) * 100.0) / adr_pct
    assert room >= 3
    assert result.gates.room_to_200_ok is True
    assert result.gates.room_to_200_adr == room


def test_score_history_etf_liquidity_and_earnings_bypass():
    result = score_history(
        industry="Exchange Traded Fund",
        history=make_ohlcv(220, volume=1_500_000.0),
        spy_history=make_ohlcv(220, start_close=400.0, close_step=0.01),
        earnings_date=None,
        today=TODAY,
        source_screens=["liquid_leveraged_etf"],
    )
    assert result.gates.liq_ok is True
    assert result.gates.earn_ok == "not_applicable"
    assert result.gates.earnings_date is None
    assert result.gates.days_to_earnings is None
    assert result.readiness == "chart_review_ready"
    assert result.fail_reasons == ""


def test_score_history_etf_below_100m_liquidity_fails():
    result = score_history(
        industry="Exchange Traded Fund",
        history=make_ohlcv(220, volume=200_000.0),
        spy_history=make_ohlcv(220, start_close=400.0, close_step=0.01),
        earnings_date=None,
        today=TODAY,
        source_screens=["liquid_leveraged_etf"],
    )
    assert result.gates.liq_ok is False
    assert "liquidity" in result.fail_reasons.split(";")
    assert result.gates.earn_ok == "not_applicable"


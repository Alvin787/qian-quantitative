from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from backend.marketdata import indicators
from backend.marketdata.calendar import sessions_before_earnings
from backend.screener.leveraged_etfs import ETF_LIQ_MIN
from backend.watchlists.store import Gates

ADR_MIN = 3.0
LIQ_MIN = 20_000_000
EXT_MAX = 4.0
EARN_MIN_SESSIONS = 6
RS_SESSIONS = 63
RISING_LOOKBACK = 10
BIOTECH_SUBSTR = ("biotechnology", "biotech")
NEAR_MA_PCT = 3.0
DRYUP_MAX = 0.7
COMPRESS_MAX = 0.7
GAP_DOWN = 0.97
HIGH_VOL_SELL_X = 1.5
ROOM_TO_200_ADR = 3.0

_OHLCV = ("Open", "High", "Low", "Close", "Volume")


@dataclass
class ScoreResult:
    gates: Gates
    readiness: str
    fail_reasons: str
    unknown: bool


def ny_today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()


def _f(value: object) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _b(value: bool) -> bool:
    return bool(value)


def _sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def _last(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return _f(series.iloc[-1])


def _rising(sma: pd.Series) -> bool:
    now = _last(sma)
    if now is None or len(sma) <= RISING_LOOKBACK:
        return False
    prev = _f(sma.iloc[-1 - RISING_LOOKBACK])
    if prev is None:
        return False
    return now > prev


def _index_as_dates(index: pd.Index) -> pd.Index:
    ts = pd.to_datetime(index)
    if getattr(ts, "tz", None) is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return pd.Index(ts.date)


def _bar_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    ts = pd.Timestamp(value)
    return ts.date()


def score_history(
    *,
    industry: str,
    history: pd.DataFrame | None,
    spy_history: pd.DataFrame | None,
    earnings_date: date | None,
    today: date,
    expected_session: date | None = None,
    source_screens: list[str] | None = None,
    earnings_required: bool = True,
) -> ScoreResult:
    if history is None or any(col not in history.columns for col in _OHLCV):
        return ScoreResult(Gates(), "unknown", "fetch", True)
    frame = history.loc[:, list(_OHLCV)].dropna()
    if len(frame) < 20:
        return ScoreResult(Gates(), "unknown", "fetch", True)

    open_ = frame["Open"]
    high = frame["High"]
    low = frame["Low"]
    close = frame["Close"]
    volume = frame["Volume"]
    n = len(frame)
    close_last = float(close.iloc[-1])
    open_last = float(open_.iloc[-1])
    vol_last = float(volume.iloc[-1])

    price_as_of_date = _bar_date(frame.index[-1])
    price_as_of = price_as_of_date.isoformat()
    data_fresh = True if expected_session is None else price_as_of_date == expected_session

    if not industry.strip():
        return ScoreResult(
            Gates(price_as_of=price_as_of, data_fresh=data_fresh),
            "data_incomplete",
            "industry",
            False,
        )

    industry_l = industry.lower()
    biotech = any(token in industry_l for token in BIOTECH_SUBSTR)
    if biotech:
        return ScoreResult(
            Gates(price_as_of=price_as_of, data_fresh=data_fresh, biotech=True),
            "excluded",
            "biotech",
            False,
        )

    if expected_session is not None and not data_fresh:
        return ScoreResult(
            Gates(
                price_as_of=price_as_of,
                data_fresh=data_fresh,
                biotech=_b(biotech),
            ),
            "data_incomplete",
            "stale",
            False,
        )

    sma10 = _sma(close, 10)
    sma20 = _sma(close, 20)
    sma50 = _sma(close, 50)
    sma200 = _sma(close, 200)
    s10 = _last(sma10)
    s20 = _last(sma20)
    s50 = _last(sma50)
    s200 = _last(sma200)

    rising_10 = _rising(sma10)
    rising_20 = _rising(sma20)
    above_10 = s10 is not None and close_last > s10
    above_20 = s20 is not None and close_last > s20

    adr_pct = indicators.adr_pct(high, low, close)
    atr_pct = indicators.atr_pct(high, low, close)
    adr_ok = adr_pct is not None and adr_pct >= ADR_MIN

    ipo = "ipo_this_year" in (source_screens or [])
    extension_basis = None
    extension_x = None
    ext_ok = False
    sma_for_ext = None
    if s50 is not None:
        extension_basis = "sma50"
        sma_for_ext = s50
    elif ipo and s20 is not None:
        extension_basis = "sma20_ipo_fallback"
        sma_for_ext = s20
    if sma_for_ext is not None and atr_pct is not None:
        extension_x = indicators.ma_extension_x(
            close=close_last, sma=sma_for_ext, atr_pct_value=atr_pct
        )
        ext_ok = extension_x is not None and extension_x <= EXT_MAX

    is_etf = "liquid_leveraged_etf" in (source_screens or [])
    dollar_n = min(50, n)
    avg_dollar_vol = float((close * volume).iloc[-dollar_n:].mean())
    if is_etf:
        liq_ok = avg_dollar_vol is not None and avg_dollar_vol >= ETF_LIQ_MIN
    else:
        liq_ok = avg_dollar_vol >= LIQ_MIN

    rs_3m_pp = None
    rs_ok = False
    rs_sessions = None
    if spy_history is not None and "Close" in spy_history.columns:
        spy_close = spy_history["Close"].dropna()
        stock_s = pd.Series(close.to_numpy(), index=_index_as_dates(close.index))
        spy_s = pd.Series(spy_close.to_numpy(), index=_index_as_dates(spy_close.index))
        joined = pd.concat(
            [stock_s.rename("stock"), spy_s.rename("spy")], axis=1, join="inner"
        ).dropna()
        if len(joined) >= 21:
            rs_sessions = min(RS_SESSIONS, len(joined) - 1)
            if rs_sessions < 20:
                rs_ok = False
                rs_3m_pp = None
            else:
                stock_ret = float(joined["stock"].iloc[-1]) / float(
                    joined["stock"].iloc[-1 - rs_sessions]
                ) - 1.0
                spy_ret = float(joined["spy"].iloc[-1]) / float(
                    joined["spy"].iloc[-1 - rs_sessions]
                ) - 1.0
                rs_3m_pp = (stock_ret - spy_ret) * 100.0
                rs_ok = rs_3m_pp > 0

    declining_200 = None
    room_to_200_adr = None
    if s200 is None:
        room_to_200_ok = True
    else:
        if len(sma200) > 20:
            prev_200 = _f(sma200.iloc[-21])
            declining_200 = prev_200 is not None and s200 < prev_200
        else:
            declining_200 = False
        if close_last < s200 and adr_pct is not None and adr_pct > 0:
            room_to_200_adr = ((s200 / close_last - 1.0) * 100.0) / adr_pct
        if not (declining_200 and close_last < s200):
            room_to_200_ok = True
        else:
            room_to_200_ok = room_to_200_adr is not None and room_to_200_adr >= ROOM_TO_200_ADR

    volume_dryup = False
    if n >= 50:
        vol_base = float(volume.iloc[-50:-5].mean())
        if vol_base > 0:
            volume_dryup = float(volume.iloc[-5:].mean()) / vol_base <= DRYUP_MAX

    range_compress = False
    if n >= 25:
        bar_range = high - low
        range_base = float(bar_range.iloc[-25:-5].mean())
        if range_base > 0:
            range_compress = float(bar_range.iloc[-5:].mean()) / range_base <= COMPRESS_MAX

    near_10_20 = False
    if s10 is not None and s20 is not None and not above_10 and not above_20:
        near_10_20 = min(abs(close_last / s10 - 1.0), abs(close_last / s20 - 1.0)) * 100.0 <= NEAR_MA_PCT

    take = min(50, n - 1)
    vol_mean_50 = float(volume.iloc[-(take + 1) : -1].mean()) if take else 0.0
    gap_down = open_last < float(close.iloc[-2]) * GAP_DOWN
    high_vol_sell = close_last < float(close.iloc[-2]) and vol_last >= HIGH_VOL_SELL_X * vol_mean_50
    sma20_now = _last(sma20)
    sma20_prev = _f(sma20.iloc[-1 - RISING_LOOKBACK]) if len(sma20) > RISING_LOOKBACK else None
    structure_break = (
        s10 is not None
        and s50 is not None
        and close_last < s10
        and close_last < s50
        and sma20_now is not None
        and sma20_prev is not None
        and sma20_now < sma20_prev
    )
    disrupted_h = gap_down or high_vol_sell or structure_break

    if is_etf:
        earnings_date = None
        earnings_iso = None
        days_to_earnings = None
        earn_ok = "not_applicable"
        earnings_pass = True
    elif not earnings_required:
        earnings_iso = None if earnings_date is None else earnings_date.isoformat()
        earn_ok = "not_checked"
        earnings_pass = True
        days_to_earnings = (
            None
            if earnings_date is None
            else sessions_before_earnings(as_of_session=today, earnings_date=earnings_date)
        )
    elif earnings_date is None:
        earnings_iso = None
        days_to_earnings = None
        earn_ok = "unknown"
        earnings_pass = False
    else:
        earnings_iso = earnings_date.isoformat()
        days_to_earnings = sessions_before_earnings(
            as_of_session=today, earnings_date=earnings_date
        )
        earn_ok = "ok" if days_to_earnings >= EARN_MIN_SESSIONS else "fail"
        earnings_pass = earn_ok == "ok"

    gates = Gates(
        adr_pct=adr_pct,
        adr_ok=None if adr_ok is None else _b(adr_ok),
        avg_dollar_vol=avg_dollar_vol,
        liq_ok=_b(liq_ok),
        close=close_last,
        sma10=s10,
        sma20=s20,
        sma50=s50,
        sma200=s200,
        above_10=_b(above_10),
        above_20=_b(above_20),
        rising_10=_b(rising_10),
        rising_20=_b(rising_20),
        extension_x=extension_x,
        ext_ok=_b(ext_ok),
        rs_3m_pp=rs_3m_pp,
        rs_ok=_b(rs_ok),
        earnings_date=earnings_iso,
        days_to_earnings=days_to_earnings,
        earn_ok=earn_ok,
        biotech=_b(biotech),
        declining_200=None if declining_200 is None else _b(declining_200),
        room_to_200_adr=room_to_200_adr,
        room_to_200_ok=_b(room_to_200_ok),
        volume_dryup=_b(volume_dryup),
        range_compress=_b(range_compress),
        near_10_20=_b(near_10_20),
        atr_pct=atr_pct,
        extension_basis=extension_basis,
        rs_sessions=rs_sessions,
        price_as_of=price_as_of,
        data_fresh=data_fresh,
    )

    if atr_pct is None or adr_pct is None:
        token = "atr" if atr_pct is None else "adr"
        return ScoreResult(gates, "data_incomplete", token, False)
    if not ipo and s200 is None:
        return ScoreResult(gates, "data_incomplete", "sma200", False)
    if disrupted_h:
        return ScoreResult(gates, "disrupted", "disrupted", False)
    if not is_etf and earnings_date is None and earnings_required:
        return ScoreResult(gates, "data_incomplete", "earnings", False)

    tokens: list[str] = []
    if not adr_ok:
        tokens.append("adr")
    if not liq_ok:
        tokens.append("liquidity")
    if not above_10:
        tokens.append("below_10")
    if not above_20:
        tokens.append("below_20")
    if not rising_10:
        tokens.append("flat_10")
    if not rising_20:
        tokens.append("flat_20")
    if not ext_ok:
        tokens.append("ext")
    if earn_ok not in {"ok", "not_checked", "not_applicable"}:
        tokens.append("earnings")
    if not rs_ok:
        tokens.append("rs")
    if not room_to_200_ok:
        tokens.append("declining_200")

    chart_except_earn = (
        adr_ok
        and liq_ok
        and above_10
        and above_20
        and rising_10
        and rising_20
        and ext_ok
        and rs_ok
        and room_to_200_ok
    )
    stalk_except_earn = (
        adr_ok
        and liq_ok
        and ext_ok
        and rs_ok
        and room_to_200_ok
        and not disrupted_h
    )
    chart_ok = chart_except_earn and earnings_pass
    stalk_ok = stalk_except_earn and earnings_pass

    if chart_ok and earnings_pass:
        readiness = "chart_review_ready"
    elif earn_ok == "fail" and (chart_except_earn or stalk_except_earn):
        readiness = "earnings_blocked"
    elif stalk_ok and earnings_pass:
        readiness = "stalk_ready"
    else:
        readiness = "watch"

    return ScoreResult(gates, readiness, ";".join(tokens), False)

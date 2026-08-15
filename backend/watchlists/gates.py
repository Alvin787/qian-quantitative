from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

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


def score_history(
    *,
    industry: str,
    history: pd.DataFrame | None,
    spy_history: pd.DataFrame | None,
    earnings_date: date | None,
    today: date,
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

    adr_series = (high / low - 1.0) * 100.0
    adr_pct = float(adr_series.iloc[-20:].mean())
    adr_ok = adr_pct >= ADR_MIN

    dollar_n = min(50, n)
    avg_dollar_vol = float((close * volume).iloc[-dollar_n:].mean())
    liq_ok = avg_dollar_vol >= LIQ_MIN

    if s50 is not None and adr_pct > 0:
        extension_x = ((close_last / s50 - 1.0) * 100.0) / adr_pct
        ext_ok = extension_x <= EXT_MAX
    else:
        extension_x = None
        ext_ok = False

    rs_3m_pp = None
    rs_ok = False
    if spy_history is not None and "Close" in spy_history.columns:
        spy_close = spy_history["Close"].dropna()
        if len(close) >= RS_SESSIONS + 1 and len(spy_close) >= RS_SESSIONS + 1:
            stock_ret = close_last / float(close.iloc[-1 - RS_SESSIONS]) - 1.0
            spy_ret = float(spy_close.iloc[-1]) / float(spy_close.iloc[-1 - RS_SESSIONS]) - 1.0
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
        if close_last < s200 and adr_pct > 0:
            room_to_200_adr = ((s200 / close_last - 1.0) * 100.0) / adr_pct
        if not (declining_200 and close_last < s200):
            room_to_200_ok = True
        else:
            room_to_200_ok = room_to_200_adr is not None and room_to_200_adr >= ROOM_TO_200_ADR

    if earnings_date is None:
        days_to_earnings = None
        earn_ok = "unknown"
        earnings_iso = None
    else:
        days_to_earnings = int(np.busday_count(today, earnings_date))
        earn_ok = "ok" if days_to_earnings >= EARN_MIN_SESSIONS else "fail"
        earnings_iso = earnings_date.isoformat()

    industry_l = industry.lower()
    biotech = any(token in industry_l for token in BIOTECH_SUBSTR)

    vol_window = min(50, n)
    vol_mean_50 = float(volume.iloc[-vol_window:].mean())
    volume_dryup = False
    if n >= 50:
        vol_mean_50_full = float(volume.iloc[-50:].mean())
        if vol_mean_50_full > 0:
            volume_dryup = float(volume.iloc[-5:].mean()) / vol_mean_50_full <= DRYUP_MAX

    range_compress = False
    rolling_adr = adr_series.rolling(20).mean()
    if n >= 50:
        last10 = rolling_adr.iloc[-10:]
        last50 = rolling_adr.iloc[-50:]
        denom = _f(last50.mean())
        if last10.notna().all() and last50.notna().all() and denom is not None and denom > 0:
            range_compress = float(last10.mean()) / denom <= COMPRESS_MAX

    near_10_20 = False
    if s10 is not None and s20 is not None and not above_10 and not above_20:
        near_10_20 = min(abs(close_last / s10 - 1.0), abs(close_last / s20 - 1.0)) * 100.0 <= NEAR_MA_PCT

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
    disrupted_h = (gap_down and high_vol_sell) or structure_break

    gates = Gates(
        adr_pct=adr_pct,
        adr_ok=_b(adr_ok),
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
    )

    tokens: list[str] = []
    if biotech:
        tokens.append("biotech")
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
    if earn_ok != "ok":
        tokens.append("earnings")
    if not rs_ok:
        tokens.append("rs")
    if not room_to_200_ok:
        tokens.append("declining_200")
    if disrupted_h:
        tokens.append("disrupted")
    fail_reasons = ";".join(tokens)

    focus_ok = (
        adr_ok
        and liq_ok
        and not biotech
        and above_10
        and above_20
        and rising_10
        and rising_20
        and ext_ok
        and earn_ok == "ok"
        and rs_ok
        and room_to_200_ok
    )
    stalk_ok = adr_ok and liq_ok and not biotech

    if biotech or disrupted_h:
        readiness = "disrupted"
    elif focus_ok:
        readiness = "focus_ready"
    elif earn_ok == "fail":
        readiness = "earnings_blocked"
    elif stalk_ok:
        readiness = "stalk_ready"
    else:
        readiness = "watch"

    return ScoreResult(gates, readiness, fail_reasons, False)

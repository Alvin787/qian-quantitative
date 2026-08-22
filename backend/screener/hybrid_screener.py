#!/usr/bin/env python3
"""
Hybrid Pullback Screener — full post-close workflow for the hybrid strategy.

What it does (in strategy-doc order)
------------------------------------
0. REGIME GATE (§9.1/A5): SPY vs rising 200-SMA + index extension.
   Below a declining 200-MA -> no dip buying at all (run still scores, but
   the output is stamped REGIME BLOCKED).
1. Pulls all pages from your Finviz screener URL (or reads a ticker file).
2. Downloads daily OHLCV via yfinance (EOD — fine after the close).
3. Applies every gate that can be computed from price/volume:
     - trend stack (above rising 50 & rising 200-SMA, Rev 3 definitions)
     - ADR% band 2–5%
     - pullback within 4% of the 20- or 50-MA
     - relative strength vs SPY (3m AND 6m, per A1)
     - persistence proxies, >=2 of 4 required (§3.2):
         #1 last two pullbacks to the 20-MA held and recovered  [automated]
         #2 closed above 20-MA on >=70% of last 50 sessions     [automated]
         #3 linear advance (R^2 of log-price trend, 6 months)   [automated proxy]
         #4 prior up-leg on volume expansion                    [automated proxy]
     - avg dollar volume >= $20M
     - extension <= 4x ATR% from the 50-MA
     - biotech hard exclude
4. EARNINGS GATE (§7 #9): fetches the next earnings date for every name that
   survives the price gates and requires >= 6 sessions of leeway. Unknown
   dates are flagged for manual verification, not silently passed.
5. Flags likely waterfalls (depth > 2.5x ADR or expanding down-volume) so the
   chart pass starts pre-sorted.
6. Writes pass/fail CSVs.

Install (once)
--------------
    # macOS system Python blocks bare pip installs; use a venv:
    python3 -m venv ~/.venvs/trading
    ~/.venvs/trading/bin/pip install yfinance pandas

Run
---
    cd ~/Downloads
    ~/.venvs/trading/bin/python hybrid_screener.py

    # or with your own URL / ticker file:
    ~/.venvs/trading/bin/python hybrid_screener.py --url "https://finviz.com/screener?..."
    ~/.venvs/trading/bin/python hybrid_screener.py --tickers tickers.txt
    ~/.venvs/trading/bin/python hybrid_screener.py --skip-earnings   # offline/fast

Outputs (under screener_output/ by default)
-------------------------------------------
    hybrid_candidates_YYYY-MM-DD_HHMMSS.csv   — names that PASS the automated gates
    hybrid_all_results_YYYY-MM-DD_HHMMSS.csv  — every ticker with pass/fail + reason columns

Still manual after this script (cannot be automated from price data)
--------------------------------------------------------------------
    - One-line news test (§5.2): WHY is it down? Best case = no news.
    - Solvency veto (§5.1): runway / covenants / going-concern (60s per name).
    - Final eyeball: the proxy #1/#3/#4 and waterfall checks here are
      heuristics — confirm them on the chart before Leader Watchlist.
    - Everything intraday, next session: trigger, LoD <= 0.60 ATR, sizing.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from backend.marketdata.calendar import latest_completed_session, sessions_before_earnings
from backend.marketdata.indicators import adr_pct, atr_pct, ma_extension_x
from backend.screener.finviz import scrape_finviz
from backend.screener.screens import get_screen

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Missing packages. Run:\n  ~/.venvs/trading/bin/pip install yfinance pandas")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Defaults — your Screener A URL
# ---------------------------------------------------------------------------
DEFAULT_FINVIZ_URL = get_screen("reversal_pullback").url

# Hybrid thresholds (from hybrid-buy-the-dip-strategy.md Appendix A / §3)
ADR_MIN = 2.0
ADR_MAX = 5.0
PULLBACK_PCT_MAX = 4.0           # within ~2–4% of 20 or 50 MA
PERSIST_MIN = 0.70               # proxy #2: >=70% of last 50 closes above 20-MA
PROXIES_REQUIRED = 2             # §3.2: at least 2 of the 4 proxies
AVG_DOLLAR_VOL_MIN = 20_000_000  # $20M floor (prefer 20–50M+)
EXT_MAX = 4.0                    # sanity check; genuine dips rarely bind
RISING_50_LOOKBACK = 10
RISING_200_LOOKBACK = 20
HISTORY_DAYS = 400               # SMA200 + 6mo RS/linearity windows + buffer
MIN_BARS = 260

# Relative strength vs SPY (A1): 3m and 6m stock return must beat SPY's
RS_SHORT_SESSIONS = 63
RS_LONG_SESSIONS = 126

# Earnings gate (§7 #9): >= 5–6 sessions of leeway. Use 6, no exceptions.
EARN_MIN_SESSIONS = 6

# Persistence proxy heuristics
PULLBACK_LOOKBACK = 130          # window for episode detection (~6 months)
PULLBACK_RECOVER_MAX = 15        # sessions a pullback may take to reclaim 20-MA
PULLBACK_HOLD_TOL = 0.01         # "held" = never closed >1% below the 50-SMA
LINEAR_R2_MIN = 0.70             # proxy #3: R^2 of log-close vs time, 6 months
VOLEXP_RATIO_MIN = 1.2           # proxy #4: up-day vol / down-day vol in the leg

# Waterfall heuristic (§7 #3) — warning, not a hard fail; eyeball decides
WATERFALL_DEPTH_ADR = 2.5        # pullback depth from 20d high, in ADR units
WATERFALL_DVOL_X = 1.5           # recent down-day volume vs 50d average

# Index regime (§9.1 / §9.3)
INDEX_EXT_CAUTION = 4.0
INDEX_EXT_EXTREME = 6.0

# Optional hard-exclude by Finviz industry string (substring match, case-insensitive)
BIOTECH_INDUSTRY_SUBSTR = ("biotechnology", "biotech")


def load_tickers_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"[\s,;]+", text.strip())
    out: list[str] = []
    for p in parts:
        t = p.strip().upper()
        if t and re.fullmatch(r"[A-Z0-9.\-]+", t) and t not in out:
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Index regime (§9.1 / A5) — run FIRST, before any stock work
# ---------------------------------------------------------------------------
@dataclass
class Regime:
    ok: bool
    close: float
    sma200: float
    rising_200: bool
    above_200: bool
    extension_x: float
    note: str


def compute_regime(spy: pd.DataFrame) -> Regime | None:
    if spy is None or spy.empty or len(spy) < 230:
        return None
    if isinstance(spy.columns, pd.MultiIndex):
        spy = spy.copy()
        spy.columns = spy.columns.get_level_values(0)

    close = spy["Close"].dropna()
    high = spy["High"].dropna()
    low = spy["Low"].dropna()

    c = float(close.iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200_series = close.rolling(200).mean()
    s200 = float(sma200_series.iloc[-1])
    rising_200 = s200 > float(sma200_series.iloc[-1 - RISING_200_LOOKBACK])
    above_200 = c > s200

    atr_pct_val = atr_pct(high=high, low=low, close=close)
    ext_val = (
        ma_extension_x(close=c, sma=sma50, atr_pct_value=atr_pct_val)
        if (sma50 > 0 and atr_pct_val is not None)
        else None
    )
    ext = ext_val if ext_val is not None else float("nan")

    if above_200 and rising_200:
        note = "OK — dip buying permitted"
    elif above_200 and not rising_200:
        note = "CAUTION — above a flat/declining 200-MA; §9.2 chop check applies"
    elif not above_200 and rising_200:
        note = "CAUTION — below a still-rising 200-MA; breaks usually resolve, but size down"
    else:
        note = "BLOCKED — below a declining 200-MA: NO dip buying (§9.1, hard rule)"

    if ext >= INDEX_EXT_EXTREME:
        note += f" | index EXTREME at {ext:.1f}x from 50-MA (6–7x zone)"
    elif ext >= INDEX_EXT_CAUTION:
        note += f" | index extended {ext:.1f}x from 50-MA — reluctant to add risk near 4x"

    ok = not (not above_200 and not rising_200)
    return Regime(ok=ok, close=c, sma200=s200, rising_200=rising_200,
                  above_200=above_200, extension_x=ext, note=note)


# ---------------------------------------------------------------------------
# Persistence proxies (§3.2) — heuristics, confirm on the chart
# ---------------------------------------------------------------------------
def pullback_episodes(close: pd.Series, sma20: pd.Series) -> list[tuple[int, int | None]]:
    """Contiguous runs of closes below the 20-SMA -> (start, end) index pairs.
    end is the bar of the first close back above; None if still ongoing."""
    below = (close < sma20).to_numpy()
    episodes: list[tuple[int, int | None]] = []
    start: int | None = None
    for i, b in enumerate(below):
        if b and start is None:
            start = i
        elif not b and start is not None:
            episodes.append((start, i))
            start = None
    if start is not None:
        episodes.append((start, None))
    return episodes


def proxy1_last_two_pullbacks(close: pd.Series, sma20: pd.Series,
                              sma50: pd.Series) -> tuple[bool, int]:
    """Proxy #1: the last two COMPLETED pullbacks to the 20-MA both held
    (never closed >1% below the 50-SMA) and recovered within 15 sessions.
    The current, ongoing pullback is excluded — it's the trade, not evidence."""
    window = min(len(close), PULLBACK_LOOKBACK)
    c = close.tail(window).reset_index(drop=True)
    s20 = sma20.tail(window).reset_index(drop=True)
    s50 = sma50.tail(window).reset_index(drop=True)

    eps = [e for e in pullback_episodes(c, s20) if e[1] is not None]
    if len(eps) < 2:
        return False, len(eps)

    def held_and_recovered(ep: tuple[int, int | None]) -> bool:
        start, end = ep
        assert end is not None
        if end - start > PULLBACK_RECOVER_MAX:
            return False
        seg_close = c.iloc[start:end]
        seg_s50 = s50.iloc[start:end]
        return bool((seg_close >= seg_s50 * (1 - PULLBACK_HOLD_TOL)).all())

    last_two = eps[-2:]
    return all(held_and_recovered(e) for e in last_two), len(eps)


def proxy3_linearity(close: pd.Series) -> tuple[bool, float]:
    """Proxy #3: linear advance. R^2 of log-close against time over ~6 months,
    with a positive slope. High R^2 = steady climb, low = violent staircase."""
    y = np.log(close.tail(RS_LONG_SESSIONS).to_numpy(dtype=float))
    x = np.arange(len(y), dtype=float)
    if len(y) < 60:
        return False, float("nan")
    slope = np.polyfit(x, y, 1)[0]
    r = np.corrcoef(x, y)[0, 1]
    r2 = float(r * r)
    return bool(slope > 0 and r2 >= LINEAR_R2_MIN), r2


def proxy4_volume_expansion(close: pd.Series, volume: pd.Series,
                            sma20: pd.Series) -> tuple[bool, float]:
    """Proxy #4: prior up-leg on volume expansion. Take the leg since the last
    completed pullback ended (or the last 40 sessions if none), and compare
    up-day volume to down-day volume within it."""
    window = min(len(close), PULLBACK_LOOKBACK)
    c = close.tail(window).reset_index(drop=True)
    v = volume.tail(window).reset_index(drop=True)
    s20 = sma20.tail(window).reset_index(drop=True)

    eps = pullback_episodes(c, s20)
    completed = [e for e in eps if e[1] is not None]
    # Leg = after the previous pullback recovered, up to the start of the
    # current pullback (or the end of data).
    leg_start = completed[-1][1] if completed else max(0, len(c) - 40)
    leg_end = eps[-1][0] if eps and eps[-1][1] is None else len(c)
    if leg_end - leg_start < 5:
        leg_start = max(0, len(c) - 40)
        leg_end = len(c)

    chg = c.diff()
    seg = slice(leg_start, leg_end)
    up_vol = v.iloc[seg][chg.iloc[seg] > 0]
    dn_vol = v.iloc[seg][chg.iloc[seg] < 0]
    if len(up_vol) == 0 or len(dn_vol) == 0 or dn_vol.mean() == 0:
        return False, float("nan")
    ratio = float(up_vol.mean() / dn_vol.mean())
    return ratio >= VOLEXP_RATIO_MIN, ratio


# ---------------------------------------------------------------------------
# Row scoring
# ---------------------------------------------------------------------------
@dataclass
class Row:
    ticker: str
    pass_all: bool = False
    fail_reasons: str = ""
    warnings: str = ""
    close: float = float("nan")
    sma20: float = float("nan")
    sma50: float = float("nan")
    sma200: float = float("nan")
    rising_50: bool = False
    rising_200: bool = False
    above_stack: bool = False
    adr_pct: float = float("nan")
    adr_ok: bool = False
    near_20_pct: float = float("nan")
    near_50_pct: float = float("nan")
    pullback_ok: bool = False
    rs_3m_pp: float = float("nan")   # stock minus SPY, percentage points
    rs_6m_pp: float = float("nan")
    rs_ok: bool = False
    p1_pullbacks: bool = False
    p1_episodes: int = 0
    p2_persist: bool = False
    persist_70: float = float("nan")
    p3_linear: bool = False
    linear_r2: float = float("nan")
    p4_volexp: bool = False
    volexp_ratio: float = float("nan")
    proxies_passed: int = 0
    proxies_ok: bool = False
    waterfall_flag: bool = False
    pullback_depth_adr: float = float("nan")
    avg_dollar_vol: float = float("nan")
    liq_ok: bool = False
    extension_x: float = float("nan")
    ext_ok: bool = False
    earnings_date: str = ""
    days_to_earnings: float = float("nan")
    earn_ok: str = "not_checked"     # ok / FAIL / unknown / not_checked / skipped
    industry: str = ""
    biotech: bool = False
    _fails: list[str] = field(default_factory=list, repr=False)


def compute_row(ticker: str, df: pd.DataFrame, spy_r3: float, spy_r6: float,
                industry: str = "") -> Row | None:
    if df is None or df.empty or len(df) < MIN_BARS:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)

    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col not in df.columns:
            return None

    df = df.dropna(subset=["High", "Low", "Close", "Volume"]).copy()
    if len(df) < MIN_BARS:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()

    c = float(close.iloc[-1])
    s20 = float(sma20.iloc[-1])
    s50 = float(sma50.iloc[-1])
    s200 = float(sma200.iloc[-1])

    rising_50 = s50 > float(sma50.iloc[-1 - RISING_50_LOOKBACK])
    rising_200 = s200 > float(sma200.iloc[-1 - RISING_200_LOOKBACK])
    above_stack = (c > s50) and (c > s200) and rising_50 and rising_200

    # ADR% via shared marketdata indicator
    adr_val = adr_pct(high=df["High"], low=df["Low"], close=df["Close"])
    adr_ok = (adr_val is not None) and (ADR_MIN <= adr_val <= ADR_MAX)

    near_20_pct = abs(c / s20 - 1.0) * 100.0
    near_50_pct = abs(c / s50 - 1.0) * 100.0
    pullback_ok = (near_20_pct <= PULLBACK_PCT_MAX) or (near_50_pct <= PULLBACK_PCT_MAX)

    # Relative strength vs SPY (A1): both windows must beat the index
    rs_3m_pp = rs_6m_pp = float("nan")
    rs_ok = False
    if len(close) > RS_LONG_SESSIONS:
        r3 = c / float(close.iloc[-1 - RS_SHORT_SESSIONS]) - 1.0
        r6 = c / float(close.iloc[-1 - RS_LONG_SESSIONS]) - 1.0
        rs_3m_pp = (r3 - spy_r3) * 100.0
        rs_6m_pp = (r6 - spy_r6) * 100.0
        rs_ok = rs_3m_pp > 0 and rs_6m_pp > 0

    # Persistence proxies (§3.2) — need >= 2 of 4
    p1, p1_eps = proxy1_last_two_pullbacks(close, sma20, sma50)
    last50 = close.tail(50)
    persist_70 = float((last50 > sma20.tail(50)).mean())
    p2 = persist_70 >= PERSIST_MIN
    p3, r2 = proxy3_linearity(close)
    p4, volexp = proxy4_volume_expansion(close, volume, sma20)
    proxies_passed = sum([p1, p2, p3, p4])
    proxies_ok = proxies_passed >= PROXIES_REQUIRED

    # Waterfall heuristic (§7 #3): depth from the 20d high in ADR units,
    # or expanding down-day volume in the last 5 sessions.
    high20 = float(high.tail(20).max())
    depth_adr = (
        ((high20 / c - 1.0) * 100.0) / adr_val
        if (adr_val is not None and adr_val > 0)
        else float("nan")
    )
    vol50 = float(volume.tail(50).mean())
    chg_recent = close.diff().tail(5)
    dn_vols = volume.tail(5)[chg_recent < 0]
    dn_vol_x = float(dn_vols.mean() / vol50) if len(dn_vols) and vol50 > 0 else 0.0
    waterfall = (not math.isnan(depth_adr) and depth_adr > WATERFALL_DEPTH_ADR) or \
                (dn_vol_x > WATERFALL_DVOL_X)

    dollar_vol = (close * volume).tail(50).mean()
    avg_dollar_vol = float(dollar_vol)
    liq_ok = avg_dollar_vol >= AVG_DOLLAR_VOL_MIN

    atr_pct_val = atr_pct(high=df["High"], low=df["Low"], close=df["Close"])
    extension_x = (
        ma_extension_x(close=c, sma=s50, atr_pct_value=atr_pct_val)
        if (s50 is not None and atr_pct_val is not None)
        else None
    )
    ext_ok = (extension_x is not None) and (extension_x <= EXT_MAX)

    industry_l = (industry or "").lower()
    biotech = any(s in industry_l for s in BIOTECH_INDUSTRY_SUBSTR)

    fails: list[str] = []
    warns: list[str] = []
    if biotech:
        fails.append("biotech")
    if not above_stack:
        fails.append("trend_stack")
    if not adr_ok:
        fails.append(f"adr({adr_val:.1f}%)" if adr_val is not None else "adr(nan%)")
    if not pullback_ok:
        fails.append("not_near_ma")
    if not rs_ok:
        fails.append(f"rs_vs_spy(3m{rs_3m_pp:+.0f}/6m{rs_6m_pp:+.0f}pp)")
    if not proxies_ok:
        fails.append(f"proxies({proxies_passed}/4)")
    if not liq_ok:
        fails.append("liquidity")
    if not ext_ok:
        fails.append(f"ext({extension_x:.1f}x)" if extension_x is not None else "ext(nanx)")
    if waterfall:
        warns.append(f"waterfall?(depth {depth_adr:.1f}xADR, dnvol {dn_vol_x:.1f}x)")

    return Row(
        ticker=ticker,
        pass_all=len(fails) == 0,
        fail_reasons=";".join(fails),
        warnings=";".join(warns),
        close=c, sma20=s20, sma50=s50, sma200=s200,
        rising_50=rising_50, rising_200=rising_200, above_stack=above_stack,
        adr_pct=adr_val if adr_val is not None else float("nan"), adr_ok=adr_ok,
        near_20_pct=near_20_pct, near_50_pct=near_50_pct, pullback_ok=pullback_ok,
        rs_3m_pp=rs_3m_pp, rs_6m_pp=rs_6m_pp, rs_ok=rs_ok,
        p1_pullbacks=p1, p1_episodes=p1_eps,
        p2_persist=p2, persist_70=persist_70,
        p3_linear=p3, linear_r2=r2,
        p4_volexp=p4, volexp_ratio=volexp,
        proxies_passed=proxies_passed, proxies_ok=proxies_ok,
        waterfall_flag=waterfall, pullback_depth_adr=depth_adr,
        avg_dollar_vol=avg_dollar_vol, liq_ok=liq_ok,
        extension_x=extension_x if extension_x is not None else float("nan"), ext_ok=ext_ok,
        industry=industry, biotech=biotech,
        _fails=fails,
    )


# ---------------------------------------------------------------------------
# Earnings gate (§7 #9) — only fetched for names that pass the price gates
# ---------------------------------------------------------------------------
def next_earnings_date(ticker: str) -> date | None:
    try:
        t = yf.Ticker(ticker)
        # Preferred: calendar dict with 'Earnings Date'
        try:
            cal = t.calendar
            dates = None
            if isinstance(cal, dict):
                dates = cal.get("Earnings Date")
            elif cal is not None and hasattr(cal, "loc"):
                if "Earnings Date" in getattr(cal, "index", []):
                    dates = list(cal.loc["Earnings Date"])
            if dates:
                future = [d for d in pd.to_datetime(pd.Series(list(dates))).dt.date
                          if d >= date.today()]
                if future:
                    return min(future)
        except Exception:
            pass
        # Fallback: earnings_dates table (includes future rows)
        ed = t.get_earnings_dates(limit=8)
        if ed is not None and not ed.empty:
            future = [ts.date() for ts in ed.index if ts.date() >= date.today()]
            if future:
                return min(future)
    except Exception:
        return None
    return None


def annotate_earnings(row: Row, earnings_date: date | None, as_of: date | None = None) -> None:
    if as_of is None:
        as_of = latest_completed_session()
    if earnings_date is None:
        row.earn_ok = "unknown"
        row.warnings = ";".join(x for x in [row.warnings, "earnings_unknown_VERIFY"] if x)
    else:
        sessions = sessions_before_earnings(as_of_session=as_of, earnings_date=earnings_date)
        row.earnings_date = earnings_date.isoformat()
        row.days_to_earnings = float(sessions)
        if sessions >= EARN_MIN_SESSIONS:
            row.earn_ok = "ok"
        else:
            row.earn_ok = "FAIL"
            row._fails.append(f"earnings_in_{sessions}d")
            row.fail_reasons = ";".join(row._fails)
            row.pass_all = False


def apply_earnings_gate(rows: list[Row], sleep_s: float = 0.2, as_of: date | None = None) -> None:
    candidates = [r for r in rows if r.pass_all]
    if not candidates:
        return
    print(f"\nEarnings gate: checking next earnings date for "
          f"{len(candidates)} surviving names...")
    for r in candidates:
        d = next_earnings_date(r.ticker)
        annotate_earnings(r, d, as_of=as_of)
        if d is None:
            print(f"  {r.ticker:<6} earnings date UNKNOWN — verify manually")
        else:
            sessions = int(r.days_to_earnings)
            if r.earn_ok == "ok":
                print(f"  {r.ticker:<6} earnings {d} ({sessions} sessions) — ok")
            else:
                print(f"  {r.ticker:<6} earnings {d} ({sessions} sessions) — REJECT (<{EARN_MIN_SESSIONS})")
        time.sleep(sleep_s)


# ---------------------------------------------------------------------------
# Download / output
# ---------------------------------------------------------------------------
def download_history(tickers: list[str]) -> dict[str, pd.DataFrame]:
    print(f"\nDownloading EOD history for {len(tickers)} tickers via yfinance...")
    data = yf.download(
        tickers=tickers,
        period=f"{HISTORY_DAYS}d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    out: dict[str, pd.DataFrame] = {}
    if len(tickers) == 1:
        out[tickers[0]] = data
        return out

    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        level1 = data.columns.get_level_values(1)
        if tickers[0] in set(level0):
            for t in tickers:
                if t in level0:
                    out[t] = data[t].dropna(how="all")
        else:
            for t in tickers:
                if t in set(level1):
                    out[t] = data.xs(t, axis=1, level=1).dropna(how="all")
    return out


def rows_to_frame(rows: list[Row]) -> pd.DataFrame:
    records = [{k: v for k, v in r.__dict__.items() if not k.startswith("_")}
               for r in rows]
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["avg_dollar_vol_m"] = df["avg_dollar_vol"] / 1_000_000
    cols = [
        "ticker", "pass_all", "fail_reasons", "warnings",
        "close", "adr_pct", "adr_ok",
        "rising_50", "rising_200", "above_stack",
        "near_20_pct", "near_50_pct", "pullback_ok",
        "rs_3m_pp", "rs_6m_pp", "rs_ok",
        "p1_pullbacks", "p1_episodes", "p2_persist", "persist_70",
        "p3_linear", "linear_r2", "p4_volexp", "volexp_ratio",
        "proxies_passed", "proxies_ok",
        "waterfall_flag", "pullback_depth_adr",
        "avg_dollar_vol_m", "liq_ok",
        "extension_x", "ext_ok",
        "earnings_date", "days_to_earnings", "earn_ok",
        "sma20", "sma50", "sma200",
        "industry", "biotech",
    ]
    return df[cols].sort_values(
        ["pass_all", "proxies_passed", "adr_pct"],
        ascending=[False, False, True],
    )


# ---------------------------------------------------------------------------
# Run outputs
# ---------------------------------------------------------------------------
SCREENER_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCREENER_DIR / "screener_output"
LEGACY_ALL_RESULTS = SCREENER_DIR / "hybrid_all_results.csv"
LEGACY_CANDIDATES = SCREENER_DIR / "hybrid_candidates.csv"
RUN_ID_FMT = "%Y-%m-%d_%H%M%S"


@dataclass
class ScreenerRunResult:
    """Structured outcome of one hybrid screener execution."""

    run_id: str
    all_results_path: Path
    candidates_path: Path
    scored: int
    passed: int
    skipped: int
    skipped_tickers: list[str] = field(default_factory=list)
    regime_ok: bool | None = None
    regime_note: str | None = None


def allocate_run_id(outdir: Path, when: datetime | None = None, *, filenames: tuple[str, ...] = ("hybrid_all_results_{run_id}.csv", "hybrid_candidates_{run_id}.csv", "hybrid_run_{run_id}.json")) -> str:
    """Return a collision-safe YYYY-MM-DD_HHMMSS id for paired CSV outputs."""
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = when or datetime.now()
    while True:
        run_id = stamp.strftime(RUN_ID_FMT)
        if all(not (outdir / name.format(run_id=run_id)).exists() for name in filenames):
            return run_id
        stamp = stamp.replace(microsecond=0) + timedelta(seconds=1)


def run_screener(
    *,
    url: str = DEFAULT_FINVIZ_URL,
    tickers_path: Path | None = None,
    outdir: Path | None = None,
    keep_biotech: bool = False,
    skip_earnings: bool = False,
    run_id: str | None = None,
) -> ScreenerRunResult:
    """
    Execute the hybrid pullback screener and write paired timestamped CSVs.

    Strategy behavior matches the previous CLI main(); only output naming and
    the return value differ so callers (CLI / API) can share one path.
    """
    out = Path(outdir) if outdir is not None else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    rid = run_id or allocate_run_id(out)

    print("=" * 60)
    print("Hybrid Pullback Screener (post-close)")
    print("=" * 60)

    # ---- Step 0: regime gate (§9.1) ----
    print("\nRegime gate: downloading SPY...")
    spy = yf.download("SPY", period=f"{HISTORY_DAYS}d", interval="1d",
                      auto_adjust=True, progress=False)
    regime = compute_regime(spy)
    if regime is None:
        print("WARNING: could not compute SPY regime — check manually before trading.")
        spy_r3 = spy_r6 = 0.0
    else:
        print(f"  SPY {regime.close:.2f} vs 200-SMA {regime.sma200:.2f} "
              f"({'above' if regime.above_200 else 'BELOW'}, "
              f"{'rising' if regime.rising_200 else 'NOT rising'}) | "
              f"extension {regime.extension_x:.1f}x")
        print(f"  -> {regime.note}")
        spy_close = spy["Close"] if not isinstance(spy.columns, pd.MultiIndex) \
            else spy["Close"].iloc[:, 0]
        spy_close = spy_close.dropna()
        spy_r3 = float(spy_close.iloc[-1] / spy_close.iloc[-1 - RS_SHORT_SESSIONS] - 1.0)
        spy_r6 = float(spy_close.iloc[-1] / spy_close.iloc[-1 - RS_LONG_SESSIONS] - 1.0)

    # ---- Step 1: universe ----
    industries: dict[str, str] = {}
    if tickers_path:
        tickers = load_tickers_file(tickers_path)
        print(f"\nLoaded {len(tickers)} tickers from {tickers_path}")
    else:
        print("\nScraping Finviz screener...")
        scraped = scrape_finviz(url)
        tickers = scraped.tickers
        industries = scraped.industries
        print(f"Finviz returned {len(tickers)} unique tickers")

    if not tickers:
        raise RuntimeError("No tickers found.")

    if len(tickers) > 60:
        print(f"\nNote: {len(tickers)} raw names (>60 health check). "
              "Python filters will cut further; consider tightening Finviz.")

    # ---- Step 2–3: history + price gates ----
    hist = download_history(tickers)

    rows: list[Row] = []
    skipped: list[str] = []
    for t in tickers:
        df = hist.get(t)
        industry = industries.get(t, "")
        row = compute_row(t, df, spy_r3, spy_r6, industry=industry) if df is not None else None
        if row is None:
            skipped.append(t)
            continue
        if keep_biotech and row.biotech:
            fails = [f for f in row._fails if f != "biotech"]
            row._fails = fails
            row.fail_reasons = ";".join(fails)
            row.pass_all = len(fails) == 0
        rows.append(row)

    # ---- Step 4: earnings gate on survivors ----
    if skip_earnings:
        for r in rows:
            if r.pass_all:
                r.earn_ok = "skipped"
                r.warnings = ";".join(x for x in [r.warnings, "earnings_NOT_checked"] if x)
        print("\nEarnings gate SKIPPED (--skip-earnings) — verify dates manually.")
    else:
        apply_earnings_gate(rows)

    # ---- Step 5: output ----
    results = rows_to_frame(rows)
    passed = results[results["pass_all"]] if not results.empty else results

    all_path = out / f"hybrid_all_results_{rid}.csv"
    pass_path = out / f"hybrid_candidates_{rid}.csv"
    results.to_csv(all_path, index=False)
    passed.to_csv(pass_path, index=False)

    print("\n" + "=" * 60)
    if regime is not None and not regime.ok:
        print("*** REGIME BLOCKED — below a declining 200-MA. ***")
        print("*** List is for watchlist building ONLY. No entries. (§9.1) ***")
    print(f"Scored:   {len(rows)}")
    print(f"Skipped:  {len(skipped)}" + (f" ({', '.join(skipped[:10])}...)" if skipped else ""))
    print(f"PASSED:   {len(passed)}")
    print(f"Wrote:    {pass_path}")
    print(f"Wrote:    {all_path}")
    print("=" * 60)

    if not passed.empty:
        print("\nCandidates (open on TradingView to confirm the heuristics):\n")
        show = passed[
            ["ticker", "close", "adr_pct", "near_20_pct", "rs_3m_pp", "rs_6m_pp",
             "proxies_passed", "persist_70", "linear_r2",
             "avg_dollar_vol_m", "extension_x", "earnings_date", "days_to_earnings",
             "warnings", "industry"]
        ].copy()
        show["persist_70"] = (show["persist_70"] * 100).round(0).astype(int).astype(str) + "%"
        for col in ("adr_pct", "near_20_pct", "rs_3m_pp", "rs_6m_pp", "linear_r2",
                    "avg_dollar_vol_m", "extension_x"):
            show[col] = show[col].round(2)
        print(show.to_string(index=False))
    else:
        print("\nNo names passed automated gates tonight.")

    print(
        "\nStill manual (per name, ~2 min): one-line news test (§5.2), "
        "solvency veto (§5.1),\nchart confirmation of proxies + orderly vs "
        "waterfall, then -> Leader Watchlist."
    )

    return ScreenerRunResult(
        run_id=rid,
        all_results_path=all_path,
        candidates_path=pass_path,
        scored=len(rows),
        passed=len(passed),
        skipped=len(skipped),
        skipped_tickers=skipped,
        regime_ok=None if regime is None else regime.ok,
        regime_note=None if regime is None else regime.note,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hybrid pullback post-close screener")
    parser.add_argument("--url", default=DEFAULT_FINVIZ_URL, help="Finviz screener URL")
    parser.add_argument("--tickers", type=Path,
                        help="Optional text file of tickers (skips Finviz scrape)")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Folder for timestamped CSV outputs")
    parser.add_argument("--keep-biotech", action="store_true",
                        help="Do not auto-fail biotechnology names")
    parser.add_argument("--skip-earnings", action="store_true",
                        help="Skip the per-name earnings-date fetch (faster/offline)")
    args = parser.parse_args(argv)

    try:
        run_screener(
            url=args.url,
            tickers_path=args.tickers,
            outdir=args.outdir,
            keep_biotech=args.keep_biotech,
            skip_earnings=args.skip_earnings,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

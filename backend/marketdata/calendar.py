from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

SESSION_TZ = ZoneInfo("America/New_York")
POST_CLOSE_GRACE = timedelta(minutes=15)
EXCHANGE = "XNYS"


def xnys():
    return xcals.get_calendar(EXCHANGE)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ny_date(now: datetime | None = None) -> date:
    """(now or now_utc()).astimezone(SESSION_TZ).date()"""
    return (now or now_utc()).astimezone(SESSION_TZ).date()


def is_session(d: date) -> bool:
    return bool(xnys().is_session(pd.Timestamp(d)))


def session_close_utc(d: date) -> datetime:
    """xnys().session_close(d) converted to timezone.utc."""
    close = xnys().session_close(pd.Timestamp(d))
    ts = pd.Timestamp(close)
    if ts.tzinfo is None:
        ts = ts.tz_localize(SESSION_TZ)
    return ts.tz_convert(timezone.utc).to_pydatetime()


def previous_session(d: date) -> date:
    """xnys().previous_session(pd.Timestamp(d)).date()"""
    ts = pd.Timestamp(d)
    cal = xnys()
    if cal.is_session(ts):
        return pd.Timestamp(cal.previous_session(ts)).date()
    return pd.Timestamp(cal.date_to_session(ts, direction="previous")).date()


def latest_completed_session(now: datetime | None = None) -> date:
    """
    now = now or now_utc().
    If ny_date(now) is a session AND now < session_close_utc(that day) + POST_CLOSE_GRACE:
        return previous_session(that day).
    If ny_date(now) is a session AND now >= close+grace: return that day.
    If ny_date(now) is not a session: return previous_session(that day).
    """
    now = now or now_utc()
    d = ny_date(now)
    if is_session(d) and now >= session_close_utc(d) + POST_CLOSE_GRACE:
        return d
    return previous_session(d)


def breakout_run_allowed(now: datetime | None = None) -> bool:
    """
    now = now or now_utc().
    If ny_date(now) is not a session: True.
    Else: now >= session_close_utc(ny_date) + POST_CLOSE_GRACE.
    """
    now = now or now_utc()
    d = ny_date(now)
    if not is_session(d):
        return True
    return now >= session_close_utc(d) + POST_CLOSE_GRACE


def sessions_before_earnings(*, as_of_session: date, earnings_date: date) -> int:
    """
    Count XNYS sessions strictly after as_of_session and strictly before earnings_date.
    xnys().sessions_in_range(start, end) is inclusive — do not include as_of_session or earnings_date.
    If earnings_date <= as_of_session: return 0.
    """
    if earnings_date <= as_of_session:
        return 0
    start = pd.Timestamp(as_of_session) + pd.Timedelta(days=1)
    end = pd.Timestamp(earnings_date) - pd.Timedelta(days=1)
    if start > end:
        return 0
    return int(len(xnys().sessions_in_range(start, end)))

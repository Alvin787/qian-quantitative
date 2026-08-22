from __future__ import annotations

from datetime import date, datetime, timezone

from backend.marketdata.calendar import (
    breakout_run_allowed,
    latest_completed_session,
    sessions_before_earnings,
)


def test_sessions_before_earnings_excludes_endpoints():
    assert sessions_before_earnings(
        as_of_session=date(2026, 8, 14), earnings_date=date(2026, 8, 28)
    ) == 9


def test_sessions_before_earnings_skips_thanksgiving():
    assert sessions_before_earnings(
        as_of_session=date(2026, 11, 25), earnings_date=date(2026, 11, 30)
    ) == 1


def test_breakout_run_allowed_before_and_after_grace():
    assert breakout_run_allowed(datetime(2026, 8, 14, 20, 0, tzinfo=timezone.utc)) is False
    assert breakout_run_allowed(datetime(2026, 8, 14, 20, 20, tzinfo=timezone.utc)) is True


def test_saturday_allowed_and_latest_completed_is_friday():
    saturday = datetime(2026, 8, 15, 15, 0, tzinfo=timezone.utc)
    assert breakout_run_allowed(saturday) is True
    assert latest_completed_session(saturday) == date(2026, 8, 14)

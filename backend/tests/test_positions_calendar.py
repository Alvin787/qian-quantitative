"""Unit tests for session day index calendar."""

from __future__ import annotations

from datetime import date

import pytest

from backend.positions.calendar import parse_session_date, session_day_index


def test_session_day_index_mon_to_thu() -> None:
    assert session_day_index(date(2026, 8, 10), date(2026, 8, 13)) == 3


def test_session_day_index_same_day() -> None:
    assert session_day_index(date(2026, 8, 10), date(2026, 8, 10)) == 0


def test_session_day_index_weekend_spanning() -> None:
    # entry Fri 2026-08-07, as_of Mon 2026-08-10 → day_index 1
    assert session_day_index(date(2026, 8, 7), date(2026, 8, 10)) == 1


def test_session_day_index_as_of_before_entry() -> None:
    with pytest.raises(ValueError):
        session_day_index(date(2026, 8, 13), date(2026, 8, 10))


def test_parse_session_date() -> None:
    assert parse_session_date("2026-08-10") == date(2026, 8, 10)


def test_parse_session_date_malformed() -> None:
    with pytest.raises(ValueError):
        parse_session_date("not-a-date")

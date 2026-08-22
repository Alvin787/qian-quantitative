from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from backend.marketdata.calendar import xnys

SESSION_TZ = "America/New_York"  # documentary constant; dates are naive YYYY-MM-DD session dates


def parse_session_date(value: str) -> date:
    """Parse YYYY-MM-DD; raise ValueError if malformed."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid session date: {value!r}") from exc


def session_day_index(entry_date: date, as_of_date: date) -> int:
    """
    Require as_of_date >= entry_date.
    Count XNYS sessions in (entry_date, as_of_date] with entry_date as day 0.
    Example: entry=2026-08-10 (Mon), as_of=2026-08-13 (Thu) -> 3.
    Example: entry=2026-08-10, as_of=2026-08-10 -> 0.
    Raise ValueError if as_of < entry.
    """
    if as_of_date < entry_date:
        raise ValueError("as_of_date must be >= entry_date")
    if as_of_date == entry_date:
        return 0

    start = pd.Timestamp(entry_date + timedelta(days=1))
    end = pd.Timestamp(as_of_date)
    if start > end:
        return 0
    return int(len(xnys().sessions_in_range(start, end)))

from datetime import date, timedelta

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
    Count Mon–Fri dates from entry_date to as_of_date with entry_date as day 0
    (if entry_date is Sat/Sun, still treat it as day 0 but subsequent index only
    advances on weekdays — simplest rule: start at 0; for each calendar day
    after entry up to as_of inclusive of progression: if that day is weekday,
    increment. Equivalently: number of weekdays in (entry, as_of] ).
    Example: entry=2026-08-10 (Mon), as_of=2026-08-13 (Thu) -> 3.
    Example: entry=2026-08-10, as_of=2026-08-10 -> 0.
    Raise ValueError if as_of < entry.
    """
    if as_of_date < entry_date:
        raise ValueError("as_of_date must be >= entry_date")

    index = 0
    current = entry_date + timedelta(days=1)
    while current <= as_of_date:
        if current.weekday() < 5:  # Mon–Fri
            index += 1
        current += timedelta(days=1)
    return index

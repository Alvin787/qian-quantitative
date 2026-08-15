from dataclasses import dataclass


@dataclass(frozen=True)
class StopLevel:
    label: str  # "33%" | "66%" | "100%"
    price: float
    shares: int
    r_fraction: float  # 0.33 | 0.66 | 1.0


def split_tranches(shares: int) -> tuple[int, int, int]:
    """q = shares // 3; return (q, q, shares - 2*q). Require shares >= 0."""
    if shares < 0:
        raise ValueError("shares must be >= 0")
    q = shares // 3
    return (q, q, shares - 2 * q)


def build_initial_stop_book(
    *, shares: int, entry_price: float, final_stop: float
) -> list[StopLevel]:
    """
    Require entry_price > final_stop > 0 and shares >= 0.
    distance = entry_price - final_stop
    prices: entry - 0.33*distance, entry - 0.66*distance, final_stop
    shares from split_tranches(shares) in label order 33%, 66%, 100%.
    """
    if not (entry_price > final_stop > 0):
        raise ValueError("entry_price > final_stop > 0 required")
    if shares < 0:
        raise ValueError("shares must be >= 0")

    distance = entry_price - final_stop
    t33, t66, t100 = split_tranches(shares)
    return [
        StopLevel(
            label="33%",
            price=entry_price - 0.33 * distance,
            shares=t33,
            r_fraction=0.33,
        ),
        StopLevel(
            label="66%",
            price=entry_price - 0.66 * distance,
            shares=t66,
            r_fraction=0.66,
        ),
        StopLevel(
            label="100%",
            price=final_stop,
            shares=t100,
            r_fraction=1.0,
        ),
    ]

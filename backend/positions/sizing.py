from __future__ import annotations

from dataclasses import dataclass
from math import floor

from backend.positions.stops import StopLevel, build_initial_stop_book


@dataclass(frozen=True)
class SizeResult:
    method: str  # "fixed_pct" | "kelly" | "half_kelly"
    equity: float
    risk_pct: float  # percent of equity actually used after clamp
    risk_dollars: float
    entry_price: float
    final_stop: float
    r_per_share: float  # entry - final_stop
    shares: int
    stop_book: list[StopLevel]
    expected_full_stop_r: float  # (1/3)*0.33 + (1/3)*0.66 + (1/3)*1.0 == 0.663...
    kelly_f_star: float | None
    suggested_risk_pct: float | None
    suggested_shares: int | None


def kelly_fraction(*, win_rate: float, avg_win_r: float, avg_loss_r: float) -> float:
    """
    b = avg_win_r / avg_loss_r
    return win_rate - (1 - win_rate) / b
    Caller validates win_rate in (0,1), avg_win_r > 0, avg_loss_r > 0.
    """
    b = avg_win_r / avg_loss_r
    return win_rate - (1 - win_rate) / b


def compute_size(
    *,
    equity: float,
    entry_price: float,
    final_stop: float,
    method: str = "fixed_pct",
    risk_pct: float = 0.5,
    max_risk_pct: float = 1.0,
    win_rate: float | None = None,
    avg_win_r: float | None = None,
    avg_loss_r: float | None = None,
    adr_pct: float | None = None,
) -> SizeResult:
    """
    Validation precedence (raise ValueError with message; router maps to HTTP 400):
    1. equity > 0, entry_price > final_stop > 0, max_risk_pct > 0
    2. method in {"fixed_pct","kelly","half_kelly"}
    3. if method == fixed_pct: 0 < risk_pct <= max_risk_pct
    4. if method in kelly|half_kelly: win_rate, avg_win_r, avg_loss_r required and valid;
       f_star = kelly_fraction(...); if method half_kelly: f = f_star/2 else f = f_star;
       if f <= 0: raise ValueError("Kelly fraction is non-positive (no edge)")
       risk_pct = min(100.0 * f, max_risk_pct)
    5. r_per_share = entry_price - final_stop
       risk_dollars = equity * (risk_pct / 100.0)
       shares = floor(risk_dollars / r_per_share)  # int
       if shares < 1: raise ValueError("Computed shares < 1")
    6. stop_book = build_initial_stop_book(...)
       expected_full_stop_r = 0.33/3 + 0.66/3 + 1.0/3
    7. if adr_pct is not None and adr_pct > 0:
       suggested_risk_pct = clamp(risk_pct * (4.0 / adr_pct), 0.25, max_risk_pct)
       suggested_shares = floor(equity * suggested_risk_pct/100 / r_per_share)
       else both None
    """
    if not (equity > 0):
        raise ValueError("equity must be > 0")
    if not (entry_price > final_stop > 0):
        raise ValueError("entry_price > final_stop > 0 required")
    if not (max_risk_pct > 0):
        raise ValueError("max_risk_pct must be > 0")

    if method not in {"fixed_pct", "kelly", "half_kelly"}:
        raise ValueError('method must be "fixed_pct", "kelly", or "half_kelly"')

    kelly_f_star: float | None = None

    if method == "fixed_pct":
        if not (0 < risk_pct <= max_risk_pct):
            raise ValueError("risk_pct must satisfy 0 < risk_pct <= max_risk_pct")
    else:
        if win_rate is None or avg_win_r is None or avg_loss_r is None:
            raise ValueError("win_rate, avg_win_r, and avg_loss_r are required for Kelly methods")
        if not (0 < win_rate < 1):
            raise ValueError("win_rate must be in (0, 1)")
        if not (avg_win_r > 0):
            raise ValueError("avg_win_r must be > 0")
        if not (avg_loss_r > 0):
            raise ValueError("avg_loss_r must be > 0")

        f_star = kelly_fraction(
            win_rate=win_rate, avg_win_r=avg_win_r, avg_loss_r=avg_loss_r
        )
        kelly_f_star = f_star
        f = f_star / 2 if method == "half_kelly" else f_star
        if f <= 0:
            raise ValueError("Kelly fraction is non-positive (no edge)")
        risk_pct = min(100.0 * f, max_risk_pct)

    r_per_share = entry_price - final_stop
    risk_dollars = equity * (risk_pct / 100.0)
    shares = int(floor(risk_dollars / r_per_share))
    if shares < 1:
        raise ValueError("Computed shares < 1")

    stop_book = build_initial_stop_book(
        shares=shares, entry_price=entry_price, final_stop=final_stop
    )
    expected_full_stop_r = 0.33 / 3 + 0.66 / 3 + 1.0 / 3

    suggested_risk_pct: float | None = None
    suggested_shares: int | None = None
    if adr_pct is not None and adr_pct > 0:
        suggested_risk_pct = max(0.25, min(max_risk_pct, risk_pct * (4.0 / adr_pct)))
        suggested_shares = int(floor(equity * suggested_risk_pct / 100 / r_per_share))

    return SizeResult(
        method=method,
        equity=equity,
        risk_pct=risk_pct,
        risk_dollars=risk_dollars,
        entry_price=entry_price,
        final_stop=final_stop,
        r_per_share=r_per_share,
        shares=shares,
        stop_book=stop_book,
        expected_full_stop_r=expected_full_stop_r,
        kelly_f_star=kelly_f_star,
        suggested_risk_pct=suggested_risk_pct,
        suggested_shares=suggested_shares,
    )

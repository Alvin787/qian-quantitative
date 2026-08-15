from __future__ import annotations

from dataclasses import dataclass, field

from backend.positions.calendar import parse_session_date, session_day_index
from backend.positions.stops import StopLevel, build_initial_stop_book


@dataclass(frozen=True)
class PlanAction:
    code: str
    severity: str  # "info" | "action" | "alert"
    message: str


@dataclass(frozen=True)
class PlanResult:
    day_index: int
    phase: str  # "day0_init" | "day0_2" | "day3" | "day4_plus"
    entry_price: float
    final_stop: float
    r_per_share: float
    net_shares: int
    unrealized_r: float | None
    stop_mode: str  # "three_tier" | "breakeven" | "orl"
    stop_book: list[StopLevel]
    mental_stop: str | None  # e.g. "10-MA" when day_index >= 4
    actions: list[PlanAction] = field(default_factory=list)


def atr_extension(*, current_price: float, ma50: float, atr_pct: float) -> float:
    """((current_price - ma50) / ma50 * 100.0) / atr_pct"""
    return ((current_price - ma50) / ma50 * 100.0) / atr_pct


def _singular_be_book(*, shares: int, entry_price: float) -> list[StopLevel]:
    return [
        StopLevel(
            label="BE",
            price=entry_price,
            shares=shares,
            r_fraction=0.0,
        )
    ]


def compute_plan(
    *,
    shares: int,
    entry_price: float,
    final_stop: float,
    entry_date: str,
    as_of_date: str,
    current_price: float | None = None,
    shave_2r_taken: bool = False,
    day3_partial_taken: bool = False,
    consolidated_to_be: bool = False,
    ma10: float | None = None,  # noqa: ARG001 — reserved for future / display
    ma50: float | None = None,
    atr_pct: float | None = None,
    close_below_10ma_date: str | None = None,
    orl: float | None = None,
    stops_33_hit: bool = False,
    stops_66_hit: bool = False,
    prior_day_high: float | None = None,
    rescale_alert_triggered: bool = False,
    sideways_consolidation: bool = False,
    extension_override: float | None = None,
) -> PlanResult:
    """
    Validation: shares >= 1; entry_price > final_stop > 0; parse dates;
    day_index = session_day_index(...).
    """
    if shares < 1:
        raise ValueError("shares must be >= 1")
    if not (entry_price > final_stop > 0):
        raise ValueError("entry_price > final_stop > 0 required")

    entry_d = parse_session_date(entry_date)
    as_of_d = parse_session_date(as_of_date)
    day_index = session_day_index(entry_d, as_of_d)

    r_per_share = entry_price - final_stop
    unrealized_r = (
        (current_price - entry_price) / r_per_share
        if current_price is not None
        else None
    )

    if day_index == 0:
        phase = (
            "day0_2"
            if unrealized_r is not None and unrealized_r >= 2
            else "day0_init"
        )
    elif 1 <= day_index <= 2:
        phase = "day0_2"
    elif day_index == 3:
        phase = "day3"
    else:
        phase = "day4_plus"

    net_shares = shares
    stop_book = build_initial_stop_book(
        shares=shares, entry_price=entry_price, final_stop=final_stop
    )
    stop_mode = "three_tier"
    mental_stop: str | None = None
    actions: list[PlanAction] = []
    effective_consolidated = consolidated_to_be
    # Honor already-consolidated state immediately so stop_book matches the flag
    # even when SHAVE / Day-3 / Day-4+ rebuild paths are skipped.
    if effective_consolidated:
        stop_book = _singular_be_book(shares=net_shares, entry_price=entry_price)
        stop_mode = "breakeven"

    # A. Parabolic 4R before Day 4
    if unrealized_r is not None and unrealized_r >= 4 and day_index < 4:
        actions.append(
            PlanAction(
                code="PARABOLIC_4R_TO_BE",
                severity="action",
                message=(
                    "Unrealized >= 4R before Day 4: consolidate all remaining "
                    "risk to a singular stop at breakeven."
                ),
            )
        )
        effective_consolidated = True
        stop_book = _singular_be_book(shares=net_shares, entry_price=entry_price)
        stop_mode = "breakeven"

    # B. 2R shave Days 0–2
    if (
        (not shave_2r_taken)
        and unrealized_r is not None
        and unrealized_r >= 2
        and day_index <= 2
    ):
        sell = net_shares // 3
        if sell >= 1:
            net_shares -= sell
            actions.append(
                PlanAction(
                    code="SHAVE_2R",
                    severity="action",
                    message=(
                        f"Days 0-2 and >=2R: sell {sell} shares "
                        f"(33% of prior net); resize stops to new net {net_shares}."
                    ),
                )
            )
            if not effective_consolidated:
                stop_book = build_initial_stop_book(
                    shares=net_shares,
                    entry_price=entry_price,
                    final_stop=final_stop,
                )
            else:
                stop_book = _singular_be_book(
                    shares=net_shares, entry_price=entry_price
                )
                stop_mode = "breakeven"

    # C. Day 3 size-down + singular BE
    if day_index == 3:
        if not day3_partial_taken and not shave_2r_taken:
            sell = net_shares // 3
            if sell >= 1:
                net_shares -= sell
                actions.append(
                    PlanAction(
                        code="DAY3_SIZE_DOWN",
                        severity="action",
                        message=f"Day 3: sell {sell} shares (33% of net).",
                    )
                )
        actions.append(
            PlanAction(
                code="DAY3_CONSOLIDATE_BE",
                severity="action",
                message=(
                    "Day 3: consolidate all remaining stops to a singular "
                    "stop at breakeven."
                ),
            )
        )
        stop_book = _singular_be_book(shares=net_shares, entry_price=entry_price)
        stop_mode = "breakeven"
        effective_consolidated = True

    # D. Day 4+ / consolidated BE + ORL routine
    if day_index >= 4 or effective_consolidated:
        if day_index >= 4:
            mental_stop = "10-MA"
            if stop_mode != "orl":
                stop_mode = "breakeven"
                stop_book = _singular_be_book(
                    shares=net_shares, entry_price=entry_price
                )
            actions.append(
                PlanAction(
                    code="POST4_MENTAL_10MA",
                    severity="info",
                    message=(
                        "Day 4+: hard stop at breakeven; mental stop is the 10-MA. "
                        "Do not tighten unless close below 10-MA."
                    ),
                )
            )
        if close_below_10ma_date:
            close_d = parse_session_date(close_below_10ma_date)
            as_of = parse_session_date(as_of_date)
            if as_of == close_d:
                actions.append(
                    PlanAction(
                        code="ORL_MARK_CLOSE",
                        severity="alert",
                        message=(
                            "Close below 10-MA today: keep hard stop at "
                            "breakeven overnight; tomorrow run ORL routine."
                        ),
                    )
                )
            elif session_day_index(close_d, as_of) >= 1:
                if orl is not None and orl > 0:
                    stop_book = [
                        StopLevel(
                            label="ORL",
                            price=orl,
                            shares=net_shares,
                            r_fraction=0.0,
                        )
                    ]
                    stop_mode = "orl"
                    actions.append(
                        PlanAction(
                            code="ORL_SET",
                            severity="action",
                            message=(
                                f"After 5-minute opening range: move hard stop "
                                f"from breakeven to ORL={orl}."
                            ),
                        )
                    )
                else:
                    actions.append(
                        PlanAction(
                            code="ORL_PENDING",
                            severity="action",
                            message=(
                                "Keep stop at breakeven until 5-minute OR forms; "
                                "then move hard stop to that ORL."
                            ),
                        )
                    )
                actions.append(
                    PlanAction(
                        code="ORL_RESET_IF_SURVIVES",
                        severity="info",
                        message=(
                            "If not stopped by EOD: next premarket reset hard "
                            "stop to breakeven and set a new ORL after the next "
                            "5-minute OR."
                        ),
                    )
                )

    # Extension resolution (once, before E–H)
    if extension_override is not None:
        extension: float | None = extension_override
    elif (
        current_price is not None
        and ma50 is not None
        and atr_pct is not None
        and ma50 > 0
        and atr_pct > 0
    ):
        extension = atr_extension(
            current_price=current_price, ma50=ma50, atr_pct=atr_pct
        )
    else:
        extension = None

    # E. CATALYST_10X_ATR (nuance i)
    if (
        day_index == 0
        and extension is not None
        and extension >= 10
        and (
            shave_2r_taken
            or any(a.code == "SHAVE_2R" for a in actions)
        )
    ):
        actions.append(
            PlanAction(
                code="CATALYST_10X_ATR",
                severity="alert",
                message=(
                    "Day 0 hit 10x ATR% from 50-MA after 2R shave: at Day 1 open, "
                    "sell another 33% of net as partial profit."
                ),
            )
        )

    # F. POST4_EXTENSION_SHAVE (nuance ii)
    if day_index >= 4 and extension is not None and extension >= 8:
        sell = net_shares // 3
        if sell >= 1:
            net_shares -= sell
            stop_book = _singular_be_book(
                shares=net_shares, entry_price=entry_price
            )
            stop_mode = "breakeven"
            actions.append(
                PlanAction(
                    code="POST4_EXTENSION_SHAVE",
                    severity="action",
                    message=(
                        f"Day 4+ and >=8x ATR% from 50-MA: sell {sell} shares "
                        f"(33% of net); keep BE hard stop + 10-MA mental."
                    ),
                )
            )

    # G. RESCALE_AFTER_STOP (nuance iii)
    if day_index < 4 and (stops_33_hit or stops_66_hit):
        pdh_part = (
            f" ({prior_day_high})" if prior_day_high is not None else ""
        )
        actions.append(
            PlanAction(
                code="RESCALE_ALERT",
                severity="alert",
                message=(
                    f"Set price alert at prior day high{pdh_part}. "
                    "If triggered, inverse-pyramid add 50% of remaining shares."
                ),
            )
        )
        if rescale_alert_triggered:
            add = net_shares // 2
            if add >= 1:
                net_shares += add
                if stop_mode == "breakeven" or effective_consolidated:
                    stop_book = _singular_be_book(
                        shares=net_shares, entry_price=entry_price
                    )
                else:
                    stop_book = build_initial_stop_book(
                        shares=net_shares,
                        entry_price=entry_price,
                        final_stop=final_stop,
                    )
                actions.append(
                    PlanAction(
                        code="RESCALE_ADD",
                        severity="action",
                        message=(
                            f"Alert triggered: add {add} shares "
                            f"(50% of prior remaining). New net {net_shares}. "
                            "Combined attempt must stay <=1R."
                        ),
                    )
                )

    # H. ADD_ON_CONSOLIDATION (nuance iv)
    if (
        day_index >= 4
        and sideways_consolidation
        and (extension is None or extension < 4)
    ):
        add = net_shares // 2
        if add >= 1:
            net_shares += add
            stop_book = _singular_be_book(
                shares=net_shares, entry_price=entry_price
            )
            stop_mode = "breakeven"
            actions.append(
                PlanAction(
                    code="ADD_ON_CONSOLIDATION",
                    severity="action",
                    message=(
                        f"Sideways consolidation below 4x ATR% from 50-MA: "
                        f"add {add} shares (50% of prior net). Keep single-trade "
                        f"identity; trail with 10-MA mental."
                    ),
                )
            )

    return PlanResult(
        day_index=day_index,
        phase=phase,
        entry_price=entry_price,
        final_stop=final_stop,
        r_per_share=r_per_share,
        net_shares=net_shares,
        unrealized_r=unrealized_r,
        stop_mode=stop_mode,
        stop_book=stop_book,
        mental_stop=mental_stop,
        actions=actions,
    )

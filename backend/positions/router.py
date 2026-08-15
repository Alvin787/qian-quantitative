from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.positions.plan import compute_plan
from backend.positions.sizing import compute_size

router = APIRouter(prefix="/api/positions", tags=["positions"])


class SizeRequest(BaseModel):
    equity: float
    entry_price: float
    final_stop: float
    method: str = "fixed_pct"
    risk_pct: float = 0.5
    max_risk_pct: float = 1.0
    win_rate: float | None = None
    avg_win_r: float | None = None
    avg_loss_r: float | None = None
    adr_pct: float | None = None


class StopLevelResponse(BaseModel):
    label: str
    price: float
    shares: int
    r_fraction: float


class SizeResponse(BaseModel):
    method: str
    equity: float
    risk_pct: float
    risk_dollars: float
    entry_price: float
    final_stop: float
    r_per_share: float
    shares: int
    stop_book: list[StopLevelResponse]
    expected_full_stop_r: float
    kelly_f_star: float | None = None
    suggested_risk_pct: float | None = None
    suggested_shares: int | None = None


class PlanRequest(BaseModel):
    shares: int
    entry_price: float
    final_stop: float
    entry_date: str
    as_of_date: str
    current_price: float | None = None
    shave_2r_taken: bool = False
    day3_partial_taken: bool = False
    consolidated_to_be: bool = False
    ma10: float | None = None
    ma50: float | None = None
    atr_pct: float | None = None
    close_below_10ma_date: str | None = None
    orl: float | None = None
    stops_33_hit: bool = False
    stops_66_hit: bool = False
    prior_day_high: float | None = None
    rescale_alert_triggered: bool = False
    sideways_consolidation: bool = False
    extension_override: float | None = None


class PlanActionResponse(BaseModel):
    code: str
    severity: str
    message: str


class PlanResponse(BaseModel):
    day_index: int
    phase: str
    entry_price: float
    final_stop: float
    r_per_share: float
    net_shares: int
    unrealized_r: float | None
    stop_mode: str
    stop_book: list[StopLevelResponse]
    mental_stop: str | None
    actions: list[PlanActionResponse]


@router.post("/size", response_model=SizeResponse)
def post_size(body: SizeRequest) -> SizeResponse:
    try:
        result = compute_size(
            equity=body.equity,
            entry_price=body.entry_price,
            final_stop=body.final_stop,
            method=body.method,
            risk_pct=body.risk_pct,
            max_risk_pct=body.max_risk_pct,
            win_rate=body.win_rate,
            avg_win_r=body.avg_win_r,
            avg_loss_r=body.avg_loss_r,
            adr_pct=body.adr_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SizeResponse(**asdict(result))


@router.post("/plan", response_model=PlanResponse)
def post_plan(body: PlanRequest) -> PlanResponse:
    try:
        result = compute_plan(
            shares=body.shares,
            entry_price=body.entry_price,
            final_stop=body.final_stop,
            entry_date=body.entry_date,
            as_of_date=body.as_of_date,
            current_price=body.current_price,
            shave_2r_taken=body.shave_2r_taken,
            day3_partial_taken=body.day3_partial_taken,
            consolidated_to_be=body.consolidated_to_be,
            ma10=body.ma10,
            ma50=body.ma50,
            atr_pct=body.atr_pct,
            close_below_10ma_date=body.close_below_10ma_date,
            orl=body.orl,
            stops_33_hit=body.stops_33_hit,
            stops_66_hit=body.stops_66_hit,
            prior_day_high=body.prior_day_high,
            rescale_alert_triggered=body.rescale_alert_triggered,
            sideways_consolidation=body.sideways_consolidation,
            extension_override=body.extension_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlanResponse(**asdict(result))

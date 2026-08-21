from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from backend.pnl.store import PnlStore

router = APIRouter(prefix="/api/pnl", tags=["pnl"])

pnl_store = PnlStore()


def get_store() -> PnlStore:
    return pnl_store


def set_store(store: PnlStore) -> None:
    """Test helper to swap the process-wide PnL store."""
    global pnl_store
    pnl_store = store


class TradeBody(BaseModel):
    ticker: str
    entry_date: str
    entry_price: float
    shares: float
    exit_date: str | None = None
    exit_price: float | None = None
    notes: str = ""
    account: str = ""


def _fields(body: TradeBody) -> dict[str, Any]:
    return {
        "ticker": body.ticker,
        "entry_date": body.entry_date,
        "entry_price": body.entry_price,
        "shares": body.shares,
        "exit_date": body.exit_date,
        "exit_price": body.exit_price,
        "notes": body.notes,
        "account": body.account,
    }


@router.get("/")
def get_ledger() -> dict[str, Any]:
    try:
        return get_store().snapshot()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/trades")
def create_trade(body: TradeBody) -> dict[str, Any]:
    try:
        return get_store().create(**_fields(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/trades/{trade_id}")
def update_trade(trade_id: str, body: TradeBody) -> dict[str, Any]:
    try:
        return get_store().update(trade_id, **_fields(body))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="trade not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/trades/{trade_id}", status_code=204)
def delete_trade(trade_id: str) -> Response:
    try:
        get_store().delete(trade_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="trade not found") from exc
    return Response(status_code=204)

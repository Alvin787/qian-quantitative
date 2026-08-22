from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from backend.watchlists.review import WatchlistReviewService
from backend.watchlists.store import WatchlistStore

router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])

watchlist_store = WatchlistStore()


def get_store() -> WatchlistStore:
    return watchlist_store


def set_store(store: WatchlistStore) -> None:
    """Test helper to swap the process-wide watchlist store."""
    global watchlist_store
    watchlist_store = store


watchlist_review_service = WatchlistReviewService(get_store())


def get_review_service() -> WatchlistReviewService:
    return watchlist_review_service


def set_review_service(service: WatchlistReviewService) -> None:
    global watchlist_review_service
    watchlist_review_service = service


class NameBody(BaseModel):
    ticker: str
    list: str
    note: str | None = None
    group: str | None = None
    chart_checklist: dict[str, Any] | None = None


class MoveBody(BaseModel):
    list: str


def _added_at() -> str:
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


@router.get("/")
def get_funnel() -> dict[str, Any]:
    try:
        return asdict(get_store().get())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/names")
def put_name(body: NameBody) -> dict[str, Any]:
    try:
        name = get_store().upsert(
            body.ticker,
            body.list,
            note=body.note,
            group=body.group,
            chart_checklist=body.chart_checklist,
            added_at=_added_at(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(name)


@router.post("/names/{ticker}/move")
def move_name(ticker: str, body: MoveBody) -> dict[str, Any]:
    try:
        name = get_store().move(ticker, body.list)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticker not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(name)


@router.post("/names/{ticker}/checklist")
def update_checklist(ticker: str, body: dict[str, Any]) -> dict[str, Any]:
    try:
        name = get_store().update_checklist(ticker, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticker not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(name)


@router.delete("/names/{ticker}", status_code=204)
def delete_name(ticker: str) -> Response:
    try:
        get_store().delete(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticker not found") from exc
    return Response(status_code=204)


@router.post("/reviews", status_code=202)
def start_review() -> dict[str, Any]:
    try:
        meta = get_review_service().start_review()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return asdict(meta)


@router.get("/reviews/{review_id}")
def get_review(review_id: str) -> dict[str, Any]:
    meta = get_review_service().get_review(review_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="review not found")
    return asdict(meta)

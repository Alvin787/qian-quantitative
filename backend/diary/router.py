"""FastAPI routes for market diary snapshots."""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.diary.etf import avg_dollar_volume_20, build_etf_row, load_history
from backend.diary.service import DiaryService, snapshot_to_dict
from backend.diary.store import (
    DiaryStore,
    FocusItem,
    NamedGroup,
    Narrative,
    Watchlists,
)

router = APIRouter(prefix="/api/diary", tags=["diary"])

diary_service = DiaryService()
diary_store = DiaryStore()

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class EtfRowResponse(BaseModel):
    symbol: str
    last: float
    daily_change_pct: float
    pct_from_52w_low: float
    pct_from_52w_high: float
    short_term_trend: str
    priority: bool = False
    ratio_to: str | None = None
    ratio_value: float | None = None


class SectionStatusResponse(BaseModel):
    status: str
    source: str
    error: str | None = None


class DiarySnapshotResponse(BaseModel):
    as_of: str
    as_of_date: str
    market: list[EtfRowResponse] = Field(default_factory=list)
    market_ratios: list[EtfRowResponse] = Field(default_factory=list)
    submarket: list[EtfRowResponse] = Field(default_factory=list)
    sectors: list[EtfRowResponse] = Field(default_factory=list)
    breadth: Any | None = None
    cnbc: Any | None = None
    sections: dict[str, SectionStatusResponse] = Field(default_factory=dict)


class NarrativePutBody(BaseModel):
    date: str
    body: str


class NarrativeResponse(BaseModel):
    date: str
    body: str
    updated_at: str


class FocusItemBody(BaseModel):
    ticker: str
    group: str = ""
    note: str = ""


class NamedGroupBody(BaseModel):
    name: str
    tickers: list[str] = Field(default_factory=list)


class WatchlistsBody(BaseModel):
    focus: list[FocusItemBody] = Field(default_factory=list)
    stalk: list[str] = Field(default_factory=list)
    themes: list[NamedGroupBody] = Field(default_factory=list)
    leadership: list[NamedGroupBody] = Field(default_factory=list)


class WatchlistsResponse(BaseModel):
    focus: list[FocusItemBody] = Field(default_factory=list)
    stalk: list[str] = Field(default_factory=list)
    themes: list[NamedGroupBody] = Field(default_factory=list)
    leadership: list[NamedGroupBody] = Field(default_factory=list)


class EnrichRequest(BaseModel):
    tickers: list[str] = Field(default_factory=list)


class EnrichRowResponse(BaseModel):
    ticker: str
    daily_change_pct: float | None = None
    pct_from_52w_low: float | None = None
    avg_dollar_volume_20: float | None = None
    error: str | None = None


class EnrichResponse(BaseModel):
    rows: list[EnrichRowResponse] = Field(default_factory=list)

def get_service() -> DiaryService:
    return diary_service


def set_service(service: DiaryService) -> None:
    """Test helper to swap the process-wide diary service."""
    global diary_service
    diary_service = service


def get_store() -> DiaryStore:
    return diary_store


def set_store(store: DiaryStore) -> None:
    """Test helper to swap the process-wide diary store."""
    global diary_store
    diary_store = store


def _validate_date(date: str) -> None:
    if not _DATE_RE.match(date):
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")


@router.get("/snapshot", response_model=DiarySnapshotResponse)
def get_diary_snapshot() -> dict[str, Any]:
    snapshot = get_service().build_snapshot()
    return snapshot_to_dict(snapshot)


@router.get("/narrative", response_model=NarrativeResponse)
def get_narrative(
    date: str = Query(..., description="YYYY-MM-DD"),
) -> dict[str, Any]:
    _validate_date(date)
    try:
        narrative = get_store().get_narrative(date)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if narrative is None:
        raise HTTPException(status_code=404, detail="narrative not found")
    return asdict(narrative)


@router.put("/narrative", response_model=NarrativeResponse)
def put_narrative(body: NarrativePutBody) -> dict[str, Any]:
    _validate_date(body.date)
    narrative: Narrative = get_store().put_narrative(body.date, body.body)
    return asdict(narrative)


def _watchlists_from_body(body: WatchlistsBody) -> Watchlists:
    return Watchlists(
        focus=[
            FocusItem(ticker=item.ticker, group=item.group, note=item.note)
            for item in body.focus
        ],
        stalk=list(body.stalk),
        themes=[
            NamedGroup(name=group.name, tickers=list(group.tickers))
            for group in body.themes
        ],
        leadership=[
            NamedGroup(name=group.name, tickers=list(group.tickers))
            for group in body.leadership
        ],
    )


@router.get("/watchlists", response_model=WatchlistsResponse)
def get_watchlists() -> dict[str, Any]:
    try:
        return asdict(get_store().get_watchlists())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/watchlists", response_model=WatchlistsResponse)
def put_watchlists(body: WatchlistsBody) -> dict[str, Any]:
    saved = get_store().put_watchlists(_watchlists_from_body(body))
    return asdict(saved)


@router.post("/watchlists/enrich", response_model=EnrichResponse)
def enrich_watchlists(body: EnrichRequest) -> dict[str, Any]:
    seen: set[str] = set()
    tickers: list[str] = []
    for raw in body.tickers:
        ticker = raw.strip().upper()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        tickers.append(ticker)
        if len(tickers) >= 50:
            break

    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        try:
            history = load_history(ticker)
            etf = build_etf_row(ticker, history)
            rows.append(
                {
                    "ticker": ticker,
                    "daily_change_pct": etf.daily_change_pct,
                    "pct_from_52w_low": etf.pct_from_52w_low,
                    "avg_dollar_volume_20": avg_dollar_volume_20(history),
                    "error": None,
                }
            )
        except Exception as exc:  # noqa: BLE001 — per-ticker isolation
            rows.append(
                {
                    "ticker": ticker,
                    "daily_change_pct": None,
                    "pct_from_52w_low": None,
                    "avg_dollar_volume_20": None,
                    "error": str(exc),
                }
            )
    return {"rows": rows}

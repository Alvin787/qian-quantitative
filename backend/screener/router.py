"""FastAPI routes for strategy-scoped screener runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.screener.run_service import ScreenerRunService, screener_run_service
from backend.screener.screens import get_screen
from backend.screener.strategies import get_strategy, list_strategies

router = APIRouter(prefix="/api/screener", tags=["screener"])


class StartRunRequest(BaseModel):
    options: dict[str, Any] = Field(default_factory=dict)


class ScreenInfo(BaseModel):
    id: str
    label: str
    url: str


class StrategyInfo(BaseModel):
    id: str
    label: str
    description: str
    views: list[str]
    default_view: str
    screens: list[ScreenInfo]


class StrategyListResponse(BaseModel):
    strategies: list[StrategyInfo]


class RunSummary(BaseModel):
    run_id: str
    strategy_id: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    scored: int | None = None
    passed: int | None = None
    skipped: int | None = None
    files: dict[str, str] | None = None
    views: list[str] | None = None
    notes: str | None = None
    regime_ok: bool | None = None
    error: str | None = None
    legacy: bool = False


class RunListResponse(BaseModel):
    runs: list[RunSummary]


class ResultsResponse(BaseModel):
    run_id: str
    strategy_id: str
    view: str
    status: str
    columns: list[str]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int


def get_service() -> ScreenerRunService:
    return screener_run_service


def set_service(service: ScreenerRunService) -> None:
    """Test helper to swap the process-wide run service."""
    global screener_run_service
    screener_run_service = service


def _require_strategy(strategy_id: str):
    try:
        return get_strategy(strategy_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unknown strategy: {strategy_id}"
        ) from exc


def _resolve_view(definition, view: str | None) -> str:
    resolved = definition.views[0] if view is None else view
    if resolved not in definition.views:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Query param 'view' must be one of: {', '.join(definition.views)}"
            ),
        )
    return resolved


@router.get("/strategies", response_model=StrategyListResponse)
def get_strategies() -> dict[str, Any]:
    strategies = []
    for definition in list_strategies():
        screens = []
        for screen_id in definition.screen_ids:
            screen = get_screen(screen_id)
            screens.append(
                {"id": screen.id, "label": screen.label, "url": screen.url}
            )
        strategies.append(
            {
                "id": definition.id,
                "label": definition.label,
                "description": definition.description,
                "views": list(definition.views),
                "default_view": definition.views[0],
                "screens": screens,
            }
        )
    return {"strategies": strategies}


@router.post("/{strategy_id}/runs", status_code=202, response_model=RunSummary)
def start_strategy_run(
    strategy_id: str, body: StartRunRequest | None = None
) -> dict[str, Any]:
    definition = _require_strategy(strategy_id)
    payload = body or StartRunRequest()
    options = payload.options or {}
    for key in options:
        if key not in definition.allowed_options:
            raise HTTPException(status_code=400, detail=f"Unsupported option: {key}")
    service = get_service()
    try:
        meta = service.start_run(strategy_id, options)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return meta


@router.get("/{strategy_id}/runs", response_model=RunListResponse)
def list_strategy_runs(strategy_id: str) -> dict[str, Any]:
    _require_strategy(strategy_id)
    service = get_service()
    return {"runs": service.list_runs(strategy_id)}


@router.get("/{strategy_id}/runs/{run_id}", response_model=RunSummary)
def get_strategy_run(strategy_id: str, run_id: str) -> dict[str, Any]:
    _require_strategy(strategy_id)
    service = get_service()
    meta = service.get_run(strategy_id, run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return meta


@router.get("/{strategy_id}/runs/{run_id}/results", response_model=ResultsResponse)
def get_strategy_run_results(
    strategy_id: str,
    run_id: str,
    view: str | None = Query(default=None),
) -> dict[str, Any]:
    definition = _require_strategy(strategy_id)
    parsed = _resolve_view(definition, view)
    service = get_service()
    try:
        meta, columns, rows = service.load_results(strategy_id, run_id, parsed)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "run_id": run_id,
        "strategy_id": strategy_id,
        "view": parsed,
        "status": meta.get("status", "completed"),
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }


@router.get("/{strategy_id}/runs/{run_id}/download")
def download_strategy_run_results(
    strategy_id: str,
    run_id: str,
    view: str | None = Query(default=None),
) -> FileResponse:
    definition = _require_strategy(strategy_id)
    parsed = _resolve_view(definition, view)
    service = get_service()
    meta = service.get_run(strategy_id, run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("status") == "running":
        raise HTTPException(status_code=409, detail=f"Run {run_id} is still running")

    path = service.resolve_csv(strategy_id, run_id, parsed)
    if path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Results not found for run {run_id} view={parsed}",
        )
    return FileResponse(
        path,
        media_type="text/csv",
        filename=path.name,
    )

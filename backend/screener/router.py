"""FastAPI routes for the hybrid Discover screener."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.screener.hybrid_run_service import HybridRunService, ViewName, hybrid_run_service

router = APIRouter(prefix="/api/screener/hybrid", tags=["hybrid-screener"])


class StartRunRequest(BaseModel):
    skip_earnings: bool = False
    keep_biotech: bool = False


class RunSummary(BaseModel):
    run_id: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    scored: int | None = None
    passed: int | None = None
    skipped: int | None = None
    all_results_file: str | None = None
    candidates_file: str | None = None
    regime_ok: bool | None = None
    regime_note: str | None = None
    error: str | None = None
    legacy: bool = False


class RunListResponse(BaseModel):
    runs: list[RunSummary]


class ResultsResponse(BaseModel):
    run_id: str
    view: Literal["all", "candidates"]
    status: str
    columns: list[str]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int


def _parse_view(view: str) -> ViewName:
    if view not in ("all", "candidates"):
        raise HTTPException(
            status_code=400,
            detail="Query param 'view' must be 'all' or 'candidates'",
        )
    return view  # type: ignore[return-value]


def get_service() -> HybridRunService:
    return hybrid_run_service


def set_service(service: HybridRunService) -> None:
    """Test helper to swap the process-wide run service."""
    global hybrid_run_service
    hybrid_run_service = service


@router.post("/runs", status_code=202, response_model=RunSummary)
def start_hybrid_run(body: StartRunRequest | None = None) -> dict[str, Any]:
    service = get_service()
    payload = body or StartRunRequest()
    try:
        meta = service.start_run(
            skip_earnings=payload.skip_earnings,
            keep_biotech=payload.keep_biotech,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return meta


@router.get("/runs", response_model=RunListResponse)
def list_hybrid_runs() -> dict[str, Any]:
    service = get_service()
    return {"runs": service.list_runs()}


@router.get("/runs/{run_id}", response_model=RunSummary)
def get_hybrid_run(run_id: str) -> dict[str, Any]:
    service = get_service()
    meta = service.get_run(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return meta


@router.get("/runs/{run_id}/results", response_model=ResultsResponse)
def get_hybrid_run_results(
    run_id: str,
    view: str = Query(default="all"),
) -> dict[str, Any]:
    service = get_service()
    parsed = _parse_view(view)
    try:
        meta, columns, rows = service.load_results(run_id, parsed)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "run_id": run_id,
        "view": parsed,
        "status": meta.get("status", "completed"),
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }


@router.get("/runs/{run_id}/download")
def download_hybrid_run_results(
    run_id: str,
    view: str = Query(default="all"),
) -> FileResponse:
    service = get_service()
    parsed = _parse_view(view)
    meta = service.get_run(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("status") == "running":
        raise HTTPException(status_code=409, detail=f"Run {run_id} is still running")

    path = service.resolve_csv(run_id, parsed)
    if path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Results not found for run {run_id} view={parsed}",
        )
    filename = path.name
    return FileResponse(
        path,
        media_type="text/csv",
        filename=filename,
    )

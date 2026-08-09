from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ViewName = str  # "all" | "candidates"


@dataclass
class StrategyRunResult:
    run_id: str
    paths: dict[ViewName, Path]  # keys must equal StrategyDefinition.views
    scored: int
    passed: int | None
    skipped: int
    skipped_tickers: list[str] = field(default_factory=list)
    notes: str | None = None
    regime_ok: bool | None = None


RunCallable = Callable[..., StrategyRunResult]  # called as run(outdir=Path, run_id=str, options=dict[str, Any])


@dataclass(frozen=True)
class StrategyDefinition:
    id: str  # URL slug
    label: str
    description: str
    screen_ids: tuple[str, ...]
    views: tuple[ViewName, ...]  # views[0] is the default view
    view_files: dict[ViewName, str]  # view -> filename template containing "{run_id}"
    meta_file: str  # filename template containing "{run_id}"
    allowed_options: tuple[str, ...]
    run: RunCallable
    supports_legacy: bool = False

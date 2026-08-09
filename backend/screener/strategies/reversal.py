from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.screener.hybrid_screener import run_screener
from backend.screener.screens import get_screen
from backend.screener.strategies.base import StrategyDefinition, StrategyRunResult


def run_reversal(*, outdir: Path, run_id: str, options: dict[str, Any]) -> StrategyRunResult:
    result = run_screener(
        url=get_screen("reversal_pullback").url,
        outdir=outdir,
        run_id=run_id,
        skip_earnings=bool(options.get("skip_earnings", False)),
        keep_biotech=bool(options.get("keep_biotech", False)),
    )
    return StrategyRunResult(
        run_id=result.run_id,
        paths={"all": result.all_results_path, "candidates": result.candidates_path},
        scored=result.scored,
        passed=result.passed,
        skipped=result.skipped,
        skipped_tickers=result.skipped_tickers,
        notes=result.regime_note,
        regime_ok=result.regime_ok,
    )


REVERSAL = StrategyDefinition(
    id="reversal",
    label="Reversal",
    description="Hybrid buy-the-dip: pullbacks to the 20/50-MA inside a confirmed uptrend.",
    screen_ids=("reversal_pullback",),
    views=("candidates", "all"),
    view_files={
        "all": "hybrid_all_results_{run_id}.csv",
        "candidates": "hybrid_candidates_{run_id}.csv",
    },
    meta_file="hybrid_run_{run_id}.json",
    allowed_options=("skip_earnings", "keep_biotech"),
    run=run_reversal,
    supports_legacy=True,
)

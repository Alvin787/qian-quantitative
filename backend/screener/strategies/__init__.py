from __future__ import annotations

from backend.screener.strategies.base import (
    StrategyDefinition,
    StrategyRunResult,
    ViewName,
)
from backend.screener.strategies.breakout import BREAKOUT
from backend.screener.strategies.reversal import REVERSAL

STRATEGIES: dict[str, StrategyDefinition] = {
    BREAKOUT.id: BREAKOUT,
    REVERSAL.id: REVERSAL,
}


def get_strategy(strategy_id: str) -> StrategyDefinition:
    return STRATEGIES[strategy_id]


def list_strategies() -> list[StrategyDefinition]:
    return list(STRATEGIES.values())


__all__ = [
    "STRATEGIES",
    "StrategyDefinition",
    "StrategyRunResult",
    "ViewName",
    "get_strategy",
    "list_strategies",
]

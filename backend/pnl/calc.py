"""Derived PnL fields for a long-only trade ledger."""

from __future__ import annotations

from typing import Any


def cost_value(entry_price: float, shares: float) -> float:
    return round(entry_price * shares, 2)


def is_closed(exit_date: str | None, exit_price: float | None) -> bool:
    return exit_date is not None and exit_price is not None


def realized_pnl(
    entry_price: float, exit_price: float | None, shares: float
) -> float | None:
    if exit_price is None:
        return None
    return round((exit_price - entry_price) * shares, 2)


def realized_percent(entry_price: float, exit_price: float | None) -> float | None:
    if exit_price is None or entry_price == 0:
        return None
    return round((exit_price - entry_price) / entry_price * 100, 2)


def enrich_trade(trade: dict[str, Any]) -> dict[str, Any]:
    entry_price = float(trade["entry_price"])
    shares = float(trade["shares"])
    exit_date = trade.get("exit_date")
    exit_price = trade.get("exit_price")
    closed = is_closed(exit_date, exit_price)
    pnl = realized_pnl(entry_price, exit_price, shares) if closed else None
    percent = realized_percent(entry_price, exit_price) if closed else None
    return {
        **trade,
        "value": cost_value(entry_price, shares),
        "pnl": pnl,
        "percent": percent,
        "status": "closed" if closed else "open",
    }


def ledger_totals(trades: list[dict[str, Any]]) -> dict[str, float | int]:
    realized = [t["pnl"] for t in trades if t.get("pnl") is not None]
    open_trades = [t for t in trades if t.get("status") != "closed"]
    return {
        "total_pnl": round(sum(realized), 2),
        "open_count": len(open_trades),
        "closed_count": len(trades) - len(open_trades),
        "open_value": round(sum(float(t["value"]) for t in open_trades), 2),
    }

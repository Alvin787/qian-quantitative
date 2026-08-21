from __future__ import annotations

import json
import math
import re
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.pnl.calc import enrich_trade, ledger_totals

DATA_DIR = Path(__file__).resolve().parent / "pnl_data"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Trade:
    id: str
    ticker: str
    entry_date: str
    entry_price: float
    shares: float
    exit_date: str | None = None
    exit_price: float | None = None
    notes: str = ""
    account: str = ""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _require_date(value: str, *, field: str) -> str:
    if not _DATE_RE.match(value):
        raise ValueError(f"{field} must be YYYY-MM-DD")
    return value


def _optional_date(value: str | None, *, field: str) -> str | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    return _require_date(value, field=field)


def _require_positive(value: float, *, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be greater than 0")
    return number


def _optional_price(value: float | None, *, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be 0 or greater")
    return number


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise ValueError("empty ticker")
    return normalized


def _validate_trade(
    *,
    ticker: str,
    entry_date: str,
    entry_price: float,
    shares: float,
    exit_date: str | None,
    exit_price: float | None,
    notes: str,
    account: str,
) -> tuple[str, str, float, float, str | None, float | None, str, str]:
    ticker = _normalize_ticker(ticker)
    entry_date = _require_date(entry_date.strip(), field="entry_date")
    entry_price = _require_positive(entry_price, field="entry_price")
    shares = _require_positive(shares, field="shares")
    exit_date = _optional_date(exit_date, field="exit_date")
    exit_price = _optional_price(exit_price, field="exit_price")
    if exit_date is not None and exit_date < entry_date:
        raise ValueError("exit_date must be on or after entry_date")
    return (
        ticker,
        entry_date,
        entry_price,
        shares,
        exit_date,
        exit_price,
        notes.strip() if notes else "",
        account.strip() if account else "",
    )


def _parse_trade(item: object) -> Trade:
    if not isinstance(item, dict):
        raise TypeError("trade must be an object")
    exit_price_raw = item.get("exit_price")
    validated = _validate_trade(
        ticker=str(item.get("ticker", "")),
        entry_date=str(item.get("entry_date", "")),
        entry_price=item["entry_price"],
        shares=item["shares"],
        exit_date=item.get("exit_date"),
        exit_price=None if exit_price_raw is None else exit_price_raw,
        notes=str(item.get("notes", "")),
        account=str(item.get("account", "")),
    )
    trade_id = str(item.get("id", "")).strip()
    if not trade_id:
        raise ValueError("missing trade id")
    return Trade(
        id=trade_id,
        ticker=validated[0],
        entry_date=validated[1],
        entry_price=validated[2],
        shares=validated[3],
        exit_date=validated[4],
        exit_price=validated[5],
        notes=validated[6],
        account=validated[7],
    )


def _sort_trades(trades: list[Trade]) -> list[Trade]:
    def key(trade: Trade) -> tuple[int, str, str]:
        open_first = 0 if trade.exit_date and trade.exit_price is not None else 1
        recency = trade.exit_date or trade.entry_date
        return (open_first, recency, trade.id)

    return sorted(trades, key=key, reverse=True)


class PnlStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else DATA_DIR
        self._lock = threading.Lock()

    def _path(self) -> Path:
        return self.root / "trades.json"

    def snapshot(self) -> dict:
        with self._lock:
            trades, updated_at = self._get_unlocked()
        views = [enrich_trade(asdict(trade)) for trade in _sort_trades(trades)]
        return {
            "updated_at": updated_at,
            "trades": views,
            **ledger_totals(views),
        }

    def create(
        self,
        *,
        ticker: str,
        entry_date: str,
        entry_price: float,
        shares: float,
        exit_date: str | None = None,
        exit_price: float | None = None,
        notes: str = "",
        account: str = "",
    ) -> dict:
        validated = _validate_trade(
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            exit_date=exit_date,
            exit_price=exit_price,
            notes=notes,
            account=account,
        )
        trade = Trade(
            id=uuid.uuid4().hex,
            ticker=validated[0],
            entry_date=validated[1],
            entry_price=validated[2],
            shares=validated[3],
            exit_date=validated[4],
            exit_price=validated[5],
            notes=validated[6],
            account=validated[7],
        )
        with self._lock:
            trades, _ = self._get_unlocked()
            trades.append(trade)
            self._put_unlocked(trades)
        return enrich_trade(asdict(trade))

    def update(
        self,
        trade_id: str,
        *,
        ticker: str,
        entry_date: str,
        entry_price: float,
        shares: float,
        exit_date: str | None = None,
        exit_price: float | None = None,
        notes: str = "",
        account: str = "",
    ) -> dict:
        validated = _validate_trade(
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            exit_date=exit_date,
            exit_price=exit_price,
            notes=notes,
            account=account,
        )
        with self._lock:
            trades, _ = self._get_unlocked()
            for index, existing in enumerate(trades):
                if existing.id != trade_id:
                    continue
                trades[index] = Trade(
                    id=trade_id,
                    ticker=validated[0],
                    entry_date=validated[1],
                    entry_price=validated[2],
                    shares=validated[3],
                    exit_date=validated[4],
                    exit_price=validated[5],
                    notes=validated[6],
                    account=validated[7],
                )
                self._put_unlocked(trades)
                return enrich_trade(asdict(trades[index]))
            raise KeyError(trade_id)

    def delete(self, trade_id: str) -> None:
        with self._lock:
            trades, _ = self._get_unlocked()
            kept = [trade for trade in trades if trade.id != trade_id]
            if len(kept) == len(trades):
                raise KeyError(trade_id)
            self._put_unlocked(kept)

    def _get_unlocked(self) -> tuple[list[Trade], str]:
        path = self._path()
        if not path.is_file():
            return [], _now_utc()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("ledger root must be an object")
            trades_raw = data.get("trades") or []
            if not isinstance(trades_raw, list):
                raise TypeError("trades must be a list")
            trades = [_parse_trade(item) for item in trades_raw]
            updated_at = str(data.get("updated_at") or _now_utc())
            return trades, updated_at
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"corrupt trades.json: {exc}") from exc

    def _put_unlocked(self, trades: list[Trade]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path()
        tmp = path.with_suffix(".json.tmp")
        payload = {
            "updated_at": _now_utc(),
            "trades": [asdict(trade) for trade in trades],
        }
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

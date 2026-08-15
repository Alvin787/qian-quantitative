from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

LISTS: tuple[str, ...] = ("master", "stalk", "focus", "back")
DATA_DIR = Path(__file__).resolve().parent / "watchlist_data"


@dataclass
class Gates:
    adr_pct: float | None = None
    adr_ok: bool | None = None
    avg_dollar_vol: float | None = None
    liq_ok: bool | None = None
    close: float | None = None
    sma10: float | None = None
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    above_10: bool | None = None
    above_20: bool | None = None
    rising_10: bool | None = None
    rising_20: bool | None = None
    extension_x: float | None = None
    ext_ok: bool | None = None
    rs_3m_pp: float | None = None
    rs_ok: bool | None = None
    earnings_date: str | None = None
    days_to_earnings: int | None = None
    earn_ok: str | None = None
    biotech: bool | None = None
    declining_200: bool | None = None
    room_to_200_adr: float | None = None
    room_to_200_ok: bool | None = None
    volume_dryup: bool | None = None
    range_compress: bool | None = None
    near_10_20: bool | None = None


@dataclass
class Name:
    ticker: str
    list: str
    added_at: str
    source_screens: list[str] = field(default_factory=list)
    industry: str = ""
    note: str = ""
    group: str = ""
    readiness: str = "unscored"
    queue_reason: str | None = None
    fail_reasons: str = ""
    gates: Gates = field(default_factory=Gates)
    last_scored_at: str | None = None


@dataclass
class ReviewMeta:
    review_id: str | None = None
    status: str = "idle"
    started_at: str | None = None
    finished_at: str | None = None
    ingested: int | None = None
    scored: int | None = None
    unknown: int | None = None
    error: str | None = None
    notes: str | None = None
    breakout_run_id: str | None = None


@dataclass
class FunnelState:
    updated_at: str
    review: ReviewMeta = field(default_factory=ReviewMeta)
    names: list[Name] = field(default_factory=list)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_name(item: object) -> Name:
    if not isinstance(item, dict):
        raise TypeError("name must be an object")
    gates_raw = item.get("gates") or {}
    if not isinstance(gates_raw, dict):
        raise TypeError("gates must be an object")
    source_screens = item.get("source_screens") or []
    return Name(
        ticker=item["ticker"],
        list=item["list"],
        added_at=item["added_at"],
        source_screens=list(source_screens),
        industry=item.get("industry", ""),
        note=item.get("note", ""),
        group=item.get("group", ""),
        readiness=item.get("readiness", "unscored"),
        queue_reason=item.get("queue_reason"),
        fail_reasons=item.get("fail_reasons", ""),
        gates=Gates(**gates_raw),
        last_scored_at=item.get("last_scored_at"),
    )


def _state_from_data(data: object) -> FunnelState:
    if not isinstance(data, dict):
        raise TypeError("funnel root must be an object")
    review_raw = data.get("review") or {}
    if not isinstance(review_raw, dict):
        raise TypeError("review must be an object")
    names_raw = data.get("names") or []
    if not isinstance(names_raw, list):
        raise TypeError("names must be a list")
    return FunnelState(
        updated_at=data["updated_at"],
        review=ReviewMeta(**review_raw),
        names=_unique_names([_parse_name(item) for item in names_raw]),
    )


def _unique_names(names: list[Name]) -> list[Name]:
    by_ticker: dict[str, Name] = {}
    for name in names:
        ticker = str(name.ticker).strip().upper()
        name.ticker = ticker
        by_ticker[ticker] = name
    return list(by_ticker.values())


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise ValueError("empty ticker")
    return normalized


def _require_list(list_name: str) -> str:
    if list_name not in LISTS:
        raise ValueError(f"invalid list: {list_name}")
    return list_name


class WatchlistStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else DATA_DIR
        self._lock = threading.Lock()

    def _path(self) -> Path:
        return self.root / "funnel.json"

    def get(self) -> FunnelState:
        with self._lock:
            return self._get_unlocked()

    def put(self, state: FunnelState) -> FunnelState:
        with self._lock:
            return self._put_unlocked(state)

    def upsert(
        self,
        ticker: str,
        list_name: str,
        *,
        note: str | None = None,
        group: str | None = None,
        added_at: str,
    ) -> Name:
        ticker = _normalize_ticker(ticker)
        list_name = _require_list(list_name)
        with self._lock:
            state = self._get_unlocked()
            existing = next((name for name in state.names if name.ticker == ticker), None)
            if existing is not None:
                existing.list = list_name
                if note is not None:
                    existing.note = note
                if group is not None:
                    existing.group = group
                self._put_unlocked(state)
                return existing
            name = Name(ticker, list_name, added_at, readiness="unscored")
            state.names.append(name)
            self._put_unlocked(state)
            return name

    def move(self, ticker: str, list_name: str) -> Name:
        ticker = _normalize_ticker(ticker)
        list_name = _require_list(list_name)
        with self._lock:
            state = self._get_unlocked()
            for name in state.names:
                if name.ticker == ticker:
                    name.list = list_name
                    self._put_unlocked(state)
                    return name
            raise KeyError(ticker)

    def delete(self, ticker: str) -> None:
        ticker = ticker.strip().upper()
        with self._lock:
            state = self._get_unlocked()
            kept = [name for name in state.names if name.ticker != ticker]
            if len(kept) == len(state.names):
                raise KeyError(ticker)
            state.names = kept
            self._put_unlocked(state)

    def apply_review(self, scored: list[Name], *, review: ReviewMeta) -> FunnelState:
        from backend.watchlists.review import queue_reason

        scored_by_ticker = {name.ticker: name for name in scored}
        with self._lock:
            current = self._get_unlocked()
            merged: list[Name] = []
            for name in current.names:
                scored_name = scored_by_ticker.get(name.ticker)
                if scored_name is None:
                    merged.append(name)
                    continue
                merged.append(
                    replace(
                        scored_name,
                        list=name.list,
                        note=name.note,
                        group=name.group,
                        added_at=name.added_at,
                        queue_reason=queue_reason(
                            readiness=scored_name.readiness,
                            list_name=name.list,
                            newly_ingested=scored_name.queue_reason == "new_ingest",
                        ),
                    )
                )
            current.names = merged
            current.review = review
            return self._put_unlocked(current)

    def _get_unlocked(self) -> FunnelState:
        path = self._path()
        if not path.is_file():
            return FunnelState(
                updated_at=_now_utc(),
                review=ReviewMeta(),
                names=[],
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _state_from_data(data)
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"corrupt funnel.json: {exc}") from exc

    def _put_unlocked(self, state: FunnelState) -> FunnelState:
        self.root.mkdir(parents=True, exist_ok=True)
        state.updated_at = _now_utc()
        state.names = _unique_names(state.names)
        path = self._path()
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        return state

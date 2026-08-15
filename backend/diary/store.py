"""Filesystem persistence for per-day diary narratives."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "diary_data"


@dataclass
class Narrative:
    date: str  # YYYY-MM-DD
    body: str
    updated_at: str  # ISO-8601


@dataclass
class FocusItem:
    ticker: str
    group: str = ""
    note: str = ""


@dataclass
class NamedGroup:
    name: str
    tickers: list[str]


@dataclass
class Watchlists:
    focus: list[FocusItem] = field(default_factory=list)
    stalk: list[str] = field(default_factory=list)
    themes: list[NamedGroup] = field(default_factory=list)
    leadership: list[NamedGroup] = field(default_factory=list)


class DiaryStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else DATA_DIR

    def _path(self, date: str) -> Path:
        return self.root / f"narrative_{date}.json"

    def _watchlists_path(self) -> Path:
        return self.root / "watchlists.json"

    def get_narrative(self, date: str) -> Narrative | None:
        path = self._path(date)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Narrative(
                date=data["date"],
                body=data["body"],
                updated_at=data["updated_at"],
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"corrupt narrative for {date}: {exc}") from exc

    def put_narrative(self, date: str, body: str) -> Narrative:
        self.root.mkdir(parents=True, exist_ok=True)
        narrative = Narrative(
            date=date,
            body=body,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._path(date).write_text(
            json.dumps(asdict(narrative), indent=2) + "\n",
            encoding="utf-8",
        )
        return narrative

    def get_watchlists(self) -> Watchlists:
        path = self._watchlists_path()
        if not path.is_file():
            return Watchlists()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("watchlists root must be an object")
            return Watchlists(
                focus=[
                    FocusItem(
                        ticker=item.get("ticker", ""),
                        group=item.get("group", ""),
                        note=item.get("note", ""),
                    )
                    for item in data.get("focus", [])
                ],
                stalk=list(data.get("stalk", [])),
                themes=[
                    NamedGroup(
                        name=group.get("name", ""),
                        tickers=list(group.get("tickers", [])),
                    )
                    for group in data.get("themes", [])
                ],
                leadership=[
                    NamedGroup(
                        name=group.get("name", ""),
                        tickers=list(group.get("tickers", [])),
                    )
                    for group in data.get("leadership", [])
                ],
            )
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"corrupt watchlists.json: {exc}") from exc

    def put_watchlists(self, watchlists: Watchlists) -> Watchlists:
        self.root.mkdir(parents=True, exist_ok=True)
        self._watchlists_path().write_text(
            json.dumps(asdict(watchlists), indent=2) + "\n",
            encoding="utf-8",
        )
        return watchlists

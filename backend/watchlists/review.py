from __future__ import annotations

import threading
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from backend.marketdata.calendar import latest_completed_session
from backend.marketdata.eod_cache import read_eod_cache, write_eod_cache
from backend.marketdata.yahoo import frames_from_yf_download, yahoo_symbol
from backend.screener.screens import SCREEN_FAMILY, SCREENS, screen_family_count
from backend.screener.strategies.breakout import BREAKOUT_SCREEN_IDS
from backend.watchlists.gates import ny_today, score_history
from backend.watchlists.store import FunnelState, Name, ReviewMeta, WatchlistStore

if TYPE_CHECKING:
    from backend.screener.run_service import ScreenerRunService

_LOADER_TIMEOUT_S = 15
_BATCH_CHUNK_SIZE = 25
REQUIRED_CSV_COLUMNS = ("ticker", "industry", "source_screens")
KNOWN_SCREEN_IDS = set(SCREENS) | set(SCREEN_FAMILY)
READINESS_RANK = {
    "chart_review_ready": 0,
    "stalk_ready": 1,
    "watch": 2,
    "earnings_blocked": 3,
    "data_incomplete": 4,
    "disrupted": 5,
    "excluded": 6,
    "unscored": 7,
    "unknown": 8,
}


def parse_source_screens(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        parts = [str(item).strip() for item in raw]
        return [part for part in parts if part]
    return [part.strip() for part in str(raw).split(";") if part.strip()]


def _order_screens(screens: list[str]) -> list[str]:
    known = [sid for sid in BREAKOUT_SCREEN_IDS if sid in screens]
    seen = set(known)
    leftovers = []
    for sid in screens:
        if sid not in seen:
            leftovers.append(sid)
            seen.add(sid)
    return known + leftovers


def _union_screens(existing: list[str], incoming: list[str]) -> list[str]:
    combined = list(existing)
    for sid in incoming:
        if sid not in combined:
            combined.append(sid)
    return _order_screens(combined)


def ingest_breakout_rows(
    state: FunnelState, rows: list[dict], *, added_at: str
) -> tuple[FunnelState, set[str]]:
    names = [
        replace(
            name,
            source_screens=list(name.source_screens),
            historical_source_screens=list(name.historical_source_screens),
        )
        for name in state.names
    ]
    by_ticker = {name.ticker: name for name in names}
    added: set[str] = set()
    incoming_tickers: set[str] = set()
    for row in rows:
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        incoming_tickers.add(ticker)
        screens = parse_source_screens(row.get("source_screens"))
        current = _order_screens(screens)
        industry = str(row.get("industry") or "")
        existing = by_ticker.get(ticker)
        if existing is None:
            name = Name(
                ticker=ticker,
                list="master",
                added_at=added_at,
                source_screens=current,
                historical_source_screens=list(current),
                industry=industry,
                readiness="unscored",
            )
            names.append(name)
            by_ticker[ticker] = name
            added.add(ticker)
        else:
            existing.historical_source_screens = _union_screens(
                _union_screens(existing.historical_source_screens, existing.source_screens),
                screens,
            )
            existing.source_screens = current
            if industry:
                existing.industry = industry
    for name in names:
        if name.ticker not in incoming_tickers:
            name.source_screens = []
    return replace(state, names=names), added


def queue_reason(
    *,
    readiness: str,
    list_name: str,
    newly_ingested: bool,
    source_screens: list[str] | None = None,
    historical_source_screens: list[str] | None = None,
) -> str | None:
    if newly_ingested:
        return "new_ingest"
    if (
        source_screens == []
        and historical_source_screens
        and list_name != "back"
    ):
        return "dropped"
    if readiness == "disrupted" and list_name != "back":
        return "disrupted"
    if readiness == "excluded" and list_name != "back":
        return "excluded"
    if readiness == "unknown":
        return "score_failed"
    if readiness == "data_incomplete" and list_name in {"master", "stalk", "focus"}:
        return "data_incomplete"
    if readiness == "chart_review_ready" and list_name in {"master", "stalk"}:
        return "chart_review_ready"
    if readiness == "earnings_blocked" and list_name in {"stalk", "focus"}:
        return "earnings_blocked"
    if readiness == "stalk_ready" and list_name == "master":
        return "stalk_ready"
    return None


def validate_breakout_snapshot(*, meta: dict, rows: list[dict], expected_session: date) -> str | None:
    if meta.get("status") != "completed":
        return f"breakout run status {meta.get('status')!r} is not completed"
    expected_iso = expected_session.isoformat()
    as_of = meta.get("as_of_session")
    if as_of != expected_iso:
        return f"as_of_session {as_of!r} != expected {expected_iso}"
    if not rows:
        if meta.get("scored") not in (0, None):
            return "breakout results unreadable"
    else:
        keys = rows[0].keys() if isinstance(rows[0], dict) else []
        missing = [col for col in REQUIRED_CSV_COLUMNS if col not in keys]
        if missing:
            return f"missing columns: {missing}"
    scored = meta.get("scored")
    if isinstance(scored, int) and scored != len(rows):
        return f"scored {scored} != row count {len(rows)}"
    tickers = [str(row.get("ticker", "")).strip().upper() for row in rows]
    if any(not ticker for ticker in tickers):
        return "empty ticker"
    if len(tickers) != len(set(tickers)):
        return "duplicate tickers"
    for row in rows:
        screens = parse_source_screens(row.get("source_screens"))
        deduped = _order_screens(screens)
        for sid in screens:
            if sid not in KNOWN_SCREEN_IDS:
                return f"unknown screen id {sid}"
        if row.get("screen_count") not in (None, ""):
            try:
                if int(row["screen_count"]) != len(deduped):
                    return "screen_count mismatch"
            except (TypeError, ValueError):
                return "screen_count mismatch"
        if row.get("screen_family_count") not in (None, ""):
            try:
                if int(row["screen_family_count"]) != screen_family_count(deduped):
                    return "screen_family_count mismatch"
            except (TypeError, ValueError):
                return "screen_family_count mismatch"
    return None


def apply_review(
    store: WatchlistStore,
    scored: list[Name],
    *,
    review: ReviewMeta,
) -> FunnelState:
    return store.apply_review(scored, review=review)


def _as_date(value, default_fn):
    if value is None:
        return default_fn()
    if callable(value):
        return value()
    return value


def _funnel_sort_key(name: Name) -> tuple:
    family_count = screen_family_count(name.source_screens)
    screen_count = len(name.source_screens)
    rs_3m_pp = name.gates.rs_3m_pp
    return (
        READINESS_RANK.get(name.readiness, 99),
        -(family_count or 0),
        -(rs_3m_pp if rs_3m_pp is not None else -1e18),
        -(screen_count or 0),
        name.ticker,
    )


def _timeout_call(fn, *args, timeout_s: float = _LOADER_TIMEOUT_S):
    holder: dict[str, object] = {}

    def runner() -> None:
        try:
            holder["value"] = fn(*args)
        except Exception as exc:  # noqa: BLE001 — timeout wrapper maps errors to None
            holder["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive() or "error" in holder:
        return None
    return holder.get("value")


def _yf_history(ticker: str) -> pd.DataFrame | None:
    import yfinance as yf

    try:
        frame = yf.Ticker(yahoo_symbol(ticker)).history(period="2y", auto_adjust=True)
        if frame is None or frame.empty:
            return None
        missing = [col for col in ("Open", "High", "Low", "Close", "Volume") if col not in frame.columns]
        if missing:
            return None
        out = frame.loc[:, ["Open", "High", "Low", "Close", "Volume"]].copy()
        out.index = pd.DatetimeIndex(out.index)
        return out
    except Exception:
        return None


def _yf_earnings(ticker: str) -> date | None:
    import yfinance as yf

    try:
        calendar = yf.Ticker(yahoo_symbol(ticker)).calendar
        raw = None
        if isinstance(calendar, dict):
            raw = calendar.get("Earnings Date") or calendar.get("earningsDate")
            if isinstance(raw, (list, tuple)) and raw:
                raw = raw[0]
        elif isinstance(calendar, pd.DataFrame) and not calendar.empty:
            if "Earnings Date" in calendar.index:
                raw = calendar.loc["Earnings Date"].iloc[0]
            elif "Earnings Date" in calendar.columns:
                raw = calendar["Earnings Date"].iloc[0]
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw
        if isinstance(raw, pd.Timestamp):
            return raw.date()
    except Exception:
        return None
    return None


def _yf_download_batch(tickers: list[str], *, include_spy: bool = True) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    unique_tickers = list(dict.fromkeys(tickers))
    yf_tickers = [yahoo_symbol(t) for t in unique_tickers]
    if include_spy and "SPY" not in yf_tickers:
        yf_tickers.append("SPY")
    if not yf_tickers:
        return {}

    yf_frames: dict[str, pd.DataFrame] = {}

    for i in range(0, len(yf_tickers), _BATCH_CHUNK_SIZE):
        chunk = yf_tickers[i : i + _BATCH_CHUNK_SIZE]

        def _download_chunk(current_chunk: list[str]):
            return yf.download(
                tickers=current_chunk,
                period="2y",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                threads=min(4, len(current_chunk)),
                progress=False,
                timeout=20,
            )

        data = _timeout_call(_download_chunk, chunk, timeout_s=30)
        if data is not None and isinstance(data, pd.DataFrame) and not data.empty:
            chunk_frames = frames_from_yf_download(data, chunk)
            yf_frames.update(chunk_frames)

    mapped: dict[str, pd.DataFrame] = {}
    for original in unique_tickers:
        frame = yf_frames.get(yahoo_symbol(original))
        if frame is not None:
            mapped[original] = frame
    if include_spy:
        spy = yf_frames.get("SPY")
        if spy is not None:
            mapped["SPY"] = spy
    return mapped


def _default_load_history(ticker: str) -> pd.DataFrame | None:
    return _timeout_call(_yf_history, ticker, timeout_s=_LOADER_TIMEOUT_S)


def _default_load_spy() -> pd.DataFrame | None:
    return _timeout_call(_yf_history, "SPY", timeout_s=_LOADER_TIMEOUT_S)


def _default_load_earnings(ticker: str) -> date | None:
    return _timeout_call(_yf_earnings, ticker, timeout_s=10)


class WatchlistReviewService:
    def __init__(
        self,
        store: WatchlistStore,
        *,
        screener: ScreenerRunService | None = None,
        load_history=None,
        load_spy=None,
        load_earnings=None,
        load_history_batch=None,
        today=None,
        expected_session=None,
        cache_root: Path | None = None,
    ) -> None:
        self.store = store
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        if screener is None:
            from backend.screener.run_service import screener_run_service

            screener = screener_run_service
        self.screener = screener
        self._load_history_provided = load_history is not None
        self._load_history_batch = load_history_batch
        self._load_history = load_history if load_history is not None else _default_load_history
        self._load_spy = load_spy if load_spy is not None else _default_load_spy
        self._load_earnings = load_earnings if load_earnings is not None else _default_load_earnings
        self._today = today
        self._expected_session = expected_session
        if cache_root is None:
            cache_root = Path(__file__).resolve().parents[1] / "marketdata" / "eod_cache"
        self.cache_root = cache_root
        self.reconcile_stale()

    def _thread_live(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def reconcile_stale(self) -> None:
        if self._thread_live():
            return
        with self.store._lock:
            state = self.store._get_unlocked()
            if state.review.status != "running":
                return
            state.review.status = "failed"
            state.review.error = "interrupted by restart"
            state.review.finished_at = datetime.now(timezone.utc).isoformat()
            self.store._put_unlocked(state)

    def get_review(self, review_id: str) -> ReviewMeta | None:
        review = self.store.get().review
        if review.review_id == review_id:
            return review
        return None

    def start_review(self) -> ReviewMeta:
        with self._lock:
            with self.store._lock:
                state = self.store._get_unlocked()
                if self._thread_live() or state.review.status == "running":
                    raise RuntimeError("Review already in progress")
                review_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
                review = ReviewMeta(
                    review_id=review_id,
                    status="running",
                    started_at=datetime.now(timezone.utc).isoformat(),
                    finished_at=None,
                    ingested=None,
                    scored=None,
                    unknown=None,
                    error=None,
                    notes=None,
                    breakout_run_id=None,
                )
                state.review = review
                self.store._put_unlocked(state)
            thread = threading.Thread(
                target=self._worker,
                args=(review.review_id,),
                name=f"watchlist-review-{review.review_id}",
                daemon=True,
            )
            self._thread = thread
            thread.start()
            return review

    def _breakout_rows(self) -> tuple[list[dict], str | None, str | None, dict | None]:
        runs = self.screener.list_runs("breakout")
        completed = next((row for row in runs if row.get("status") == "completed"), None)
        if completed is None:
            return [], "no completed breakout run", None, None
        run_id = completed["run_id"]
        meta, _columns, rows = self.screener.load_results("breakout", run_id, "all")
        return rows, None, run_id, meta

    def _load_frames(self, tickers: list[str], expected: date | None = None) -> dict[str, pd.DataFrame | None]:
        if expected is None:
            expected = _as_date(self._expected_session, latest_completed_session)
        session_str = expected.isoformat() if hasattr(expected, "isoformat") else str(expected)
        unique_tickers = list(dict.fromkeys(tickers))
        cached_frames: dict[str, pd.DataFrame] = {}
        missing_tickers: list[str] = []

        for t in unique_tickers:
            cached = read_eod_cache(self.cache_root, session_str, yahoo_symbol(t))
            if cached is not None:
                cached_frames[t] = cached
            else:
                missing_tickers.append(t)

        cached_spy = read_eod_cache(self.cache_root, session_str, "SPY")
        spy_missing = cached_spy is None
        if not spy_missing:
            cached_frames["SPY"] = cached_spy

        if not missing_tickers and not spy_missing:
            return cached_frames

        if self._load_history_batch is not None:
            fresh_frames = self._load_history_batch(missing_tickers)
        elif self._load_history_provided:
            fresh_frames = {ticker: self._load_history(ticker) for ticker in missing_tickers}
            if spy_missing:
                spy_frame = self._load_spy()
                if spy_frame is not None:
                    fresh_frames["SPY"] = spy_frame
        else:
            fresh_frames = _yf_download_batch(missing_tickers, include_spy=spy_missing)

        if fresh_frames:
            for t, f in fresh_frames.items():
                if f is not None and isinstance(f, pd.DataFrame) and not f.empty:
                    write_eod_cache(self.cache_root, session_str, yahoo_symbol(t), f)

        combined: dict[str, pd.DataFrame | None] = dict(cached_frames)
        if fresh_frames:
            combined.update(fresh_frames)
        return combined

    def _score_name(
        self,
        name: Name,
        history,
        spy_history,
        earnings,
        expected: date,
        newly: set[str],
        *,
        earnings_required: bool,
    ) -> Name:
        result = score_history(
            industry=name.industry,
            history=history,
            spy_history=spy_history,
            earnings_date=earnings,
            today=expected,
            expected_session=expected,
            source_screens=name.source_screens,
            earnings_required=earnings_required,
        )
        return replace(
            name,
            readiness=result.readiness,
            queue_reason=queue_reason(
                readiness=result.readiness,
                list_name=name.list,
                newly_ingested=name.ticker in newly,
                source_screens=name.source_screens,
                historical_source_screens=name.historical_source_screens,
            ),
            fail_reasons=result.fail_reasons,
            gates=result.gates,
            last_scored_at=datetime.now(timezone.utc).isoformat(),
            screen_count=len(name.source_screens),
            screen_family_count=screen_family_count(name.source_screens),
        )

    def _mark_failed(self, review_id: str | None, error: str) -> None:
        finished = datetime.now(timezone.utc).isoformat()
        with self.store._lock:
            state = self.store._get_unlocked()
            if state.review.review_id != review_id:
                return
            state.review.status = "failed"
            state.review.error = error
            state.review.finished_at = finished
            self.store._put_unlocked(state)

    def _worker(self, review_id: str) -> None:
        try:
            today = _as_date(self._today, ny_today)
            expected = _as_date(self._expected_session, latest_completed_session)
            rows, notes, breakout_run_id, meta = self._breakout_rows()
            added_at = today.isoformat() if hasattr(today, "isoformat") else str(today)
            newly: set[str] = set()
            if breakout_run_id is None:
                notes = notes or "no completed breakout run"
            else:
                reason = validate_breakout_snapshot(
                    meta=meta or {},
                    rows=rows,
                    expected_session=expected,
                )
                if reason is not None:
                    self._mark_failed(review_id, reason)
                    return
                with self.store._lock:
                    current = self.store._get_unlocked()
                    ingested, newly = ingest_breakout_rows(current, rows, added_at=added_at)
                    self.store._put_unlocked(ingested)
            snapshot = self.store.get()
            tickers = [name.ticker for name in snapshot.names]
            frames = self._load_frames(tickers, expected)
            if "SPY" in frames and frames["SPY"] is not None:
                spy_history = frames["SPY"]
            else:
                spy_history = self._load_spy()
                if spy_history is not None and isinstance(spy_history, pd.DataFrame) and not spy_history.empty:
                    session_str = expected.isoformat() if hasattr(expected, "isoformat") else str(expected)
                    write_eod_cache(self.cache_root, session_str, "SPY", spy_history)
            scored = [
                self._score_name(
                    name,
                    frames.get(name.ticker),
                    spy_history,
                    None,
                    expected,
                    newly,
                    earnings_required=False,
                )
                for name in snapshot.names
            ]
            scored_by_ticker = {name.ticker: name for name in scored}
            for name in list(scored):
                if "liquid_leveraged_etf" in (name.source_screens or []):
                    continue
                if frames.get(name.ticker) is None:
                    continue
                if name.list in {"stalk", "focus"} or name.readiness in {
                    "chart_review_ready",
                    "stalk_ready",
                }:
                    earnings = self._load_earnings(name.ticker)
                    scored_by_ticker[name.ticker] = self._score_name(
                        name,
                        frames.get(name.ticker),
                        spy_history,
                        earnings,
                        expected,
                        newly,
                        earnings_required=True,
                    )
            scored = [scored_by_ticker[name.ticker] for name in scored]
            unknown = sum(1 for name in scored if name.readiness == "unknown")
            review = ReviewMeta(
                review_id=review_id,
                status="completed",
                started_at=snapshot.review.started_at,
                finished_at=datetime.now(timezone.utc).isoformat(),
                ingested=len(newly),
                scored=len(scored),
                unknown=unknown,
                error=None,
                notes=notes,
                breakout_run_id=breakout_run_id,
            )
            state = apply_review(self.store, scored, review=review)
            state.names.sort(key=_funnel_sort_key)
            self.store.put(state)
        except Exception as exc:  # noqa: BLE001 — persist any worker failure
            self._mark_failed(review_id, str(exc))
        finally:
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None

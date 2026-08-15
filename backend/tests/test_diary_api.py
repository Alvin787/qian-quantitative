"""Diary API tests with network mocked."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.diary.barchart import BarchartHistoryPoint
from backend.diary.cnbc import CnbcBrief
from backend.diary.etf import EtfRow
from backend.diary.service import BreadthBlock, DiaryService, DiarySnapshot
from backend.diary.store import DiaryStore
from backend.diary import router as diary_router
from backend.main import app


def _row(symbol: str, *, priority: bool = False) -> EtfRow:
    return EtfRow(
        symbol=symbol,
        last=100.0,
        daily_change_pct=1.25,
        pct_from_52w_low=10.0,
        pct_from_52w_high=-5.0,
        short_term_trend="Up, Above 20-MA",
        priority=priority,
    )


def _breadth() -> BreadthBlock:
    return BreadthBlock(
        mmtw_last=64.12,
        mmtw_history=[
            BarchartHistoryPoint(date="2026-08-04", last=52.0),
            BarchartHistoryPoint(date="2026-08-05", last=55.0),
            BarchartHistoryPoint(date="2026-08-06", last=58.5),
            BarchartHistoryPoint(date="2026-08-07", last=61.0),
            BarchartHistoryPoint(date="2026-08-08", last=64.12),
        ],
        mmtw_bullish_bias=True,
        finviz_new_highs=180,
        finviz_new_lows=92,
        finviz_net=88,
        nyhl=10.0,
        nahl=-3.0,
        sources={
            "mmtw": "barchart:$MMTW",
            "finviz_nhnl": "finviz:ta_newhigh/ta_newlow",
            "nyhl_nahl": "barchart:$NYHL+$NAHL",
        },
    )


def _cnbc() -> CnbcBrief:
    return CnbcBrief(
        title="5 Things to Know Before the Stock Market Opens",
        url=(
            "https://www.cnbc.com/2026/08/08/"
            "5-things-to-know-before-the-stock-market-opens.html"
        ),
        excerpt="Futures mixed ahead of the open.",
        published="2026-08-08",
    )


class FakeDiaryService(DiaryService):
    def build_snapshot(self) -> DiarySnapshot:
        return DiarySnapshot(
            as_of="2026-08-08T16:00:00+00:00",
            as_of_date="2026-08-08",
            market=[_row("RSP"), _row("QQQE"), _row("IWM")],
            market_ratios=[
                EtfRow(
                    symbol="RSP",
                    last=100.0,
                    daily_change_pct=1.0,
                    pct_from_52w_low=10.0,
                    pct_from_52w_high=-5.0,
                    short_term_trend="Up, Above 20-MA",
                    ratio_to="SPY",
                    ratio_value=0.5,
                )
            ],
            submarket=[_row("IJS"), _row("IJT")],
            sectors=[_row("XLE", priority=True), _row("XLK", priority=True)],
            breadth=_breadth(),
            cnbc=_cnbc(),
            sections={
                "market": {"status": "ok", "source": "yfinance", "error": None},
                "submarket": {"status": "ok", "source": "yfinance", "error": None},
                "sectors": {"status": "ok", "source": "yfinance", "error": None},
                "breadth": {
                    "status": "ok",
                    "source": "barchart+finviz",
                    "error": None,
                },
                "cnbc": {
                    "status": "ok",
                    "source": "cnbc:5-things-to-know",
                    "error": None,
                },
            },
        )


def test_get_diary_snapshot_returns_etf_sections():
    previous = diary_router.get_service()
    diary_router.set_service(FakeDiaryService())
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/snapshot")
        assert resp.status_code == 200
        body = resp.json()
        assert "market" in body
        assert "submarket" in body
        assert "sectors" in body
        assert len(body["market"]) == 3
        assert body["market"][0]["symbol"] == "RSP"
        assert len(body["submarket"]) == 2
        assert len(body["sectors"]) == 2
        assert body["sectors"][0]["priority"] is True
        assert body["breadth"] is not None
        assert "finviz_new_highs" in body["breadth"]
        assert "finviz_new_lows" in body["breadth"]
        assert "exchange_new_highs" not in body["breadth"]
        assert body["breadth"]["mmtw_last"] == 64.12
        assert body["breadth"]["finviz_new_highs"] == 180
        assert body["cnbc"] is not None
        assert body["cnbc"]["title"].startswith("5 Things")
        assert body["cnbc"]["url"].endswith(
            "5-things-to-know-before-the-stock-market-opens.html"
        )
        assert body["sections"]["cnbc"]["status"] == "ok"
        assert body["sections"]["cnbc"]["source"] == "cnbc:5-things-to-know"
        assert body["sections"]["market"]["status"] == "ok"
        assert body["sections"]["breadth"]["status"] == "ok"
        assert body["market_ratios"][0]["ratio_to"] == "SPY"
        assert "narrative" not in body
    finally:
        diary_router.set_service(previous)


def test_get_narrative_404(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/narrative", params={"date": "2026-08-08"})
        assert resp.status_code == 404
    finally:
        diary_router.set_store(previous)


def test_put_then_get_narrative_round_trip(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        put = client.put(
            "/api/diary/narrative",
            json={"date": "2026-08-08", "body": "Notes for today."},
        )
        assert put.status_code == 200
        put_body = put.json()
        assert put_body["date"] == "2026-08-08"
        assert put_body["body"] == "Notes for today."
        assert put_body["updated_at"]

        get = client.get("/api/diary/narrative", params={"date": "2026-08-08"})
        assert get.status_code == 200
        get_body = get.json()
        assert get_body["body"] == "Notes for today."
        assert get_body["updated_at"] == put_body["updated_at"]
    finally:
        diary_router.set_store(previous)


def test_narrative_invalid_date_400(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/narrative", params={"date": "08-08-2026"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "date must be YYYY-MM-DD"

        put = client.put(
            "/api/diary/narrative",
            json={"date": "08-08-2026", "body": "notes"},
        )
        assert put.status_code == 400
        assert put.json()["detail"] == "date must be YYYY-MM-DD"
    finally:
        diary_router.set_store(previous)


def test_get_narrative_corrupt_returns_500(tmp_path: Path):
    previous = diary_router.get_store()
    diary_router.set_store(DiaryStore(root=tmp_path))
    (tmp_path / "narrative_2026-08-08.json").write_text("{not-json", encoding="utf-8")
    client = TestClient(app)
    try:
        resp = client.get("/api/diary/narrative", params={"date": "2026-08-08"})
        assert resp.status_code == 500
        assert "corrupt narrative" in resp.json()["detail"]
    finally:
        diary_router.set_store(previous)


def test_cnbc_failure_preserves_etf_and_breadth(monkeypatch):
    """CNBC scrape errors must not blank market/submarket/sectors/breadth."""
    from backend.diary.service import DiaryService

    market_rows = [_row("RSP"), _row("QQQE")]
    breadth = _breadth()
    breadth_section = {
        "status": "ok",
        "source": "barchart+finviz",
        "error": None,
    }

    monkeypatch.setattr(
        "backend.diary.service._load_group",
        lambda symbols, *, priority_set=None: (
            (market_rows if symbols and symbols[0] == "RSP" else [_row(symbols[0])], [])
            if symbols
            else ([], [])
        ),
    )
    monkeypatch.setattr(
        "backend.diary.service.load_history",
        lambda symbol: (_ for _ in ()).throw(ValueError("no network")),
    )
    monkeypatch.setattr(
        "backend.diary.service._build_breadth",
        lambda: (breadth, breadth_section),
    )
    monkeypatch.setattr(
        "backend.diary.service.latest_five_things",
        lambda: (_ for _ in ()).throw(RuntimeError("cnbc unreachable")),
    )

    snapshot = DiaryService().build_snapshot()
    assert snapshot.cnbc is None
    assert snapshot.sections["cnbc"]["status"] == "error"
    assert snapshot.sections["cnbc"]["source"] == "cnbc:5-things-to-know"
    assert "cnbc unreachable" in (snapshot.sections["cnbc"]["error"] or "")
    assert len(snapshot.market) == 2
    assert snapshot.market[0].symbol == "RSP"
    assert snapshot.breadth is not None
    assert snapshot.breadth.mmtw_last == 64.12
    assert snapshot.sections["breadth"]["status"] == "ok"
    assert snapshot.sections["market"]["status"] == "ok"


def test_as_of_date_uses_us_eastern(monkeypatch):
    """UTC early morning can still be previous calendar day in US/Eastern."""
    from datetime import datetime, timezone

    from backend.diary.service import DiaryService

    fixed = datetime(2026, 8, 9, 3, 0, 0, tzinfo=timezone.utc)  # Aug 8 23:00 ET

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed.replace(tzinfo=None)
            return fixed.astimezone(tz)

    monkeypatch.setattr("backend.diary.service.datetime", _FixedDateTime)
    monkeypatch.setattr(
        "backend.diary.service._load_group",
        lambda symbols, *, priority_set=None: ([], []),
    )
    monkeypatch.setattr(
        "backend.diary.service.load_history",
        lambda symbol: (_ for _ in ()).throw(ValueError("no network")),
    )
    monkeypatch.setattr(
        "backend.diary.service._build_breadth",
        lambda: (
            BreadthBlock(
                mmtw_last=None,
                mmtw_history=[],
                mmtw_bullish_bias=None,
                finviz_new_highs=None,
                finviz_new_lows=None,
                finviz_net=None,
                nyhl=None,
                nahl=None,
                sources={
                    "mmtw": "barchart:$MMTW",
                    "finviz_nhnl": "finviz:ta_newhigh/ta_newlow",
                    "nyhl_nahl": "barchart:$NYHL+$NAHL",
                },
            ),
            {"status": "error", "source": "barchart+finviz", "error": "stub"},
        ),
    )
    monkeypatch.setattr(
        "backend.diary.service.latest_five_things",
        lambda: (_ for _ in ()).throw(RuntimeError("cnbc stub")),
    )

    snapshot = DiaryService().build_snapshot()
    assert snapshot.as_of_date == "2026-08-08"
    assert snapshot.as_of.startswith("2026-08-09")

"""Unit tests for diary breadth helpers (network mocked)."""

from __future__ import annotations

from backend.diary import barchart, finviz_breadth
from backend.diary.barchart import BarchartHistoryPoint, BarchartQuote
from backend.diary.service import BreadthBlock, _build_breadth


_FINVIZ_HIGH_HTML = """
<html><body>
  <td>#1 / 180</td>
</body></html>
"""

_FINVIZ_LOW_HTML = """
<html><body>
  <td>#1 / 92</td>
</body></html>
"""

_QUOTES_JSON = {
    "data": [
        {"symbol": "$MMTW", "lastPrice": "64.12"},
        {"symbol": "$NYHL", "lastPrice": "120.5"},
        {"symbol": "$NAHL", "lastPrice": "-45.0"},
    ]
}

_HISTORY_JSON = {
    "data": [
        {
            "tradeTime": "08/08/2026",
            "lastPrice": "64.12",
            "raw": {"tradeTime": "2026-08-08", "lastPrice": 64.12},
        },
        {
            "tradeTime": "08/07/2026",
            "lastPrice": "61.00",
            "raw": {"tradeTime": "2026-08-07", "lastPrice": 61.0},
        },
        {
            "tradeTime": "08/06/2026",
            "lastPrice": "58.50",
            "raw": {"tradeTime": "2026-08-06", "lastPrice": 58.5},
        },
        {
            "tradeTime": "08/05/2026",
            "lastPrice": "55.00",
            "raw": {"tradeTime": "2026-08-05", "lastPrice": 55.0},
        },
        {
            "tradeTime": "08/04/2026",
            "lastPrice": "52.00",
            "raw": {"tradeTime": "2026-08-04", "lastPrice": 52.0},
        },
    ]
}


def test_screener_total_parses_finviz_count(monkeypatch):
    monkeypatch.setattr(
        finviz_breadth,
        "fetch_html",
        lambda url: _FINVIZ_HIGH_HTML if "ta_newhigh" in url else _FINVIZ_LOW_HTML,
    )
    assert finviz_breadth.screener_total(
        "https://finviz.com/screener.ashx?v=111&s=ta_newhigh"
    ) == 180
    highs, lows = finviz_breadth.new_high_low_counts()
    assert highs.count == 180
    assert lows.count == 92
    assert highs.label == "new_highs"
    assert lows.label == "new_lows"


def test_fetch_history_returns_ascending(monkeypatch):
    monkeypatch.setattr(barchart, "_open_session", lambda: (object(), "xsrf"))
    monkeypatch.setattr(
        barchart,
        "_api_get",
        lambda opener, xsrf, url, params: _HISTORY_JSON,
    )

    points = barchart.fetch_history("$MMTW", limit=5)
    assert len(points) == 5
    dates = [p.date for p in points]
    assert dates == sorted(dates)
    assert dates[0] == "2026-08-04"
    assert dates[-1] == "2026-08-08"
    assert points[-1].last == 64.12


def test_fetch_quotes_parses_last(monkeypatch):
    monkeypatch.setattr(barchart, "_open_session", lambda: (object(), "xsrf"))
    monkeypatch.setattr(
        barchart,
        "_api_get",
        lambda opener, xsrf, url, params: _QUOTES_JSON,
    )

    quotes = barchart.fetch_quotes(["$MMTW", "$NYHL", "$NAHL"])
    assert quotes["$MMTW"] == BarchartQuote(symbol="$MMTW", last=64.12)
    assert quotes["$NYHL"].last == 120.5
    assert quotes["$NAHL"].last == -45.0


def test_build_breadth_bullish_bias_and_counts(monkeypatch):
    monkeypatch.setattr(
        "backend.diary.service.fetch_quotes",
        lambda symbols: {
            "$MMTW": BarchartQuote(symbol="$MMTW", last=64.12),
            "$NYHL": BarchartQuote(symbol="$NYHL", last=10.0),
            "$NAHL": BarchartQuote(symbol="$NAHL", last=-3.0),
        },
    )
    monkeypatch.setattr(
        "backend.diary.service.fetch_history",
        lambda symbol, *, limit=5: [
            BarchartHistoryPoint(date="2026-08-04", last=52.0),
            BarchartHistoryPoint(date="2026-08-05", last=55.0),
            BarchartHistoryPoint(date="2026-08-06", last=58.5),
            BarchartHistoryPoint(date="2026-08-07", last=61.0),
            BarchartHistoryPoint(date="2026-08-08", last=64.12),
        ],
    )
    monkeypatch.setattr(
        "backend.diary.service.new_high_low_counts",
        lambda: (
            finviz_breadth.FinvizCount(
                label="new_highs",
                count=180,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newhigh",
            ),
            finviz_breadth.FinvizCount(
                label="new_lows",
                count=92,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newlow",
            ),
        ),
    )

    block, section = _build_breadth()
    assert isinstance(block, BreadthBlock)
    assert block.mmtw_last == 64.12
    assert block.mmtw_bullish_bias is True
    assert [p.date for p in block.mmtw_history] == sorted(
        p.date for p in block.mmtw_history
    )
    assert block.finviz_new_highs == 180
    assert block.finviz_new_lows == 92
    assert block.finviz_net == 88
    assert block.nyhl == 10.0
    assert block.nahl == -3.0
    assert block.sources["mmtw"] == "barchart:$MMTW"
    assert block.sources["finviz_nhnl"] == "finviz:ta_newhigh/ta_newlow"
    assert block.sources["nyhl_nahl"] == "barchart:$NYHL+$NAHL"
    assert section["status"] == "ok"
    assert section["source"] == "barchart+finviz"
    assert section["error"] is None
    assert not hasattr(block, "exchange_new_highs")


def test_build_breadth_bullish_bias_false_at_or_below_50(monkeypatch):
    monkeypatch.setattr(
        "backend.diary.service.fetch_quotes",
        lambda symbols: {"$MMTW": BarchartQuote(symbol="$MMTW", last=50.0)},
    )
    monkeypatch.setattr(
        "backend.diary.service.fetch_history",
        lambda symbol, *, limit=5: [],
    )
    monkeypatch.setattr(
        "backend.diary.service.new_high_low_counts",
        lambda: (
            finviz_breadth.FinvizCount(
                label="new_highs",
                count=10,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newhigh",
            ),
            finviz_breadth.FinvizCount(
                label="new_lows",
                count=20,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newlow",
            ),
        ),
    )

    block, section = _build_breadth()
    assert block.mmtw_last == 50.0
    assert block.mmtw_bullish_bias is False
    assert section["status"] == "ok"
    assert section["source"] == "barchart+finviz"


def test_build_breadth_partial_when_finviz_fails(monkeypatch):
    monkeypatch.setattr(
        "backend.diary.service.fetch_quotes",
        lambda symbols: {"$MMTW": BarchartQuote(symbol="$MMTW", last=64.12)},
    )
    monkeypatch.setattr(
        "backend.diary.service.fetch_history",
        lambda symbol, *, limit=5: [],
    )

    def boom():
        raise RuntimeError("finviz down")

    monkeypatch.setattr("backend.diary.service.new_high_low_counts", boom)

    block, section = _build_breadth()
    assert block.mmtw_last == 64.12
    assert block.mmtw_bullish_bias is True
    assert block.finviz_new_highs is None
    assert block.sources["mmtw"] == "barchart:$MMTW"
    assert block.sources["finviz_nhnl"] == "finviz:ta_newhigh/ta_newlow"
    assert block.sources["nyhl_nahl"] == "barchart:$NYHL+$NAHL"
    assert section["status"] == "ok"
    assert section["source"] == "barchart+finviz"
    assert section["error"] is not None
    assert "Finviz NH/NL" in section["error"]


def test_build_breadth_partial_when_mmtw_fails(monkeypatch):
    def boom_quotes(symbols):
        raise RuntimeError("barchart down")

    monkeypatch.setattr("backend.diary.service.fetch_quotes", boom_quotes)
    monkeypatch.setattr(
        "backend.diary.service.new_high_low_counts",
        lambda: (
            finviz_breadth.FinvizCount(
                label="new_highs",
                count=180,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newhigh",
            ),
            finviz_breadth.FinvizCount(
                label="new_lows",
                count=92,
                url="https://finviz.com/screener.ashx?v=111&s=ta_newlow",
            ),
        ),
    )

    block, section = _build_breadth()
    assert block.mmtw_last is None
    assert block.mmtw_bullish_bias is None
    assert block.finviz_new_highs == 180
    assert block.finviz_new_lows == 92
    assert block.finviz_net == 88
    assert block.sources["mmtw"] == "barchart:$MMTW"
    assert block.sources["finviz_nhnl"] == "finviz:ta_newhigh/ta_newlow"
    assert section["status"] == "ok"
    assert section["source"] == "barchart+finviz"
    assert section["error"] is not None
    assert "$MMTW" in section["error"]


def test_build_breadth_error_when_both_fail(monkeypatch):
    def boom_quotes(symbols):
        raise RuntimeError("barchart down")

    def boom_finviz():
        raise RuntimeError("finviz down")

    monkeypatch.setattr("backend.diary.service.fetch_quotes", boom_quotes)
    monkeypatch.setattr("backend.diary.service.new_high_low_counts", boom_finviz)

    block, section = _build_breadth()
    assert block.mmtw_last is None
    assert block.finviz_new_highs is None
    assert block.sources == {
        "mmtw": "barchart:$MMTW",
        "finviz_nhnl": "finviz:ta_newhigh/ta_newlow",
        "nyhl_nahl": "barchart:$NYHL+$NAHL",
    }
    assert section["status"] == "error"
    assert section["source"] == "barchart+finviz"
    assert "$MMTW" in (section["error"] or "")
    assert "Finviz NH/NL" in (section["error"] or "")

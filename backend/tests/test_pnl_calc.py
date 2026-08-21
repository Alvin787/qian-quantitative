from backend.pnl.calc import (
    cost_value,
    enrich_trade,
    is_closed,
    ledger_totals,
    realized_percent,
    realized_pnl,
)


def test_rblx_matches_spreadsheet():
    assert cost_value(34.56, 100) == 3456.0
    assert realized_pnl(34.56, 38.15, 100) == 359.0
    assert realized_percent(34.56, 38.15) == 10.39


def test_open_trade_has_cost_but_no_pnl():
    view = enrich_trade(
        {
            "id": "1",
            "ticker": "LXEO",
            "entry_date": "2026-07-29",
            "entry_price": 4.24,
            "shares": 200,
            "exit_date": None,
            "exit_price": None,
            "notes": "",
            "account": "401k",
        }
    )
    assert view["value"] == 848.0
    assert view["pnl"] is None
    assert view["percent"] is None
    assert view["status"] == "open"
    assert is_closed(None, None) is False


def test_partial_exit_fields_stay_open():
    view = enrich_trade(
        {
            "ticker": "CELH",
            "entry_date": "2026-07-29",
            "entry_price": 33.78,
            "shares": 150,
            "exit_date": "2026-08-04",
            "exit_price": None,
        }
    )
    assert view["status"] == "open"
    assert view["pnl"] is None


def test_total_pnl_sums_realized_only():
    trades = [
        enrich_trade(
            {
                "ticker": "LXEO",
                "entry_price": 4.24,
                "shares": 200,
                "exit_date": None,
                "exit_price": None,
            }
        ),
        enrich_trade(
            {
                "ticker": "RBLX",
                "entry_price": 34.56,
                "shares": 100,
                "exit_date": "2026-08-04",
                "exit_price": 38.15,
            }
        ),
        enrich_trade(
            {
                "ticker": "CELH",
                "entry_price": 33.78,
                "shares": 150,
                "exit_date": None,
                "exit_price": None,
            }
        ),
    ]
    totals = ledger_totals(trades)
    assert totals["total_pnl"] == 359.0
    assert totals["open_count"] == 2
    assert totals["closed_count"] == 1
    assert totals["open_value"] == 848.0 + 5067.0

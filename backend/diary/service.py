from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.diary.barchart import (
    BarchartHistoryPoint,
    fetch_history,
    fetch_quotes,
)
from backend.diary.cnbc import CnbcBrief, latest_five_things
from backend.diary.config import (
    MARKET_RATIO_PAIRS,
    MARKET_SYMBOLS,
    PRIORITY_SECTORS,
    SECTOR_SYMBOLS,
    SUBMARKET_SYMBOLS,
)
from backend.diary.etf import EtfRow, build_etf_row, load_history
from backend.diary.finviz_breadth import new_high_low_counts


@dataclass
class BreadthBlock:
    mmtw_last: float | None
    mmtw_history: list[BarchartHistoryPoint]  # up to 5, oldest first
    mmtw_bullish_bias: bool | None  # True iff mmtw_last is not None and > 50.0
    finviz_new_highs: int | None
    finviz_new_lows: int | None
    finviz_net: int | None  # highs - lows when both present
    nyhl: float | None  # Barchart $NYHL
    nahl: float | None  # Barchart $NAHL
    sources: dict[str, str]  # keys: mmtw, finviz_nhnl, nyhl_nahl


@dataclass
class DiarySnapshot:
    as_of: str  # ISO-8601 UTC timestamp when built
    as_of_date: str  # YYYY-MM-DD (US-oriented calendar date used for diary day)
    market: list[EtfRow]
    market_ratios: list[EtfRow]  # one row per MARKET_RATIO_PAIRS with ratio_to/ratio_value set; symbol=numerator
    submarket: list[EtfRow]
    sectors: list[EtfRow]
    breadth: BreadthBlock | None
    cnbc: CnbcBrief | None
    sections: dict[str, dict]  # name -> {"status": "ok"|"error"|"pending", "source": str, "error": str|None}


_BREADTH_SOURCES = {
    "mmtw": "barchart:$MMTW",
    "finviz_nhnl": "finviz:ta_newhigh/ta_newlow",
    "nyhl_nahl": "barchart:$NYHL+$NAHL",
}


def _empty_breadth() -> BreadthBlock:
    return BreadthBlock(
        mmtw_last=None,
        mmtw_history=[],
        mmtw_bullish_bias=None,
        finviz_new_highs=None,
        finviz_new_lows=None,
        finviz_net=None,
        nyhl=None,
        nahl=None,
        sources=dict(_BREADTH_SOURCES),
    )


def _build_breadth() -> tuple[BreadthBlock, dict]:
    """Populate breadth; never raise — return (block, section status dict)."""
    block = _empty_breadth()
    mmtw_ok = False
    finviz_ok = False
    mmtw_error: str | None = None
    finviz_error: str | None = None

    try:
        quotes = fetch_quotes(["$MMTW", "$NYHL", "$NAHL"])
        mmtw = quotes.get("$MMTW")
        if mmtw is not None:
            block.mmtw_last = mmtw.last
            block.mmtw_bullish_bias = mmtw.last > 50.0
            mmtw_ok = True
            try:
                block.mmtw_history = fetch_history("$MMTW", limit=5)
            except Exception:  # noqa: BLE001 — history best-effort once quote ok
                pass
        else:
            mmtw_error = "$MMTW quote missing"
        nyhl = quotes.get("$NYHL")
        if nyhl is not None:
            block.nyhl = nyhl.last
        nahl = quotes.get("$NAHL")
        if nahl is not None:
            block.nahl = nahl.last
    except Exception as exc:  # noqa: BLE001 — isolate breadth half
        mmtw_error = f"$MMTW: {exc}"

    try:
        highs, lows = new_high_low_counts()
        block.finviz_new_highs = highs.count
        block.finviz_new_lows = lows.count
        block.finviz_net = highs.count - lows.count
        finviz_ok = True
    except Exception as exc:  # noqa: BLE001 — isolate breadth half
        finviz_error = f"Finviz NH/NL: {exc}"

    if mmtw_ok and finviz_ok:
        section = {
            "status": "ok",
            "source": "barchart+finviz",
            "error": None,
        }
    elif mmtw_ok or finviz_ok:
        failed = []
        if not mmtw_ok:
            failed.append(mmtw_error or "$MMTW failed")
        if not finviz_ok:
            failed.append(finviz_error or "Finviz NH/NL failed")
        section = {
            "status": "ok",
            "source": "barchart+finviz",
            "error": "; ".join(failed),
        }
    else:
        errors = [e for e in (mmtw_error, finviz_error) if e]
        section = {
            "status": "error",
            "source": "barchart+finviz",
            "error": "; ".join(errors) if errors else "breadth failed",
        }

    return block, section


def _section_status(rows: list[EtfRow], symbols: list[str], errors: list[str]) -> dict:
    if symbols and len(rows) == 0:
        return {
            "status": "error",
            "source": "yfinance",
            "error": "; ".join(errors) if errors else "all symbols failed",
        }
    return {
        "status": "ok",
        "source": "yfinance",
        "error": "; ".join(errors) if errors else None,
    }


def _load_group(
    symbols: list[str], *, priority_set: frozenset[str] | None = None
) -> tuple[list[EtfRow], list[str]]:
    rows: list[EtfRow] = []
    errors: list[str] = []
    for symbol in symbols:
        try:
            history = load_history(symbol)
            priority = symbol in priority_set if priority_set else False
            rows.append(build_etf_row(symbol, history, priority=priority))
        except Exception as exc:  # noqa: BLE001 — per-symbol isolation
            errors.append(f"{symbol}: {exc}")
    return rows, errors


_US_EASTERN = ZoneInfo("America/New_York")


class DiaryService:
    def build_snapshot(self) -> DiarySnapshot:
        now = datetime.now(timezone.utc)
        as_of = now.isoformat()
        # Diary day is the US session calendar date, not UTC date.
        as_of_date = now.astimezone(_US_EASTERN).date().isoformat()

        market, market_errors = _load_group(MARKET_SYMBOLS)
        submarket, submarket_errors = _load_group(SUBMARKET_SYMBOLS)
        sectors, sector_errors = _load_group(
            SECTOR_SYMBOLS, priority_set=PRIORITY_SECTORS
        )

        market_ratios: list[EtfRow] = []
        for numerator, denominator in MARKET_RATIO_PAIRS:
            try:
                num_hist = load_history(numerator)
                den_hist = load_history(denominator)
                num_row = build_etf_row(numerator, num_hist)
                den_last = float(den_hist["Close"].iloc[-1])
                ratio_value = (
                    num_row.last / den_last if den_last != 0 else 0.0
                )
                market_ratios.append(
                    EtfRow(
                        symbol=numerator,
                        last=num_row.last,
                        daily_change_pct=num_row.daily_change_pct,
                        pct_from_52w_low=num_row.pct_from_52w_low,
                        pct_from_52w_high=num_row.pct_from_52w_high,
                        short_term_trend=num_row.short_term_trend,
                        priority=False,
                        ratio_to=denominator,
                        ratio_value=ratio_value,
                    )
                )
            except Exception:  # noqa: BLE001 — omit failed ratio rows
                continue

        breadth, breadth_section = _build_breadth()

        cnbc: CnbcBrief | None = None
        try:
            cnbc = latest_five_things()
            cnbc_section = {
                "status": "ok",
                "source": "cnbc:5-things-to-know",
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 — CNBC must not fail ETF/breadth
            cnbc_section = {
                "status": "error",
                "source": "cnbc:5-things-to-know",
                "error": str(exc),
            }

        sections = {
            "market": _section_status(market, MARKET_SYMBOLS, market_errors),
            "submarket": _section_status(
                submarket, SUBMARKET_SYMBOLS, submarket_errors
            ),
            "sectors": _section_status(sectors, SECTOR_SYMBOLS, sector_errors),
            "breadth": breadth_section,
            "cnbc": cnbc_section,
        }

        return DiarySnapshot(
            as_of=as_of,
            as_of_date=as_of_date,
            market=market,
            market_ratios=market_ratios,
            submarket=submarket,
            sectors=sectors,
            breadth=breadth,
            cnbc=cnbc,
            sections=sections,
        )


def snapshot_to_dict(snapshot: DiarySnapshot) -> dict:
    breadth = asdict(snapshot.breadth) if snapshot.breadth is not None else None
    cnbc = asdict(snapshot.cnbc) if snapshot.cnbc is not None else None
    return {
        "as_of": snapshot.as_of,
        "as_of_date": snapshot.as_of_date,
        "market": [asdict(row) for row in snapshot.market],
        "market_ratios": [asdict(row) for row in snapshot.market_ratios],
        "submarket": [asdict(row) for row in snapshot.submarket],
        "sectors": [asdict(row) for row in snapshot.sectors],
        "breadth": breadth,
        "cnbc": cnbc,
        "sections": snapshot.sections,
    }

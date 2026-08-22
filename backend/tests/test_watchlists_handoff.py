from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.marketdata.eod_cache import cache_path, read_eod_cache, write_eod_cache
from backend.marketdata.yahoo import frames_from_yf_download, yahoo_symbol
from backend.tests.test_watchlists_review import (
    CHART_HISTORY,
    CHART_SPY,
    EARNINGS,
    FROZEN,
    HISTORY,
    _service,
    make_ohlcv,
    wait_review,
)
from backend.watchlists.store import FunnelState, Name


def test_yahoo_symbol_replaces_dot():
    assert yahoo_symbol("brk.b") == "BRK-B"


def test_frames_from_yf_download_multiindex_and_single():
    idx = pd.bdate_range(end="2026-08-14", periods=3)
    close = pd.Series([10.0, 11.0, 12.0], index=idx)
    ohlcv = {
        "Open": close,
        "High": close * 1.01,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000.0, 1_000.0, 1_000.0], index=idx),
    }
    multi = pd.concat({"AAA": pd.DataFrame(ohlcv), "SPY": pd.DataFrame(ohlcv)}, axis=1)
    frames = frames_from_yf_download(multi, ["AAA", "SPY", "ZZZ"])
    assert set(frames) == {"AAA", "SPY"}
    single = pd.DataFrame(ohlcv)
    frames_one = frames_from_yf_download(single, ["AAA"])
    assert set(frames_one) == {"AAA"}
    empty = pd.DataFrame(ohlcv).iloc[0:0]
    assert frames_from_yf_download(empty, ["AAA"]) == {}


def test_stale_snapshot_fails_review_without_ingest(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[
            {
                "ticker": "TICK",
                "industry": "Software",
                "source_screens": "ipo_this_year",
            }
        ],
        as_of_session="2026-08-13",
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="TICK",
                    list="master",
                    added_at="2026-01-01",
                    source_screens=["canslim_calibrated"],
                    industry="Software",
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "failed"
    assert done.error is not None
    names = store.get().names
    assert len(names) == 1
    assert names[0].ticker == "TICK"
    assert names[0].list == "master"
    assert names[0].source_screens == ["canslim_calibrated"]


def test_current_screens_replace_historical_unions(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[
            {
                "ticker": "OLD",
                "industry": "Software",
                "source_screens": "canslim_calibrated",
            }
        ],
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="OLD",
                    list="stalk",
                    added_at="2026-01-01",
                    source_screens=["ipo_this_year"],
                    industry="Software",
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    old = next(name for name in store.get().names if name.ticker == "OLD")
    assert old.source_screens == ["canslim_calibrated"]
    assert "canslim_calibrated" in old.historical_source_screens
    assert "ipo_this_year" in old.historical_source_screens
    assert old.list == "stalk"


def test_batch_omit_ticker_does_not_call_load_history(tmp_path: Path):
    def load_history(ticker: str):
        raise AssertionError(f"load_history should not be called for {ticker}")

    def load_spy():
        raise AssertionError("load_spy should not be called when SPY is in the batch")

    def load_history_batch(tickers):
        assert "ZZZ" in tickers
        return {"SPY": CHART_SPY}

    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history=load_history,
        load_spy=load_spy,
        load_history_batch=load_history_batch,
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="ZZZ",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    zzz = next(name for name in store.get().names if name.ticker == "ZZZ")
    assert zzz.readiness in {"unknown", "data_incomplete"}


def test_earnings_fetched_only_for_actionable_or_stalk_focus(tmp_path: Path):
    requested: list[str] = []

    def load_history(ticker: str):
        if ticker == "WWW":
            return make_ohlcv(220, end="2026-08-14", close_step=0.0)
        if ticker == "FFF":
            return HISTORY
        return CHART_HISTORY

    def load_earnings(ticker: str):
        requested.append(ticker)
        return EARNINGS

    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history=load_history,
        load_spy=lambda: CHART_SPY,
        load_earnings=load_earnings,
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="WWW",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                ),
                Name(
                    ticker="CCC",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                ),
                Name(
                    ticker="FFF",
                    list="focus",
                    added_at="2026-01-01",
                    industry="Software",
                ),
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    by_ticker = {name.ticker: name for name in store.get().names}
    assert by_ticker["WWW"].readiness == "watch"
    assert by_ticker["CCC"].readiness == "chart_review_ready"
    assert "WWW" not in requested
    assert "CCC" in requested
    assert "FFF" in requested


def test_sort_prefers_family_count_over_raw_momentum_screens(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history=lambda ticker: CHART_HISTORY,
        load_spy=lambda: CHART_SPY,
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAA",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                    source_screens=[
                        "strongest_mover_1w",
                        "strongest_mover_1m",
                        "strongest_mover_3m",
                        "strongest_mover_6m",
                    ],
                ),
                Name(
                    ticker="BBB",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                    source_screens=[
                        "strongest_mover_1w",
                        "extended_base_above_sma200",
                    ],
                ),
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    names = store.get().names
    assert [name.ticker for name in names] == ["BBB", "AAA"]
    by_ticker = {name.ticker: name for name in names}
    assert by_ticker["AAA"].readiness == "chart_review_ready"
    assert by_ticker["BBB"].readiness == "chart_review_ready"
    assert by_ticker["AAA"].screen_family_count == 1
    assert by_ticker["BBB"].screen_family_count == 2
    assert by_ticker["AAA"].screen_count == 4
    assert by_ticker["BBB"].screen_count == 2


def test_unknown_screen_id_fails_review(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[
            {
                "ticker": "AAA",
                "industry": "Software",
                "source_screens": "not_a_real_screen",
            }
        ],
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAA",
                    list="master",
                    added_at="2026-01-01",
                    source_screens=["canslim_calibrated"],
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "failed"
    aaa = next(name for name in store.get().names if name.ticker == "AAA")
    assert aaa.source_screens == ["canslim_calibrated"]
    assert aaa.list == "master"


def test_review_ingest_new_on_master_old_stays_stalk(tmp_path: Path):
    store, service = _service(
        tmp_path,
        rows=[
            {"ticker": "OLD", "industry": "Software", "source_screens": "canslim_calibrated"},
            {"ticker": "NEW", "industry": "Software", "source_screens": "high_adr_hottest"},
        ],
        today=FROZEN,
        expected_session=FROZEN,
    )
    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="OLD",
                    list="stalk",
                    added_at="2026-01-01",
                    source_screens=["ipo_this_year"],
                )
            ],
        )
    )
    meta = service.start_review()
    done = wait_review(service, meta.review_id)
    assert done.status == "completed"
    by_ticker = {name.ticker: name for name in store.get().names}
    assert by_ticker["NEW"].list == "master"
    assert by_ticker["OLD"].list == "stalk"
    assert by_ticker["OLD"].source_screens == ["canslim_calibrated"]
    assert "ipo_this_year" in by_ticker["OLD"].historical_source_screens
    assert "canslim_calibrated" in by_ticker["OLD"].historical_source_screens


def test_eod_cache_sequential_update(tmp_path: Path):
    cache_root = tmp_path / "eod_cache"
    session = "2026-08-14"
    df1 = make_ohlcv(20, end=session, close_step=1.0)
    df2 = make_ohlcv(20, end=session, close_step=2.0)
    assert df1["Close"].iloc[-1] != df2["Close"].iloc[-1]

    write_eod_cache(cache_root, session, "AAA", df1)
    loaded1 = read_eod_cache(cache_root, session, "AAA")
    assert loaded1 is not None
    assert loaded1["Close"].iloc[-1] == df1["Close"].iloc[-1]

    write_eod_cache(cache_root, session, "AAA", df2)
    loaded2 = read_eod_cache(cache_root, session, "AAA")
    assert loaded2 is not None
    assert loaded2["Close"].iloc[-1] == df2["Close"].iloc[-1]


def test_eod_cache_session_isolation(tmp_path: Path):
    cache_root = tmp_path / "eod_cache"
    s1 = "2026-08-13"
    s2 = "2026-08-14"
    df1 = make_ohlcv(20, end=s1, close_step=1.0)
    df2 = make_ohlcv(20, end=s2, close_step=2.0)

    write_eod_cache(cache_root, s1, "AAA", df1)
    write_eod_cache(cache_root, s2, "AAA", df2)

    loaded_s1 = read_eod_cache(cache_root, s1, "AAA")
    loaded_s2 = read_eod_cache(cache_root, s2, "AAA")
    assert loaded_s1 is not None
    assert loaded_s2 is not None
    assert loaded_s1.index[-1].strftime("%Y-%m-%d") == s1
    assert loaded_s2.index[-1].strftime("%Y-%m-%d") == s2
    assert loaded_s1["Close"].iloc[-1] == df1["Close"].iloc[-1]
    assert loaded_s2["Close"].iloc[-1] == df2["Close"].iloc[-1]


def test_eod_cache_stale_or_malformed_returns_none(tmp_path: Path):
    cache_root = tmp_path / "eod_cache"
    session = "2026-08-14"
    # non-existent
    assert read_eod_cache(cache_root, session, "NONE") is None

    # stale (last row date != as_of_session)
    df_stale = make_ohlcv(20, end="2026-08-13", close_step=1.0)
    write_eod_cache(cache_root, session, "STALE", df_stale)
    assert read_eod_cache(cache_root, session, "STALE") is None

    # malformed (corrupt CSV)
    bad_path = cache_path(cache_root, session, "CORRUPT")
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text("invalid,csv,data\n1,2\n")
    assert read_eod_cache(cache_root, session, "CORRUPT") is None


def test_review_uses_eod_cache_hit(tmp_path: Path):
    cache_root = tmp_path / "eod_cache"
    batch_calls: list[list[str]] = []

    def counting_batch_loader(tickers: list[str]) -> dict[str, pd.DataFrame]:
        batch_calls.append(list(tickers))
        out = {"SPY": CHART_SPY}
        for t in tickers:
            if t == "AAA":
                out["AAA"] = CHART_HISTORY
            elif t == "BBB":
                out["BBB"] = CHART_HISTORY
        return out

    store, service = _service(
        tmp_path,
        rows=[],
        runs=[],
        load_history_batch=counting_batch_loader,
        today=FROZEN,
        expected_session=FROZEN,
    )
    # Set the custom cache root on the review service
    service.cache_root = cache_root
    service._cache_root = cache_root

    store.put(
        FunnelState(
            updated_at="2026-01-01T00:00:00+00:00",
            names=[
                Name(
                    ticker="AAA",
                    list="master",
                    added_at="2026-01-01",
                    industry="Software",
                    source_screens=["canslim_calibrated"],
                )
            ],
        )
    )

    # First review: loads data and populates cache
    meta1 = service.start_review()
    done1 = wait_review(service, meta1.review_id)
    assert done1.status == "completed"
    assert len(batch_calls) == 1
    assert "AAA" in batch_calls[0]
    assert (cache_root / FROZEN.isoformat() / "AAA.csv").exists()
    assert (cache_root / FROZEN.isoformat() / "SPY.csv").exists()

    # Second review for same session: cache hit, batch loader NOT called
    meta2 = service.start_review()
    done2 = wait_review(service, meta2.review_id)
    assert done2.status == "completed"
    assert len(batch_calls) == 1  # No additional batch loader calls

    # Third review: add a new ticker BBB; batch loader called ONLY for BBB
    state = store.get()
    state.names.append(
        Name(
            ticker="BBB",
            list="master",
            added_at="2026-01-01",
            industry="Software",
            source_screens=["canslim_calibrated"],
        )
    )
    store.put(state)

    meta3 = service.start_review()
    done3 = wait_review(service, meta3.review_id)
    assert done3.status == "completed"
    assert len(batch_calls) == 2
    assert batch_calls[1] == ["BBB"]  # Only missing ticker BBB requested
    assert (cache_root / FROZEN.isoformat() / "BBB.csv").exists()


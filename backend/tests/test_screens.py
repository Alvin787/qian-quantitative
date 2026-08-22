"""Tests for the Finviz screen catalog and structured scraper."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.screener.finviz import FinvizScrapeError, scrape_finviz
from backend.screener.hybrid_screener import DEFAULT_FINVIZ_URL
from backend.screener.screens import SCREENS, get_screen, list_screens

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "finviz"

CANSLIM_URL = (
    "https://finviz.com/screener?v=111&f=cap_midover,fa_salesqoq_high,fa_salesyoyttm_high,"
    "geo_usa,sh_avgvol_o500,sh_curvol_o2000,sh_insttrans_pos,ta_highlow20d_a5h,"
    "ta_highlow50d_a5h,ta_volatility_wo4&ft=4&o=change&preset=s151703676"
)


class TestScreenCatalog:
    def test_list_screens_has_fifteen_entries(self):
        screens = list_screens()
        assert len(screens) == 15

    def test_ids_unique_and_match_screens_keys(self):
        screens = list_screens()
        ids = [s.id for s in screens]
        assert len(ids) == len(set(ids))
        assert set(ids) == set(SCREENS.keys())

    def test_every_url_is_finviz_screener_with_preset(self):
        for screen in list_screens():
            if screen.url != "":
                assert screen.url.startswith("https://finviz.com/screener?")
                if screen.id not in ("strongest_mover_1w", "liquid_leveraged_etf"):
                    assert "preset=" in screen.url

    def test_canslim_calibrated_label_and_url_preserved(self):
        screen = get_screen("canslim_calibrated")
        assert screen.label == "CANSLIM-inspired calibrated"
        assert screen.url == CANSLIM_URL

    def test_strongest_mover_1w_baseline_and_tight_filters(self):
        assert "ta_perf_1w20o" in get_screen("strongest_mover_1w").url
        assert "ta_perf_1w30o" in get_screen("strongest_mover_1w_tight").url

    def test_reversal_pullback_matches_default_url(self):
        assert get_screen("reversal_pullback").url == DEFAULT_FINVIZ_URL

    def test_get_screen_unknown_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_screen("nope")


class TestScrapeFinviz:
    def test_scrape_totals_ok_fixture(self, monkeypatch):
        content = (FIXTURES_DIR / "totals_ok.html").read_text(encoding="utf-8")
        monkeypatch.setattr("backend.screener.finviz.fetch_html", lambda url: content)

        result = scrape_finviz(
            "https://finviz.com/screener?v=111&preset=test",
            sleep_s=0.0,
        )

        assert result.tickers == ["AAA", "BBB"]
        assert result.industries == {
            "AAA": "Software",
            "BBB": "Semiconductors",
        }
        assert result.reported_total == 2
        assert result.pages == 1

    def test_scrape_attribute_order_fixture(self, monkeypatch):
        content = (FIXTURES_DIR / "attribute_order.html").read_text(encoding="utf-8")
        monkeypatch.setattr("backend.screener.finviz.fetch_html", lambda url: content)

        result = scrape_finviz(
            "https://finviz.com/screener?v=111&preset=test",
            sleep_s=0.0,
        )

        assert result.tickers == ["CCC"]
        assert result.industries == {"CCC": "Banks"}
        assert result.reported_total == 1
        assert result.pages == 1

    def test_dedupes_in_order_and_populates_industries(self, monkeypatch):
        pages = {
            1: (
                '<tr><td data-boxover-ticker="AAA" data-boxover-industry="Software">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="BBB" data-boxover-industry="Semiconductors">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="AAA" data-boxover-industry="Software">'
                '</td></tr>'
                '<span>#1 / 3</span>'
            ),
            21: (
                '<tr><td data-boxover-ticker="CCC" data-boxover-industry="Banks">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="BBB" data-boxover-industry="Semiconductors">'
                '</td></tr>'
                '<span>#3 / 3</span>'
            ),
            41: "",
        }

        def fake_fetch(url: str) -> str:
            if "&r=1" in url or url.endswith("&r=1"):
                return pages[1]
            if "&r=21" in url:
                return pages[21]
            if "&r=41" in url:
                return pages[41]
            return ""

        monkeypatch.setattr("backend.screener.finviz.fetch_html", fake_fetch)

        result = scrape_finviz(
            "https://finviz.com/screener?v=111&preset=test",
            sleep_s=0.0,
        )

        assert result.tickers == ["AAA", "BBB", "CCC"]
        assert result.industries == {
            "AAA": "Software",
            "BBB": "Semiconductors",
            "CCC": "Banks",
        }
        assert result.reported_total == 3
        assert result.pages == 2

    def test_parses_industry_before_ticker_with_single_quotes(self, monkeypatch):
        content = (FIXTURES_DIR / "attribute_order.html").read_text(encoding="utf-8")
        monkeypatch.setattr("backend.screener.finviz.fetch_html", lambda url: content)

        result = scrape_finviz(
            "https://finviz.com/screener?v=111&preset=test",
            sleep_s=0.0,
        )
        assert result.tickers == ["CCC"]
        assert result.industries == {"CCC": "Banks"}
        assert result.reported_total == 1
        assert result.pages == 1

    def test_missing_result_total_raises(self, monkeypatch):
        html = (
            '<td data-boxover-ticker="AAA" data-boxover-industry="Software"></td>'
        )

        def fake_fetch(url: str) -> str:
            if "&r=1" in url or url.endswith("&r=1"):
                return html
            return ""

        monkeypatch.setattr("backend.screener.finviz.fetch_html", fake_fetch)
        with pytest.raises(FinvizScrapeError, match="missing Finviz result total"):
            scrape_finviz(
                "https://finviz.com/screener?v=111&preset=test",
                sleep_s=0.0,
            )

    def test_reported_total_mismatch_raises(self, monkeypatch):
        html = (
            '<td data-boxover-ticker="AAA" data-boxover-industry="Software"></td>'
            "<span>#1 / 2</span>"
        )

        def fake_fetch(url: str) -> str:
            if "&r=1" in url or url.endswith("&r=1"):
                return html
            return ""

        monkeypatch.setattr("backend.screener.finviz.fetch_html", fake_fetch)
        with pytest.raises(FinvizScrapeError, match="Finviz total mismatch"):
            scrape_finviz(
                "https://finviz.com/screener?v=111&preset=test",
                sleep_s=0.0,
            )

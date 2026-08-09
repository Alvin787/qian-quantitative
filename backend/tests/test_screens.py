"""Tests for the Finviz screen catalog and structured scraper."""

from __future__ import annotations

import pytest

from backend.screener.finviz import scrape_finviz
from backend.screener.hybrid_screener import DEFAULT_FINVIZ_URL
from backend.screener.screens import SCREENS, get_screen, list_screens


class TestScreenCatalog:
    def test_list_screens_has_thirteen_entries(self):
        screens = list_screens()
        assert len(screens) == 13

    def test_ids_unique_and_match_screens_keys(self):
        screens = list_screens()
        ids = [s.id for s in screens]
        assert len(ids) == len(set(ids))
        assert set(ids) == set(SCREENS.keys())

    def test_every_url_is_finviz_screener_with_preset(self):
        for screen in list_screens():
            assert screen.url.startswith("https://finviz.com/screener?")
            assert "preset=" in screen.url

    def test_reversal_pullback_matches_default_url(self):
        assert get_screen("reversal_pullback").url == DEFAULT_FINVIZ_URL

    def test_get_screen_unknown_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_screen("nope")


class TestScrapeFinviz:
    def test_dedupes_in_order_and_populates_industries(self, monkeypatch):
        pages = {
            1: (
                '<tr><td data-boxover-ticker="AAA" data-boxover-industry="Software">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="BBB" data-boxover-industry="Semiconductors">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="AAA" data-boxover-industry="Software">'
                '</td></tr>'
                '<span>#1 / 4</span>'
            ),
            21: (
                '<tr><td data-boxover-ticker="CCC" data-boxover-industry="Banks">'
                '</td></tr>'
                '<tr><td data-boxover-ticker="BBB" data-boxover-industry="Semiconductors">'
                '</td></tr>'
                '<span>#3 / 4</span>'
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

"""Unit tests for CNBC 5 Things scraper (network mocked)."""

from __future__ import annotations

import pytest

from backend.diary import cnbc as cnbc_mod


LISTING_HTML = """
<html><body>
  <a href="https://www.cnbc.com/2026/08/07/5-things-to-know-before-the-stock-market-opens.html">Older</a>
  <a href="https://www.cnbc.com/2026/08/08/5-things-to-know-before-the-stock-market-opens.html">Newer</a>
</body></html>
"""

ARTICLE_HTML = """
<html>
<head><title>Five Things Before the Open | CNBC</title></head>
<body>
  <h1>Five Things Before the Open</h1>
  <p>First paragraph about futures.</p>
  <p>Second paragraph about yields.</p>
  <p>Third paragraph ignored.</p>
</body>
</html>
"""


def test_latest_five_things_picks_newest_and_excerpt(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        if url == cnbc_mod.LISTING_URL:
            return LISTING_HTML
        if "2026/08/08" in url:
            return ARTICLE_HTML
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(cnbc_mod, "fetch_html", fake_fetch)

    brief = cnbc_mod.latest_five_things()
    assert brief.url == (
        "https://www.cnbc.com/2026/08/08/"
        "5-things-to-know-before-the-stock-market-opens.html"
    )
    assert brief.published == "2026-08-08"
    assert brief.title == "Five Things Before the Open"
    assert brief.excerpt == (
        "First paragraph about futures. Second paragraph about yields."
    )
    assert calls[0] == cnbc_mod.LISTING_URL
    assert "2026/08/08" in calls[1]


def test_latest_five_things_raises_when_no_links(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cnbc_mod, "fetch_html", lambda url: "<html></html>")
    with pytest.raises(RuntimeError, match="No CNBC 5 Things"):
        cnbc_mod.latest_five_things()

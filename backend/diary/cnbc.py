"""CNBC Morning Squawk / 5 Things scraper."""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass

from backend.screener.finviz import USER_AGENT, fetch_html

LISTING_URL = "https://www.cnbc.com/5-things-to-know/"

_ARTICLE_HREF_RE = re.compile(
    r'href="(https://www\.cnbc\.com/(\d{4})/(\d{2})/(\d{2})/'
    r'5-things-to-know-before-the-stock-market-opens\.html)"',
    re.I,
)
_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
_P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class CnbcBrief:
    title: str
    url: str
    excerpt: str | None
    published: str | None


def _strip_tags(raw: str) -> str:
    text = _TAG_RE.sub("", raw)
    return html_lib.unescape(text).strip()


def _pick_latest_article(listing_html: str) -> tuple[str, str]:
    """Return (url, published YYYY-MM-DD) for the most recently dated article."""
    candidates: list[tuple[str, str]] = []
    for match in _ARTICLE_HREF_RE.finditer(listing_html):
        url = match.group(1)
        published = f"{match.group(2)}-{match.group(3)}-{match.group(4)}"
        candidates.append((url, published))
    if not candidates:
        raise RuntimeError("No CNBC 5 Things article links found")
    # Prefer most recently dated path; stable on ties by first occurrence.
    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0]


def _title_from_html(html: str, fallback: str) -> str:
    h1 = _H1_RE.search(html)
    if h1:
        title = _strip_tags(h1.group(1))
        if title:
            return title
    title_tag = _TITLE_TAG_RE.search(html)
    if title_tag:
        title = _strip_tags(title_tag.group(1))
        # CNBC titles often append " | CNBC"
        title = re.sub(r"\s*\|\s*CNBC\s*$", "", title, flags=re.I).strip()
        if title:
            return title
    return fallback


def _excerpt_from_html(html: str) -> str | None:
    paragraphs: list[str] = []
    for match in _P_RE.finditer(html):
        text = _strip_tags(match.group(1))
        if text:
            paragraphs.append(text)
        if len(paragraphs) >= 2:
            break
    if not paragraphs:
        return None
    excerpt = " ".join(paragraphs)
    if len(excerpt) > 600:
        excerpt = excerpt[:600]
    return excerpt


def latest_five_things() -> CnbcBrief:
    """
    GET https://www.cnbc.com/5-things-to-know/ with USER_AGENT.
    Pick the first article href matching
    https://www.cnbc.com/YYYY/MM/DD/5-things-to-know-before-the-stock-market-opens.html
    (prefer most recently dated path). Title = nearby headline text or <title> of article.
    Optionally GET the article URL and take the first 1–2 non-empty paragraph texts
    joined as excerpt (cap 600 chars). On failure raise RuntimeError.
    """
    _ = USER_AGENT  # documented reuse; fetch_html applies the same header
    try:
        listing_html = fetch_html(LISTING_URL)
        url, published = _pick_latest_article(listing_html)
        article_html = fetch_html(url)
        title = _title_from_html(
            article_html,
            fallback="5 Things to Know Before the Stock Market Opens",
        )
        excerpt = _excerpt_from_html(article_html)
        return CnbcBrief(
            title=title,
            url=url,
            excerpt=excerpt,
            published=published,
        )
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 — surface as RuntimeError
        raise RuntimeError(f"CNBC 5 Things scrape failed: {exc}") from exc

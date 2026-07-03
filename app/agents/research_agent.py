"""
Research Agent: fetches top-ranking competitor pages for a topic.

Data source is pluggable via SearchProvider so this doesn't hardwire the
pipeline to one paid API. SerpAPIProvider is the production path (needs
SERPAPI_KEY); MockSearchProvider lets the rest of the pipeline be built,
tested, and demoed without live credentials.

SerpAPIProvider goes a step beyond the SERP results: it fetches each
competitor URL and extracts the full article body (via trafilatura), so the
downstream RAG store grounds the outline in what pages *actually* cover in
depth - not just their ~150-word search snippet. Any page that fails to
fetch or yields too little content transparently falls back to its snippet,
so one dead/paywalled URL never degrades the rest of the run.
"""

from __future__ import annotations

import asyncio
import os
import re
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional

import httpx
import trafilatura

from app.core.schemas import CompetitorPage

# A page must yield at least this many words of extracted body text to be
# considered a successful scrape; below it we keep the SERP snippet instead.
_MIN_ARTICLE_WORDS = 60
_PAGE_TIMEOUT = httpx.Timeout(10.0)
# Many sites 403 the default httpx UA; present as a normal browser/bot.
_USER_AGENT = (
    "Mozilla/5.0 (compatible; SEOIntelBot/1.0; +https://github.com/seo-intel)"
)

_HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")

# An async callable that fetches a URL and returns raw HTML, or None on failure.
Fetcher = Callable[[str], Awaitable[Optional[str]]]


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int) -> list[CompetitorPage]:
        raise NotImplementedError


def extract_readable_text(html: str) -> str:
    """Extract the main article body from raw HTML, stripping nav/boilerplate.

    Returns "" when nothing meaningful can be pulled out (paywalls, JS-only
    pages, listing pages) so the caller can fall back to the SERP snippet.
    """
    if not html:
        return ""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )
    return (text or "").strip()


def extract_headings(html: str) -> list[str]:
    """Best-effort H1-H3 extraction via regex - no extra parser dependency."""
    if not html:
        return []
    headings = []
    for raw in _HEADING_RE.findall(html):
        clean = re.sub(r"\s+", " ", _TAG_RE.sub("", raw)).strip()
        if clean:
            headings.append(clean)
    return headings


async def _fetch_html(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch a URL, returning HTML text or None on any error/non-HTML response."""
    if not url:
        return None
    try:
        resp = await client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None
    if "html" not in resp.headers.get("content-type", "").lower():
        return None
    return resp.text


async def enrich_pages_with_full_content(
    pages: list[CompetitorPage], fetcher: Fetcher
) -> list[CompetitorPage]:
    """Replace each page's snippet-based raw_text with full extracted article
    text, fetched concurrently. Falls back to the existing page (its snippet)
    whenever the fetch errors or extraction yields too little content.

    The fetcher is injected so this is unit-testable with fake HTML and never
    touches the network in CI.
    """
    results = await asyncio.gather(
        *(fetcher(p.url) for p in pages), return_exceptions=True
    )

    enriched: list[CompetitorPage] = []
    for page, html in zip(pages, results):
        if isinstance(html, BaseException) or not html:
            enriched.append(page)
            continue
        text = extract_readable_text(html)
        if len(text.split()) < _MIN_ARTICLE_WORDS:
            enriched.append(page)
            continue
        enriched.append(
            page.model_copy(
                update={
                    "raw_text": text,
                    "word_count": len(text.split()),
                    "headings": extract_headings(html) or page.headings,
                }
            )
        )
    return enriched


class SerpAPIProvider(SearchProvider):
    """Production provider using SerpAPI. Requires SERPAPI_KEY.

    Set SCRAPE_FULL_PAGES=false to disable full-page fetching and use only
    the SERP snippets (faster, but far less RAG context).
    """

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, scrape_full_pages: Optional[bool] = None):
        self._api_key = os.environ.get("SERPAPI_KEY")
        if not self._api_key:
            raise RuntimeError("SERPAPI_KEY not set.")
        if scrape_full_pages is None:
            scrape_full_pages = (
                os.environ.get("SCRAPE_FULL_PAGES", "true").lower() != "false"
            )
        self._scrape_full_pages = scrape_full_pages

    async def search(self, query: str, num_results: int) -> list[CompetitorPage]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.BASE_URL,
                params={"q": query, "api_key": self._api_key, "num": num_results},
            )
            resp.raise_for_status()
            data = resp.json()

        pages = []
        for i, result in enumerate(data.get("organic_results", [])[:num_results]):
            pages.append(
                CompetitorPage(
                    url=result.get("link", ""),
                    rank=i + 1,
                    title=result.get("title", ""),
                    headings=[],
                    word_count=len(result.get("snippet", "").split()),
                    raw_text=result.get("snippet", ""),
                )
            )

        if self._scrape_full_pages and pages:
            async with httpx.AsyncClient(
                timeout=_PAGE_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
                follow_redirects=True,
            ) as client:
                pages = await enrich_pages_with_full_content(
                    pages, lambda url: _fetch_html(client, url)
                )

        return pages


class MockSearchProvider(SearchProvider):
    """
    Deterministic fixture provider for offline dev, tests, and demos.
    Returns realistic-shaped data so downstream agents (RAG, outline,
    scoring) can be built and verified without a live SERP API key.
    """

    async def search(self, query: str, num_results: int) -> list[CompetitorPage]:
        fixtures = [
            CompetitorPage(
                url=f"https://example{i}.com/{query.replace(' ', '-')}",
                rank=i,
                title=f"{query.title()}: The Complete Guide ({i})",
                headings=[f"What is {query}", f"Benefits of {query}", f"How to choose {query}"],
                word_count=1200 + i * 150,
                raw_text=(
                    f"{query} is an important topic for businesses today. "
                    f"This guide covers what {query} means, why it matters, "
                    f"common mistakes teams make, and a step-by-step approach "
                    f"to getting started with {query}. Experts recommend "
                    f"evaluating your current process before adopting {query} "
                    f"to ensure measurable ROI within the first quarter."
                )
                * 3,
            )
            for i in range(1, num_results + 1)
        ]
        return fixtures


def get_search_provider() -> SearchProvider:
    if os.environ.get("SERPAPI_KEY"):
        return SerpAPIProvider()
    return MockSearchProvider()

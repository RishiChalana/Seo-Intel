import httpx
import pytest
from tenacity import wait_none

from app.agents import research_agent
from app.agents.research_agent import (
    MockSearchProvider,
    SerpAPIProvider,
    enrich_pages_with_full_content,
    extract_headings,
    extract_readable_text,
)
from app.core.schemas import CompetitorPage

# A realistic article page: nav + script boilerplate wrapped around a real
# multi-paragraph article body. trafilatura should pull the body and drop the
# chrome.
_ARTICLE_HTML = """
<html><head><title>Email Marketing Automation Guide</title></head>
<body>
  <nav><a href="/">Home</a><a href="/blog">Blog</a><a href="/pricing">Pricing</a></nav>
  <script>var tracking = init(); doAnalytics();</script>
  <article>
    <h1>The Complete Guide to Email Marketing Automation</h1>
    <p>Email marketing automation lets businesses send timely, personalized
    messages triggered by customer behavior. Instead of blasting the same
    newsletter to everyone, marketers build workflows that respond to signups,
    purchases, and abandoned carts automatically.</p>
    <h2>How Automated Workflows Work</h2>
    <p>A workflow begins with a trigger, such as a new subscriber joining a
    list. From there, predefined rules decide which email goes out, when it is
    sent, and how the content is personalized based on the customer's actions
    and profile data. Segmentation keeps every message relevant.</p>
    <h3>Measuring Success</h3>
    <p>Track open rates, click-through rates, and conversions to understand
    which automated campaigns actually drive revenue for your business over
    time. Continuous testing and optimization compound results quarter over
    quarter.</p>
  </article>
  <footer>Copyright 2026. All rights reserved. Privacy policy.</footer>
</body></html>
"""


def test_extract_readable_text_pulls_article_and_drops_boilerplate():
    text = extract_readable_text(_ARTICLE_HTML)
    assert "email marketing automation" in text.lower()
    assert "predefined rules" in text.lower()
    # Boilerplate should be stripped
    assert "doAnalytics" not in text
    assert "Privacy policy" not in text
    assert len(text.split()) >= 60


def test_extract_readable_text_empty_and_garbage():
    assert extract_readable_text("") == ""
    assert extract_readable_text("<html><body></body></html>") == ""


def test_extract_headings_returns_h1_h2_h3():
    headings = extract_headings(_ARTICLE_HTML)
    assert "The Complete Guide to Email Marketing Automation" in headings
    assert "How Automated Workflows Work" in headings
    assert "Measuring Success" in headings


def test_extract_headings_empty():
    assert extract_headings("") == []
    assert extract_headings("<p>no headings here</p>") == []


def _snippet_page() -> CompetitorPage:
    return CompetitorPage(
        url="https://competitor.com/guide",
        rank=1,
        title="Guide",
        raw_text="Short SERP snippet about email automation.",
        word_count=6,
    )


async def test_enrich_replaces_snippet_with_full_text_on_success():
    async def fetcher(url):
        return _ARTICLE_HTML

    [page] = await enrich_pages_with_full_content([_snippet_page()], fetcher)
    assert page.word_count >= 60
    assert "predefined rules" in page.raw_text.lower()
    assert len(page.headings) >= 3


async def test_enrich_falls_back_to_snippet_when_fetch_returns_none():
    async def fetcher(url):
        return None

    original = _snippet_page()
    [page] = await enrich_pages_with_full_content([original], fetcher)
    assert page.raw_text == original.raw_text
    assert page.word_count == original.word_count


async def test_enrich_falls_back_when_fetcher_raises():
    async def fetcher(url):
        raise RuntimeError("connection reset")

    original = _snippet_page()
    [page] = await enrich_pages_with_full_content([original], fetcher)
    assert page.raw_text == original.raw_text


async def test_enrich_keeps_snippet_when_extracted_text_too_thin():
    # A page that extracts to just a few words should not overwrite the snippet.
    async def fetcher(url):
        return "<html><body><article><p>Too short.</p></article></body></html>"

    original = _snippet_page()
    [page] = await enrich_pages_with_full_content([original], fetcher)
    assert page.raw_text == original.raw_text


async def test_enrich_handles_mixed_success_and_failure():
    good = CompetitorPage(url="https://a.com", rank=1, title="A",
                          raw_text="snippet a", word_count=2)
    bad = CompetitorPage(url="https://b.com", rank=2, title="B",
                         raw_text="snippet b", word_count=2)

    async def fetcher(url):
        return _ARTICLE_HTML if url == "https://a.com" else None

    pages = await enrich_pages_with_full_content([good, bad], fetcher)
    assert pages[0].word_count >= 60  # scraped
    assert pages[1].raw_text == "snippet b"  # fell back


# --- existing MockSearchProvider coverage --------------------------------


async def test_mock_provider_returns_requested_count():
    provider = MockSearchProvider()
    pages = await provider.search("content automation", num_results=4)
    assert len(pages) == 4


async def test_mock_provider_ranks_are_sequential_starting_at_one():
    provider = MockSearchProvider()
    pages = await provider.search("seo tools", num_results=3)
    assert [p.rank for p in pages] == [1, 2, 3]


async def test_mock_provider_includes_topic_in_content():
    provider = MockSearchProvider()
    pages = await provider.search("email marketing", num_results=1)
    assert "email marketing" in pages[0].raw_text.lower()
    assert pages[0].word_count > 0


# --- SerpAPIProvider timeout / retry degradation -------------------------


class _TimeoutClient:
    """Fake httpx.AsyncClient whose GET always raises a read timeout.

    Records how many times it was called so the test can assert the retry
    decorator actually re-attempted the request. Mirrors the existing pattern
    of faking the HTTP layer so no real network call happens in CI.
    """

    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        type(self).calls += 1
        raise httpx.ReadTimeout("read timed out")


async def test_serp_search_retries_then_returns_empty_on_read_timeout(monkeypatch):
    monkeypatch.setenv("SERPAPI_KEY", "test-key")
    _TimeoutClient.calls = 0
    monkeypatch.setattr(research_agent.httpx, "AsyncClient", _TimeoutClient)
    # Drop the exponential backoff so the 3 attempts don't actually sleep.
    monkeypatch.setattr(
        SerpAPIProvider._fetch_serp_results.retry, "wait", wait_none()
    )

    provider = SerpAPIProvider()
    # A SerpAPI outage must degrade to an empty result set, not raise.
    pages = await provider.search("email marketing", num_results=3)

    assert pages == []
    # stop_after_attempt(3): the request is tried exactly three times.
    assert _TimeoutClient.calls == 3

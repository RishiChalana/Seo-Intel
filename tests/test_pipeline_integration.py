"""
Full pipeline integration test.

Runs the actual LangGraph graph end-to-end (research -> index -> keywords ->
outline -> score) with a FakeLLMClient and MockSearchProvider so it's fast,
free, and deterministic in CI, while still exercising every real node,
including the RAG store and the deterministic scoring logic. This is the
test that proves the wiring works, not just each piece in isolation.
"""

import pytest

from app.agents.keyword_agent import _ClusterLabelResponse
from app.agents.research_agent import MockSearchProvider
from app.core.llm import FakeLLMClient
from app.core.schemas import (
    ContentOutline,
    KeywordCluster,
    OutlineSection,
    PipelineRequest,
    SearchIntent,
)
from app.graph import run_pipeline
from app.rag.embedder import TfidfEmbedder


def _build_fake_llm() -> FakeLLMClient:
    cluster = _ClusterLabelResponse(
        primary_keyword="podcast editing",
        related_keywords=["audio editing software", "podcast automation"],
        intent=SearchIntent.COMMERCIAL,
    )
    outline = ContentOutline(
        title="Podcast Editing: The Complete Guide",
        meta_description="Everything you need to know about podcast editing and automation tools.",
        sections=[
            OutlineSection(
                heading="What is podcast editing",
                level=2,
                talking_points=["Define podcast editing", "Cite a study on adoption rates"],
                target_keywords=["podcast editing"],
            ),
            OutlineSection(
                heading="Best audio editing software",
                level=2,
                talking_points=["Compare top tools", "Expert recommendation"],
                target_keywords=["audio editing software"],
            ),
            OutlineSection(
                heading="Podcast automation workflow",
                level=2,
                talking_points=["Step by step example", "Data on time saved"],
                target_keywords=["podcast automation"],
            ),
        ],
        estimated_word_count=1800,
    )
    return FakeLLMClient(
        responses={
            "_ClusterLabelResponse": cluster,
            "ContentOutline": outline,
        }
    )


@pytest.mark.asyncio
async def test_full_pipeline_produces_valid_brief():
    request = PipelineRequest(topic="podcast editing", max_competitors=3)
    llm = _build_fake_llm()

    brief = await run_pipeline(
        request=request,
        search_provider=MockSearchProvider(),
        llm=llm,
        embedder_factory=lambda: TfidfEmbedder(n_components=8),
    )

    assert brief.topic == "podcast editing"
    assert brief.competitor_pages_analyzed == 3
    assert len(brief.keyword_clusters) >= 1
    assert brief.outline.title
    assert len(brief.outline.sections) == 3
    assert 0.0 <= brief.score.overall <= 1.0
    # LLM should have been called at least once for clustering and once for outline
    assert len(llm.calls) >= 2


@pytest.mark.asyncio
async def test_pipeline_score_reflects_grounded_outline():
    """The good outline (with keywords + E-E-A-T markers baked in) should score decently."""
    request = PipelineRequest(topic="podcast editing", max_competitors=2)
    llm = _build_fake_llm()

    brief = await run_pipeline(
        request=request,
        search_provider=MockSearchProvider(),
        llm=llm,
        embedder_factory=lambda: TfidfEmbedder(n_components=8),
    )

    assert brief.score.structure_completeness == 1.0
    assert brief.score.eeat_signal_score > 0

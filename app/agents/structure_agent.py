"""
Structure Agent: generates the content outline.

The key design choice here is that the LLM prompt is grounded with RAG-
retrieved competitor chunks (what top-ranking pages actually cover) rather
than asked to "write an outline about X" cold. This is what turns a generic
LLM outline into a competitive content brief - it can identify gaps
competitors share (copy weaknesses) and topics competitors cover that a
naive brief would miss.
"""

from __future__ import annotations

from app.core.llm import LLMClient
from app.core.schemas import ContentOutline, KeywordCluster
from app.rag.store import CompetitorRAGStore


async def generate_outline(
    topic: str,
    clusters: list[KeywordCluster],
    rag_store: CompetitorRAGStore,
    llm: LLMClient,
) -> ContentOutline:
    retrieved = rag_store.retrieve(topic, k=8)
    context_blocks = "\n---\n".join(
        f"[{r['title']}] {r['text'][:500]}" for r in retrieved
    ) or "No competitor content indexed; rely on general SEO best practice."

    keyword_summary = "\n".join(
        f"- {c.primary_keyword} ({c.intent.value}): {', '.join(c.related_keywords[:5])}"
        for c in clusters
    )

    outline = await llm.complete_structured(
        system=(
            "You are an SEO content strategist writing a content brief for a "
            "writer. Ground the outline in the competitor content excerpts "
            "provided - identify what they cover, then propose sections that "
            "match or exceed that coverage plus at least one genuine content "
            "gap the competitors miss. Keep section count between 4 and 8."
        ),
        prompt=(
            f"Topic: {topic}\n\n"
            f"Keyword clusters to target:\n{keyword_summary}\n\n"
            f"Top-ranking competitor content excerpts:\n{context_blocks}"
        ),
        schema=ContentOutline,
    )
    return outline

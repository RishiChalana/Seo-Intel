"""
LangGraph orchestration: wires Research -> Index (RAG) -> Keywords -> Outline
-> Score into a single stateful graph.

Why a graph instead of a linear function call chain: each node's state is
independently inspectable/loggable (useful when a client run misbehaves -
you can see exactly which stage produced bad output), and it's the same
architectural pattern as EchoRoom/Helm which makes this pipeline consistent
with the rest of the portfolio rather than a one-off script.
"""

from __future__ import annotations

from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.eval_agent import score_brief
from app.agents.keyword_agent import cluster_keywords
from app.agents.research_agent import SearchProvider
from app.agents.structure_agent import generate_outline
from app.core.llm import LLMClient
from app.core.schemas import (
    CompetitorPage,
    ContentBrief,
    ContentOutline,
    KeywordCluster,
    PipelineRequest,
)
from app.rag.embedder import Embedder, get_embedder
from app.rag.store import CompetitorRAGStore


class PipelineState(TypedDict, total=False):
    request: PipelineRequest
    pages: list[CompetitorPage]
    clusters: list[KeywordCluster]
    outline: ContentOutline
    brief: ContentBrief
    chunks_indexed: int


def build_graph(
    search_provider: SearchProvider,
    llm: LLMClient,
    embedder_factory: Optional[Callable[[], Embedder]] = None,
):
    """
    Returns a compiled LangGraph app.

    embedder_factory produces a FRESH Embedder instance per call. This
    matters: the RAG store (competitor chunks) and the keyword clustering
    step both call fit_transform on their own corpus. If they shared one
    embedder instance, fitting one would silently invalidate the other's
    fitted vocabulary/dimensionality - which surfaced as a real dimension-
    mismatch bug during testing. Each consumer gets its own instance.
    """
    make_embedder = embedder_factory or get_embedder

    # The RAG store holds an in-memory Chroma collection, which isn't JSON-
    # serializable and shouldn't live in the graph's typed state (LangGraph
    # may copy state between node invocations rather than mutate in place,
    # so stashing it directly on the state dict is not safe - this bit us
    # in testing too). A closure-scoped ref keeps it reachable across nodes
    # within a single pipeline run without polluting state.
    run_store: dict[str, CompetitorRAGStore] = {}

    async def research_node(state: PipelineState) -> PipelineState:
        req = state["request"]
        pages = await search_provider.search(req.topic, req.max_competitors)
        return {"pages": pages}

    async def index_node(state: PipelineState) -> PipelineState:
        store = CompetitorRAGStore(make_embedder())
        n = store.index_pages(state["pages"])
        run_store["store"] = store
        return {"chunks_indexed": n}

    async def keyword_node(state: PipelineState) -> PipelineState:
        clusters = await cluster_keywords(
            topic=state["request"].topic,
            pages=state["pages"],
            embedder=make_embedder(),
            llm=llm,
        )
        return {"clusters": clusters}

    async def outline_node(state: PipelineState) -> PipelineState:
        store = run_store["store"]
        outline = await generate_outline(
            topic=state["request"].topic,
            clusters=state["clusters"],
            rag_store=store,
            llm=llm,
        )
        return {"outline": outline}

    async def score_node(state: PipelineState) -> PipelineState:
        score = score_brief(state["outline"], state["clusters"])
        brief = ContentBrief(
            topic=state["request"].topic,
            keyword_clusters=state["clusters"],
            competitor_pages_analyzed=len(state["pages"]),
            outline=state["outline"],
            score=score,
            # All LLM calls (keyword + outline nodes) have run by now, so the
            # tracker holds the full per-run usage. llm is closure-scoped here.
            usage=llm.usage.summary(),
        )
        return {"brief": brief}

    graph = StateGraph(PipelineState)
    graph.add_node("research", research_node)
    graph.add_node("index", index_node)
    graph.add_node("keywords", keyword_node)
    graph.add_node("outline", outline_node)
    graph.add_node("score", score_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "index")
    graph.add_edge("index", "keywords")
    graph.add_edge("keywords", "outline")
    graph.add_edge("outline", "score")
    graph.add_edge("score", END)

    return graph.compile()


async def run_pipeline(
    request: PipelineRequest,
    search_provider: SearchProvider,
    llm: LLMClient,
    embedder_factory: Optional[Callable[[], Embedder]] = None,
) -> ContentBrief:
    # Reset so usage reflects only this run, even if the client is reused.
    llm.usage.reset()
    app = build_graph(search_provider, llm, embedder_factory)
    result = await app.ainvoke({"request": request})
    return result["brief"]

"""
FastAPI entrypoint. Exposes the multi-agent SEO pipeline as a single
POST endpoint. Auth/rate-limiting deliberately kept out of scope here -
this is an internal tool, not a public API - but the layering (routes thin,
logic lives in app/graph.py) mirrors EchoRoom's structure for consistency.
"""

from __future__ import annotations

import logging
import time

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.research_agent import get_search_provider
from app.core.llm import get_llm_client
from app.core.schemas import ContentBrief, PipelineRequest
from app.graph import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-intel")

app = FastAPI(
    title="SEO Content Intelligence Pipeline",
    description=(
        "Multi-agent pipeline that turns a topic into a competitor-grounded, "
        "SEO-optimized content brief using RAG over top-ranking pages."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/brief", response_model=ContentBrief)
async def create_brief(request: PipelineRequest):
    start = time.monotonic()
    try:
        search_provider = get_search_provider()
        llm = get_llm_client()
        brief = await run_pipeline(request, search_provider, llm)
    except Exception as exc:  # noqa: BLE001 - surface as clean 500 for API consumers
        logger.exception("Pipeline failed for topic=%s", request.topic)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.monotonic() - start
    logger.info(
        "Brief generated for '%s' in %.2fs | %d LLM calls, %d tokens, ~$%.5f",
        request.topic,
        elapsed,
        brief.usage.total_calls,
        brief.usage.total_tokens,
        brief.usage.estimated_cost_usd,
    )
    return brief

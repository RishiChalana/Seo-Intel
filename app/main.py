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
from tenacity import RetryError

from app.agents.research_agent import get_search_provider
from app.core.llm import get_llm_client
from app.core.schemas import ContentBrief, PipelineRequest
from app.graph import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-intel")


def friendly_error(exc: Exception) -> tuple[int, str]:
    """Translate an internal pipeline exception into a clean (status, detail)
    for API consumers. Unwraps tenacity's RetryError to the underlying cause
    and special-cases Gemini rate-limit/quota and missing-key errors so the
    frontend shows something actionable instead of "RetryError[...]".
    """
    root: BaseException = exc
    if isinstance(exc, RetryError) and exc.last_attempt is not None:
        cause = exc.last_attempt.exception()
        if cause is not None:
            root = cause

    text = str(root)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return 429, (
            "Gemini API rate limit or daily quota reached. Wait a moment and "
            "try again, or switch to a billed API key."
        )
    if "No LLM API key" in text or "SERPAPI_KEY not set" in text:
        return 503, text
    return 500, f"Pipeline failed: {text}"

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
    except Exception as exc:  # noqa: BLE001 - surface a clean error to API consumers
        logger.exception("Pipeline failed for topic=%s", request.topic)
        status, detail = friendly_error(exc)
        raise HTTPException(status_code=status, detail=detail) from exc

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

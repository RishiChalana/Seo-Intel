"""
FastAPI entrypoint. Exposes the multi-agent SEO pipeline as a single
POST endpoint. Auth/rate-limiting deliberately kept out of scope here -
this is an internal tool, not a public API - but the layering (routes thin,
logic lives in app/graph.py) mirrors EchoRoom's structure for consistency.
"""

from __future__ import annotations

import logging
import os
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

    # Some exceptions carry an empty message (e.g. MemoryError), which would
    # otherwise surface as a useless "Pipeline failed: ". Fall back to the
    # class name so the error is always identifiable.
    text = str(root).strip() or type(root).__name__

    if isinstance(root, MemoryError):
        return 503, (
            "The server ran out of memory while building the analysis. This "
            "pipeline (vector store + embeddings) needs more RAM than a small "
            "free instance provides — upgrade the instance size and retry."
        )
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return 429, (
            "Gemini API rate limit or daily quota reached. Wait a moment and "
            "try again, or switch to a billed API key."
        )
    if "No LLM API key" in text or "SERPAPI_KEY not set" in text:
        return 503, text
    return 500, f"Pipeline failed ({type(root).__name__}): {text}"

app = FastAPI(
    title="SEO Content Intelligence Pipeline",
    description=(
        "Multi-agent pipeline that turns a topic into a competitor-grounded, "
        "SEO-optimized content brief using RAG over top-ranking pages."
    ),
    version="1.0.0",
)

# CORS origins are env-driven so the deployed API can be locked to the Vercel
# domain without a code change. Defaults to "*" (open) for local dev and the
# initial deploy; set ALLOWED_ORIGINS to a comma-separated list once the
# frontend URL is known, e.g. "https://seo-intel.vercel.app".
#
# A blank/unset value means "use the open default" — NOT "allow nothing".
# An empty allow-list would silently reject every cross-origin request
# (preflights 400, no CORS headers), which is a confusing way to fail.
_origins_env = os.environ.get("ALLOWED_ORIGINS", "*").strip()
_parsed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
allow_origins = ["*"] if (not _parsed_origins or "*" in _parsed_origins) else _parsed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    # No cookies/credentials are used; keeping this False is what makes the
    # "*" origin legal per the CORS spec.
    allow_credentials=False,
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

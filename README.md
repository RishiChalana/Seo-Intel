# SEO Content Intelligence Pipeline

A multi-agent system that turns a topic into a competitor-grounded, SEO-optimized
content brief: it researches top-ranking pages, indexes them into a vector store,
clusters target keywords by intent, generates a structured outline grounded in
what competitors actually cover, and scores the result against a deterministic
rubric.

Built for a content marketing team's internal tooling — the kind of research
work a strategist currently does manually across search results, keyword tools,
and spreadsheets, compressed into a single API call.

## Why this architecture

**Multi-agent over a single prompt.** A single "write me a content brief about X"
prompt produces a generic outline that could apply to any topic. Splitting into
Research → Index → Keywords → Outline → Score means each stage has one job,
is independently testable, and — critically — later stages are *grounded* in
earlier stages' real output instead of the LLM inventing structure from its
training prior.

**RAG over competitor content, not just an LLM asked to "know" the topic.**
The Structure agent doesn't outline from memory. It retrieves the most relevant
chunks of actual top-ranking competitor pages (via a Chroma vector store) and
writes the outline against that retrieved context — this is what lets it
identify genuine content gaps ("competitors all cover X and Y, none cover Z")
instead of producing a plausible-sounding but generic structure.

**Scoring is a rubric, not an LLM opinion.** `eval_agent.py` computes
`keyword_coverage`, `structure_completeness`, and `eeat_signal_score`
deterministically from the outline object, and `readability_grade` via the
established Flesch-Kincaid formula (`textstat`). No "ask the LLM to grade
itself" — that's ungrounded and irreproducible. Anyone can re-run the same
outline through `score_brief()` and get the same number.

**Every external dependency is pluggable.** Search provider, embedding
backend, and LLM client are all defined as abstract interfaces with a
production implementation and a local/offline implementation:

| Component | Production | Local/offline default |
|---|---|---|
| Search | `SerpAPIProvider` (needs `SERPAPI_KEY`) | `MockSearchProvider` (deterministic fixtures) |
| Embeddings | `VoyageEmbedder` (needs `VOYAGE_API_KEY`) | `TfidfEmbedder` (scikit-learn, zero cost) |
| LLM | `GeminiLLMClient` (needs `GEMINI_API_KEY`) | `FakeLLMClient` (test stub, injected) |

This means the full pipeline — including the RAG store and every agent — is
tested end-to-end without any paid API key, and swapping to production
providers is a config change, not a code change.

## Architecture

```
PipelineRequest
      │
      ▼
 ┌─────────┐    ┌───────┐    ┌──────────┐    ┌──────────┐    ┌───────┐
 │Research │───▶│ Index │───▶│ Keywords │───▶│ Outline  │───▶│ Score │──▶ ContentBrief
 │ Agent   │    │ (RAG) │    │  Agent   │    │  Agent   │    │ Agent │
 └─────────┘    └───────┘    └──────────┘    └──────────┘    └───────┘
   fetches       chunks +     clusters        retrieves        computes
   top-N          embeds      candidate       competitor        rubric
   competitor    competitor   keywords by     chunks from       score
   pages         pages into   embedding       RAG store,        (no LLM
                 Chroma       similarity      generates         self-grading)
                 (per-run)    (KMeans),       grounded
                              LLM labels      outline
                              intent
```

Orchestrated as a LangGraph `StateGraph` (same pattern used in EchoRoom/Helm)
so each node's input/output is independently inspectable — useful when a run
produces a bad brief and you need to know which stage caused it.

## Real bugs hit building this (kept here because they were worth learning from)

1. **RAG store lost between graph nodes.** Initially stashed the `CompetitorRAGStore`
   (a live Chroma collection, not serializable) directly on the LangGraph state
   dict. LangGraph doesn't guarantee state dict mutations persist as-is across
   async node boundaries — the outline node saw a `KeyError` because the store
   never made it through. Fixed by keeping the store in a closure-scoped
   reference instead of the typed graph state.

2. **Shared embedder instance corrupted fitted state across agents.** The RAG
   store and the keyword-clustering step both call `embedder.fit_transform()`
   on their own corpus (competitor chunks vs. candidate keyword phrases). They
   were sharing one `Embedder` instance — fitting it a second time (for
   keywords) silently invalidated the vocabulary/dimensionality the RAG store
   had already fit, causing a `chromadb.errors.InvalidArgumentError: expecting
   embedding with dimension of 1, got 8` when the outline node later queried
   the store. Fixed by giving each consumer its own embedder instance via a
   factory function rather than sharing one.

Both were caught by the integration test (`test_pipeline_integration.py`)
before ever touching a real API — which is the actual argument for writing
that test in the first place.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY

uvicorn app.main:app --reload
# POST http://localhost:8000/brief  {"topic": "email marketing automation"}
```

Without `SERPAPI_KEY` set, the app runs against `MockSearchProvider` fixtures —
useful for demoing the full pipeline without a paid search API key.

## Testing

```bash
pytest -q
```

17 tests covering: deterministic scoring logic, RAG chunking/retrieval
correctness (including a semantic relevance check — a query about pasta
should retrieve the cooking page, not the finance page), keyword phrase
extraction, and two full end-to-end pipeline runs through the actual
LangGraph graph with fakes injected at the LLM/search boundary.

## What's out of scope (by design, not oversight)

- Auth/rate-limiting on the API — internal tool, not public-facing
- Persistent storage of past briefs — each run is stateless; add a DB layer
  if history/versioning becomes a requirement
- Real competitor page scraping (vs. SERP snippets) — `SerpAPIProvider`
  currently uses search snippets; a production version would fetch and parse
  full page HTML for richer RAG context

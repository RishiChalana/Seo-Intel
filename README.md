# SEO Content Intelligence Pipeline

A multi-agent system that turns a topic into a competitor-grounded, SEO-optimized
content brief: it researches top-ranking pages, fetches and parses their full HTML,
indexes them into a vector store, clusters target keywords by intent, generates a
structured outline grounded in what competitors actually cover, and scores the result
against a deterministic rubric.

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

**RAG over full competitor articles, not just search snippets.**
The Structure agent doesn't outline from memory. `SerpAPIProvider` fetches each
competitor URL and extracts the full article body with trafilatura (stripping nav,
scripts, and boilerplate), so the Chroma RAG store contains thousands of words of
real competitor content instead of 150-word SERP snippets. Any page that fails to
fetch or yields thin content transparently falls back to its snippet — one
paywalled or bot-blocking URL never degrades the rest of the run.

**Scoring is a rubric, not an LLM opinion.** `eval_agent.py` computes
`keyword_coverage`, `structure_completeness`, and `eeat_signal_score`
deterministically from the outline object, and `readability_grade` via the
established Flesch-Kincaid formula (`textstat`). No "ask the LLM to grade
itself" — that's ungrounded and irreproducible. Anyone can re-run the same
outline through `score_brief()` and get the same number.

**Token and cost telemetry is first-class.** Every LLM call records its input
and output token counts (for Gemini 2.5, thinking tokens fold into output, since
they're billed at the output rate). The `UsageTracker` buckets usage by
response-schema name — so the `usage.by_step` field on every `ContentBrief`
gives a per-pipeline-stage breakdown without threading a "step name" through any
agent's call signature, and `usage.model` reports which model ran. Cost
estimates use a clearly-labeled per-provider pricing table; they're relative
visibility, not billing-grade accounting.

**Every external dependency is pluggable.** Search provider, page-content source,
embedding backend, and LLM client are all defined as abstract interfaces with a
production implementation and a local/offline implementation:

| Component | Production | Local/offline default |
|---|---|---|
| Search | `SerpAPIProvider` (needs `SERPAPI_KEY`) | `MockSearchProvider` (deterministic fixtures) |
| Page content | Full HTML fetch + trafilatura extraction (`SCRAPE_FULL_PAGES=true`, default) | SERP snippets only (`SCRAPE_FULL_PAGES=false`, ~150 words/page) |
| Embeddings | `VoyageEmbedder` (needs `VOYAGE_API_KEY`) | `TfidfEmbedder` (scikit-learn, zero cost) |
| LLM | `GroqLLMClient` (`GROQ_API_KEY`, default) or `GeminiLLMClient` (`GEMINI_API_KEY`) | `FakeLLMClient` (test stub, injected) |

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
 │ Agent   │    │ (RAG) │    │  Agent   │    │  Agent   │    │ Agent │     + usage
 └─────────┘    └───────┘    └──────────┘    └──────────┘    └───────┘
   fetches        chunks +    clusters        retrieves        computes
   top-N           embeds     candidate       competitor        rubric
   competitor     competitor  keywords by     chunks from       score
   pages; fetches  pages into embedding       RAG store,        (no LLM
   full HTML,      Chroma     similarity      generates         self-grading)
   falls back      (per-run)  (KMeans),       grounded
   to snippet                 LLM labels      outline
   on error                   intent
```

Token + cost telemetry is a cross-cutting concern: whichever LLM client is
active (`GroqLLMClient` or `GeminiLLMClient`) records token usage from every
response into a `UsageTracker`. At the end of the run the tracker snapshots
per-step and aggregate totals onto `ContentBrief.usage`.

Orchestrated as a LangGraph `StateGraph` (same pattern used in EchoRoom/Helm)
so each node's input/output is independently inspectable — useful when a run
produces a bad brief and you need to know which stage caused it.

## Real bugs and constraints hit building this

The interesting part of the project. Each of these was a genuine failure with a
non-obvious cause; each is now covered by a test so it can't silently return.

### Pipeline correctness

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

3. **Keyword extraction collapsed on real scraped text.** Against clean fixtures
   the word-frequency extractor was fine; against live SERP/article text it
   produced garbage `related_keywords` like `"have"`, `"taken"`, `"guesswork"`,
   `"out"`, `"now"`, `"don"` — dragging `keyword_coverage` to **0.381** and
   tripping a "Low keyword coverage" warning on an otherwise good outline. Three
   compounding causes: a 27-word stopword set that missed common filler;
   contractions tokenizing to fragments (`"don't"` → `"don"`); and bigrams built
   from the *post-stopword-removal* token stream, which invented adjacencies that
   never existed in the source. On top of that, the clustering prompt said "list
   the rest as related_keywords," so the LLM dutifully echoed every noisy
   candidate back, inflating the coverage denominator. Fixed with a ~170-word
   stopword set plus contraction-stem filtering, bigrams rebuilt from the raw
   token sequence and weighted 3× so real phrases dominate, and a prompt that
   selects and discards instead of echoing. Coverage went **0.381 → ~1.0**.

### Integration & environment

4. **`.env` was never loaded — "No LLM API key found" with the key right there.**
   The app read `os.environ` directly, but `python-dotenv` wasn't installed and
   `load_dotenv()` was never called, so the `.env` file was inert. Fixed by
   adding `python-dotenv` and calling `load_dotenv()` at the top of `app/main.py`
   before anything reads a key.

5. **Full-page scraping reliably blocked by major SEO properties.** Even with a
   legitimate browser User-Agent string, large content-marketing sites (Mailchimp,
   tool-comparison blogs) return 403 or time out — they detect non-browser
   request patterns. On a typical 3-page live fetch, 1–2 pages succeed (10–20×
   more content than their snippet) and the remainder fall back silently. The
   fallback path is validated end-to-end: any page that returns an error, a
   non-200 status, or fewer than 60 extracted words reverts to its SERP snippet,
   and the pipeline completes normally. Consistent full-page extraction at scale
   would require a scraping API (ScraperAPI, Zyte) with rotating proxies and JS
   rendering — the correct production path, but out of scope here.

### Going live (deployment)

6. **A blank env var silently blocked all CORS.** After deploying the frontend to
   Vercel and the API to Render, the browser couldn't call the API: every
   preflight returned `400` and no response carried an `Access-Control-Allow-Origin`
   header (curl worked, because curl ignores CORS — which is exactly why the
   failure hid until a real browser tried it). Root cause: `ALLOWED_ORIGINS` was
   set to an *empty string* on Render, and the origin parser read `""` as "an
   explicit allow-list of zero origins" → reject everything. Fixed so a
   blank/whitespace value falls back to the open default (`["*"]`); only a
   non-empty value restricts. Also documented the trailing-slash trap — browsers
   send `Origin` with no trailing slash, so `https://app.vercel.app/` never
   matches.

7. **Production 500s that said nothing.** A failing run surfaced to the client as
   `"Pipeline failed: "` — an empty message — because the underlying exceptions
   (`MemoryError`, `TimeoutError`) carry an empty `str()`, and tenacity's
   `RetryError` wrapped the real cause out of view. Fixed the error handler to
   unwrap `RetryError` to its root cause, fall back to the exception's class name
   when the message is blank, and map known failures to actionable responses
   (Gemini quota → `429` with a "wait and retry" note, out-of-memory → `503`).
   Errors are now always identifiable, in the logs and in the API response the
   frontend shows.

Every one of these is now guarded by a test (unit or the end-to-end integration
run) — the actual argument for writing the tests in the first place.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY (or GEMINI_API_KEY) and SERPAPI_KEY

uvicorn app.main:app --reload
# POST http://localhost:8000/brief  {"topic": "email marketing automation"}
# GET  http://localhost:8000/docs   (OpenAPI schema with full ContentBrief response)
```

The LLM backend is auto-selected, **preferring Groq** (`llama-3.3-70b`, fast and
a far more generous free tier) when `GROQ_API_KEY` is set, and falling back to
Gemini (`gemini-2.5-flash`) otherwise. Force a provider with `LLM_BACKEND=groq`
or `LLM_BACKEND=gemini`.

Without `SERPAPI_KEY` set, the app runs against `MockSearchProvider` fixtures —
useful for demoing the full pipeline without a paid search API key.

Set `SCRAPE_FULL_PAGES=false` to skip full-page fetching and use SERP snippets
only (faster, zero extra HTTP requests, but shallower RAG context).

## Frontend

A React + TypeScript + Vite + Tailwind UI lives in `frontend/`, styled from the
EMIAC "Strategic Precision" design system (Forest Green, warm paper backgrounds,
Plus Jakarta Sans + DM Sans). It walks the user through topic input → an animated
pipeline-execution view → a full content-brief dashboard (score gauges, outline
document, real per-step token/cost telemetry, keyword clusters, content gaps),
with export to Markdown / JSON / PDF.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api -> :8000
```

Run the backend (`uvicorn app.main:app --reload`) alongside it. See
`frontend/README.md` for details. `src/lib/types.ts` mirrors the backend
Pydantic schema exactly, so the API contract stays type-checked end to end.

## Testing

```bash
pytest -q
```

56 tests covering: deterministic scoring logic, RAG chunking/retrieval
correctness (including a semantic relevance check — a query about pasta
should retrieve the cooking page, not the finance page), keyword phrase
extraction with real-world noisy text, full-page scraping extraction and
all fallback paths (fetch failure, 403, thin content, mixed success/failure),
token/cost telemetry math and per-step bucketing, CORS origin resolution
(blank/whitespace → open, real origins → restricted), clean API error mapping
(quota/rate-limit → 429, out-of-memory → 503, empty-message exceptions → named
type), and two full end-to-end pipeline runs through the actual LangGraph graph
with fakes injected at the LLM/search boundary.

## Deployment

Split deployment: the FastAPI backend runs on **Render**, the Vite frontend on
**Vercel**. The two are decoupled by a single build-time env var — the frontend
reads `VITE_API_URL`; nothing else is host-aware.

- **Live frontend:** https://seo-intel-murex.vercel.app
- **Live API:** https://seo-intel-api.onrender.com

**Backend (Render).** `render.yaml` is a Blueprint: New → Blueprint → point at
this repo, or configure a Web Service manually with:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Env vars: `GROQ_API_KEY` (or `GEMINI_API_KEY`) and `SERPAPI_KEY` (secrets, set
  in the dashboard); `EMBEDDING_BACKEND=tfidf`, `SCRAPE_FULL_PAGES=true`, and
  `ALLOWED_ORIGINS` (defaults to `*`; set to the Vercel URL to lock down CORS)
  ship as defaults.

**Frontend (Vercel).** Import the repo, set **Root Directory** to `frontend`
(Vercel auto-detects Vite from there; `vercel.json` pins the build command,
`dist` output, and an SPA rewrite). Set one env var: `VITE_API_URL` = the Render
API origin (no trailing slash, no `/brief`). Because Vite inlines `VITE_*` at
build time, a change to this var requires a redeploy.

**CORS note.** The API ships open (`allow_origins=["*"]`, no credentials, which
is spec-legal). A blank/unset `ALLOWED_ORIGINS` also resolves to open — only a
non-empty value restricts. To lock down, set `ALLOWED_ORIGINS` on Render to the
Vercel origin **with no trailing slash** (browsers send `Origin` without one, so
`https://seo-intel.vercel.app/` would fail to match — use
`https://seo-intel.vercel.app`). Comma-separate multiple origins.

**Free-tier caveat.** Render's free plan cold-starts after ~15 min idle (~50s
spin-up), and a full brief run is itself ~30-45s. The first request after idle
can therefore be slow; a warm service responds in normal pipeline time.

## What's out of scope (by design, not oversight)

- Auth/rate-limiting on the API — internal tool, not public-facing
- Persistent storage of past briefs — each run is stateless; add a DB layer
  if history/versioning becomes a requirement
- Scraping-API integration for consistent full-page extraction at scale —
  direct fetches succeed on ~50% of pages due to bot-blocking; ScraperAPI or
  Zyte with rotating proxies would fix this but adds a paid dependency and
  operational overhead not warranted for an internal tool

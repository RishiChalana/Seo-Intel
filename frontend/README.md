# EMIAC SEO Intelligence — Frontend

React + TypeScript + Vite + Tailwind UI for the SEO Content Intelligence
pipeline. Design system adapted from the EMIAC Stitch spec ("Strategic
Precision" — Forest Green brand, warm paper backgrounds, Plus Jakarta Sans +
DM Sans, tonal-layer depth).

## Screens / flow

A single-page flow driven by a small state machine in `App.tsx`:

1. **Topic Input** — topic, competitor count, optional audience → `POST /brief`.
2. **Pipeline Execution** — animated 5-stage stepper (Research → Index → Keywords
   → Outline → Score) while the request is in flight. The backend is synchronous
   with no progress stream, so stages advance on estimated timing and the last
   one holds until the real response arrives (never claims "done" early).
3. **Content Brief Dashboard** — score gauges, the outline document, run
   telemetry (real token/cost by pipeline stage), semantic keyword clusters,
   and content gaps.
4. **Export modal** — download the brief as Markdown, JSON (both real
   client-side downloads), or PDF (browser print of the outline via print CSS).

## 21st.dev-inspired components

- `GlowCard` — cursor-follow radial spotlight (Aceternity/21st.dev "Glowing
  Effect"), used on the telemetry widget.
- `ScoreBento` — bento-grid score layout with an emphasized Overall tile.
- `GeneratingView` — animated pipeline stepper (framer-motion).

## Data contract

`src/lib/types.ts` mirrors the backend Pydantic schema (`app/core/schemas.py`
+ `app/core/usage.py`) exactly. `src/lib/api.ts` is the typed client.

## Running

```bash
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api/*` → `http://127.0.0.1:8000` (see `vite.config.ts`),
so start the backend first:

```bash
# from the project root
uvicorn app.main:app --reload
```

For a deployed backend, set `VITE_API_URL` (e.g. `https://seo-intel-api.onrender.com`)
instead of relying on the proxy. See `.env.example`.

```bash
npm run build        # type-check + production bundle to dist/
npm run preview      # serve the built bundle
```

## Note on the live API

The backend prefers Groq (`llama-3.3-70b`) and falls back to Gemini. If the
provider's rate limit is hit, a `429` is surfaced on the input screen — wait a
moment and retry, or use a billed key. The UI handles it gracefully (the error
is shown, no crash), and the telemetry card reports whichever model actually
ran via `usage.model`.

import type { ContentBrief, PipelineRequest } from "./types";

// Backend API base URL.
// - Production (Vercel): set VITE_API_URL to the deployed backend origin,
//   e.g. https://seo-intel-api.onrender.com  (no trailing /brief).
// - Local dev: leave it unset -> falls back to "/api", which Vite proxies to
//   http://127.0.0.1:8000 (see vite.config.ts).
// Trailing slash is stripped so `${API_BASE}/brief` never doubles up.
const API_BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function generateBrief(
  request: PipelineRequest,
): Promise<ContentBrief> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}/brief`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw new ApiError(
      "Could not reach the pipeline API. Is the backend running on port 8000?",
    );
  }

  if (!resp.ok) {
    let detail = `Request failed (HTTP ${resp.status})`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body; keep the generic message */
    }
    throw new ApiError(detail, resp.status);
  }

  return (await resp.json()) as ContentBrief;
}

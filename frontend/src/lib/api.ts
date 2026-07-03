import type { ContentBrief, PipelineRequest } from "./types";

// In dev, Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.ts).
// Override with VITE_API_BASE for a deployed backend.
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

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

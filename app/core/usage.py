"""
LLM token + cost telemetry.

Every real LLM call reports token usage; this module accumulates it for a
single pipeline run and buckets it by call label. The label is the response
schema's class name, which maps 1:1 to a pipeline step (_ClusterLabelResponse
= keyword clustering, ContentOutline = outline generation) - so we get a
per-step cost breakdown for free, without threading a "step name" through
every agent's call signature.

Cost is estimated from a static pricing table, labeled clearly as an
estimate since provider prices change. The point is relative visibility
("outline generation costs 4x what clustering does"), not billing-grade
accounting.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Gemini pricing in USD per 1M tokens: (input, output). Estimates - update if
# Google changes rates. Output price is applied to completion + thinking
# tokens, which Gemini 2.5 bills at the output rate.
_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}
_DEFAULT_PRICING = (0.30, 2.50)


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_price, out_price = _PRICING_PER_1M.get(model, _DEFAULT_PRICING)
    return (prompt_tokens / 1_000_000) * in_price + (completion_tokens / 1_000_000) * out_price


class StepUsage(BaseModel):
    """Per-step token + cost breakdown (one entry per pipeline stage)."""

    label: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class TokenUsage(BaseModel):
    """Aggregate LLM usage for a single pipeline run, surfaced on the API."""

    total_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    by_step: list[StepUsage] = Field(default_factory=list)


class UsageTracker:
    """
    Mutable accumulator an LLMClient writes to on every call.

    Kept separate from the immutable TokenUsage summary so the client records
    incrementally (cheap) and the API snapshots totals once via summary().
    """

    def __init__(self) -> None:
        self._records: list[dict] = []

    def record(
        self, label: str, model: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        self._records.append(
            {
                "label": label,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }
        )

    def reset(self) -> None:
        self._records.clear()

    def summary(self) -> TokenUsage:
        by_step: dict[str, StepUsage] = {}
        total_prompt = total_completion = 0
        total_cost = 0.0

        for r in self._records:
            p, c = r["prompt_tokens"], r["completion_tokens"]
            cost = estimate_cost_usd(r["model"], p, c)
            total_prompt += p
            total_completion += c
            total_cost += cost

            step = by_step.get(r["label"])
            if step is None:
                by_step[r["label"]] = StepUsage(
                    label=r["label"],
                    calls=1,
                    prompt_tokens=p,
                    completion_tokens=c,
                    total_tokens=p + c,
                    estimated_cost_usd=round(cost, 6),
                )
            else:
                step.calls += 1
                step.prompt_tokens += p
                step.completion_tokens += c
                step.total_tokens += p + c
                step.estimated_cost_usd = round(step.estimated_cost_usd + cost, 6)

        return TokenUsage(
            total_calls=len(self._records),
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            estimated_cost_usd=round(total_cost, 6),
            by_step=list(by_step.values()),
        )

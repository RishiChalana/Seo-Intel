"""
Thin, provider-agnostic LLM client.

Agents call complete_structured() and get back a validated Pydantic model.
Two production backends are supported behind one interface:

- GroqLLMClient  (llama-3.3-70b) — fast, generous free tier; the default when
  GROQ_API_KEY is set, since Gemini's free tier rate-limits aggressively.
- GeminiLLMClient (gemini-2.5-flash) — native schema-enforced JSON output.

Tests inject FakeLLMClient. Backend selection lives in get_llm_client().
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.usage import UsageTracker

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    def __init__(self) -> None:
        # Every client exposes a usage tracker so callers can read per-run
        # token/cost telemetry uniformly, regardless of backend.
        self.usage = UsageTracker()

    @abstractmethod
    async def complete_structured(
        self, system: str, prompt: str, schema: Type[T]
    ) -> T:
        """Call the model and parse its response into `schema`."""
        raise NotImplementedError


class GeminiLLMClient(LLMClient):
    """
    Production client using Google's Gemini API. Requires GEMINI_API_KEY.

    Uses Gemini's native structured-output support (response_schema) rather
    than prompt-and-parse JSON — Gemini enforces the schema at generation
    time, which is more reliable than asking nicely in the prompt.
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        super().__init__()
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No LLM API key found. Set GEMINI_API_KEY in your environment "
                "(see .env.example)."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def complete_structured(
        self, system: str, prompt: str, schema: Type[T]
    ) -> T:
        from google.genai import types

        resp = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        self._record_usage(schema.__name__, resp)
        return schema.model_validate_json(resp.text)

    def _record_usage(self, label: str, resp) -> None:
        """Extract token counts from the Gemini response and log them.

        Thinking tokens (Gemini 2.5's internal reasoning) are billed at the
        output rate, so they're folded into completion_tokens. Guarded
        throughout because usage_metadata fields can be None on some responses.
        """
        um = getattr(resp, "usage_metadata", None)
        if um is None:
            return
        prompt_tokens = getattr(um, "prompt_token_count", 0) or 0
        completion_tokens = (getattr(um, "candidates_token_count", 0) or 0) + (
            getattr(um, "thoughts_token_count", 0) or 0
        )
        self.usage.record(label, self._model, prompt_tokens, completion_tokens)


class GroqLLMClient(LLMClient):
    """
    Production client using Groq's OpenAI-compatible API. Requires GROQ_API_KEY.

    Groq doesn't enforce a response schema at generation time the way Gemini
    does, so we use JSON mode (`response_format={"type": "json_object"}`) plus
    the schema injected into the system prompt, then validate with Pydantic.
    tenacity retries cover the occasional malformed-JSON completion.
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        super().__init__()
        from groq import AsyncGroq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No LLM API key found. Set GROQ_API_KEY in your environment "
                "(see .env.example)."
            )
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def complete_structured(
        self, system: str, prompt: str, schema: Type[T]
    ) -> T:
        schema_hint = json.dumps(schema.model_json_schema())
        full_system = (
            f"{system}\n\nRespond with ONLY a valid JSON object matching this "
            f"schema (no markdown, no prose):\n{schema_hint}"
        )
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=8000,
        )
        self._record_usage(schema.__name__, resp)
        return schema.model_validate_json(resp.choices[0].message.content or "")

    def _record_usage(self, label: str, resp) -> None:
        u = getattr(resp, "usage", None)
        if u is None:
            return
        self.usage.record(
            label,
            self._model,
            getattr(u, "prompt_tokens", 0) or 0,
            getattr(u, "completion_tokens", 0) or 0,
        )


class FakeLLMClient(LLMClient):
    """
    Deterministic stub for tests and offline development.

    Takes a mapping of {schema_class_name: instance_to_return} so each test
    can control exactly what each agent "receives" without mocking internals.
    """

    def __init__(self, responses: dict[str, BaseModel]):
        super().__init__()
        self._responses = responses
        self.calls: list[tuple[str, str]] = []

    async def complete_structured(
        self, system: str, prompt: str, schema: Type[T]
    ) -> T:
        self.calls.append((system, prompt))
        key = schema.__name__
        if key not in self._responses:
            raise KeyError(f"FakeLLMClient has no stubbed response for {key}")
        return self._responses[key]  # type: ignore[return-value]


def get_llm_client() -> LLMClient:
    """Select the LLM backend.

    LLM_BACKEND ("groq"|"gemini") forces a choice. Otherwise auto-select,
    preferring Groq when its key is present — its free tier is far more
    generous than Gemini's, which rate-limits after ~20 requests/day.
    """
    backend = os.environ.get("LLM_BACKEND", "").strip().lower()
    if backend == "gemini":
        return GeminiLLMClient()
    if backend == "groq":
        return GroqLLMClient()

    if os.environ.get("GROQ_API_KEY"):
        return GroqLLMClient()
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiLLMClient()

    raise RuntimeError(
        "No LLM API key found. Set GROQ_API_KEY or GEMINI_API_KEY in your "
        "environment (see .env.example)."
    )

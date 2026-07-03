"""
Thin LLM client abstraction over Google Gemini.

Agents call complete_structured() and get back a validated Pydantic model.
Tests inject FakeLLMClient; production wires up GeminiLLMClient from the env.
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
    return GeminiLLMClient()

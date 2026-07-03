import math

import pytest
from pydantic import BaseModel

from app.core.llm import FakeLLMClient, GeminiLLMClient
from app.core.usage import UsageTracker, estimate_cost_usd


def test_empty_tracker_summarizes_to_zero():
    summary = UsageTracker().summary()
    assert summary.total_calls == 0
    assert summary.total_tokens == 0
    assert summary.estimated_cost_usd == 0.0
    assert summary.by_step == []


def test_tracker_aggregates_totals():
    t = UsageTracker()
    t.record("StepA", "gemini-2.5-flash", 100, 50)
    t.record("StepB", "gemini-2.5-flash", 200, 80)
    s = t.summary()
    assert s.total_calls == 2
    assert s.prompt_tokens == 300
    assert s.completion_tokens == 130
    assert s.total_tokens == 430


def test_tracker_buckets_by_step_label():
    t = UsageTracker()
    t.record("_ClusterLabelResponse", "gemini-2.5-flash", 100, 50)
    t.record("_ClusterLabelResponse", "gemini-2.5-flash", 100, 50)
    t.record("ContentOutline", "gemini-2.5-flash", 500, 300)
    s = t.summary()

    by_label = {step.label: step for step in s.by_step}
    assert set(by_label) == {"_ClusterLabelResponse", "ContentOutline"}
    assert by_label["_ClusterLabelResponse"].calls == 2
    assert by_label["_ClusterLabelResponse"].prompt_tokens == 200
    assert by_label["ContentOutline"].calls == 1
    assert by_label["ContentOutline"].total_tokens == 800


def test_cost_estimate_matches_pricing_table():
    # gemini-2.5-flash: $0.30/1M input, $2.50/1M output
    cost = estimate_cost_usd("gemini-2.5-flash", 1_000_000, 1_000_000)
    assert math.isclose(cost, 0.30 + 2.50, rel_tol=1e-9)

    small = estimate_cost_usd("gemini-2.5-flash", 100, 50)
    assert math.isclose(small, (100 / 1e6) * 0.30 + (50 / 1e6) * 2.50, rel_tol=1e-9)


def test_unknown_model_falls_back_to_default_pricing():
    # Should not raise; uses default pricing rather than KeyError.
    cost = estimate_cost_usd("some-future-model", 1000, 1000)
    assert cost > 0


def test_step_cost_is_sum_of_call_costs():
    t = UsageTracker()
    t.record("ContentOutline", "gemini-2.5-flash", 100, 100)
    t.record("ContentOutline", "gemini-2.5-flash", 100, 100)
    s = t.summary()
    step = s.by_step[0]
    single = estimate_cost_usd("gemini-2.5-flash", 100, 100)
    assert math.isclose(step.estimated_cost_usd, round(single, 6) + round(single, 6), rel_tol=1e-6) \
        or math.isclose(step.estimated_cost_usd, round(single * 2, 6), rel_tol=1e-6)


def test_all_clients_expose_a_usage_tracker(monkeypatch):
    fake = FakeLLMClient(responses={})
    assert isinstance(fake.usage, UsageTracker)

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    gemini = GeminiLLMClient()
    assert isinstance(gemini.usage, UsageTracker)


# --- GeminiLLMClient usage extraction (mocked, no network) ---------------


class _FakeUsageMeta:
    prompt_token_count = 120
    candidates_token_count = 60
    thoughts_token_count = 15  # 2.5 thinking tokens, billed as output


class _FakeResponse:
    text = '{"value": "hello"}'
    usage_metadata = _FakeUsageMeta()


class _FakeModels:
    async def generate_content(self, **kwargs):
        return _FakeResponse()


class _FakeAio:
    models = _FakeModels()


class _FakeGenaiClient:
    aio = _FakeAio()


class _Schema(BaseModel):
    value: str


async def test_gemini_client_records_usage_from_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    client = GeminiLLMClient()
    client._client = _FakeGenaiClient()  # swap real SDK client for fake

    result = await client.complete_structured("sys", "prompt", _Schema)
    assert result.value == "hello"

    summary = client.usage.summary()
    assert summary.total_calls == 1
    assert summary.prompt_tokens == 120
    # completion = candidates (60) + thoughts (15)
    assert summary.completion_tokens == 75
    assert summary.by_step[0].label == "_Schema"
    assert summary.estimated_cost_usd > 0
    assert summary.model == "gemini-2.5-flash"


# --- GroqLLMClient usage extraction (mocked, no network) -----------------


class _FakeGroqUsage:
    prompt_tokens = 200
    completion_tokens = 90


class _FakeGroqMessage:
    content = '{"value": "hi"}'


class _FakeGroqChoice:
    message = _FakeGroqMessage()


class _FakeGroqResponse:
    choices = [_FakeGroqChoice()]
    usage = _FakeGroqUsage()


class _FakeCompletions:
    async def create(self, **kwargs):
        return _FakeGroqResponse()


class _FakeChat:
    completions = _FakeCompletions()


class _FakeGroqClient:
    chat = _FakeChat()


async def test_groq_client_records_usage_from_response(monkeypatch):
    from app.core.llm import GroqLLMClient

    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    client = GroqLLMClient()
    client._client = _FakeGroqClient()  # swap real SDK client for fake

    result = await client.complete_structured("sys", "prompt", _Schema)
    assert result.value == "hi"

    summary = client.usage.summary()
    assert summary.total_calls == 1
    assert summary.prompt_tokens == 200
    assert summary.completion_tokens == 90
    assert summary.model == "llama-3.3-70b-versatile"
    assert summary.estimated_cost_usd > 0

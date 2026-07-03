import pytest

from app.core.llm import GeminiLLMClient, get_llm_client


def test_get_llm_client_raises_when_no_key_set(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="No LLM API key found"):
        get_llm_client()


def test_get_llm_client_returns_gemini_client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    client = get_llm_client()
    assert isinstance(client, GeminiLLMClient)

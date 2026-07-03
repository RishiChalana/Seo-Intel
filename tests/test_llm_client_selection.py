import pytest

from app.core.llm import GeminiLLMClient, GroqLLMClient, get_llm_client


@pytest.fixture(autouse=True)
def clear_llm_env(monkeypatch):
    """Start each test from a clean LLM env so ambient keys don't leak in."""
    for var in ("GROQ_API_KEY", "GEMINI_API_KEY", "LLM_BACKEND"):
        monkeypatch.delenv(var, raising=False)


def test_raises_when_no_key_set():
    with pytest.raises(RuntimeError, match="No LLM API key found"):
        get_llm_client()


def test_auto_prefers_groq_when_both_keys_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    assert isinstance(get_llm_client(), GroqLLMClient)


def test_auto_uses_gemini_when_only_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    assert isinstance(get_llm_client(), GeminiLLMClient)


def test_auto_uses_groq_when_only_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq")
    assert isinstance(get_llm_client(), GroqLLMClient)


def test_backend_override_forces_gemini(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    monkeypatch.setenv("LLM_BACKEND", "gemini")
    assert isinstance(get_llm_client(), GeminiLLMClient)


def test_backend_override_forces_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    monkeypatch.setenv("LLM_BACKEND", "groq")
    assert isinstance(get_llm_client(), GroqLLMClient)

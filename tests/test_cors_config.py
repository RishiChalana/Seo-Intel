import importlib

import pytest


def _load_allow_origins(monkeypatch, value):
    """Reimport app.main with ALLOWED_ORIGINS set to `value` and return the
    resolved allow_origins list."""
    if value is None:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("ALLOWED_ORIGINS", value)
    import app.main as main

    importlib.reload(main)
    return main.allow_origins


@pytest.mark.parametrize(
    "value",
    [None, "*", "", "   ", ",", " , "],
    ids=["unset", "star", "empty", "whitespace", "comma-only", "commas-spaces"],
)
def test_blank_or_star_origins_default_to_open(monkeypatch, value):
    # A blank/unset value must fall back to open ["*"], never an empty list
    # (which would reject every cross-origin request).
    assert _load_allow_origins(monkeypatch, value) == ["*"]


def test_single_origin_is_restricted(monkeypatch):
    origins = _load_allow_origins(
        monkeypatch, "https://seo-intel-murex.vercel.app"
    )
    assert origins == ["https://seo-intel-murex.vercel.app"]


def test_multiple_origins_parsed_and_trimmed(monkeypatch):
    origins = _load_allow_origins(
        monkeypatch, "https://a.vercel.app, https://b.com ,https://c.dev"
    )
    assert origins == [
        "https://a.vercel.app",
        "https://b.com",
        "https://c.dev",
    ]


def test_star_among_others_wins(monkeypatch):
    # If "*" appears anywhere, the API is effectively open.
    assert _load_allow_origins(monkeypatch, "https://a.com,*") == ["*"]

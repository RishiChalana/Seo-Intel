import concurrent.futures

from tenacity import RetryError

from app.main import friendly_error


def _retry_error_wrapping(exc: Exception) -> RetryError:
    """Build a real tenacity RetryError whose last attempt raised `exc`."""
    fut: concurrent.futures.Future = concurrent.futures.Future()
    fut.set_exception(exc)
    return RetryError(fut)  # type: ignore[arg-type]


def test_gemini_quota_error_maps_to_429():
    err = _retry_error_wrapping(
        RuntimeError("429 RESOURCE_EXHAUSTED. You exceeded your current quota")
    )
    status, detail = friendly_error(err)
    assert status == 429
    assert "quota" in detail.lower()
    assert "RetryError" not in detail  # unwrapped, not the raw wrapper string


def test_missing_key_maps_to_503():
    status, detail = friendly_error(
        RuntimeError("No LLM API key found. Set GEMINI_API_KEY ...")
    )
    assert status == 503
    assert "GEMINI_API_KEY" in detail


def test_missing_serpapi_key_maps_to_503():
    status, detail = friendly_error(RuntimeError("SERPAPI_KEY not set."))
    assert status == 503


def test_generic_error_maps_to_500():
    status, detail = friendly_error(ValueError("something odd happened"))
    assert status == 500
    assert "something odd happened" in detail
    assert "ValueError" in detail  # type name is included for identifiability


def test_empty_message_error_falls_back_to_type_name():
    # MemoryError has an empty str(); the detail must still identify it.
    status, detail = friendly_error(RuntimeError())
    assert status == 500
    assert "RuntimeError" in detail


def test_memory_error_maps_to_503_with_helpful_message():
    status, detail = friendly_error(MemoryError())
    assert status == 503
    assert "memory" in detail.lower()


def test_retry_error_generic_cause_still_unwrapped():
    err = _retry_error_wrapping(ValueError("boom in a node"))
    status, detail = friendly_error(err)
    assert status == 500
    assert "boom in a node" in detail
    assert "RetryError" not in detail

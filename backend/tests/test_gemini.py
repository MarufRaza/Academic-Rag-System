import pytest
from app.core.config import settings
from app.core.exceptions import (
    GeminiRateLimitException,
    MissingAPIKeyException,
    ProviderException,
)
from app.rag.generator import get_llm, translate_llm_exception


def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)

    with pytest.raises(MissingAPIKeyException) as exc_info:
        get_llm()
    assert exc_info.value.status_code == 401
    assert "Missing Google Gemini API key" in exc_info.value.detail


def test_gemini_whitespace_api_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "   ")

    with pytest.raises(MissingAPIKeyException) as exc_info:
        get_llm()
    assert exc_info.value.status_code == 401
    assert "Missing Google Gemini API key" in exc_info.value.detail


def test_gemini_get_llm_success(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "dummy-key-for-instantiation")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

    llm = get_llm()
    assert llm is not None
    assert getattr(llm, "model", None) == "gemini-2.5-flash"


def test_translate_gemini_rate_limit(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")

    e = Exception("429 Resource has been exhausted (e.g. check quota).")
    translated = translate_llm_exception(e)
    assert isinstance(translated, GeminiRateLimitException)
    assert translated.status_code == 429
    assert translated.detail == "Gemini free-tier rate limit reached. Please wait a minute and try again."


def test_translate_gemini_invalid_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")

    e = Exception("API key not valid. Please pass a valid API key. [API_KEY_INVALID]")
    translated = translate_llm_exception(e)
    assert isinstance(translated, MissingAPIKeyException)
    assert translated.status_code == 401
    assert "Invalid Google Gemini API key" in translated.detail


def test_translate_gemini_generic_error(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "super-secret-key-1234")

    e = Exception("An internal error occurred with key super-secret-key-1234 on server")
    translated = translate_llm_exception(e)
    assert isinstance(translated, ProviderException)
    assert "super-secret-key-1234" not in translated.detail
    assert "[REDACTED]" in translated.detail


def test_health_endpoint_reports_gemini(client, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-secret-never-exposed")

    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["llm_provider"] == "gemini"
    assert data["llm_model"] == "gemini-2.5-flash"
    assert "test-secret-never-exposed" not in str(data)

import pytest
from types import SimpleNamespace
from google import genai
from app.core.config import settings
from app.core.exceptions import (
    GeminiRateLimitException,
    MissingAPIKeyException,
    ProviderException,
)
from app.rag.generator import (
    check_gemini_model_availability,
    get_llm,
    translate_llm_exception,
)


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
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")

    llm = get_llm()
    assert llm is not None
    assert getattr(llm, "model", None) == "gemini-3.8-flash"


def test_gemini_404_does_not_retry_with_another_model(monkeypatch):
    class NotFoundLLM:
        model = "gemini-3.8-flash"

        def invoke(self, prompt_text):
            raise RuntimeError("404 model not found")

    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-key")

    with pytest.raises(ProviderException):
        from app.rag.generator import invoke_llm_safely

        invoke_llm_safely(NotFoundLLM(), "test prompt")


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
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-secret-never-exposed")

    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["llm_provider"] == "gemini"
    assert data["llm_model"] == "gemini-3.8-flash"
    assert "test-secret-never-exposed" not in str(data)


def test_gemini_model_availability_warns_with_closest_model(monkeypatch, caplog):
    class FakeModels:
        def list(self, config):
            assert config == {"query_base": True}
            return [
                SimpleNamespace(
                    name="models/gemini-3.8-flash",
                    supported_actions=["generateContent"],
                )
            ]

    class FakeClient:
        def __init__(self, api_key, http_options):
            assert api_key == "test-key"
            assert http_options == {"timeout": 10000}
            self.models = FakeModels()

    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.7-flash")
    monkeypatch.setattr(genai, "Client", FakeClient)

    check_gemini_model_availability()

    assert "is not in the available model list" in caplog.text
    assert "gemini-3.8-flash" in caplog.text

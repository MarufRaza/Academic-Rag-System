from typing import Optional
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.config import settings
from app.core.exceptions import (
    AcademicRAGException,
    MissingAPIKeyException,
    ProviderException,
    OllamaNotRunningException,
    GeminiRateLimitException,
)
from app.core.logging import logger


def _redact_secrets(message: str) -> str:
    redacted = message
    for secret in (settings.GOOGLE_API_KEY, settings.OPENAI_API_KEY):
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def _readable_error_message(exc: Exception) -> str:
    raw = getattr(exc, "message", None) or str(exc)
    raw = _redact_secrets(str(raw).strip())
    first_line = raw.splitlines()[0] if raw else "Unknown provider error."
    return first_line


def translate_llm_exception(exc: Exception) -> AcademicRAGException:
    """Map provider SDK errors to the project's HTTP exceptions (never leak stack traces)."""
    if isinstance(exc, AcademicRAGException):
        return exc

    # Inspect full error text across exc and any chained cause
    full_parts = [str(exc)]
    if getattr(exc, "message", None):
        full_parts.append(str(exc.message))
    if getattr(exc, "__cause__", None):
        full_parts.append(str(exc.__cause__))
    full_text = _redact_secrets(" ".join(full_parts)).lower()

    error_msg = _readable_error_message(exc)
    status_code = (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
        or getattr(getattr(exc, "__cause__", None), "status_code", None)
        or getattr(getattr(exc, "__cause__", None), "code", None)
    )
    provider = (settings.LLM_PROVIDER or "").lower()

    if provider == "gemini":
        if (
            status_code == 429
            or "429" in full_text
            or "resource_exhausted" in full_text
            or "resource exhausted" in full_text
            or "quota" in full_text
            or "rate limit" in full_text
            or "ratelimit" in full_text
        ):
            return GeminiRateLimitException()
        if (
            status_code in (401, 403)
            or "api_key_invalid" in full_text
            or "api key not valid" in full_text
            or "invalid api key" in full_text
            or ("invalid argument" in full_text and "api key" in full_text)
            or "unauthenticated" in full_text
            or ("permission_denied" in full_text and "api key" in full_text)
        ):
            return MissingAPIKeyException("Google Gemini (Invalid API Key)")
        return ProviderException("Gemini", error_msg)

    if "api_key" in full_text or "authentication" in full_text or "incorrect api key" in full_text:
        return MissingAPIKeyException("OpenAI (Invalid or expired API Key)")
    if "connection refused" in full_text or "connecterror" in full_text:
        return OllamaNotRunningException(settings.OLLAMA_BASE_URL)
    return ProviderException(settings.LLM_PROVIDER, error_msg)


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.1,
) -> BaseChatModel:
    """
    Factory function returning the configured BaseChatModel instance.
    Supports 'openai', 'gemini', and 'ollama'.
    """
    provider = (provider or settings.LLM_PROVIDER).lower()

    if provider == "openai":
        if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
            raise MissingAPIKeyException("OpenAI")

        model = model_name or settings.OPENAI_MODEL
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature,
            )
        except Exception as e:
            logger.error(f"Failed to instantiate ChatOpenAI: {e}")
            raise ProviderException("OpenAI", str(e))

    elif provider == "gemini":
        if not settings.GOOGLE_API_KEY or not settings.GOOGLE_API_KEY.strip():
            raise MissingAPIKeyException("Google Gemini")

        model = model_name or settings.GEMINI_MODEL
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.2 if temperature is None else temperature,
            )
        except AcademicRAGException:
            raise
        except Exception as e:
            logger.error(f"Failed to instantiate ChatGoogleGenerativeAI: {_redact_secrets(str(e))}")
            raise translate_llm_exception(e)

    elif provider == "ollama":
        model = model_name or settings.OLLAMA_MODEL
        base_url = settings.OLLAMA_BASE_URL

        # Check if Ollama is reachable
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{base_url}/api/version")
                if res.status_code != 200:
                    logger.warning(f"Ollama health check returned status {res.status_code}")
        except Exception as e:
            logger.error(f"Ollama connection check failed for {base_url}: {e}")
            raise OllamaNotRunningException(base_url)

        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                base_url=base_url,
                temperature=temperature,
            )
        except Exception as e:
            logger.error(f"Failed to instantiate ChatOllama: {e}")
            raise ProviderException("Ollama", str(e))

    else:
        raise ProviderException(
            "LLM Factory",
            f"Unsupported LLM_PROVIDER '{provider}'. Allowed values are 'openai', 'gemini', or 'ollama'."
        )


def invoke_llm_safely(llm: BaseChatModel, prompt_text: str) -> str:
    """
    Invokes the LLM and translates network/API exceptions into clear custom exceptions.
    """
    try:
        response = llm.invoke(prompt_text)
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
    except httpx.ConnectError:
        if settings.LLM_PROVIDER.lower() == "ollama":
            raise OllamaNotRunningException(settings.OLLAMA_BASE_URL)
        raise ProviderException(settings.LLM_PROVIDER, "Failed to connect to the LLM server.")
    except AcademicRAGException:
        raise
    except Exception as e:
        error_msg = _redact_secrets(str(e))
        logger.error(f"LLM invocation failed: {error_msg}")
        raise translate_llm_exception(e)

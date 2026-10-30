from typing import Any, Optional
from difflib import get_close_matches
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


def check_gemini_model_availability() -> None:
    """Log whether the configured Gemini model is available to this API key."""
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_API_KEY.strip():
        logger.warning(
            "Gemini model availability check skipped: GOOGLE_API_KEY is not configured."
        )
        return

    try:
        from google import genai

        client = genai.Client(
            api_key=settings.GOOGLE_API_KEY,
            http_options={"timeout": 10000},
        )
        available_models = []
        for model in client.models.list(config={"query_base": True}):
            name = getattr(model, "name", "") or ""
            model_name = name.rsplit("/", 1)[-1]
            supported_actions = getattr(model, "supported_actions", None)
            if (
                model_name
                and (
                    not supported_actions
                    or "generateContent" in supported_actions
                )
            ):
                available_models.append(model_name)

        configured_model = settings.GEMINI_MODEL.rsplit("/", 1)[-1]
        if configured_model in available_models:
            logger.info(
                f"Configured Gemini model '{configured_model}' is available."
            )
            return

        closest_model = get_close_matches(
            configured_model,
            available_models,
            n=1,
            cutoff=0.35,
        )
        suggestion = (
            f" Closest available model: '{closest_model[0]}'."
            if closest_model
            else " No similar text-generation model was returned."
        )
        logger.warning(
            f"Configured Gemini model '{configured_model}' is not in the "
            f"available model list.{suggestion}"
        )
    except Exception as e:
        logger.warning(
            "Gemini model availability check failed for configured model "
            f"'{settings.GEMINI_MODEL}': {_redact_secrets(str(e))}"
        )


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


def extract_text_content(content: Any) -> str:
    """
    Normalizes LLM response content into plain text:
    - str -> as is
    - list -> join the 'text' of blocks with type 'text' (and plain str items)
    - None -> ""
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    parts.append(str(item["text"]))
                elif "text" in item and item.get("type") != "thinking":
                    parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts)
    return str(content)


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
            kwargs = {
                "model": model,
                "google_api_key": settings.GOOGLE_API_KEY,
                "temperature": 0.2 if temperature is None else temperature,
                "max_output_tokens": 2048,
            }
            try:
                return ChatGoogleGenerativeAI(**kwargs, thinking_budget=0)
            except (TypeError, ValueError):
                return ChatGoogleGenerativeAI(**kwargs)
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
    Normalizes response content to plain text.
    """
    try:
        response = llm.invoke(prompt_text)

        content = getattr(response, "content", response)
        text = extract_text_content(content)

        if not text.strip():
            resp_metadata = getattr(response, "response_metadata", {})
            finish_reason = resp_metadata.get("finish_reason") or resp_metadata.get("finishReason") or "unknown"
            usage_metadata = getattr(response, "usage_metadata", {})
            logger.error(
                f"LLM returned empty response. finish_reason: {finish_reason}, usage_metadata: {usage_metadata}"
            )
            raise ProviderException(
                settings.LLM_PROVIDER,
                "The model returned an empty response. Please try again."
            )

        model_name = (
            getattr(llm, "model", None)
            or getattr(llm, "model_name", None)
            or "provider default"
        )
        logger.info(
            f"LLM response generated using provider='{settings.LLM_PROVIDER}' model='{model_name}'."
        )
        return text
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
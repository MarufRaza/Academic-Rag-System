from typing import Optional
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.config import settings
from app.core.exceptions import (
    MissingAPIKeyException,
    ProviderException,
    OllamaNotRunningException,
)
from app.core.logging import logger


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.1,
) -> BaseChatModel:
    """
    Factory function returning the configured BaseChatModel instance.
    Supports 'openai' and 'ollama'.
    """
    provider = (provider or settings.LLM_PROVIDER).lower()

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
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
            f"Unsupported LLM_PROVIDER '{provider}'. Allowed values are 'openai' or 'ollama'."
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
    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM invocation failed: {error_msg}")
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "incorrect api key" in error_msg.lower():
            raise MissingAPIKeyException("OpenAI (Invalid or expired API Key)")
        if "connection refused" in error_msg.lower() or "connecterror" in error_msg.lower():
            raise OllamaNotRunningException(settings.OLLAMA_BASE_URL)
        raise ProviderException(settings.LLM_PROVIDER, error_msg)

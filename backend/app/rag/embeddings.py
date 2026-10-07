import threading
from typing import Optional
from langchain_core.embeddings import Embeddings
from app.core.config import settings
from app.core.exceptions import MissingAPIKeyException, ProviderException
from app.core.logging import logger

_embedding_instance: Optional[Embeddings] = None
_embedding_lock = threading.Lock()
_current_provider_config = ""


def get_embedding_function(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    force_reload: bool = False
) -> Embeddings:
    """
    Singleton factory returning the configured Embeddings instance.
    Loads once on startup and caches in memory.
    Supports 'huggingface' (local CPU lightweight) and 'openai'.
    """
    global _embedding_instance, _current_provider_config

    provider = (provider or settings.EMBEDDING_PROVIDER).lower()
    config_key = f"{provider}:{model_name or ''}"

    if _embedding_instance is not None and not force_reload and _current_provider_config == config_key:
        return _embedding_instance

    with _embedding_lock:
        if _embedding_instance is not None and not force_reload and _current_provider_config == config_key:
            return _embedding_instance

        logger.info(f"Initializing embedding provider: '{provider}'...")

        if provider == "huggingface":
            hf_model = model_name or settings.HF_EMBEDDING_MODEL
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                # Load lightweight model on CPU
                embeddings = HuggingFaceEmbeddings(
                    model_name=hf_model,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
                logger.info(f"Loaded HuggingFace embedding model: {hf_model} (CPU)")
            except Exception as e:
                logger.error(f"Failed to load HuggingFace embeddings: {e}")
                raise ProviderException("HuggingFace Embeddings", str(e))

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise MissingAPIKeyException("OpenAI Embeddings")
            openai_model = model_name or settings.OPENAI_EMBEDDING_MODEL
            try:
                from langchain_openai import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings(
                    model=openai_model,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                logger.info(f"Loaded OpenAI embedding model: {openai_model}")
            except Exception as e:
                logger.error(f"Failed to load OpenAI embeddings: {e}")
                raise ProviderException("OpenAI Embeddings", str(e))

        else:
            raise ProviderException(
                "Embedding Factory",
                f"Unsupported EMBEDDING_PROVIDER '{provider}'. Choose 'huggingface' or 'openai'."
            )

        _embedding_instance = embeddings
        _current_provider_config = config_key
        return _embedding_instance


def get_active_embedding_info() -> dict:
    """Returns active embedding provider and model identifier."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    model = (
        settings.HF_EMBEDDING_MODEL
        if provider == "huggingface"
        else settings.OPENAI_EMBEDDING_MODEL
    )
    return {
        "provider": provider,
        "model": model,
        "signature": f"{provider}::{model}"
    }

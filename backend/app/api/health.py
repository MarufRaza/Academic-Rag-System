from fastapi import APIRouter
from app.core.config import settings
from app.models.health import HealthResponse
from app.rag.embeddings import get_active_embedding_info
from app.rag.vectorstore import get_total_chunks_count
from app.utils.manifest import list_all_documents

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="System health and status")
async def health_check():
    """Returns active providers, document count, and vector store stats."""
    emb_info = get_active_embedding_info()
    docs = list_all_documents()
    chunks_count = get_total_chunks_count()

    llm_model = (
        settings.OPENAI_MODEL
        if settings.LLM_PROVIDER.lower() == "openai"
        else settings.OLLAMA_MODEL
    )

    return HealthResponse(
        status="ok",
        llm_provider=settings.LLM_PROVIDER,
        llm_model=llm_model,
        embedding_provider=emb_info["provider"],
        embedding_model=emb_info["model"],
        document_count=len(docs),
        total_chunks=chunks_count,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        chroma_status="connected",
        message="Academic RAG System is operational."
    )

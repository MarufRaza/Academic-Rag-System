import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.exceptions import AcademicRAGException
from app.core.logging import logger
from app.rag.embeddings import get_embedding_function
from app.rag.generator import check_gemini_model_availability
from app.rag.vectorstore import get_or_create_vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: warms up directories and vector database on startup."""
    logger.info("Initializing Academic Question Answering System Using RAG...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

    # Preload embedding model (singleton) so first user query is fast
    try:
        logger.info(f"Preloading embedding model ({settings.EMBEDDING_PROVIDER})...")
        get_embedding_function()
        logger.info("Embedding model loaded successfully.")
    except Exception as e:
        logger.warning(f"Embedding model preload notice: {e}")

    # Initialize / verify vectorstore
    try:
        get_or_create_vectorstore()
        logger.info("ChromaDB vectorstore connection verified.")
    except Exception as e:
        logger.warning(f"Vectorstore initialization notice: {e}")

    if settings.LLM_PROVIDER.lower() == "gemini":
        await run_in_threadpool(check_gemini_model_availability)

    yield

    logger.info("Shutting down Academic RAG System.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A production-quality Academic Question Answering System using Retrieval-Augmented Generation (RAG).",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for structured RAG errors
@app.exception_handler(AcademicRAGException)
async def academic_rag_exception_handler(request: Request, exc: AcademicRAGException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": f"An unexpected error occurred: {str(exc)}",
            "status_code": 500,
        },
    )


# Include API routes
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_STR,
    }

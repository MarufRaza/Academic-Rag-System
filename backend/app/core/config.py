import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Academic Question Answering System Using RAG"
    API_V1_STR: str = "/api"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # "openai" or "ollama"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Embedding Provider Configuration
    EMBEDDING_PROVIDER: str = "huggingface"  # "huggingface" or "openai"
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Storage Paths (relative to backend directory or absolute)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    CHROMA_PERSIST_DIR: str = os.path.join(BASE_DIR, "chroma_db")
    CHROMA_COLLECTION_NAME: str = "academic_rag_docs"
    MANIFEST_FILE: str = os.path.join(BASE_DIR, "uploads", "documents_manifest.json")

    # RAG Tuning Parameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 4
    # Score threshold for cosine similarity (relevance score between 0 and 1)
    # If chunks score below this, they are considered irrelevant
    SCORE_THRESHOLD: float = 0.30

    # Upload Constraints
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

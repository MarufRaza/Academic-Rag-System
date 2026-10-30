import os
from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Academic Question Answering System Using RAG"
    API_V1_STR: str = "/api"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "gemini"  # "openai", "gemini", or "ollama"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"

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
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]

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

    @model_validator(mode="after")
    def resolve_api_keys(self):
        # Fallback if Google API key was entered under OPENAI_API_KEY in .env
        if not self.GOOGLE_API_KEY or not self.GOOGLE_API_KEY.strip():
            if self.OPENAI_API_KEY and not self.OPENAI_API_KEY.strip().startswith("sk-"):
                self.GOOGLE_API_KEY = self.OPENAI_API_KEY.strip()
        return self


settings = Settings()
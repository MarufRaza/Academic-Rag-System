from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall health status")
    llm_provider: str = Field(..., description="Active LLM provider (openai/gemini/ollama)")
    llm_model: str = Field(..., description="Active LLM model name")
    embedding_provider: str = Field(..., description="Active embedding provider (huggingface/openai)")
    embedding_model: str = Field(..., description="Active embedding model name")
    document_count: int = Field(..., description="Number of ingested documents")
    total_chunks: int = Field(..., description="Total vector chunks stored in ChromaDB")
    collection_name: str = Field(..., description="ChromaDB collection name")
    chroma_status: str = Field(default="connected", description="ChromaDB connection status")
    message: Optional[str] = Field(default=None)

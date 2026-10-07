from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str = Field(..., description="Unique UUID for the uploaded document")
    filename: str = Field(..., description="Original name of the uploaded PDF")
    file_path: str = Field(..., description="Relative or absolute path on disk")
    file_hash: str = Field(..., description="SHA-256 hash of the file contents")
    file_size_bytes: int = Field(..., description="Size in bytes")
    file_size_formatted: str = Field(..., description="Human-readable size e.g. 1.25 MB")
    page_count: int = Field(..., description="Total number of pages extracted")
    chunk_count: int = Field(..., description="Total number of chunks embedded in ChromaDB")
    upload_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = Field(default="ready", description="Status: ready, processing, or error")


class DocumentUploadItemResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    status: str
    message: str


class DocumentUploadResponse(BaseModel):
    success: bool
    uploaded: List[DocumentUploadItemResponse]
    errors: List[str] = []


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[DocumentMetadata]


class DocumentDeleteResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    deleted_chunks: int
    message: str

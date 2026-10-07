from typing import List
from fastapi import APIRouter, File, UploadFile, status

from app.models.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index one or more academic PDF documents",
)
async def upload_documents(
    files: List[UploadFile] = File(..., description="PDF files to be processed and indexed")
):
    """
    Accepts multiple PDF uploads, validates file constraints, extracts text,
    splits into chunks, creates vector embeddings, and registers them in ChromaDB.
    """
    return await DocumentService.process_multiple_uploads(files)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all ingested academic documents",
)
async def get_documents():
    """Returns the list of all ingested documents along with page and chunk counts."""
    return DocumentService.get_documents_list()


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document and purge its vectors from ChromaDB",
)
async def delete_document(document_id: str):
    """Deletes the PDF from disk and permanently deletes all related vector embeddings."""
    return DocumentService.delete_document(document_id)

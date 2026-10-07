import os
import uuid
from typing import List
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    DuplicateDocumentException,
    InvalidPDFException,
    VectorStoreException,
)
from app.core.logging import logger
from app.models.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadItemResponse,
    DocumentUploadResponse,
)
from app.rag.loader import load_and_preprocess_pdf
from app.rag.splitter import split_documents
from app.rag.vectorstore import (
    add_documents_to_vectorstore,
    delete_documents_by_id,
    get_total_chunks_count,
)
from app.utils.file_utils import (
    compute_file_hash,
    format_file_size,
    sanitize_filename,
    validate_pdf,
)
from app.utils.manifest import (
    add_document_to_manifest,
    find_document_by_hash,
    get_document_by_id,
    list_all_documents,
    remove_document_from_manifest,
)


class DocumentService:
    @staticmethod
    async def process_and_index_upload(file: UploadFile) -> DocumentUploadItemResponse:
        """Processes a single uploaded PDF file and indexes its chunks."""
        filename = sanitize_filename(file.filename or "uploaded.pdf")
        logger.info(f"Starting processing for file: {filename}")

        # Read content bytes
        content_bytes = await file.read()

        # Step 1: Validate PDF constraints (magic bytes, size, extension)
        validate_pdf(filename, content_bytes, settings.MAX_FILE_SIZE_MB)

        # Step 2: Content Hash & Duplicate Detection
        file_hash = compute_file_hash(content_bytes)
        existing_doc = find_document_by_hash(file_hash)
        if existing_doc:
            raise DuplicateDocumentException(filename, existing_doc.filename)

        # Step 3: Save to uploads directory
        doc_id = str(uuid.uuid4())
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        unique_disk_name = f"{doc_id}_{filename}"
        disk_path = os.path.join(settings.UPLOAD_DIR, unique_disk_name)

        with open(disk_path, "wb") as f:
            f.write(content_bytes)

        try:
            # Step 4: Load & clean text from PDF
            page_docs = load_and_preprocess_pdf(disk_path, filename)
            page_count = len(page_docs)

            # Step 5: Split text into chunks
            split_chunks = split_documents(
                documents=page_docs,
                document_id=doc_id,
                filename=filename,
                file_hash=file_hash,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            # Step 6: Embed & store in persistent ChromaDB
            chunk_count = add_documents_to_vectorstore(split_chunks)

            # Step 7: Record in persistent manifest
            meta = DocumentMetadata(
                document_id=doc_id,
                filename=filename,
                file_path=disk_path,
                file_hash=file_hash,
                file_size_bytes=len(content_bytes),
                file_size_formatted=format_file_size(len(content_bytes)),
                page_count=page_count,
                chunk_count=chunk_count,
                status="ready"
            )
            add_document_to_manifest(meta)

            return DocumentUploadItemResponse(
                document_id=doc_id,
                filename=filename,
                page_count=page_count,
                chunk_count=chunk_count,
                status="ready",
                message=f"Successfully processed {page_count} pages and indexed {chunk_count} chunks."
            )

        except Exception as e:
            # Clean up saved file if processing failed
            if os.path.exists(disk_path):
                try:
                    os.remove(disk_path)
                except Exception:
                    pass
            # Clean up any partial vectors
            try:
                delete_documents_by_id(doc_id)
            except Exception:
                pass
            raise e

    @classmethod
    async def process_multiple_uploads(cls, files: List[UploadFile]) -> DocumentUploadResponse:
        """Processes multiple uploaded PDF files in a batch."""
        uploaded: List[DocumentUploadItemResponse] = []
        errors: List[str] = []

        if not files:
            raise InvalidPDFException("None", "No files provided in request.")

        for file in files:
            try:
                res = await cls.process_and_index_upload(file)
                uploaded.append(res)
            except Exception as e:
                detail = getattr(e, "detail", str(e))
                errors.append(f"{file.filename}: {detail}")

        success = len(uploaded) > 0
        return DocumentUploadResponse(
            success=success,
            uploaded=uploaded,
            errors=errors
        )

    @staticmethod
    def get_documents_list() -> DocumentListResponse:
        """Returns the list of all indexed documents and total chunk count."""
        docs = list_all_documents()
        total_chunks = get_total_chunks_count()
        return DocumentListResponse(
            total_documents=len(docs),
            total_chunks=total_chunks,
            documents=docs
        )

    @staticmethod
    def delete_document(document_id: str) -> DocumentDeleteResponse:
        """Removes a document from the manifest, deletes its vector chunks, and removes its file."""
        doc_meta = get_document_by_id(document_id)
        if not doc_meta:
            raise InvalidPDFException(document_id, f"Document with ID '{document_id}' not found.")

        # Delete vectors from ChromaDB
        deleted_count = delete_documents_by_id(document_id)

        # Delete file on disk
        if os.path.exists(doc_meta.file_path):
            try:
                os.remove(doc_meta.file_path)
                logger.info(f"Deleted file from disk: {doc_meta.file_path}")
            except Exception as e:
                logger.warning(f"Could not delete physical file {doc_meta.file_path}: {e}")

        # Remove from manifest
        remove_document_from_manifest(document_id)

        return DocumentDeleteResponse(
            success=True,
            document_id=document_id,
            filename=doc_meta.filename,
            deleted_chunks=deleted_count,
            message=f"Document '{doc_meta.filename}' and {deleted_count} vectors successfully deleted."
        )

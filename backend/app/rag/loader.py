import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from app.rag.cleaner import clean_academic_text
from app.core.exceptions import InvalidPDFException, EmptyPDFException, ScannedPDFException
from app.core.logging import logger


def load_and_preprocess_pdf(file_path: str, filename: str) -> List[Document]:
    """
    Loads a PDF using PyPDFLoader, cleans text page-by-page,
    ensures page indexing is 1-based, and validates extractable content.
    """
    if not os.path.exists(file_path):
        raise InvalidPDFException(filename, "File not found on disk")

    try:
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
    except Exception as e:
        logger.error(f"PyPDFLoader failed to parse {filename}: {e}")
        raise InvalidPDFException(filename, f"Failed to parse PDF content: {str(e)}")

    if not raw_docs:
        raise EmptyPDFException(filename)

    processed_docs: List[Document] = []
    total_text_length = 0

    for idx, doc in enumerate(raw_docs):
        cleaned_text = clean_academic_text(doc.page_content)
        total_text_length += len(cleaned_text.strip())

        # PyPDFLoader provides 0-indexed page in metadata
        raw_page = doc.metadata.get("page", idx)
        try:
            page_num = int(raw_page) + 1
        except (ValueError, TypeError):
            page_num = idx + 1

        doc_metadata = {
            "source": filename,
            "filename": filename,
            "page": page_num,
        }

        # Keep non-empty pages
        if cleaned_text.strip():
            processed_docs.append(Document(
                page_content=cleaned_text,
                metadata=doc_metadata
            ))

    # Check if document has practically zero extractable text (e.g. scanned images)
    if total_text_length < 20 or not processed_docs:
        raise ScannedPDFException(filename)

    logger.info(f"Loaded {len(raw_docs)} pages from {filename} ({len(processed_docs)} pages with text, {total_text_length} chars)")
    return processed_docs


def load_and_preprocess_docx(file_path: str, filename: str) -> List[Document]:
    """Loads and cleans DOCX text while retaining the uploaded filename as its source."""
    if not os.path.exists(file_path):
        raise InvalidPDFException(filename, "File not found on disk")

    try:
        from langchain_community.document_loaders import Docx2txtLoader

        raw_docs = Docx2txtLoader(file_path).load()
    except Exception as e:
        logger.error(f"Docx2txtLoader failed to parse {filename}: {e}")
        raise InvalidPDFException(filename, f"Failed to parse DOCX content: {str(e)}") from e

    if not raw_docs:
        raise EmptyPDFException(filename)

    processed_docs: List[Document] = []
    for doc in raw_docs:
        cleaned_text = clean_academic_text(doc.page_content)
        if cleaned_text.strip():
            processed_docs.append(Document(
                page_content=cleaned_text,
                metadata={
                    **doc.metadata,
                    "source": filename,
                    "filename": filename,
                    "page": 1,
                },
            ))

    if not processed_docs:
        raise ScannedPDFException(filename)

    logger.info(f"Loaded {len(processed_docs)} text section(s) from {filename}")
    return processed_docs


def load_and_preprocess_document(file_path: str, filename: str) -> List[Document]:
    """Loads a supported document and normalizes its metadata for downstream chunking."""
    extension = os.path.splitext(filename)[1].lower()
    if extension == ".pdf":
        return load_and_preprocess_pdf(file_path, filename)
    if extension == ".docx":
        return load_and_preprocess_docx(file_path, filename)
    raise InvalidPDFException(filename, "Only .pdf and .docx documents are supported")

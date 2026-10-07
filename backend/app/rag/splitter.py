from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging import logger


def split_documents(
    documents: List[Document],
    document_id: str,
    filename: str,
    file_hash: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> List[Document]:
    """
    Splits page-level documents into smaller, semantically coherent chunks
    suitable for dense vector retrieval.
    Injects document_id, filename, page, and chunk_index metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        length_function=len,
    )

    split_chunks: List[Document] = []
    chunk_counter = 0

    for doc in documents:
        page_chunks = text_splitter.split_text(doc.page_content)
        page_num = doc.metadata.get("page", 1)

        for text_chunk in page_chunks:
            stripped = text_chunk.strip()
            if not stripped:
                continue

            metadata = {
                "document_id": str(document_id),
                "filename": str(filename),
                "page": int(page_num),
                "chunk_index": int(chunk_counter),
                "file_hash": str(file_hash),
            }

            split_chunks.append(Document(
                page_content=stripped,
                metadata=metadata
            ))
            chunk_counter += 1

    logger.info(f"Split {len(documents)} pages from '{filename}' into {len(split_chunks)} chunks.")
    return split_chunks

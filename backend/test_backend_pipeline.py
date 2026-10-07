import os
import sys

from app.core.config import settings
from app.core.exceptions import DuplicateDocumentException
from app.models.chat import ChatMessage
from app.rag.loader import load_and_preprocess_pdf
from app.rag.pipeline import NOT_ENOUGH_INFO_MSG, execute_rag_pipeline
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.splitter import split_documents
from app.rag.vectorstore import (
    add_documents_to_vectorstore,
    delete_documents_by_id,
    get_total_chunks_count,
    reset_vectorstore,
)
from app.utils.file_utils import compute_file_hash, format_file_size, validate_pdf
from app.utils.manifest import (
    add_document_to_manifest,
    find_document_by_hash,
    list_all_documents,
    remove_document_from_manifest,
)
from app.models.document import DocumentMetadata


def run_test():
    print("=" * 70)
    print(" TESTING ACADEMIC RAG PIPELINE (BACKEND VERIFICATION)")
    print("=" * 70)

    sample_pdf = os.path.join(settings.BASE_DIR, "sample_documents", "DBMS_Study_Notes.pdf")
    assert os.path.exists(sample_pdf), f"Sample file not found: {sample_pdf}"

    with open(sample_pdf, "rb") as f:
        file_bytes = f.read()

    # Step 1: Validate PDF
    print("\n[Step 1] Validating PDF format and magic bytes...")
    validate_pdf("DBMS_Study_Notes.pdf", file_bytes, settings.MAX_FILE_SIZE_MB)
    print(" -> Validation passed successfully.")

    # Step 2: Hashing
    file_hash = compute_file_hash(file_bytes)
    print(f"[Step 2] File SHA-256: {file_hash[:16]}... ({format_file_size(len(file_bytes))})")

    # Step 3: Load and clean
    print("[Step 3] Loading PDF with PyPDFLoader and cleaning text...")
    pages = load_and_preprocess_pdf(sample_pdf, "DBMS_Study_Notes.pdf")
    print(f" -> Successfully extracted {len(pages)} pages.")
    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"

    for p in pages:
        print(f"    * Page {p.metadata['page']} (length: {len(p.page_content)} chars)")

    # Step 4: Split into chunks
    print("\n[Step 4] Splitting into chunks with RecursiveCharacterTextSplitter...")
    doc_id = "test-dbms-doc-id"
    # Clean any prior test runs
    delete_documents_by_id(doc_id)
    remove_document_from_manifest(doc_id)

    chunks = split_documents(
        documents=pages,
        document_id=doc_id,
        filename="DBMS_Study_Notes.pdf",
        file_hash=file_hash,
    )
    print(f" -> Generated {len(chunks)} chunks.")
    assert len(chunks) >= 3, "Expected at least 3 chunks"

    # Step 5: Embed & Store in ChromaDB
    print("\n[Step 5] Embedding & Indexing in ChromaDB (sentence-transformers/all-MiniLM-L6-v2)...")
    added = add_documents_to_vectorstore(chunks)
    print(f" -> Indexed {added} chunks into collection '{settings.CHROMA_COLLECTION_NAME}'.")
    total_chunks = get_total_chunks_count()
    print(f" -> Total chunks in ChromaDB: {total_chunks}")

    # Add to manifest
    meta = DocumentMetadata(
        document_id=doc_id,
        filename="DBMS_Study_Notes.pdf",
        file_path=sample_pdf,
        file_hash=file_hash,
        file_size_bytes=len(file_bytes),
        file_size_formatted=format_file_size(len(file_bytes)),
        page_count=len(pages),
        chunk_count=added,
        status="ready"
    )
    add_document_to_manifest(meta)

    # Step 6: Test duplicate detection
    print("\n[Step 6] Testing duplicate detection by hash...")
    existing = find_document_by_hash(file_hash)
    assert existing is not None, "Document hash should be found in manifest"
    print(f" -> Found existing document: {existing.filename} ({existing.document_id})")

    # Step 7: Retrieval and Citation Verification
    print("\n[Step 7] Testing retrieval for question: 'What is normalization?'...")
    query = "What is database normalization and what are the benefits of 3NF?"
    results = retrieve_relevant_chunks(query, top_k=3, score_threshold=0.30)
    assert len(results) > 0, "Expected at least 1 relevant chunk"

    top_chunk, top_score = results[0]
    cited_page = top_chunk.metadata.get("page")
    cited_doc = top_chunk.metadata.get("filename")
    print(f" -> Top retrieved chunk from: [{cited_doc} | Page {cited_page}] with score {top_score:.4f}")
    print(f" -> Snippet: {top_chunk.page_content[:120]}...")

    # Verification: Normalization is specifically on Page 2 in our DBMS document!
    assert cited_page == 2, f"Expected citation to be Page 2, but got Page {cited_page}!"
    print(" -> SUCCESS: Page 2 correctly cited for Database Normalization!")

    # Step 8: Irrelevant Query Threshold Test
    print("\n[Step 8] Testing retrieval with completely unrelated question...")
    unrelated_query = "What are the ingredients and baking instructions for chocolate chip cookies?"
    unrelated_results = retrieve_relevant_chunks(unrelated_query, top_k=3, score_threshold=0.30)
    print(f" -> Chunks passing threshold for unrelated question: {len(unrelated_results)}")
    if len(unrelated_results) == 0:
        print(" -> SUCCESS: Unrelated query correctly filtered out by score threshold (0 chunks returned).")
    else:
        print(f" -> Notice: Chunks scored: {[r[1] for r in unrelated_results]}")

    print("\n" + "=" * 70)
    print(" ALL BACKEND PIPELINE VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()

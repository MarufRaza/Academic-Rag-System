import os
from app.rag.loader import load_and_preprocess_document
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_documents_to_vectorstore, delete_documents_by_id
from app.utils.file_utils import compute_file_hash, format_file_size
from app.utils.manifest import add_document_to_manifest, remove_document_from_manifest
from app.models.document import DocumentMetadata


def ingest_samples():
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")
    files = [
        ("DBMS_Study_Notes.pdf", "sample-dbms-001"),
        ("Computer_Networks_Guide.pdf", "sample-net-002"),
        ("Cloud_Computing_Essentials.pdf", "sample-cloud-003"),
        ("RAG_Docx_Sample.docx", "sample-docx-004"),
    ]

    for fname, doc_id in files:
        src_path = os.path.join(sample_dir, fname)
        with open(src_path, "rb") as f:
            b = f.read()

        file_hash = compute_file_hash(b)
        delete_documents_by_id(doc_id)
        remove_document_from_manifest(doc_id)

        os.makedirs("uploads", exist_ok=True)
        dest_path = os.path.join("uploads", f"{doc_id}_{fname}")
        with open(dest_path, "wb") as f:
            f.write(b)

        pages = load_and_preprocess_document(dest_path, fname)
        chunks = split_documents(pages, doc_id, fname, file_hash)
        added = add_documents_to_vectorstore(chunks)

        meta = DocumentMetadata(
            document_id=doc_id,
            filename=fname,
            file_path=dest_path,
            file_hash=file_hash,
            file_size_bytes=len(b),
            file_size_formatted=format_file_size(len(b)),
            page_count=len(pages),
            chunk_count=added,
            status="ready"
        )
        add_document_to_manifest(meta)
        print(f"Ingested '{fname}': {len(pages)} pages, {added} chunks.")


if __name__ == "__main__":
    ingest_samples()

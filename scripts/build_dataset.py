"""Build a retrieval/reference dataset from the bundled sample documents."""

import csv
import hashlib
import sys
import uuid
from pathlib import Path
from typing import Dict, Iterable, List

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from langchain_chroma import Chroma

from app.core.config import settings
from app.rag.embeddings import get_active_embedding_info, get_embedding_function
from app.rag.loader import load_and_preprocess_document
from app.rag.splitter import split_documents


DATASET_COLUMNS = [
    "doc_id",
    "doc_type",
    "source",
    "chunk_id",
    "chunk_text",
    "embedding_model",
    "retrieval_score",
    "query",
    "answer",
]

DATA_DICTIONARY = [
    ("doc_id", "string", "Stable identifier derived from the source document content hash."),
    ("doc_type", "string", "Source document type, such as pdf or docx."),
    ("source", "string", "Source document filename."),
    ("chunk_id", "string", "Zero-indexed chunk identifier within the source document."),
    ("chunk_text", "string", "Text content of the retrieved document chunk."),
    ("embedding_model", "string", "Embedding provider and model used to index the chunks."),
    ("retrieval_score", "float", "Chroma relevance score for this chunk and query."),
    ("query", "string", "Benchmark question used to retrieve the chunk."),
    ("answer", "string", "Reference answer excerpt copied from the retrieved source chunk."),
]

BENCHMARK_QUERIES = [
    "What is database normalization and what are the benefits of 3NF?",
    "Explain the 7 layers of the OSI model and their key responsibilities.",
    "What is the key difference between TCP and UDP in terms of reliability and overhead?",
    "Explain the core service models of cloud computing: IaaS, PaaS, and SaaS.",
    "What is the difference between preemptive and non-preemptive CPU scheduling algorithms?",
]


def _read_sample_documents() -> List:
    sample_dir = BACKEND_ROOT / "sample_documents"
    files = sorted(
        path for path in sample_dir.iterdir()
        if path.is_file() and path.suffix.lower() in settings.ALLOWED_EXTENSIONS
    )
    if not files:
        raise FileNotFoundError(f"No supported sample documents found in {sample_dir}")

    chunks = []
    for path in files:
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        document_id = content_hash[:16]
        pages = load_and_preprocess_document(str(path), path.name)
        chunks.extend(split_documents(
            documents=pages,
            document_id=document_id,
            filename=path.name,
            file_hash=content_hash,
        ))
    return chunks


def _create_rows() -> Iterable[Dict[str, str]]:
    chunks = _read_sample_documents()
    embedding_info = get_active_embedding_info()
    embedding_model = f"{embedding_info['provider']}::{embedding_info['model']}"
    vectorstore = Chroma(
        collection_name=f"dataset_build_{uuid.uuid4().hex[:12]}",
        embedding_function=get_embedding_function(),
        collection_metadata={"hnsw:space": "cosine"},
    )
    try:
        vectorstore.add_documents(chunks)
        for query in BENCHMARK_QUERIES:
            results = vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=settings.TOP_K,
            )
            above_threshold = [
                (document, score)
                for document, score in results
                if score >= settings.SCORE_THRESHOLD
            ]
            if above_threshold:
                for document, score in above_threshold:
                    metadata = document.metadata
                    yield {
                        "doc_id": str(metadata["document_id"]),
                        "doc_type": Path(metadata["filename"]).suffix.lstrip(".").lower(),
                        "source": str(metadata["filename"]),
                        "chunk_id": str(metadata["chunk_index"]),
                        "chunk_text": document.page_content.strip(),
                        "embedding_model": embedding_model,
                        "retrieval_score": str(round(float(score), 6)),
                        "query": query.strip(),
                        "answer": document.page_content.strip(),
                    }
            else:
                yield {
                    "doc_id": "no-relevant-document",
                    "doc_type": "control",
                    "source": "none",
                    "chunk_id": "-1",
                    "chunk_text": "No sample document chunk met the configured relevance threshold.",
                    "embedding_model": embedding_model,
                    "retrieval_score": "0.0",
                    "query": query.strip(),
                    "answer": "I couldn't find enough information in the uploaded documents to answer this question.",
                }
    finally:
        vectorstore.delete_collection()


def _clean_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    cleaned = []
    seen = set()
    for row in rows:
        normalized = {column: (row.get(column) or "").strip() for column in DATASET_COLUMNS}
        if any(not value for value in normalized.values()):
            continue
        key = tuple(normalized[column] for column in DATASET_COLUMNS)
        if key not in seen:
            seen.add(key)
            cleaned.append(normalized)
    if not cleaned:
        raise ValueError("Dataset generation produced no complete, unique rows.")
    return cleaned


def main() -> None:
    dataset_path = REPOSITORY_ROOT / "dataset.csv"
    dictionary_path = REPOSITORY_ROOT / "data_dictionary.csv"

    if dataset_path.exists():
        print(f"Using existing dataset without overwriting it: {dataset_path}")
    else:
        rows = _clean_rows(_create_rows())
        with dataset_path.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=DATASET_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} retrieval/reference rows to {dataset_path}")

    with dictionary_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["column_name", "type", "description"])
        writer.writerows(DATA_DICTIONARY)
    print(f"Wrote the nine-column data dictionary to {dictionary_path}")


if __name__ == "__main__":
    main()

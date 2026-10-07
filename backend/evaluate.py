import time
from typing import List, Dict, Any
from app.core.config import settings
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.vectorstore import get_total_chunks_count
from app.utils.manifest import list_all_documents

# 5 representative academic evaluation questions
SAMPLE_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is database normalization and what are the benefits of 3NF?",
        "topic": "Database Management Systems (DBMS)",
    },
    {
        "id": "Q2",
        "question": "Explain the 7 layers of the OSI model and their key responsibilities.",
        "topic": "Computer Networks",
    },
    {
        "id": "Q3",
        "question": "What is the key difference between TCP and UDP in terms of reliability and overhead?",
        "topic": "Computer Networks / Transport Layer",
    },
    {
        "id": "Q4",
        "question": "Explain the core service models of cloud computing: IaaS, PaaS, and SaaS.",
        "topic": "Cloud Computing",
    },
    {
        "id": "Q5",
        "question": "What is the difference between preemptive and non-preemptive CPU scheduling algorithms?",
        "topic": "Operating Systems",
    }
]


def run_evaluation() -> None:
    print("=" * 75)
    print(" ACADEMIC RAG PIPELINE EVALUATION HARNESS")
    print("=" * 75)
    print(f"Embedding Provider : {settings.EMBEDDING_PROVIDER}")
    print(f"Embedding Model    : {settings.HF_EMBEDDING_MODEL if settings.EMBEDDING_PROVIDER == 'huggingface' else settings.OPENAI_EMBEDDING_MODEL}")
    print(f"Top-K Chunks       : {settings.TOP_K}")
    print(f"Score Threshold    : {settings.SCORE_THRESHOLD}")
    print("-" * 75)

    docs = list_all_documents()
    total_chunks = get_total_chunks_count()

    print(f"Indexed Documents  : {len(docs)}")
    print(f"Total Vector Chunks: {total_chunks}")
    print("-" * 75)

    if total_chunks == 0:
        print("[!] No documents currently in ChromaDB.")
        print("    Upload academic PDFs (e.g. DBMS, Networking, or OS notes) first")
        print("    via the web interface or /api/documents/upload before running evaluate.py.")
        print("=" * 75)
        return

    print("\nRunning retrieval evaluation across 5 sample benchmark questions:\n")

    results_summary: List[Dict[str, Any]] = []

    for item in SAMPLE_QUESTIONS:
        q_id = item["id"]
        q_text = item["question"]
        topic = item["topic"]

        print(f"[{q_id}] Query: \"{q_text}\"")
        print(f"     Topic: {topic}")

        start_time = time.perf_counter()
        retrieved = retrieve_relevant_chunks(
            query=q_text,
            top_k=settings.TOP_K,
            score_threshold=settings.SCORE_THRESHOLD
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        passed = len(retrieved) > 0
        top_score = retrieved[0][1] if retrieved else 0.0

        print(f"     Status: {'PASS (Found relevant chunks)' if passed else 'FAIL (Below threshold / Not enough info)'}")
        print(f"     Chunks Retrieved: {len(retrieved)} / {settings.TOP_K} | Top Score: {top_score:.4f} | Latency: {latency_ms:.1f}ms")

        if retrieved:
            for idx, (chunk, score) in enumerate(retrieved, 1):
                doc_name = chunk.metadata.get("filename", "Unknown")
                page = chunk.metadata.get("page", "?")
                snippet = chunk.page_content.replace("\n", " ")[:90]
                print(f"       -> Chunk #{idx}: [{doc_name} | Page {page}] (Score: {score:.4f}) \"{snippet}...\"")

        print("-" * 75)
        results_summary.append({
            "id": q_id,
            "passed": passed,
            "chunks": len(retrieved),
            "top_score": top_score,
            "latency_ms": latency_ms
        })

    # Summary table
    print("\n" + "=" * 75)
    print(" EVALUATION SUMMARY")
    print("=" * 75)
    total_passed = sum(1 for r in results_summary if r["passed"])
    avg_latency = sum(r["latency_ms"] for r in results_summary) / len(results_summary)

    print(f"Passed Threshold : {total_passed} / {len(SAMPLE_QUESTIONS)} ({total_passed / len(SAMPLE_QUESTIONS) * 100:.1f}%)")
    print(f"Average Latency  : {avg_latency:.1f}ms")
    print("=" * 75)


if __name__ == "__main__":
    run_evaluation()

import time
from typing import List, Dict, Any
from app.core.config import settings
from app.rag.pipeline import execute_rag_pipeline, NOT_ENOUGH_INFO_MSG
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.vectorstore import get_total_chunks_count
from app.utils.manifest import list_all_documents

# 5 representative academic evaluation questions
# Includes positive tests (grounded domain queries) AND negative control (refusal guardrail test)
SAMPLE_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is database normalization and what are the benefits of 3NF?",
        "topic": "Database Management Systems (DBMS)",
        "expected_relevant": True,
        "target_doc": "DBMS_Study_Notes.pdf",
        "target_page": 2,
    },
    {
        "id": "Q2",
        "question": "Explain the 7 layers of the OSI model and their key responsibilities.",
        "topic": "Computer Networks",
        "expected_relevant": True,
        "target_doc": "Computer_Networks_Guide.pdf",
        "target_page": 2,
    },
    {
        "id": "Q3",
        "question": "What is the key difference between TCP and UDP in terms of reliability and overhead?",
        "topic": "Computer Networks / Transport Layer",
        "expected_relevant": True,
        "target_doc": "Computer_Networks_Guide.pdf",
        "target_page": 3,
    },
    {
        "id": "Q4",
        "question": "Explain the core service models of cloud computing: IaaS, PaaS, and SaaS.",
        "topic": "Cloud Computing",
        "expected_relevant": True,
        "target_doc": "Cloud_Computing_Essentials.pdf",
        "target_page": 2,
    },
    {
        "id": "Q5",
        "question": "What is the difference between preemptive and non-preemptive CPU scheduling algorithms?",
        "topic": "Operating Systems (Negative Control / Refusal Test)",
        "expected_relevant": False,  # Topic is not present in uploaded docs, MUST be rejected
        "target_doc": None,
        "target_page": None,
    }
]


def run_evaluation() -> None:
    print("=" * 80)
    print(" ACADEMIC RAG BENCHMARK & RETRIEVAL EVALUATION HARNESS")
    print("=" * 80)
    print(f"Embedding Provider : {settings.EMBEDDING_PROVIDER}")
    print(f"Embedding Model    : {settings.HF_EMBEDDING_MODEL if settings.EMBEDDING_PROVIDER == 'huggingface' else settings.OPENAI_EMBEDDING_MODEL}")
    print(f"LLM Provider       : {settings.LLM_PROVIDER}")
    print(f"Top-K Chunks       : {settings.TOP_K}")
    print(f"Score Threshold    : {settings.SCORE_THRESHOLD}")
    print("-" * 80)

    docs = list_all_documents()
    total_chunks = get_total_chunks_count()

    print(f"Indexed Documents  : {len(docs)}")
    print(f"Total Vector Chunks: {total_chunks}")
    print("-" * 80)

    if total_chunks == 0:
        print("[!] No documents currently in ChromaDB.")
        print("    Upload academic PDFs (e.g. DBMS, Networking, or Cloud notes) first")
        print("    via the web interface or run `python ingest_sample_docs.py`.")
        print("=" * 80)
        return

    print("\nRunning benchmark across 5 questions (4 relevant + 1 negative refusal test):\n")

    results_summary: List[Dict[str, Any]] = []

    for item in SAMPLE_QUESTIONS:
        q_id = item["id"]
        q_text = item["question"]
        topic = item["topic"]
        expected_rel = item["expected_relevant"]
        target_doc = item["target_doc"]
        target_page = item["target_page"]

        print(f"[{q_id}] Query: \"{q_text}\"")
        print(f"     Topic: {topic}")
        print(f"     Expected Behavior: {'Retrieve relevant document chunks' if expected_rel else 'REJECT / Zero Hallucination Guardrail'}")

        start_time = time.perf_counter()
        retrieved = retrieve_relevant_chunks(
            query=q_text,
            top_k=settings.TOP_K,
            score_threshold=settings.SCORE_THRESHOLD
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Evaluate correctness
        if expected_rel:
            # Positive test: must retrieve >= 1 chunk above threshold, top chunk should match target doc & page
            has_chunks = len(retrieved) > 0
            doc_matched = has_chunks and (retrieved[0][0].metadata.get("filename") == target_doc)
            page_matched = has_chunks and (retrieved[0][0].metadata.get("page") == target_page)
            passed = has_chunks and doc_matched
            reason = f"Retrieved {len(retrieved)} chunk(s). Top cited: [{retrieved[0][0].metadata.get('filename') if has_chunks else 'None'} | Page {retrieved[0][0].metadata.get('page') if has_chunks else 'None'}]"
        else:
            # Negative control test: MUST retrieve 0 chunks above threshold to prevent hallucination
            passed = len(retrieved) == 0
            reason = f"Correctly blocked ({len(retrieved)} chunks passed threshold). Refusal guardrail active." if passed else f"FAILED: Retrieved {len(retrieved)} false positive chunk(s)!"

        status_label = "PASS" if passed else "FAIL"
        top_score = retrieved[0][1] if retrieved else 0.0

        print(f"     Status: {status_label} ({reason})")
        print(f"     Top Score: {top_score:.4f} | Latency: {latency_ms:.1f}ms")

        if retrieved:
            for idx, (chunk, score) in enumerate(retrieved[:2], 1):
                doc_name = chunk.metadata.get("filename", "Unknown")
                page = chunk.metadata.get("page", "?")
                snippet = chunk.page_content.replace("\n", " ")[:80]
                print(f"       -> Chunk #{idx}: [{doc_name} | Page {page}] (Score: {score:.4f}) \"{snippet}...\"")

        print("-" * 80)
        results_summary.append({
            "id": q_id,
            "passed": passed,
            "expected_relevant": expected_rel,
            "chunks": len(retrieved),
            "top_score": top_score,
            "latency_ms": latency_ms
        })

    # Summary table
    print("\n" + "=" * 80)
    print(" BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    total_passed = sum(1 for r in results_summary if r["passed"])
    positive_passed = sum(1 for r in results_summary if r["passed"] and r["expected_relevant"])
    negative_passed = sum(1 for r in results_summary if r["passed"] and not r["expected_relevant"])
    avg_latency = sum(r["latency_ms"] for r in results_summary) / len(results_summary)

    print(f"Overall Benchmark Score : {total_passed} / {len(SAMPLE_QUESTIONS)} ({total_passed / len(SAMPLE_QUESTIONS) * 100:.1f}%)")
    print(f"Positive Retrieval Rate : {positive_passed} / 4 ({positive_passed / 4 * 100:.1f}%)")
    print(f"Refusal Guardrail Rate  : {negative_passed} / 1 ({negative_passed / 1 * 100:.1f}%)")
    print(f"Average Search Latency  : {avg_latency:.1f}ms")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()

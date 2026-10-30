"""Evaluate dataset queries through the end-to-end RAG answer pipeline."""

import csv
import re
import shutil
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.core.config import settings
from app.rag.pipeline import NOT_ENOUGH_INFO_MSG, execute_rag_pipeline

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPOSITORY_ROOT / "dataset.csv"
RESULTS_DIR = REPOSITORY_ROOT / "evaluation_results"
LATENCY_THRESHOLD_MS = 10_000.0
ANSWER_QUALITY_THRESHOLD = 0.20


def _load_dataset() -> List[Dict[str, str]]:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {DATASET_PATH}. Run scripts/build_dataset.py first."
        )
    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as dataset_file:
        rows = list(csv.DictReader(dataset_file))
    if not rows:
        raise ValueError(f"No evaluation queries found in {DATASET_PATH}.")
    if not {"source", "query", "answer"}.issubset(rows[0]):
        raise ValueError("dataset.csv must include source, query, and answer columns.")
    return rows


def _answer_quality_score(answer: str, reference: str) -> float:
    """Return reference-token recall as a lightweight answer-content heuristic."""
    reference_tokens = {
        token.lower()
        for token in re.findall(r"\b[\w'-]+\b", reference)
        if len(token) > 2
    }
    if reference.strip() == NOT_ENOUGH_INFO_MSG:
        return 1.0 if answer.strip() == NOT_ENOUGH_INFO_MSG else 0.0
    if not reference_tokens:
        return 0.0
    answer_tokens = {
        token.lower()
        for token in re.findall(r"\b[\w'-]+\b", answer)
        if len(token) > 2
    }
    return len(reference_tokens & answer_tokens) / len(reference_tokens)


def run_evaluation() -> None:
    evaluated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dataset_rows = _load_dataset()
    results: List[Dict[str, object]] = []

    query_groups: Dict[str, List[Dict[str, str]]] = {}
    for row in dataset_rows:
        query_groups.setdefault(row["query"].strip(), []).append(row)

    warmup_query = next(iter(query_groups))
    execute_rag_pipeline(question=warmup_query)

    for query, query_rows in query_groups.items():
        expected_chunks = {
            (row["source"].strip(), row["chunk_id"].strip())
            for row in query_rows
            if row["source"].strip().lower() != "none"
        }
        reference_answers = list(dict.fromkeys(row["answer"].strip() for row in query_rows))
        reference_answer = "\n".join(reference_answers)
        started = time.perf_counter()
        response = execute_rag_pipeline(question=query)
        latency_ms = (time.perf_counter() - started) * 1000

        citations = response.sources
        top_source = citations[0] if citations else None
        actual_source = top_source.document if top_source else "none"
        matching_citations = [
            citation for citation in citations
            if (Path(citation.document).name, str(citation.chunk_index)) in {
                (Path(source).name, chunk_id)
                for source, chunk_id in expected_chunks
            }
        ]
        retrieval_score = max(
            (float(citation.score or 0.0) for citation in matching_citations),
            default=0.0,
        )
        if not expected_chunks:
            retrieval_pass = not citations
        else:
            retrieval_pass = (
                bool(matching_citations)
                and retrieval_score >= settings.SCORE_THRESHOLD
            )

        quality_score = _answer_quality_score(response.answer, reference_answer)
        quality_pass = quality_score >= ANSWER_QUALITY_THRESHOLD
        latency_pass = latency_ms <= LATENCY_THRESHOLD_MS
        results.append({
            "evaluated_at": evaluated_at,
            "query": query,
            "expected_source": ";".join(sorted({source for source, _ in expected_chunks})) or "none",
            "retrieved_source": actual_source,
            "retrieval_score": round(retrieval_score, 6),
            "retrieval_pass": retrieval_pass,
            "answer_quality_score": round(quality_score, 6),
            "answer_quality_pass": quality_pass,
            "end_to_end_latency_ms": round(latency_ms, 2),
            "latency_pass": latency_pass,
            "overall_pass": retrieval_pass and quality_pass and latency_pass,
            "answer": response.answer,
        })

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / "results.csv"
    summary_path = RESULTS_DIR / "summary.md"
    timestamped_results_path = RESULTS_DIR / f"results_{run_id}.csv"
    timestamped_summary_path = RESULTS_DIR / f"summary_{run_id}.md"
    fieldnames = list(results[0].keys())

    if results_path.exists():
        shutil.copy2(
            results_path,
            RESULTS_DIR / f"results_previous_{run_id}.csv",
        )
    if summary_path.exists():
        shutil.copy2(
            summary_path,
            RESULTS_DIR / f"summary_previous_{run_id}.md",
        )

    with timestamped_results_path.open("w", encoding="utf-8", newline="") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    shutil.copy2(timestamped_results_path, results_path)

    passed = sum(bool(result["overall_pass"]) for result in results)
    average_latency = statistics.mean(
        float(result["end_to_end_latency_ms"]) for result in results
    )
    average_quality = statistics.mean(
        float(result["answer_quality_score"]) for result in results
    )
    summary = f"""# RAG Evaluation Summary

- Evaluated at: {evaluated_at}
- Dataset rows: {len(results)}
- Overall pass rate: {passed}/{len(results)} ({passed / len(results):.1%})
- Average end-to-end latency: {average_latency:.2f} ms
- Average reference-token recall: {average_quality:.3f}

## Pass thresholds

- Retrieval: at least one dataset-listed source/chunk is cited with a score at least `{settings.SCORE_THRESHOLD:.2f}`; control rows with source `none` must have no citations.
- Answer quality: reference-token recall is at least `{ANSWER_QUALITY_THRESHOLD:.2f}`. This is a lexical heuristic, not a semantic faithfulness guarantee.
- Latency: complete query-to-answer pipeline is at most `{LATENCY_THRESHOLD_MS:.0f} ms`.

Detailed per-query records (including the timestamp) are appended to [results.csv](./results.csv).
"""
    timestamped_summary_path.write_text(summary, encoding="utf-8")
    shutil.copy2(timestamped_summary_path, summary_path)
    print(f"Evaluation completed: {passed}/{len(results)} passed.")
    print(f"Saved results to {results_path} and summary to {RESULTS_DIR / 'summary.md'}.")


if __name__ == "__main__":
    run_evaluation()

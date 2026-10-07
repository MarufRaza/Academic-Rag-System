from typing import List, Tuple
from langchain_core.documents import Document
from app.core.config import settings
from app.core.logging import logger
from app.rag.vectorstore import get_or_create_vectorstore, get_total_chunks_count


def retrieve_relevant_chunks(
    query: str,
    top_k: int = settings.TOP_K,
    score_threshold: float = settings.SCORE_THRESHOLD,
) -> List[Tuple[Document, float]]:
    """
    Performs similarity search with relevance scores against the Chroma vectorstore.
    Filters out any chunks whose relevance score falls below `score_threshold`.
    Returns list of (Document, score) pairs.
    """
    total_chunks = get_total_chunks_count()
    if total_chunks == 0:
        logger.info("ChromaDB collection is empty. Returning 0 relevant chunks.")
        return []

    vectorstore = get_or_create_vectorstore()

    try:
        # similarity_search_with_relevance_scores returns List[Tuple[Document, float]]
        results_with_scores = vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
        )
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        # Fallback to standard similarity search if score method fails
        raw_docs = vectorstore.similarity_search(query=query, k=top_k)
        results_with_scores = [(doc, 0.5) for doc in raw_docs]

    filtered_results: List[Tuple[Document, float]] = []

    for doc, score in results_with_scores:
        logger.info(
            f"Candidate chunk: Doc='{doc.metadata.get('filename')}' "
            f"Page={doc.metadata.get('page')} Score={score:.4f}"
        )
        if score >= score_threshold:
            filtered_results.append((doc, float(score)))

    logger.info(
        f"Retrieved {len(filtered_results)} chunks (out of {len(results_with_scores)} candidates) "
        f"above score threshold {score_threshold:.2f} for query: '{query[:60]}...'"
    )

    return filtered_results

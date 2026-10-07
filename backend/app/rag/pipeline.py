from typing import List, Optional
from app.core.config import settings
from app.core.exceptions import EmptyQuestionException
from app.core.logging import logger
from app.models.chat import ChatMessage, ChatResponse, SourceCitation
from app.rag.generator import get_llm, invoke_llm_safely
from app.rag.prompts import ACADEMIC_RAG_PROMPT, CONDENSE_QUESTION_PROMPT
from app.rag.retriever import retrieve_relevant_chunks

NOT_ENOUGH_INFO_MSG = "I couldn't find enough information in the uploaded documents to answer this question."


def condense_followup_question(question: str, chat_history: List[ChatMessage]) -> str:
    """
    Condenses follow-up question into a standalone question using the LLM.
    If LLM condensation fails or returns blank, falls back to original question.
    """
    if not chat_history:
        return question

    # Format history turns
    history_lines = []
    for msg in chat_history[-6:]:  # Keep up to last 6 turns for brevity and speed
        role = "Student" if msg.role == "user" else "Assistant"
        history_lines.append(f"{role}: {msg.content}")
    formatted_history = "\n".join(history_lines)

    try:
        llm = get_llm(temperature=0.0)
        prompt_text = CONDENSE_QUESTION_PROMPT.format(
            chat_history=formatted_history,
            question=question
        )
        condensed = invoke_llm_safely(llm, prompt_text).strip()
        # Clean any accidental quotes
        condensed = condensed.strip('"').strip("'")
        if condensed:
            logger.info(f"Rephrased question: '{question}' -> '{condensed}'")
            return condensed
    except Exception as e:
        logger.warning(f"Question condensation skipped due to error: {e}")

    return question


def format_retrieved_context(chunks: list) -> str:
    """Formats retrieved document chunks into clean academic context blocks."""
    context_parts = []
    for doc, _ in chunks:
        doc_name = doc.metadata.get("filename", "Unknown Document")
        page_num = doc.metadata.get("page", 1)
        part = f"--- Document: {doc_name} | Page: {page_num} ---\n{doc.page_content.strip()}"
        context_parts.append(part)
    return "\n\n".join(context_parts)


def execute_rag_pipeline(
    question: str,
    chat_history: Optional[List[ChatMessage]] = None,
    top_k: int = settings.TOP_K,
    score_threshold: float = settings.SCORE_THRESHOLD,
) -> ChatResponse:
    """
    Executes the end-to-end Academic RAG pipeline:
    1. Validates non-empty question.
    2. Condenses follow-up question if chat_history is provided.
    3. Retrieves top-k chunks with relevance score filtering.
    4. If no relevant chunks pass threshold, returns the exact required message without calling LLM.
    5. Formats context, invokes LLM with ACADEMIC_RAG_PROMPT.
    6. Formats deduplicated source citations (document, page, snippet).
    """
    cleaned_question = question.strip() if question else ""
    if not cleaned_question:
        raise EmptyQuestionException()

    # Step 1: Condense follow-up if history is present
    standalone_q = condense_followup_question(
        question=cleaned_question,
        chat_history=chat_history or []
    )

    # Step 2: Dense vector retrieval
    relevant_chunks = retrieve_relevant_chunks(
        query=standalone_q,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    # Step 3: Hard constraint check - if no relevant chunks found, return exact phrase immediately!
    if not relevant_chunks:
        logger.info("No relevant chunks found above score threshold. Returning default message without calling LLM.")
        return ChatResponse(
            answer=NOT_ENOUGH_INFO_MSG,
            sources=[],
            standalone_question=standalone_q if standalone_q != cleaned_question else None
        )

    # Step 4: Build context from retrieved chunks
    context_text = format_retrieved_context(relevant_chunks)

    # Step 5: Format prompt and call generation LLM
    llm = get_llm(temperature=0.1)
    prompt_text = ACADEMIC_RAG_PROMPT.format(
        context=context_text,
        question=standalone_q
    )

    raw_answer = invoke_llm_safely(llm, prompt_text).strip()

    # If the LLM itself determined that the context does not contain enough information,
    # ensure clean source handling
    if NOT_ENOUGH_INFO_MSG.lower() in raw_answer.lower():
        return ChatResponse(
            answer=NOT_ENOUGH_INFO_MSG,
            sources=[],
            standalone_question=standalone_q if standalone_q != cleaned_question else None
        )

    # Step 6: Construct deduplicated sources
    seen_sources = set()
    sources: List[SourceCitation] = []

    for doc, score in relevant_chunks:
        doc_name = doc.metadata.get("filename", "Document")
        page_num = int(doc.metadata.get("page", 1))
        content_snippet = doc.page_content.strip()

        # Deduplicate based on document and page and preview
        source_key = (doc_name, page_num, content_snippet[:80])
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append(SourceCitation(
                document=doc_name,
                page=page_num,
                content=content_snippet,
                score=round(score, 4)
            ))

    return ChatResponse(
        answer=raw_answer,
        sources=sources,
        standalone_question=standalone_q if standalone_q != cleaned_question else None
    )

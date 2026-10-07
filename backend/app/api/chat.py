from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.models.chat import ChatRequest, ChatResponse
from app.rag.pipeline import stream_rag_pipeline
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question grounded in the uploaded academic documents (blocking)",
)
async def ask_question(request: ChatRequest):
    """
    Takes a student question and conversation history, executes RAG retrieval
    and answer generation with source citations.
    Uses run_in_threadpool so heavy embedding and inference never block the asyncio event loop.
    """
    return await run_in_threadpool(ChatService.answer_question, request)


@router.post(
    "/stream",
    summary="Ask a question and stream response tokens via Server-Sent Events (SSE)",
)
async def ask_question_stream(request: ChatRequest):
    """
    Streams answer tokens in real-time as Server-Sent Events (SSE), followed by source citations.
    """
    return StreamingResponse(
        stream_rag_pipeline(
            question=request.question,
            chat_history=request.chat_history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

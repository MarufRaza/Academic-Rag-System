from fastapi import APIRouter, status
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question grounded in the uploaded academic documents",
)
async def ask_question(request: ChatRequest):
    """
    Takes a student question and conversation history, executes RAG retrieval
    and answer generation with source citations.
    """
    return ChatService.answer_question(request)

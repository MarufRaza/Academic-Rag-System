from app.models.chat import ChatRequest, ChatResponse
from app.rag.pipeline import execute_rag_pipeline


class ChatService:
    @staticmethod
    def answer_question(request: ChatRequest) -> ChatResponse:
        """Processes a student question through the RAG pipeline."""
        return execute_rag_pipeline(
            question=request.question,
            chat_history=request.chat_history,
        )

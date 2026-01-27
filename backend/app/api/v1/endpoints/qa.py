"""Q&A endpoints using RAG system."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.qa import QuestionRequest, QuestionResponse
from app.api.dependencies import get_current_active_user
from app.services.rag_service import rag_service
from app.services.huggingface_service import huggingface_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    question_data: QuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask a question and get an answer using RAG.

    The system will:
    1. Search for relevant document excerpts
    2. Use them as context for Llama3
    3. Generate an answer based on the context
    """
    try:
        relevant_documents = rag_service.search(
            question_data.question,
            k=question_data.context_limit
        )

        if not relevant_documents:
            return QuestionResponse(
                question=question_data.question,
                answer="I don't have enough context to answer this question. Please upload relevant documents first.",
                relevant_documents=[],
                confidence=0.0
            )

        context = rag_service.get_context_for_question(
            question_data.question,
            k=question_data.context_limit
        )

        answer = await huggingface_service.answer_question(
            question_data.question,
            context
        )

        avg_confidence = sum(doc.relevance_score for doc in relevant_documents) / len(relevant_documents)

        logger.info(f"Question answered for user {current_user.id}: {question_data.question[:50]}...")

        return QuestionResponse(
            question=question_data.question,
            answer=answer,
            relevant_documents=relevant_documents,
            confidence=avg_confidence
        )

    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer question"
        )

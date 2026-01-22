"""Q&A-related Pydantic schemas for RAG system."""
from typing import Optional
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Schema for asking a question."""
    question: str = Field(..., min_length=10, max_length=1000)
    context_limit: Optional[int] = Field(default=5, ge=1, le=20)


class DocumentExcerpt(BaseModel):
    """Schema for relevant document excerpt."""
    document_id: int
    filename: str
    excerpt: str
    relevance_score: float


class QuestionResponse(BaseModel):
    """Schema for question answer response."""
    question: str
    answer: str
    relevant_documents: list[DocumentExcerpt]
    confidence: Optional[float] = None

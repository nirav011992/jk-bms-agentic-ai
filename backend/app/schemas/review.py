"""Review-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """Base review schema with common attributes."""
    review_text: str = Field(..., min_length=10)
    rating: float = Field(..., ge=1.0, le=5.0)


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    book_id: int


class ReviewUpdate(BaseModel):
    """Schema for updating review information."""
    review_text: Optional[str] = Field(None, min_length=10)
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)


class ReviewResponse(ReviewBase):
    """Schema for review response."""
    id: int
    book_id: int
    user_id: int
    sentiment_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewSummaryResponse(BaseModel):
    """Schema for aggregated review summary."""
    average_rating: float
    total_reviews: int
    rating_distribution: dict[str, int]
    summary: str

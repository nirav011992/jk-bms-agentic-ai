"""Book-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookBase(BaseModel):
    """Base book schema with common attributes."""
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=255)
    genre: str = Field(..., min_length=1, max_length=100)
    year_published: int = Field(..., ge=1000, le=9999)


class BookCreate(BookBase):
    """Schema for creating a new book."""
    content: Optional[str] = None
    summary: Optional[str] = None


class BookUpdate(BaseModel):
    """Schema for updating book information."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    genre: Optional[str] = Field(None, min_length=1, max_length=100)
    year_published: Optional[int] = Field(None, ge=1000, le=9999)
    content: Optional[str] = None
    summary: Optional[str] = None


class BookResponse(BookBase):
    """Schema for book response."""
    id: int
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookSummaryResponse(BaseModel):
    """Schema for book summary with aggregated ratings."""
    book: BookResponse
    average_rating: Optional[float]
    total_reviews: int
    summary: str

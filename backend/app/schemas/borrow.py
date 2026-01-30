"""Pydantic schemas for borrow operations."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.borrow import BorrowStatus


class BorrowBase(BaseModel):
    """Base borrow schema."""
    pass


class BorrowCreate(BorrowBase):
    """Schema for creating a borrow transaction."""
    book_id: int = Field(..., description="ID of the book to borrow")
    loan_period_days: int = Field(default=14, ge=1, le=90, description="Loan period in days (1-90)")


class BorrowReturn(BaseModel):
    """Schema for returning a borrowed book."""
    pass


class BorrowResponse(BorrowBase):
    """Schema for borrow response."""
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    status: BorrowStatus
    is_overdue: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BorrowWithDetails(BorrowResponse):
    """Schema for borrow with book and user details."""
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    user_email: Optional[str] = None
    user_username: Optional[str] = None

    class Config:
        from_attributes = True


class BorrowHistory(BaseModel):
    """Schema for user's borrow history."""
    total_borrows: int
    active_borrows: int
    returned_borrows: int
    overdue_borrows: int
    borrows: list[BorrowWithDetails]

    class Config:
        from_attributes = True


class BookAvailability(BaseModel):
    """Schema for book availability status."""
    book_id: int
    is_available: bool
    active_borrows: int
    total_borrows: int

    class Config:
        from_attributes = True

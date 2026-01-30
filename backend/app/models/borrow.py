"""Borrow model for tracking book borrowing transactions."""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class BorrowStatus(str, enum.Enum):
    """Borrow status enumeration."""
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class Borrow(Base):
    """Borrow database model for tracking book loans."""

    __tablename__ = "borrows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    borrow_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(BorrowStatus), default=BorrowStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="borrows")
    book = relationship("Book", back_populates="borrows")

    def __repr__(self) -> str:
        return f"<Borrow(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, status={self.status})>"

    @property
    def is_overdue(self) -> bool:
        """Check if the borrow is overdue."""
        if self.status == BorrowStatus.RETURNED:
            return False
        return datetime.utcnow() > self.due_date

    @staticmethod
    def calculate_due_date(borrow_date: datetime = None, loan_period_days: int = 14) -> datetime:
        """Calculate due date based on borrow date and loan period."""
        if borrow_date is None:
            borrow_date = datetime.utcnow()
        return borrow_date + timedelta(days=loan_period_days)

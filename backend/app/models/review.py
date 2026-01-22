"""Review model for book reviews and ratings."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Review(Base):
    """Review database model."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    __table_args__ = (
        CheckConstraint('rating >= 1.0 AND rating <= 5.0', name='check_rating_range'),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, book_id={self.book_id}, rating={self.rating})>"

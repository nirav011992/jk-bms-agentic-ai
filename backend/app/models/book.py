"""Book model for storing book information."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship

from app.db.session import Base


class Book(Base):
    """Book database model."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=False, index=True)
    year_published = Column(Integer, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_books_genre_year', 'genre', 'year_published'),
        Index('ix_books_author_title', 'author', 'title'),
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title={self.title}, author={self.author})>"

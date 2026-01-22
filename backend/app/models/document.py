"""Document model for RAG system."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base


class Document(Base):
    """Document database model for RAG ingestion."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    embeddings = Column(JSON, nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    ingestion_status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.ingestion_status})>"

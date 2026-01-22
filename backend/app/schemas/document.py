"""Document-related Pydantic schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema with common attributes."""
    filename: str = Field(..., min_length=1, max_length=500)


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    content: str = Field(..., min_length=1)
    doc_metadata: Optional[dict[str, Any]] = None


class DocumentUpload(BaseModel):
    """Schema for document upload with file content."""
    file_content: str
    filename: str
    doc_metadata: Optional[dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: int
    owner_id: int
    ingestion_status: str
    doc_metadata: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

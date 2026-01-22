"""Document management endpoints for RAG system."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse
from app.api.dependencies import get_current_active_user
from app.services.rag_service import rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a new document for RAG ingestion."""
    try:
        new_document = Document(
            owner_id=current_user.id,
            filename=document_data.filename,
            content=document_data.content,
            doc_metadata=document_data.doc_metadata,
            ingestion_status="pending"
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        logger.info(f"Document created: {new_document.filename} (ID: {new_document.id})")
        return new_document

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document"
        )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a document file."""
    try:
        content = await file.read()
        content_str = content.decode('utf-8')

        new_document = Document(
            owner_id=current_user.id,
            filename=file.filename,
            content=content_str,
            doc_metadata={"content_type": file.content_type, "size": len(content)},
            ingestion_status="pending"
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        logger.info(f"Document uploaded: {new_document.filename}")
        return new_document

    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all documents for current user."""
    try:
        result = await db.execute(
            select(Document)
            .where(Document.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()
        return documents

    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific document."""
    try:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document."""
    try:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        await db.delete(document)
        await db.commit()

        logger.info(f"Document deleted: {document.filename} (ID: {document.id})")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger ingestion process for all pending documents."""
    try:
        result = await db.execute(
            select(Document).where(
                Document.owner_id == current_user.id,
                Document.ingestion_status == "pending"
            )
        )
        pending_documents = result.scalars().all()

        if not pending_documents:
            return {"message": "No pending documents to ingest"}

        documents_data = [
            {"id": doc.id, "filename": doc.filename, "content": doc.content}
            for doc in pending_documents
        ]

        rag_service.build_index(documents_data)

        for doc in pending_documents:
            doc.ingestion_status = "completed"

        await db.commit()

        logger.info(f"Ingested {len(pending_documents)} documents for user {current_user.id}")
        return {
            "message": f"Successfully ingested {len(pending_documents)} documents",
            "count": len(pending_documents)
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error ingesting documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest documents"
        )

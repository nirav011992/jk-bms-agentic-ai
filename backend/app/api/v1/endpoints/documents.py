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
from app.utils.document_processor import document_processor

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new document with text content directly (for plain text submissions)."""
    try:
        # Validate content
        if not document_data.content or not document_data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )

        # Check for null bytes (invalid UTF-8)
        if '\x00' in document_data.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content contains invalid characters. If uploading a PDF or binary file, please use the /upload endpoint instead."
            )

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

    except HTTPException:
        raise
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
    """Upload a document file and extract text content."""
    try:
        # Read file content
        file_content = await file.read()

        # Process document based on file type
        try:
            extracted_text, file_format = document_processor.process_document(
                file_content,
                file.filename,
                file.content_type
            )
        except ValueError as ve:
            logger.warning(f"Document processing failed: {str(ve)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )

        # Validate extracted text
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content could be extracted from the document"
            )

        # Create document record
        new_document = Document(
            owner_id=current_user.id,
            filename=file.filename,
            content=extracted_text,
            doc_metadata={
                "content_type": file.content_type,
                "size": len(file_content),
                "format": file_format,
                "text_length": len(extracted_text)
            },
            ingestion_status="pending"
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        logger.info(
            f"Document uploaded and processed: {new_document.filename} "
            f"(format: {file_format}, text length: {len(extracted_text)})"
        )
        return new_document

    except HTTPException:
        raise
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


@router.post("/{document_id}/ingest", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger ingestion process for a single document."""
    try:
        # Get the document
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

        if document.ingestion_status == "completed":
            logger.info(f"Document {document_id} already ingested")
            return document

        # Process the document
        documents_data = [
            {"id": document.id, "filename": document.filename, "content": document.content}
        ]

        rag_service.build_index(documents_data)

        # Update status
        document.ingestion_status = "completed"
        await db.commit()
        await db.refresh(document)

        logger.info(f"Ingested document: {document.filename} (ID: {document.id})")
        return document

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error ingesting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest document"
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

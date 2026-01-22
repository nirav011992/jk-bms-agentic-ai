"""Book management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookSummaryResponse
from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.services.llama_service import llama_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new book (Admin only)."""
    try:
        summary = None
        if book_data.content and not book_data.summary:
            summary = await llama_service.generate_book_summary(
                book_data.content,
                book_data.title,
                book_data.author
            )
        else:
            summary = book_data.summary

        new_book = Book(
            title=book_data.title,
            author=book_data.author,
            genre=book_data.genre,
            year_published=book_data.year_published,
            content=book_data.content,
            summary=summary
        )

        db.add(new_book)
        await db.commit()
        await db.refresh(new_book)

        logger.info(f"Book created: {new_book.title} (ID: {new_book.id})")
        return new_book

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book"
        )


@router.get("/", response_model=List[BookResponse])
async def get_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = None,
    author: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all books with optional filters."""
    try:
        query = select(Book)

        if genre:
            query = query.where(Book.genre == genre)
        if author:
            query = query.where(Book.author.ilike(f"%{author}%"))

        query = query.offset(skip).limit(limit).order_by(desc(Book.created_at))

        result = await db.execute(query)
        books = result.scalars().all()

        return books

    except Exception as e:
        logger.error(f"Error retrieving books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve books"
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific book by ID."""
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        return book

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve book"
        )


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a book (Admin only)."""
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        update_data = book_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(book, field, value)

        await db.commit()
        await db.refresh(book)

        logger.info(f"Book updated: {book.title} (ID: {book.id})")
        return book

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update book"
        )


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a book (Admin only)."""
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        await db.delete(book)
        await db.commit()

        logger.info(f"Book deleted: {book.title} (ID: {book.id})")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete book"
        )


@router.get("/{book_id}/summary", response_model=BookSummaryResponse)
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get book summary with aggregated ratings and reviews."""
    try:
        result = await db.execute(
            select(Book).options(selectinload(Book.reviews)).where(Book.id == book_id)
        )
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        reviews = book.reviews
        total_reviews = len(reviews)
        average_rating = None

        if total_reviews > 0:
            average_rating = sum(r.rating for r in reviews) / total_reviews

            review_data = [
                {"review_text": r.review_text, "rating": r.rating}
                for r in reviews
            ]
            review_summary = await llama_service.generate_review_summary(review_data)
        else:
            review_summary = "No reviews available yet."

        return BookSummaryResponse(
            book=book,
            average_rating=average_rating,
            total_reviews=total_reviews,
            summary=review_summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating book summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate book summary"
        )


@router.post("/generate-summary")
async def generate_book_summary(
    title: str,
    author: str,
    content: str,
    current_user: User = Depends(get_current_active_user)
):
    """Generate a summary for given book content."""
    try:
        summary = await llama_service.generate_book_summary(content, title, author)
        return {"summary": summary}

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary"
        )

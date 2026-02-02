"""Book recommendation endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.book import Book
from app.schemas.book import BookResponse
from app.api.dependencies import get_current_active_user
from app.ml.recommendation_model import recommendation_model
from app.ml.model_initializer import retrain_recommendation_model
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/train")
async def train_recommendation_model(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger recommendation model training with current data.

    Note: The model is automatically trained on application startup.
    Use this endpoint to retrain after significant data changes.
    """
    try:
        # Use the centralized training function
        training_stats = await retrain_recommendation_model(db)

        if training_stats["content_trained"] or training_stats["collaborative_trained"]:
            logger.info(f"Manual model training completed: {training_stats}")
            return {
                "message": "Model trained successfully",
                "books_count": training_stats["books_count"],
                "reviews_count": training_stats["reviews_count"],
                "content_trained": training_stats["content_trained"],
                "collaborative_trained": training_stats["collaborative_trained"],
                "errors": training_stats["errors"] if training_stats["errors"] else None
            }
        else:
            logger.warning(f"Model training completed with errors: {training_stats}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to train model: {training_stats['errors']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train recommendation model: {str(e)}"
        )


@router.get("/", response_model=List[BookResponse])
async def get_recommendations(
    book_id: Optional[int] = Query(None, description="Book ID for content-based recommendations"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get book recommendations for the current user.

    Uses hybrid approach combining:
    - Content-based filtering (if book_id provided)
    - Collaborative filtering (based on user's ratings)
    """
    try:
        recommendations = recommendation_model.get_hybrid_recommendations(
            user_id=current_user.id,
            book_id=book_id,
            n_recommendations=limit
        )

        if not recommendations:
            result = await db.execute(
                select(Book).order_by(Book.created_at.desc()).limit(limit)
            )
            books = result.scalars().all()
            return books

        book_ids = [rec.get('id', rec.get('book_id')) for rec in recommendations]

        result = await db.execute(
            select(Book).where(Book.id.in_(book_ids))
        )
        books = result.scalars().all()

        book_map = {book.id: book for book in books}
        sorted_books = [book_map[book_id] for book_id in book_ids if book_id in book_map]

        logger.info(f"Generated {len(sorted_books)} recommendations for user {current_user.id}")
        return sorted_books

    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.get("/similar/{book_id}", response_model=List[BookResponse])
async def get_similar_books(
    book_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get books similar to a specific book."""
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        recommendations = recommendation_model.get_content_based_recommendations(
            book_id=book_id,
            n_recommendations=limit
        )

        if not recommendations:
            return []

        book_ids = [rec['id'] for rec in recommendations]

        result = await db.execute(
            select(Book).where(Book.id.in_(book_ids))
        )
        similar_books = result.scalars().all()

        logger.info(f"Found {len(similar_books)} similar books for book {book_id}")
        return similar_books

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get similar books"
        )

"""Review management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.models.borrow import Borrow
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.api.dependencies import get_current_active_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new review for a book."""
    try:
        result = await db.execute(select(Book).where(Book.id == review_data.book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        existing_review = await db.execute(
            select(Review).where(
                and_(
                    Review.book_id == review_data.book_id,
                    Review.user_id == current_user.id
                )
            )
        )
        if existing_review.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this book"
            )

        # Check if user has borrowed this book (requirement: can only review borrowed books)
        borrow_check = await db.execute(
            select(Borrow).where(
                and_(
                    Borrow.user_id == current_user.id,
                    Borrow.book_id == review_data.book_id
                )
            )
        )
        if not borrow_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only review books you have borrowed"
            )

        new_review = Review(
            book_id=review_data.book_id,
            user_id=current_user.id,
            review_text=review_data.review_text,
            rating=review_data.rating
        )

        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)

        # Perform sentiment analysis asynchronously (don't wait for it)
        try:
            from app.services.huggingface_service import huggingface_service
            sentiment_score = await huggingface_service.analyze_sentiment(
                review_text=review_data.review_text,
                rating=review_data.rating
            )
            new_review.sentiment_score = sentiment_score
            await db.commit()
            await db.refresh(new_review)
            logger.info(f"Sentiment score {sentiment_score} calculated for review {new_review.id}")
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment, continuing without it: {str(e)}")
            # Continue even if sentiment analysis fails

        logger.info(f"Review created for book {review_data.book_id} by user {current_user.id}")
        return new_review

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )


@router.get("/book/{book_id}", response_model=List[ReviewResponse])
async def get_book_reviews(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all reviews for a specific book (public endpoint)."""
    try:
        result = await db.execute(
            select(Review)
            .where(Review.book_id == book_id)
            .offset(skip)
            .limit(limit)
            .order_by(Review.created_at.desc())
        )
        reviews = result.scalars().all()
        logger.info(f"Retrieved {len(reviews)} reviews for book {book_id}")
        return reviews

    except Exception as e:
        logger.error(f"Error retrieving reviews for book {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reviews: {str(e)}"
        )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a review (only by the review owner)."""
    try:
        result = await db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        if review.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this review"
            )

        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)

        await db.commit()
        await db.refresh(review)

        logger.info(f"Review updated: ID {review.id}")
        return review

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a review (only by the review owner)."""
    try:
        result = await db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        if review.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this review"
            )

        await db.delete(review)
        await db.commit()

        logger.info(f"Review deleted: ID {review.id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete review"
        )

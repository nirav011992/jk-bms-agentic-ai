"""
Recommendation model initialization and training utilities.
Handles automatic training on application startup.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.book import Book
from app.models.review import Review
from app.ml.recommendation_model import recommendation_model
from app.core.logging import get_logger

logger = get_logger(__name__)


async def train_recommendation_model_on_startup(db: AsyncSession) -> dict:
    """
    Train the recommendation model with existing data from the database.

    This function is called during application startup to ensure the
    recommendation model is ready to serve predictions.

    Args:
        db: Database session

    Returns:
        Dictionary with training statistics

    Best Practices:
    - Non-blocking: Doesn't prevent app startup if training fails
    - Graceful fallback: App continues working even if model isn't trained
    - Detailed logging: Tracks success/failure for debugging
    """
    training_stats = {
        "content_trained": False,
        "collaborative_trained": False,
        "books_count": 0,
        "reviews_count": 0,
        "errors": []
    }

    try:
        logger.info("Starting recommendation model training on startup...")

        # Train content-based model
        await _train_content_based_model(db, training_stats)

        # Train collaborative filtering model
        await _train_collaborative_model(db, training_stats)

        # Log final status
        if training_stats["content_trained"] and training_stats["collaborative_trained"]:
            logger.info(
                f"Recommendation model trained successfully: "
                f"{training_stats['books_count']} books, "
                f"{training_stats['reviews_count']} reviews"
            )
        elif training_stats["content_trained"] or training_stats["collaborative_trained"]:
            logger.warning(
                f"Recommendation model partially trained: "
                f"Content={training_stats['content_trained']}, "
                f"Collaborative={training_stats['collaborative_trained']}"
            )
        else:
            logger.warning(
                "Recommendation model not trained. "
                "Recommendations will fall back to newest books."
            )

    except Exception as e:
        logger.error(f"Unexpected error during model training: {str(e)}")
        training_stats["errors"].append(f"Unexpected error: {str(e)}")

    return training_stats


async def _train_content_based_model(db: AsyncSession, stats: dict) -> None:
    """
    Train the content-based recommendation model.

    Args:
        db: Database session
        stats: Dictionary to store training statistics
    """
    try:
        # Fetch all books from database
        books_result = await db.execute(select(Book))
        books = books_result.scalars().all()

        if not books:
            logger.warning("No books found in database. Skipping content-based training.")
            stats["errors"].append("No books available for content-based training")
            return

        # Prepare book data for training
        books_data = [
            {
                "id": book.id,
                "title": book.title or "",
                "author": book.author or "",
                "genre": book.genre or "",
                "summary": book.summary or ""
            }
            for book in books
        ]

        # Train the model
        recommendation_model.train_content_based(books_data)

        stats["content_trained"] = True
        stats["books_count"] = len(books_data)
        logger.info(f"Content-based model trained with {len(books_data)} books")

    except Exception as e:
        logger.error(f"Failed to train content-based model: {str(e)}")
        stats["errors"].append(f"Content-based training failed: {str(e)}")


async def _train_collaborative_model(db: AsyncSession, stats: dict) -> None:
    """
    Train the collaborative filtering recommendation model.

    Args:
        db: Database session
        stats: Dictionary to store training statistics
    """
    try:
        # Fetch all reviews from database
        reviews_result = await db.execute(select(Review))
        reviews = reviews_result.scalars().all()

        if not reviews:
            logger.warning("No reviews found in database. Skipping collaborative filtering training.")
            stats["errors"].append("No reviews available for collaborative training")
            return

        # Prepare review data for training
        reviews_data = [
            {
                "user_id": review.user_id,
                "book_id": review.book_id,
                "rating": review.rating
            }
            for review in reviews
        ]

        # Train the model
        recommendation_model.train_collaborative(reviews_data)

        stats["collaborative_trained"] = True
        stats["reviews_count"] = len(reviews_data)
        logger.info(f"Collaborative filtering model trained with {len(reviews_data)} reviews")

    except Exception as e:
        logger.error(f"Failed to train collaborative filtering model: {str(e)}")
        stats["errors"].append(f"Collaborative training failed: {str(e)}")


async def retrain_recommendation_model(db: AsyncSession) -> dict:
    """
    Retrain the recommendation model with latest data.

    This can be called manually or triggered by background tasks
    when new data is added (e.g., after book additions or reviews).

    Args:
        db: Database session

    Returns:
        Dictionary with training statistics
    """
    logger.info("Retraining recommendation model with latest data...")
    return await train_recommendation_model_on_startup(db)

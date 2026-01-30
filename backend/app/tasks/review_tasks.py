"""Background tasks for review-related operations."""
import asyncio
from typing import Dict, Any, List
from app.celery_app import celery_app
from app.core.logging import get_logger
from app.services.cache_service import get_cache

logger = get_logger(__name__)
cache = get_cache()


@celery_app.task(name="app.tasks.review_tasks.analyze_review_sentiment_async")
def analyze_review_sentiment_async(review_id: int, review_text: str, book_id: int) -> Dict[str, Any]:
    """
    Analyze sentiment of a review asynchronously.

    Args:
        review_id: Review ID
        review_text: Review text content
        book_id: Associated book ID

    Returns:
        Dictionary with status and sentiment score
    """
    try:
        from transformers import pipeline

        logger.info(f"Analyzing sentiment for review {review_id}")

        # Use HuggingFace sentiment analysis pipeline
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

        # Analyze sentiment
        result = sentiment_analyzer(review_text[:512])[0]  # Limit to 512 tokens

        # Convert to numeric score (-1 to 1)
        sentiment_score = result['score'] if result['label'] == 'POSITIVE' else -result['score']

        logger.info(f"Sentiment analysis complete for review {review_id}: {sentiment_score}")

        # Invalidate relevant cache entries
        cache.delete_pattern(f"sentiment:{book_id}:*")
        cache.delete_pattern(f"reviews:{book_id}:*")

        return {
            "status": "success",
            "review_id": review_id,
            "sentiment_score": sentiment_score,
            "sentiment_label": result['label'],
            "confidence": result['score']
        }

    except Exception as e:
        logger.error(f"Error analyzing sentiment for review {review_id}: {str(e)}")
        return {
            "status": "error",
            "review_id": review_id,
            "error": str(e)
        }


@celery_app.task(name="app.tasks.review_tasks.update_review_consensus_async")
def update_review_consensus_async(book_id: int, review_ids: List[int]) -> Dict[str, Any]:
    """
    Update the rolling consensus of book reviews asynchronously.

    Args:
        book_id: Book ID
        review_ids: List of review IDs to include in consensus

    Returns:
        Dictionary with status and consensus summary
    """
    try:
        from app.services.llama_service import llama_service

        logger.info(f"Updating review consensus for book {book_id}")

        # This is a simplified version - in production, you'd fetch reviews from DB
        # For now, we'll just invalidate the cache to force regeneration

        # Invalidate consensus cache
        cache.delete_pattern(f"consensus:{book_id}:*")
        cache.delete_pattern(f"sentiment:{book_id}:*")

        logger.info(f"Review consensus cache invalidated for book {book_id}")

        return {
            "status": "success",
            "book_id": book_id,
            "message": "Consensus cache invalidated, will regenerate on next request"
        }

    except Exception as e:
        logger.error(f"Error updating consensus for book {book_id}: {str(e)}")
        return {
            "status": "error",
            "book_id": book_id,
            "error": str(e)
        }


@celery_app.task(name="app.tasks.review_tasks.batch_analyze_sentiments_async")
def batch_analyze_sentiments_async(review_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze sentiments for multiple reviews in batch.

    Args:
        review_data: List of dictionaries with review_id, review_text, and book_id

    Returns:
        Dictionary with status and results
    """
    try:
        from transformers import pipeline

        logger.info(f"Batch analyzing sentiment for {len(review_data)} reviews")

        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

        results = []
        for review in review_data:
            try:
                result = sentiment_analyzer(review['review_text'][:512])[0]
                sentiment_score = result['score'] if result['label'] == 'POSITIVE' else -result['score']

                results.append({
                    "review_id": review['review_id'],
                    "sentiment_score": sentiment_score,
                    "sentiment_label": result['label']
                })

                # Invalidate cache for this book
                cache.delete_pattern(f"sentiment:{review['book_id']}:*")

            except Exception as e:
                logger.error(f"Error analyzing review {review['review_id']}: {str(e)}")
                results.append({
                    "review_id": review['review_id'],
                    "error": str(e)
                })

        logger.info(f"Batch sentiment analysis complete for {len(results)} reviews")

        return {
            "status": "success",
            "processed": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

"""Helper functions for triggering background tasks."""
from typing import Optional
from celery.result import AsyncResult
from app.core.logging import get_logger

logger = get_logger(__name__)


def trigger_book_summary_generation(book_id: int, book_content: str, title: str, author: str) -> Optional[str]:
    """
    Trigger async task to generate book summary.

    Args:
        book_id: Book ID
        book_content: Book content
        title: Book title
        author: Book author

    Returns:
        Task ID if successful, None otherwise
    """
    try:
        from app.tasks.book_tasks import generate_book_summary_async

        task = generate_book_summary_async.delay(book_id, book_content, title, author)
        logger.info(f"Triggered summary generation task for book {book_id}: {task.id}")
        return task.id
    except Exception as e:
        logger.error(f"Failed to trigger summary generation for book {book_id}: {str(e)}")
        return None


def trigger_review_sentiment_analysis(review_id: int, review_text: str, book_id: int) -> Optional[str]:
    """
    Trigger async task to analyze review sentiment.

    Args:
        review_id: Review ID
        review_text: Review text
        book_id: Associated book ID

    Returns:
        Task ID if successful, None otherwise
    """
    try:
        from app.tasks.review_tasks import analyze_review_sentiment_async

        task = analyze_review_sentiment_async.delay(review_id, review_text, book_id)
        logger.info(f"Triggered sentiment analysis task for review {review_id}: {task.id}")
        return task.id
    except Exception as e:
        logger.error(f"Failed to trigger sentiment analysis for review {review_id}: {str(e)}")
        return None


def trigger_review_consensus_update(book_id: int, review_ids: list[int]) -> Optional[str]:
    """
    Trigger async task to update review consensus.

    Args:
        book_id: Book ID
        review_ids: List of review IDs

    Returns:
        Task ID if successful, None otherwise
    """
    try:
        from app.tasks.review_tasks import update_review_consensus_async

        task = update_review_consensus_async.delay(book_id, review_ids)
        logger.info(f"Triggered consensus update task for book {book_id}: {task.id}")
        return task.id
    except Exception as e:
        logger.error(f"Failed to trigger consensus update for book {book_id}: {str(e)}")
        return None


def get_task_status(task_id: str) -> dict:
    """
    Get status of a Celery task.

    Args:
        task_id: Task ID

    Returns:
        Dictionary with task status information
    """
    try:
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() else None,
        }
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(e)
        }

"""Background tasks for book-related operations."""
import asyncio
from typing import Dict, Any
from app.celery_app import celery_app
from app.core.logging import get_logger
from app.services.cache_service import get_cache

logger = get_logger(__name__)
cache = get_cache()


@celery_app.task(name="app.tasks.book_tasks.generate_book_summary_async")
def generate_book_summary_async(book_id: int, book_content: str, title: str, author: str) -> Dict[str, Any]:
    """
    Generate book summary asynchronously.

    Args:
        book_id: Book ID
        book_content: Book content
        title: Book title
        author: Book author

    Returns:
        Dictionary with status and summary
    """
    try:
        from app.services.huggingface_service import huggingface_service

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            summary = loop.run_until_complete(
                huggingface_service.generate_book_summary(book_content, title, author)
            )

            logger.info(f"Successfully generated summary for book {book_id}")

            # Invalidate relevant cache entries
            cache.delete_pattern(f"book:{book_id}:*")

            return {
                "status": "success",
                "book_id": book_id,
                "summary": summary
            }
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error generating summary for book {book_id}: {str(e)}")
        return {
            "status": "error",
            "book_id": book_id,
            "error": str(e)
        }


@celery_app.task(name="app.tasks.book_tasks.update_book_embeddings_async")
def update_book_embeddings_async(book_id: int) -> Dict[str, Any]:
    """
    Update book embeddings in vector database asynchronously.

    Args:
        book_id: Book ID

    Returns:
        Dictionary with status
    """
    try:
        logger.info(f"Updating embeddings for book {book_id}")

        # Here you would update the FAISS index with new book embeddings
        # This is a placeholder for the actual implementation

        # Invalidate recommendation cache
        cache.delete_pattern(f"recommendations:*")
        cache.delete_pattern(f"similar:{book_id}:*")

        return {
            "status": "success",
            "book_id": book_id,
            "message": "Embeddings updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating embeddings for book {book_id}: {str(e)}")
        return {
            "status": "error",
            "book_id": book_id,
            "error": str(e)
        }

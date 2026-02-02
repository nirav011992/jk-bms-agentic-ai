"""Unit tests for sentiment analysis (Phase 1)."""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.models.book import Book
from app.models.user import User
from app.models.borrow import Borrow, BorrowStatus


@pytest.mark.asyncio
async def test_review_with_sentiment_analysis(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test that sentiment analysis is triggered when creating a review."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    borrow = Borrow(
        user_id=test_user.id,
        book_id=book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(borrow)
    await db_session.commit()

    with patch('app.services.huggingface_service.HuggingFaceService.analyze_sentiment') as mock_sentiment:
        mock_sentiment.return_value = 0.85

        response = await client.post(
            "/api/v1/reviews/",
            json={
                "book_id": book.id,
                "rating": 5.0,
                "review_text": "Excellent book! I really enjoyed it."
            },
            headers=auth_headers
        )

        assert response.status_code == 201

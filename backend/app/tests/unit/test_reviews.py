"""Unit tests for review endpoints."""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.review import Review
from app.models.user import User
from app.models.borrow import Borrow, BorrowStatus


@pytest.mark.asyncio
async def test_create_review(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test creating a review for a book."""
    # Create a book first
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    # Create a borrow record (requirement for creating reviews)
    borrow = Borrow(
        user_id=test_user.id,
        book_id=book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(borrow)
    await db_session.commit()

    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": book.id,
            "rating": 5.0,
            "review_text": "Excellent book! Really enjoyed reading it."
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5.0
    assert data["review_text"] == "Excellent book! Really enjoyed reading it."
    assert data["book_id"] == book.id
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_create_review_nonexistent_book(
    client: AsyncClient,
    auth_headers: dict
):
    """Test creating a review for non-existent book."""
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": 99999,
            "rating": 5.0,
            "review_text": "Test review comment here"
        },
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "Book not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_duplicate_review(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test creating duplicate review for same book."""
    # Create a book
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    # Create first review
    review = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=5.0,
        review_text="First review here"
    )
    db_session.add(review)
    await db_session.commit()

    # Try to create second review
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": book.id,
            "rating": 4.0,
            "review_text": "Second review here"
        },
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already reviewed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_review_invalid_rating(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test creating review with invalid rating."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    # Try rating > 5
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": book.id,
            "rating": 6.0,
            "review_text": "Invalid rating test"
        },
        headers=auth_headers
    )
    assert response.status_code == 422

    # Try rating < 1
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": book.id,
            "rating": 0.5,
            "review_text": "Invalid rating test"
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_short_text(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test creating review with too short text."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    response = await client.post(
        "/api/v1/reviews/",
        json={
            "book_id": book.id,
            "rating": 5.0,
            "review_text": "Short"  # Less than 10 characters
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_book_reviews(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test getting all reviews for a book."""
    # Create a book
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    # Create review
    review = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=5.0,
        review_text="Great book to read!"
    )
    db_session.add(review)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/reviews/book/{book.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["book_id"] == book.id


@pytest.mark.asyncio
async def test_update_review(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test updating a review."""
    book = Book(title="Test Book", author="Author", genre="Fiction", year_published=2024)
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    review = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=3.0,
        review_text="Initial review comment"
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    response = await client.put(
        f"/api/v1/reviews/{review.id}",
        json={
            "rating": 5.0,
            "review_text": "Updated review - much better now!"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5.0
    assert data["review_text"] == "Updated review - much better now!"


@pytest.mark.asyncio
async def test_update_review_not_owner(
    client: AsyncClient,
    admin_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test updating someone else's review (should fail)."""
    book = Book(title="Test Book", author="Author", genre="Fiction", year_published=2024)
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    review = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=3.0,
        review_text="User's review text"
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    response = await client.put(
        f"/api/v1/reviews/{review.id}",
        json={
            "rating": 1.0,
            "review_text": "Trying to change review"
        },
        headers=admin_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_review(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession
):
    """Test deleting a review."""
    book = Book(title="Test Book", author="Author", genre="Fiction", year_published=2024)
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    review = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=4.0,
        review_text="Test review text"
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    response = await client.delete(f"/api/v1/reviews/{review.id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_review_not_found(
    client: AsyncClient,
    auth_headers: dict
):
    """Test deleting non-existent review."""
    response = await client.delete("/api/v1/reviews/99999", headers=auth_headers)
    assert response.status_code == 404

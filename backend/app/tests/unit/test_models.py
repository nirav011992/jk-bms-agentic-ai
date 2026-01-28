"""Unit tests for database models."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.book import Book
from app.models.review import Review
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_user_model(db_session: AsyncSession):
    """Test creating a user model."""
    user = User(
        email="testmodel@example.com",
        username="testmodel",
        hashed_password=get_password_hash("Test123456"),
        full_name="Test Model User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "testmodel@example.com"
    assert user.username == "testmodel"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_book_model(db_session: AsyncSession):
    """Test creating a book model."""
    book = Book(
        title="Test Book Model",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
        summary="Test summary",
        content="Test content"
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    assert book.id is not None
    assert book.title == "Test Book Model"
    assert book.author == "Test Author"
    assert book.genre == "Fiction"
    assert book.year_published == 2024
    assert book.created_at is not None


@pytest.mark.asyncio
async def test_create_review_model(
    db_session: AsyncSession,
    test_user: User
):
    """Test creating a review model."""
    # Create book
    book = Book(
        title="Book for Review",
        author="Author",
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
    await db_session.refresh(review)

    assert review.id is not None
    assert review.book_id == book.id
    assert review.user_id == test_user.id
    assert review.rating == 5.0
    assert review.review_text == "Great book to read!"
    assert review.created_at is not None


@pytest.mark.asyncio
async def test_user_book_review_relationship(
    db_session: AsyncSession,
    test_user: User
):
    """Test relationships between user, book, and review."""
    # Create book
    book = Book(
        title="Relationship Test Book",
        author="Author",
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
        rating=4.0,
        review_text="Good read overall"
    )
    db_session.add(review)
    await db_session.commit()

    # Query review with relationships
    result = await db_session.execute(
        select(Review).where(Review.id == review.id)
    )
    fetched_review = result.scalar_one()

    assert fetched_review.book_id == book.id
    assert fetched_review.user_id == test_user.id


@pytest.mark.asyncio
async def test_user_default_role(db_session: AsyncSession):
    """Test that user has default role."""
    user = User(
        email="defaultrole@example.com",
        username="defaultrole",
        hashed_password=get_password_hash("Test123456"),
        full_name="Default Role User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.role == UserRole.USER
    assert user.is_active is True


@pytest.mark.asyncio
async def test_book_without_optional_fields(db_session: AsyncSession):
    """Test creating book without optional fields."""
    book = Book(
        title="Minimal Book",
        author="Minimal Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    assert book.id is not None
    assert book.summary is None
    assert book.content is None


@pytest.mark.asyncio
async def test_review_rating_boundaries(
    db_session: AsyncSession,
    test_user: User
):
    """Test review rating with boundary values."""
    book = Book(
        title="Rating Test Book",
        author="Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    # Test minimum rating
    review_min = Review(
        book_id=book.id,
        user_id=test_user.id,
        rating=1.0,
        review_text="Minimum rating test"
    )
    db_session.add(review_min)
    await db_session.commit()
    await db_session.refresh(review_min)

    assert review_min.rating == 1.0


@pytest.mark.asyncio
async def test_user_unique_email(db_session: AsyncSession):
    """Test that email must be unique."""
    user1 = User(
        email="unique@example.com",
        username="user1",
        hashed_password=get_password_hash("Test123456"),
        full_name="User 1"
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="unique@example.com",  # Same email
        username="user2",
        hashed_password=get_password_hash("Test123456"),
        full_name="User 2"
    )
    db_session.add(user2)

    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_unique_username(db_session: AsyncSession):
    """Test that username must be unique."""
    user1 = User(
        email="email1@example.com",
        username="uniqueuser",
        hashed_password=get_password_hash("Test123456"),
        full_name="User 1"
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="email2@example.com",
        username="uniqueuser",  # Same username
        hashed_password=get_password_hash("Test123456"),
        full_name="User 2"
    )
    db_session.add(user2)

    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.commit()


@pytest.mark.asyncio
async def test_book_timestamps(db_session: AsyncSession):
    """Test that book timestamps are set correctly."""
    book = Book(
        title="Timestamp Test",
        author="Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    assert book.created_at is not None
    assert book.updated_at is not None

    # Update book
    original_created = book.created_at
    book.title = "Updated Title"
    await db_session.commit()
    await db_session.refresh(book)

    assert book.created_at == original_created
    assert book.updated_at >= original_created

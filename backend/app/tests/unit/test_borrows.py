"""Unit tests for borrow/return system (Phase 1)."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.borrow import Borrow, BorrowStatus
from app.models.user import User


@pytest_asyncio.fixture
async def test_book(db_session: AsyncSession) -> Book:
    """Create a test book."""
    book = Book(
        title="Test Book for Borrowing",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
        summary="A test book summary"
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)
    return book


@pytest.mark.asyncio
async def test_borrow_book_success(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    test_book: Book
):
    """Test successfully borrowing a book."""
    response = await client.post(
        f"/api/v1/borrows/{test_book.id}/borrow",
        json={"book_id": test_book.id, "loan_period_days": 14},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["book_id"] == test_book.id
    assert data["user_id"] == test_user.id
    assert data["status"] in ["ACTIVE", "active"]
    assert "borrow_date" in data
    assert "due_date" in data


@pytest.mark.asyncio
async def test_borrow_book_already_borrowed(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    test_book: Book,
    db_session: AsyncSession
):
    """Test borrowing a book that's already borrowed."""
    existing_borrow = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(existing_borrow)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/borrows/{test_book.id}/borrow",
        json={"book_id": test_book.id, "loan_period_days": 14},
        headers=auth_headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_borrow_nonexistent_book(
    client: AsyncClient,
    auth_headers: dict
):
    """Test borrowing a book that doesn't exist."""
    response = await client.post(
        "/api/v1/borrows/99999/borrow",
        json={"book_id": 99999, "loan_period_days": 14},
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_return_book_success(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    test_book: Book,
    db_session: AsyncSession
):
    """Test successfully returning a borrowed book."""
    borrow = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow() - timedelta(days=7),
        due_date=datetime.utcnow() + timedelta(days=7),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(borrow)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/borrows/{test_book.id}/return",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["RETURNED", "returned"]
    assert "return_date" in data


@pytest.mark.asyncio
async def test_return_book_not_borrowed(
    client: AsyncClient,
    auth_headers: dict,
    test_book: Book
):
    """Test returning a book that wasn't borrowed."""
    response = await client.post(
        f"/api/v1/borrows/{test_book.id}/return",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_check_book_availability_available(
    client: AsyncClient,
    auth_headers: dict,
    test_book: Book
):
    """Test checking availability of an available book."""
    response = await client.get(
        f"/api/v1/borrows/book/{test_book.id}/availability",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True
    assert data["book_id"] == test_book.id


@pytest.mark.asyncio
async def test_check_book_availability_borrowed(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    test_book: Book,
    db_session: AsyncSession
):
    """Test checking availability of a borrowed book."""
    borrow = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(borrow)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/borrows/book/{test_book.id}/availability",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False


@pytest.mark.asyncio
async def test_get_user_borrows(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    test_book: Book,
    db_session: AsyncSession
):
    """Test getting user's borrow history."""
    borrow1 = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow() - timedelta(days=10),
        due_date=datetime.utcnow() + timedelta(days=4),
        status=BorrowStatus.ACTIVE
    )
    borrow2 = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow() - timedelta(days=30),
        due_date=datetime.utcnow() - timedelta(days=16),
        return_date=datetime.utcnow() - timedelta(days=15),
        status=BorrowStatus.RETURNED
    )
    db_session.add_all([borrow1, borrow2])
    await db_session.commit()

    response = await client.get(
        "/api/v1/borrows/history",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["borrows"]) == 2


@pytest.mark.asyncio
async def test_get_overdue_borrows(
    client: AsyncClient,
    admin_headers: dict,
    test_user: User,
    test_book: Book,
    db_session: AsyncSession
):
    """Test getting overdue borrows (admin only)."""
    overdue_borrow = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=6),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(overdue_borrow)
    await db_session.commit()

    response = await client.get(
        "/api/v1/borrows/overdue",
        headers=admin_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_borrow_model_is_overdue_property(db_session: AsyncSession, test_user: User, test_book: Book):
    """Test the is_overdue property of Borrow model."""
    overdue_borrow = Borrow(
        user_id=test_user.id,
        book_id=test_book.id,
        borrow_date=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=5),
        status=BorrowStatus.ACTIVE
    )
    db_session.add(overdue_borrow)
    await db_session.commit()

    assert overdue_borrow.is_overdue is True


@pytest.mark.asyncio
async def test_borrow_calculate_due_date():
    """Test the calculate_due_date static method."""
    due_days = 14
    borrow_date = datetime.utcnow()
    due_date = Borrow.calculate_due_date(borrow_date=borrow_date, loan_period_days=due_days)
    expected_date = borrow_date + timedelta(days=due_days)
    assert abs((due_date - expected_date).total_seconds()) < 60

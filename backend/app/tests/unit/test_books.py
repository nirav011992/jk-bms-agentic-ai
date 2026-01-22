"""Unit tests for book endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book


@pytest.mark.asyncio
async def test_create_book(client: AsyncClient, admin_headers: dict):
    """Test book creation by admin."""
    response = await client.post(
        "/api/v1/books/",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2024,
            "content": "This is test content for the book."
        },
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert "summary" in data


@pytest.mark.asyncio
async def test_create_book_unauthorized(client: AsyncClient, auth_headers: dict):
    """Test book creation by non-admin user (should fail)."""
    response = await client.post(
        "/api/v1/books/",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2024
        },
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_books(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test getting all books."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()

    response = await client.get("/api/v1/books/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Book"


@pytest.mark.asyncio
async def test_get_book_by_id(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Test getting a specific book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    response = await client.get(f"/api/v1/books/{book.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book.id
    assert data["title"] == "Test Book"


@pytest.mark.asyncio
async def test_update_book(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    """Test updating a book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    response = await client.put(
        f"/api/v1/books/{book.id}",
        json={"title": "Updated Title"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_book(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    """Test deleting a book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    response = await client.delete(f"/api/v1/books/{book.id}", headers=admin_headers)
    assert response.status_code == 204

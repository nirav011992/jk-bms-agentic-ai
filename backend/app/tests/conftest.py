"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash

TEST_DATABASE_URL = settings.DATABASE_TEST_URL or "postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test123456"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("Admin123456"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Test123456"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin123456"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

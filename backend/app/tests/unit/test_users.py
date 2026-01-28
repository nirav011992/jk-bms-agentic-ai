"""Unit tests for user endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_get_current_user_info(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """Test getting current user information."""
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_all_users_as_admin(
    client: AsyncClient,
    admin_headers: dict,
    test_user: User,
    test_admin: User
):
    """Test getting all users as admin."""
    response = await client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least test_user and test_admin
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_all_users_as_regular_user(
    client: AsyncClient,
    auth_headers: dict
):
    """Test getting all users as regular user (should fail)."""
    response = await client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_all_users_with_pagination(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession
):
    """Test getting users with pagination."""
    # Create additional users
    for i in range(5):
        user = User(
            email=f"user{i}@test.com",
            username=f"user{i}",
            hashed_password=get_password_hash("Test123456"),
            full_name=f"Test User {i}",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
    await db_session.commit()

    # Test pagination
    response = await client.get(
        "/api/v1/users/?skip=0&limit=3",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


@pytest.mark.asyncio
async def test_get_user_by_id_as_admin(
    client: AsyncClient,
    admin_headers: dict,
    test_user: User
):
    """Test getting specific user by ID as admin."""
    response = await client.get(
        f"/api/v1/users/{test_user.id}",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    client: AsyncClient,
    admin_headers: dict
):
    """Test getting non-existent user."""
    response = await client.get("/api/v1/users/99999", headers=admin_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_by_id_as_regular_user(
    client: AsyncClient,
    auth_headers: dict,
    test_admin: User
):
    """Test getting user by ID as regular user (should fail)."""
    response = await client.get(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_current_user(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """Test updating current user information."""
    response = await client.put(
        "/api/v1/users/me",
        json={
            "full_name": "Updated Name",
            "email": "newemail@example.com"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "newemail@example.com"


@pytest.mark.asyncio
async def test_update_current_user_password(
    client: AsyncClient,
    auth_headers: dict
):
    """Test updating current user password."""
    response = await client.put(
        "/api/v1/users/me",
        json={
            "password": "NewPassword123"
        },
        headers=auth_headers
    )
    assert response.status_code == 200

    # Try logging in with new password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "NewPassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_update_current_user_duplicate_email(
    client: AsyncClient,
    auth_headers: dict,
    test_admin: User
):
    """Test updating user with duplicate email."""
    response = await client.put(
        "/api/v1/users/me",
        json={
            "email": test_admin.email  # Try to use admin's email
        },
        headers=auth_headers
    )
    # Endpoint returns 500 for integrity error (duplicate email)
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_update_user_by_id_as_admin(
    client: AsyncClient,
    admin_headers: dict,
    test_user: User
):
    """Test updating user by ID as admin."""
    response = await client.put(
        f"/api/v1/users/{test_user.id}",
        json={
            "full_name": "Admin Updated Name",
            "is_active": False
        },
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Admin Updated Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_by_id_as_regular_user(
    client: AsyncClient,
    auth_headers: dict,
    test_admin: User
):
    """Test updating user by ID as regular user (should fail)."""
    response = await client.put(
        f"/api/v1/users/{test_admin.id}",
        json={
            "full_name": "Hacked Name"
        },
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_as_admin(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession
):
    """Test deleting user as admin."""
    # Create a user to delete
    user = User(
        email="todelete@test.com",
        username="todelete",
        hashed_password=get_password_hash("Test123456"),
        full_name="To Delete",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.delete(
        f"/api/v1/users/{user.id}",
        headers=admin_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_as_regular_user(
    client: AsyncClient,
    auth_headers: dict,
    test_admin: User
):
    """Test deleting user as regular user (should fail)."""
    response = await client.delete(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_not_found(
    client: AsyncClient,
    admin_headers: dict
):
    """Test deleting non-existent user."""
    response = await client.delete("/api/v1/users/99999", headers=admin_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_current_user_invalid_email(
    client: AsyncClient,
    auth_headers: dict
):
    """Test updating user with invalid email format."""
    response = await client.put(
        "/api/v1/users/me",
        json={
            "email": "invalid-email"
        },
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_current_user_weak_password(
    client: AsyncClient,
    auth_headers: dict
):
    """Test updating user with weak password."""
    response = await client.put(
        "/api/v1/users/me",
        json={
            "password": "weak"
        },
        headers=auth_headers
    )
    assert response.status_code == 422

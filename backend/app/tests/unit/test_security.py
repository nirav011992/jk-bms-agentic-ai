"""Unit tests for security utilities."""
import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123"
    hashed = get_password_hash(password)

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify incorrect password
    assert verify_password("WrongPassword", hashed) is False


def test_password_hash_unique():
    """Test that same password generates different hashes."""
    password = "TestPassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different due to salt
    assert hash1 != hash2

    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_create_access_token():
    """Test access token creation."""
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)

    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_access_token_with_custom_expiry():
    """Test access token with custom expiration."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=expires_delta)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test refresh token creation."""
    data = {"sub": "testuser", "user_id": 1}
    token = create_refresh_token(data)

    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_valid():
    """Test decoding valid token."""
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)

    decoded = decode_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["user_id"] == 1


def test_decode_token_invalid():
    """Test decoding invalid token."""
    invalid_token = "invalid.token.here"

    with pytest.raises(Exception):  # Should raise HTTPException
        decode_token(invalid_token)


def test_decode_token_wrong_signature():
    """Test decoding token with wrong signature."""
    # Create token with different secret
    data = {"sub": "testuser"}
    token = jwt.encode(data, "wrong-secret", algorithm=settings.ALGORITHM)

    with pytest.raises(Exception):
        decode_token(token)


def test_access_and_refresh_token_types():
    """Test that access and refresh tokens have correct types."""
    data = {"sub": "testuser"}

    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_password_empty_string():
    """Test password hashing with empty string."""
    password = ""
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True
    assert verify_password("not-empty", hashed) is False


def test_password_special_characters():
    """Test password with special characters."""
    password = "P@ssw0rd!#$%^&*()"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True
    assert verify_password("P@ssw0rd!#$%^&*()X", hashed) is False


def test_password_unicode():
    """Test password with unicode characters."""
    password = "密码Test123"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True
    assert verify_password("密码Test124", hashed) is False


def test_token_with_additional_claims():
    """Test token creation with additional custom claims."""
    data = {
        "sub": "testuser",
        "user_id": 1,
        "role": "admin",
        "email": "test@example.com"
    }
    token = create_access_token(data)

    payload = decode_token(token)
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["role"] == "admin"
    assert payload["email"] == "test@example.com"

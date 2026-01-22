"""Authentication endpoints for user login and registration."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If email or username already exists
    """
    try:
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        hashed_password = get_password_hash(user_data.password)

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered: {new_user.username} (ID: {new_user.id})")
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        result = await db.execute(
            select(User).where(User.username == credentials.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )

        logger.info(f"User logged in: {user.username} (ID: {user.id})")
        return Token(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

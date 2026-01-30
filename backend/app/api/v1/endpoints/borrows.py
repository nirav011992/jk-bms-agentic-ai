"""Borrow management endpoints for book lending."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.book import Book
from app.models.borrow import Borrow, BorrowStatus
from app.schemas.borrow import (
    BorrowCreate,
    BorrowResponse,
    BorrowWithDetails,
    BorrowHistory,
    BookAvailability
)
from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{book_id}/borrow", response_model=BorrowResponse, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    book_id: int,
    borrow_data: BorrowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Borrow a book.

    - Validates book exists
    - Checks if book is available (not already borrowed by someone else)
    - Creates borrow transaction with due date
    - Updates book status to unavailable
    """
    try:
        # Verify book exists
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Check if user already has an active borrow for this book
        existing_borrow = await db.execute(
            select(Borrow).where(
                and_(
                    Borrow.book_id == book_id,
                    Borrow.user_id == current_user.id,
                    Borrow.status == BorrowStatus.ACTIVE
                )
            )
        )
        if existing_borrow.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already borrowed this book and haven't returned it yet"
            )

        # Check if book is available (not borrowed by anyone else)
        active_borrow = await db.execute(
            select(Borrow).where(
                and_(
                    Borrow.book_id == book_id,
                    Borrow.status == BorrowStatus.ACTIVE
                )
            )
        )
        if active_borrow.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This book is currently borrowed by another user"
            )

        # Calculate due date
        borrow_date = datetime.utcnow()
        due_date = Borrow.calculate_due_date(borrow_date, borrow_data.loan_period_days)

        # Create borrow transaction
        new_borrow = Borrow(
            user_id=current_user.id,
            book_id=book_id,
            borrow_date=borrow_date,
            due_date=due_date,
            status=BorrowStatus.ACTIVE
        )

        db.add(new_borrow)
        await db.commit()
        await db.refresh(new_borrow)

        logger.info(f"Book {book_id} borrowed by user {current_user.id}, due date: {due_date}")
        return new_borrow

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error borrowing book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to borrow book"
        )


@router.post("/{book_id}/return", response_model=BorrowResponse)
async def return_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Return a borrowed book.

    - Finds active borrow transaction for current user and book
    - Updates status to RETURNED
    - Sets return_date
    """
    try:
        # Find active borrow
        result = await db.execute(
            select(Borrow).where(
                and_(
                    Borrow.book_id == book_id,
                    Borrow.user_id == current_user.id,
                    Borrow.status == BorrowStatus.ACTIVE
                )
            )
        )
        borrow = result.scalar_one_or_none()

        if not borrow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active borrow found for this book"
            )

        # Update borrow status
        borrow.return_date = datetime.utcnow()
        borrow.status = BorrowStatus.RETURNED

        await db.commit()
        await db.refresh(borrow)

        logger.info(f"Book {book_id} returned by user {current_user.id}")
        return borrow

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error returning book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to return book"
        )


@router.get("/", response_model=List[BorrowWithDetails])
async def get_my_borrows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: BorrowStatus = Query(None, description="Filter by borrow status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's borrow history with book details."""
    try:
        query = (
            select(Borrow)
            .options(
                selectinload(Borrow.book),
                selectinload(Borrow.user)
            )
            .where(Borrow.user_id == current_user.id)
        )

        if status_filter:
            query = query.where(Borrow.status == status_filter)

        query = query.order_by(Borrow.borrow_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        borrows = result.scalars().all()

        # Format response with details
        borrows_with_details = []
        for borrow in borrows:
            borrow_dict = {
                "id": borrow.id,
                "user_id": borrow.user_id,
                "book_id": borrow.book_id,
                "borrow_date": borrow.borrow_date,
                "due_date": borrow.due_date,
                "return_date": borrow.return_date,
                "status": borrow.status,
                "is_overdue": borrow.is_overdue,
                "created_at": borrow.created_at,
                "updated_at": borrow.updated_at,
                "book_title": borrow.book.title if borrow.book else None,
                "book_author": borrow.book.author if borrow.book else None,
                "user_email": borrow.user.email if borrow.user else None,
                "user_username": borrow.user.username if borrow.user else None,
            }
            borrows_with_details.append(BorrowWithDetails(**borrow_dict))

        return borrows_with_details

    except Exception as e:
        logger.error(f"Error retrieving borrows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve borrows"
        )


@router.get("/history", response_model=BorrowHistory)
async def get_borrow_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive borrow history with statistics for current user."""
    try:
        # Get all borrows for user
        result = await db.execute(
            select(Borrow)
            .options(
                selectinload(Borrow.book),
                selectinload(Borrow.user)
            )
            .where(Borrow.user_id == current_user.id)
            .order_by(Borrow.borrow_date.desc())
        )
        borrows = result.scalars().all()

        # Calculate statistics
        total_borrows = len(borrows)
        active_borrows = sum(1 for b in borrows if b.status == BorrowStatus.ACTIVE)
        returned_borrows = sum(1 for b in borrows if b.status == BorrowStatus.RETURNED)
        overdue_borrows = sum(1 for b in borrows if b.is_overdue)

        # Format borrows with details
        borrows_with_details = []
        for borrow in borrows:
            borrow_dict = {
                "id": borrow.id,
                "user_id": borrow.user_id,
                "book_id": borrow.book_id,
                "borrow_date": borrow.borrow_date,
                "due_date": borrow.due_date,
                "return_date": borrow.return_date,
                "status": borrow.status,
                "is_overdue": borrow.is_overdue,
                "created_at": borrow.created_at,
                "updated_at": borrow.updated_at,
                "book_title": borrow.book.title if borrow.book else None,
                "book_author": borrow.book.author if borrow.book else None,
                "user_email": borrow.user.email if borrow.user else None,
                "user_username": borrow.user.username if borrow.user else None,
            }
            borrows_with_details.append(BorrowWithDetails(**borrow_dict))

        return BorrowHistory(
            total_borrows=total_borrows,
            active_borrows=active_borrows,
            returned_borrows=returned_borrows,
            overdue_borrows=overdue_borrows,
            borrows=borrows_with_details
        )

    except Exception as e:
        logger.error(f"Error retrieving borrow history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve borrow history"
        )


@router.get("/all", response_model=List[BorrowWithDetails])
async def get_all_borrows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: BorrowStatus = Query(None, description="Filter by borrow status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all borrow transactions (Admin only)."""
    try:
        query = (
            select(Borrow)
            .options(
                selectinload(Borrow.book),
                selectinload(Borrow.user)
            )
        )

        if status_filter:
            query = query.where(Borrow.status == status_filter)

        query = query.order_by(Borrow.borrow_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        borrows = result.scalars().all()

        # Format response with details
        borrows_with_details = []
        for borrow in borrows:
            borrow_dict = {
                "id": borrow.id,
                "user_id": borrow.user_id,
                "book_id": borrow.book_id,
                "borrow_date": borrow.borrow_date,
                "due_date": borrow.due_date,
                "return_date": borrow.return_date,
                "status": borrow.status,
                "is_overdue": borrow.is_overdue,
                "created_at": borrow.created_at,
                "updated_at": borrow.updated_at,
                "book_title": borrow.book.title if borrow.book else None,
                "book_author": borrow.book.author if borrow.book else None,
                "user_email": borrow.user.email if borrow.user else None,
                "user_username": borrow.user.username if borrow.user else None,
            }
            borrows_with_details.append(BorrowWithDetails(**borrow_dict))

        return borrows_with_details

    except Exception as e:
        logger.error(f"Error retrieving all borrows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve borrows"
        )


@router.get("/overdue", response_model=List[BorrowWithDetails])
async def get_overdue_borrows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all overdue borrows (Admin only)."""
    try:
        result = await db.execute(
            select(Borrow)
            .options(
                selectinload(Borrow.book),
                selectinload(Borrow.user)
            )
            .where(
                and_(
                    Borrow.status == BorrowStatus.ACTIVE,
                    Borrow.due_date < datetime.utcnow()
                )
            )
            .order_by(Borrow.due_date.asc())
            .offset(skip)
            .limit(limit)
        )
        borrows = result.scalars().all()

        # Format response with details
        borrows_with_details = []
        for borrow in borrows:
            borrow_dict = {
                "id": borrow.id,
                "user_id": borrow.user_id,
                "book_id": borrow.book_id,
                "borrow_date": borrow.borrow_date,
                "due_date": borrow.due_date,
                "return_date": borrow.return_date,
                "status": borrow.status,
                "is_overdue": borrow.is_overdue,
                "created_at": borrow.created_at,
                "updated_at": borrow.updated_at,
                "book_title": borrow.book.title if borrow.book else None,
                "book_author": borrow.book.author if borrow.book else None,
                "user_email": borrow.user.email if borrow.user else None,
                "user_username": borrow.user.username if borrow.user else None,
            }
            borrows_with_details.append(BorrowWithDetails(**borrow_dict))

        return borrows_with_details

    except Exception as e:
        logger.error(f"Error retrieving overdue borrows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue borrows"
        )


@router.get("/book/{book_id}/availability", response_model=BookAvailability)
async def check_book_availability(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if a book is available for borrowing."""
    try:
        # Verify book exists
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Count active borrows
        active_borrows_result = await db.execute(
            select(func.count(Borrow.id)).where(
                and_(
                    Borrow.book_id == book_id,
                    Borrow.status == BorrowStatus.ACTIVE
                )
            )
        )
        active_borrows = active_borrows_result.scalar()

        # Count total borrows
        total_borrows_result = await db.execute(
            select(func.count(Borrow.id)).where(Borrow.book_id == book_id)
        )
        total_borrows = total_borrows_result.scalar()

        return BookAvailability(
            book_id=book_id,
            is_available=active_borrows == 0,
            active_borrows=active_borrows,
            total_borrows=total_borrows
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking book availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check book availability"
        )


@router.get("/user/{user_id}/has-borrowed/{book_id}", response_model=bool)
async def check_user_has_borrowed_book(
    user_id: int,
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check if a user has ever borrowed a specific book.

    This is used to enforce the constraint that users can only review books they've borrowed.
    """
    try:
        # Users can check their own borrow history, admins can check any user
        if current_user.id != user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to check this user's borrow history"
            )

        result = await db.execute(
            select(Borrow).where(
                and_(
                    Borrow.user_id == user_id,
                    Borrow.book_id == book_id
                )
            )
        )
        borrow = result.scalar_one_or_none()

        return borrow is not None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking borrow history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check borrow history"
        )

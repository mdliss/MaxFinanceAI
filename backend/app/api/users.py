from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import User, AuditLog
from app.schemas import UserCreate, UserResponse, ConsentRequest, ConsentResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user without consent (consent must be granted separately)."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.user_id == user_data.user_id))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    # Create user with consent_status = False by default
    new_user = User(
        user_id=user_data.user_id,
        name=user_data.name,
        age=user_data.age,
        income_level=user_data.income_level,
        consent_status=False,
        consent_timestamp=None
    )

    db.add(new_user)

    # Log user creation
    audit_log = AuditLog(
        user_id=new_user.user_id,
        action="user_created",
        actor="system",
        details=f"User {new_user.name} created"
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user details."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all users."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

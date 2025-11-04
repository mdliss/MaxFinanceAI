from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

async def check_user_consent(user_id: str, db: AsyncSession) -> bool:
    """
    Check if user has active consent.
    Raises HTTPException if user not found or consent not granted.
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.consent_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User consent required. Please grant consent before accessing this resource."
        )

    return True

async def require_consent(user_id: str, db: AsyncSession) -> User:
    """
    Dependency function that ensures user has granted consent.
    Returns the user object if consent is active.
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.consent_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User consent required. Data processing blocked until consent is granted."
        )

    return user

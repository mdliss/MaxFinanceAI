from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, Signal, Persona, Recommendation
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["profile"])


class SignalData(BaseModel):
    signal_id: str
    signal_type: str
    value: float
    details: Optional[dict] = None
    computed_at: datetime

    class Config:
        from_attributes = True


class PersonaData(BaseModel):
    persona_id: int
    persona_type: str
    window_days: int
    priority_rank: int
    criteria_met: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class RecommendationData(BaseModel):
    recommendation_id: int
    persona_type: str
    content_type: str
    title: str
    description: str
    rationale: str
    eligibility_met: bool
    approval_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    age: Optional[int] = None
    income_level: Optional[str] = None
    consent_status: bool
    consent_timestamp: Optional[datetime] = None
    created_at: datetime
    signals: List[SignalData]
    personas: List[PersonaData]
    recommendations: List[RecommendationData]

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive user profile including:
    - Basic user information
    - All detected behavioral signals
    - All assigned personas (sorted by priority)
    - All recommendations with approval status

    Requires user consent to be granted.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required to access profile"
        )

    # Get all signals
    signals_result = await db.execute(
        select(Signal).where(Signal.user_id == user_id)
    )
    signals = signals_result.scalars().all()

    # Get all personas, ordered by priority
    personas_result = await db.execute(
        select(Persona)
        .where(Persona.user_id == user_id)
        .order_by(Persona.priority_rank)
    )
    personas = personas_result.scalars().all()

    # Get all recommendations
    recommendations_result = await db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
    )
    recommendations = recommendations_result.scalars().all()

    # Build comprehensive profile response
    profile = {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "income_level": user.income_level,
        "consent_status": user.consent_status,
        "consent_timestamp": user.consent_timestamp,
        "created_at": user.created_at,
        "signals": signals,
        "personas": personas,
        "recommendations": recommendations
    }

    return profile

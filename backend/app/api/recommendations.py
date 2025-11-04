from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, Recommendation, Feedback, AuditLog
from app.services.recommendation_engine import RecommendationEngine
from pydantic import BaseModel, Field

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationResponse(BaseModel):
    recommendation_id: int
    user_id: str
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


class FeedbackRequest(BaseModel):
    user_id: str
    recommendation_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    feedback_type: str = Field(..., description="Type of feedback: helpful, not_helpful, irrelevant, etc.")


class FeedbackResponse(BaseModel):
    feedback_id: int
    user_id: str
    recommendation_id: int
    rating: int
    comment: Optional[str] = None
    feedback_type: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{user_id}/generate", response_model=List[RecommendationResponse])
async def generate_recommendations(
    user_id: str,
    max_recommendations: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate personalized educational recommendations for a user.

    Requires:
    - User consent
    - Assigned persona
    - Detected signals

    Returns 3-5 recommendations with personalized rationales.
    """
    try:
        engine = RecommendationEngine(db)
        recommendations = await engine.generate_recommendations(user_id, max_recommendations)
        await engine.save_recommendations(user_id, recommendations)

        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=List[RecommendationResponse])
async def get_user_recommendations(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all recommendations for a user"""
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required to access recommendations"
        )

    # Get recommendations
    engine = RecommendationEngine(db)
    recommendations = await engine.get_recommendations(user_id)

    return recommendations


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit user feedback on a recommendation.

    Allows users to rate and comment on recommendations they received.
    Ratings are on a 1-5 scale.
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.user_id == feedback.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify recommendation exists and belongs to user
    rec_result = await db.execute(
        select(Recommendation).where(
            Recommendation.recommendation_id == feedback.recommendation_id,
            Recommendation.user_id == feedback.user_id
        )
    )
    recommendation = rec_result.scalar_one_or_none()

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found or does not belong to user"
        )

    # Create feedback entry
    new_feedback = Feedback(
        user_id=feedback.user_id,
        recommendation_id=feedback.recommendation_id,
        rating=feedback.rating,
        comment=feedback.comment,
        feedback_type=feedback.feedback_type
    )

    db.add(new_feedback)

    # Log feedback submission
    audit_log = AuditLog(
        user_id=feedback.user_id,
        action="feedback_submitted",
        actor=feedback.user_id,
        details=f"Rating: {feedback.rating}, Type: {feedback.feedback_type}, Recommendation: {feedback.recommendation_id}"
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(new_feedback)

    return new_feedback

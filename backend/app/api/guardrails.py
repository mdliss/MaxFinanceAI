from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services.guardrails import GuardrailsService

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


class ToneCheckRequest(BaseModel):
    text: str


class ToneCheckResponse(BaseModel):
    is_appropriate: bool
    reason: Optional[str] = None
    violations: Optional[List[str]] = None
    suggestions: List[str]


@router.get("/summary")
async def get_guardrails_summary(db: AsyncSession = Depends(get_db)):
    """
    Get a summary of all active guardrail rules.

    Returns information about:
    - User eligibility requirements
    - Content safety rules
    - Rate limits
    - Vulnerable population protections
    """
    guardrails = GuardrailsService(db)
    summary = guardrails.get_guardrail_summary()

    return {
        "message": "Active guardrail rules for FinanceMaxAI recommendations",
        "guardrails": summary
    }


@router.get("/check/{user_id}")
async def check_user_guardrails(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a specific user meets guardrail requirements.

    Returns:
    - Eligibility status
    - Rate limit status
    - Vulnerable population status
    """
    guardrails = GuardrailsService(db)

    # Check eligibility
    is_eligible, eligibility_reason = await guardrails.validate_user_eligibility(user_id)

    # Check rate limits
    within_limits, rate_limit_reason = await guardrails.check_rate_limits(user_id)

    # Get user for vulnerable population check
    from sqlalchemy import select
    from app.models import User

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    is_vulnerable, vulnerable_reason = guardrails.check_vulnerable_population(user)

    return {
        "user_id": user_id,
        "eligibility": {
            "is_eligible": is_eligible,
            "reason": eligibility_reason if not is_eligible else "User meets all eligibility requirements"
        },
        "rate_limits": {
            "within_limits": within_limits,
            "reason": rate_limit_reason if not within_limits else "User is within rate limits"
        },
        "vulnerable_population": {
            "is_vulnerable": is_vulnerable,
            "protection": vulnerable_reason if is_vulnerable else "No special protections applied"
        },
        "can_receive_recommendations": is_eligible and within_limits
    }


@router.post("/tone-check", response_model=ToneCheckResponse)
async def check_tone(
    request: ToneCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if text meets tone guardrail requirements.

    Validates that content is:
    - Empowering, not shaming
    - Neutral, not judgmental
    - Supportive, not panic-inducing
    - Respectful, not condescending
    - Suggestive, not demanding

    Returns validation result and improvement suggestions.
    """
    guardrails = GuardrailsService(db)

    # Validate tone
    is_appropriate, reason, violations = guardrails.validate_tone(request.text)

    # Get suggestions
    suggestions = guardrails.suggest_tone_improvements(request.text)

    return {
        "is_appropriate": is_appropriate,
        "reason": reason,
        "violations": violations,
        "suggestions": suggestions if not is_appropriate else []
    }

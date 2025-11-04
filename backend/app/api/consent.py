from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models import User, AuditLog
from app.schemas import ConsentRequest, ConsentResponse

router = APIRouter(prefix="/consent", tags=["consent"])

@router.post("/", response_model=ConsentResponse)
async def grant_consent(
    consent_data: ConsentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Grant or revoke user consent for data processing."""
    # Get user
    result = await db.execute(select(User).where(User.user_id == consent_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update consent status
    old_status = user.consent_status
    user.consent_status = consent_data.consent_status
    user.consent_timestamp = datetime.now() if consent_data.consent_status else None

    # Log consent change
    action = "consent_granted" if consent_data.consent_status else "consent_revoked"
    audit_log = AuditLog(
        user_id=user.user_id,
        action=action,
        actor="user",
        details=f"Consent changed from {old_status} to {consent_data.consent_status}"
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(user)

    message = "Consent granted successfully" if consent_data.consent_status else "Consent revoked successfully"

    return ConsentResponse(
        user_id=user.user_id,
        consent_status=user.consent_status,
        consent_timestamp=user.consent_timestamp,
        message=message
    )

@router.get("/{user_id}", response_model=ConsentResponse)
async def get_consent_status(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Check user consent status."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    message = "User has active consent" if user.consent_status else "User has not granted consent"

    return ConsentResponse(
        user_id=user.user_id,
        consent_status=user.consent_status,
        consent_timestamp=user.consent_timestamp,
        message=message
    )

@router.delete("/{user_id}", response_model=ConsentResponse)
async def revoke_consent(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Revoke user consent (shortcut endpoint)."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.consent_status = False
    user.consent_timestamp = None

    # Log consent revocation
    audit_log = AuditLog(
        user_id=user.user_id,
        action="consent_revoked",
        actor="user",
        details="Consent revoked via DELETE endpoint"
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(user)

    return ConsentResponse(
        user_id=user.user_id,
        consent_status=user.consent_status,
        consent_timestamp=user.consent_timestamp,
        message="Consent revoked successfully"
    )

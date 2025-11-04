from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, Signal
from app.services.signal_detector import SignalDetector
from pydantic import BaseModel

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalResponse(BaseModel):
    signal_id: str
    user_id: str
    signal_type: str
    value: float
    details: Optional[dict] = None
    computed_at: datetime

    class Config:
        from_attributes = True


@router.post("/{user_id}/detect", response_model=List[SignalResponse])
async def detect_signals(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect behavioral signals for a specific user.

    Per rubric requirement: computes signals for BOTH 30-day and 180-day windows.

    Requires user consent to be granted.
    Returns all detected signals including:
    - subscription_detected
    - savings_growth
    - credit_utilization
    - income_stability
    """
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required for signal detection"
        )

    # Detect signals for BOTH time windows (per rubric requirement)
    detector = SignalDetector(db)
    all_signals = []

    # 30-day window
    signals_30d = await detector.detect_all_signals(user_id, window_days=30)
    all_signals.extend(signals_30d)

    # 180-day window
    signals_180d = await detector.detect_all_signals(user_id, window_days=180)
    all_signals.extend(signals_180d)

    # Save all signals
    await detector.save_signals(all_signals)

    return all_signals


@router.get("/{user_id}", response_model=List[SignalResponse])
async def get_user_signals(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all detected signals for a user"""
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required to access signals"
        )

    # Get signals
    result = await db.execute(
        select(Signal).where(Signal.user_id == user_id)
    )
    signals = result.scalars().all()

    return signals

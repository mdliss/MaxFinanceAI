from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Alert, User
from app.services.alert_detector import AlertDetector

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Pydantic schemas
class AlertCreate(BaseModel):
    user_id: str
    alert_type: str
    severity: str = "info"  # info, warning, critical
    title: str
    message: str
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    action_url: str | None = None
    metadata: str | None = None

class AlertUpdate(BaseModel):
    is_read: bool | None = None
    is_dismissed: bool | None = None

class AlertResponse(BaseModel):
    alert_id: int
    user_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    related_entity_type: str | None
    related_entity_id: str | None
    is_read: bool
    is_dismissed: bool
    action_url: str | None
    metadata: str | None
    created_at: str
    read_at: str | None
    dismissed_at: str | None

    class Config:
        from_attributes = True


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new alert for a user.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.user_id == alert_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create the alert
    new_alert = Alert(
        user_id=alert_data.user_id,
        alert_type=alert_data.alert_type,
        severity=alert_data.severity,
        title=alert_data.title,
        message=alert_data.message,
        related_entity_type=alert_data.related_entity_type,
        related_entity_id=alert_data.related_entity_id,
        action_url=alert_data.action_url,
        meta_data=alert_data.metadata,
        is_read=False,
        is_dismissed=False
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    return new_alert.to_dict()


@router.get("/{user_id}", response_model=List[AlertResponse])
async def list_alerts(
    user_id: str,
    unread_only: bool = False,
    severity: str | None = None,
    alert_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all alerts for a user, with optional filters.
    """
    query = select(Alert).where(Alert.user_id == user_id)

    if unread_only:
        query = query.where(Alert.is_read == False)

    if severity:
        query = query.where(Alert.severity == severity)

    if alert_type:
        query = query.where(Alert.alert_type == alert_type)

    # Filter out dismissed alerts by default
    query = query.where(Alert.is_dismissed == False)

    query = query.order_by(Alert.created_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()

    return [alert.to_dict() for alert in alerts]


@router.get("/{user_id}/unread-count")
async def get_unread_count(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread alerts for a user.
    """
    result = await db.execute(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.is_read == False,
            Alert.is_dismissed == False
        )
    )
    alerts = result.scalars().all()

    return {
        "user_id": user_id,
        "unread_count": len(alerts),
        "by_severity": {
            "critical": len([a for a in alerts if a.severity == "critical"]),
            "warning": len([a for a in alerts if a.severity == "warning"]),
            "info": len([a for a in alerts if a.severity == "info"])
        }
    }


@router.get("/{user_id}/{alert_id}", response_model=AlertResponse)
async def get_alert(
    user_id: str,
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific alert by ID.
    """
    result = await db.execute(
        select(Alert).where(
            Alert.alert_id == alert_id,
            Alert.user_id == user_id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert.to_dict()


@router.put("/{user_id}/{alert_id}", response_model=AlertResponse)
async def update_alert(
    user_id: str,
    alert_id: int,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an alert's read/dismissed status.
    """
    result = await db.execute(
        select(Alert).where(
            Alert.alert_id == alert_id,
            Alert.user_id == user_id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields if provided
    if alert_data.is_read is not None:
        alert.is_read = alert_data.is_read
        if alert_data.is_read and not alert.read_at:
            alert.read_at = datetime.now()

    if alert_data.is_dismissed is not None:
        alert.is_dismissed = alert_data.is_dismissed
        if alert_data.is_dismissed and not alert.dismissed_at:
            alert.dismissed_at = datetime.now()

    await db.commit()
    await db.refresh(alert)

    return alert.to_dict()


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Dismiss an alert by ID.
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_dismissed = True
    if not alert.dismissed_at:
        alert.dismissed_at = datetime.now()

    await db.commit()
    await db.refresh(alert)

    return alert.to_dict()


@router.post("/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an alert as read by ID.
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    if not alert.read_at:
        alert.read_at = datetime.now()

    await db.commit()
    await db.refresh(alert)

    return alert.to_dict()


@router.post("/{user_id}/mark-all-read")
async def mark_all_read(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all alerts as read for a user.
    """
    result = await db.execute(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.is_read == False
        )
    )
    alerts = result.scalars().all()

    for alert in alerts:
        alert.is_read = True
        if not alert.read_at:
            alert.read_at = datetime.now()

    await db.commit()

    return {"message": f"Marked {len(alerts)} alerts as read"}


@router.delete("/{user_id}/{alert_id}")
async def delete_alert(
    user_id: str,
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an alert (hard delete).
    """
    result = await db.execute(
        select(Alert).where(
            Alert.alert_id == alert_id,
            Alert.user_id == user_id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    return {"message": "Alert deleted successfully"}


@router.post("/{user_id}/generate")
async def generate_alerts(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger alert generation for a user.

    Checks for:
    - Budget exceeded/warning alerts
    - Goal milestone alerts
    - Unusual spending patterns
    - Low balance alerts
    - Subscription renewal reminders
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate alerts
    detector = AlertDetector(db)
    alerts = await detector.generate_alerts_for_user(user_id)

    return {
        "user_id": user_id,
        "alerts_generated": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }

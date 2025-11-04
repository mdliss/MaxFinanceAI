from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, Persona
from app.services.persona_assigner import PersonaAssigner, PERSONA_DEFINITIONS
from pydantic import BaseModel

router = APIRouter(prefix="/personas", tags=["personas"])


class PersonaResponse(BaseModel):
    persona_id: int
    user_id: str
    window_days: int
    persona_type: str
    priority_rank: int
    criteria_met: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class PersonaDefinitionResponse(BaseModel):
    persona_type: str
    priority: int
    description: str


@router.post("/{user_id}/assign", response_model=List[PersonaResponse])
async def assign_personas(
    user_id: str,
    window_days: int = 180,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign personas to a user based on their signals.

    Requires user consent to be granted.
    Returns all assigned personas in priority order.
    """
    try:
        assigner = PersonaAssigner(db, window_days=window_days)
        personas = await assigner.assign_personas(user_id)
        await assigner.save_personas(user_id, personas)

        return personas
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=List[PersonaResponse])
async def get_user_personas(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all personas assigned to a user, ordered by priority"""
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required to access personas"
        )

    # Get personas
    assigner = PersonaAssigner(db)
    personas = await assigner.get_all_personas(user_id)

    return personas


@router.get("/{user_id}/primary", response_model=Optional[PersonaResponse])
async def get_primary_persona(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the primary (highest priority) persona for a user"""
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(
            status_code=403,
            detail="User consent required to access personas"
        )

    # Get primary persona
    assigner = PersonaAssigner(db)
    persona = await assigner.get_primary_persona(user_id)

    return persona


@router.get("/definitions/all", response_model=List[PersonaDefinitionResponse])
async def get_persona_definitions():
    """Get all available persona definitions and their criteria"""
    definitions = []
    for persona_type, info in PERSONA_DEFINITIONS.items():
        definitions.append({
            "persona_type": persona_type,
            "priority": info["priority"],
            "description": info["description"]
        })

    # Sort by priority
    definitions.sort(key=lambda x: x["priority"])

    return definitions

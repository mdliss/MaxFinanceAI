from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import FinancialGoal, User
from app.services.goal_calculator import GoalCalculator

router = APIRouter(prefix="/goals", tags=["goals"])

# Pydantic schemas
class GoalCreate(BaseModel):
    user_id: str
    goal_type: str  # emergency_fund, vacation, debt_payoff, major_purchase, retirement, custom
    title: str
    description: str | None = None
    target_amount: float
    target_date: str | None = None  # ISO 8601 date

class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_amount: float | None = None
    target_date: str | None = None
    status: str | None = None  # active, completed, paused, cancelled

class GoalResponse(BaseModel):
    goal_id: int
    user_id: str
    goal_type: str
    title: str
    description: str | None
    target_amount: float
    current_amount: float
    target_date: str | None
    status: str
    progress_percent: float
    projected_completion_date: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=GoalResponse)
async def create_goal(
    goal_data: GoalCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new financial goal for a user.

    Requires user consent to be granted.
    """
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == goal_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(status_code=403, detail="User consent required")

    # Create the goal
    new_goal = FinancialGoal(
        user_id=goal_data.user_id,
        goal_type=goal_data.goal_type,
        title=goal_data.title,
        description=goal_data.description,
        target_amount=goal_data.target_amount,
        target_date=goal_data.target_date,
        current_amount=0.0,
        progress_percent=0.0,
        status="active"
    )

    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)

    # Calculate initial progress
    calculator = GoalCalculator(db)
    await calculator.update_goal_progress(new_goal.goal_id)
    await db.refresh(new_goal)

    return new_goal.to_dict()


@router.get("/{user_id}", response_model=List[GoalResponse])
async def list_goals(
    user_id: str,
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all goals for a user, optionally filtered by status.
    """
    query = select(FinancialGoal).where(FinancialGoal.user_id == user_id)

    if status:
        query = query.where(FinancialGoal.status == status)

    query = query.order_by(FinancialGoal.created_at.desc())

    result = await db.execute(query)
    goals = result.scalars().all()

    return [goal.to_dict() for goal in goals]


@router.get("/{user_id}/{goal_id}", response_model=GoalResponse)
async def get_goal(
    user_id: str,
    goal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific goal by ID.
    """
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.goal_id == goal_id,
            FinancialGoal.user_id == user_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Update progress before returning
    calculator = GoalCalculator(db)
    await calculator.update_goal_progress(goal_id)
    await db.refresh(goal)

    return goal.to_dict()


@router.put("/{user_id}/{goal_id}", response_model=GoalResponse)
async def update_goal(
    user_id: str,
    goal_id: int,
    goal_data: GoalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a goal's details.
    """
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.goal_id == goal_id,
            FinancialGoal.user_id == user_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Update fields if provided
    if goal_data.title is not None:
        goal.title = goal_data.title
    if goal_data.description is not None:
        goal.description = goal_data.description
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.target_date is not None:
        goal.target_date = goal_data.target_date
    if goal_data.status is not None:
        goal.status = goal_data.status

    await db.commit()
    await db.refresh(goal)

    # Recalculate progress
    calculator = GoalCalculator(db)
    await calculator.update_goal_progress(goal_id)
    await db.refresh(goal)

    return goal.to_dict()


@router.delete("/{user_id}/{goal_id}")
async def delete_goal(
    user_id: str,
    goal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a goal.
    """
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.goal_id == goal_id,
            FinancialGoal.user_id == user_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await db.delete(goal)
    await db.commit()

    return {"message": "Goal deleted successfully"}


@router.post("/{user_id}/{goal_id}/progress")
async def update_goal_progress(
    user_id: str,
    goal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a goal progress recalculation.
    """
    result = await db.execute(
        select(FinancialGoal).where(
            FinancialGoal.goal_id == goal_id,
            FinancialGoal.user_id == user_id
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    calculator = GoalCalculator(db)
    await calculator.update_goal_progress(goal_id)
    await db.refresh(goal)

    return goal.to_dict()

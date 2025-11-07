from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Budget, User
from app.services.budget_tracker import BudgetTracker
from app.services.auto_budget_generator import AutoBudgetGenerator

router = APIRouter(prefix="/budgets", tags=["budgets"])

# Pydantic schemas
class BudgetCreate(BaseModel):
    user_id: str
    category: str
    amount: float
    period: str = "monthly"  # weekly, monthly, yearly
    rollover_enabled: bool = False
    alert_threshold: float = 80.0

class BudgetUpdate(BaseModel):
    amount: float | None = None
    period: str | None = None
    status: str | None = None
    rollover_enabled: bool | None = None
    alert_threshold: float | None = None

class BudgetResponse(BaseModel):
    budget_id: int
    user_id: str
    category: str
    amount: float
    period: str
    spent_amount: float
    remaining_amount: float | None
    status: str
    is_auto_generated: bool
    rollover_enabled: bool
    alert_threshold: float
    period_start_date: str | None
    period_end_date: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new budget for a user.

    Requires user consent to be granted.
    """
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == budget_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(status_code=403, detail="User consent required")

    # Calculate period dates
    period_start = datetime.now()
    if budget_data.period == "weekly":
        period_end = period_start + timedelta(days=7)
    elif budget_data.period == "monthly":
        period_end = period_start + timedelta(days=30)
    elif budget_data.period == "yearly":
        period_end = period_start + timedelta(days=365)
    else:
        period_end = period_start + timedelta(days=30)

    # Create the budget
    new_budget = Budget(
        user_id=budget_data.user_id,
        category=budget_data.category,
        amount=budget_data.amount,
        period=budget_data.period,
        spent_amount=0.0,
        remaining_amount=budget_data.amount,
        status="active",
        is_auto_generated=False,
        rollover_enabled=budget_data.rollover_enabled,
        alert_threshold=budget_data.alert_threshold,
        period_start_date=period_start.date().isoformat(),
        period_end_date=period_end.date().isoformat()
    )

    db.add(new_budget)
    await db.commit()
    await db.refresh(new_budget)

    # Calculate initial spending
    tracker = BudgetTracker(db)
    await tracker.update_budget_spending(new_budget.budget_id)
    await db.refresh(new_budget)

    return new_budget.to_dict()


@router.get("/{user_id}", response_model=List[BudgetResponse])
async def list_budgets(
    user_id: str,
    status: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all budgets for a user, optionally filtered by status or category.
    """
    query = select(Budget).where(Budget.user_id == user_id)

    if status:
        query = query.where(Budget.status == status)
    if category:
        query = query.where(Budget.category == category)

    query = query.order_by(Budget.created_at.desc())

    result = await db.execute(query)
    budgets = result.scalars().all()

    return [budget.to_dict() for budget in budgets]


@router.get("/{user_id}/summary")
async def get_budget_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get budget summary for a user (total budget, total spent, etc.).
    """
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.status == "active"
        )
    )
    budgets = result.scalars().all()

    if not budgets:
        return {
            "user_id": user_id,
            "total_budgeted": 0,
            "total_spent": 0,
            "total_remaining": 0,
            "overall_percentage": 0,
            "budget_count": 0,
            "exceeded_count": 0,
            "warning_count": 0
        }

    total_budgeted = sum(b.amount for b in budgets)
    total_spent = sum(b.spent_amount for b in budgets)
    total_remaining = sum(b.remaining_amount or 0 for b in budgets)
    exceeded_count = sum(1 for b in budgets if b.status == "exceeded")
    warning_count = sum(1 for b in budgets if b.status == "warning")

    overall_percentage = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0

    return {
        "user_id": user_id,
        "total_budgeted": total_budgeted,
        "total_spent": total_spent,
        "total_remaining": total_remaining,
        "overall_percentage": round(overall_percentage, 2),
        "budget_count": len(budgets),
        "exceeded_count": exceeded_count,
        "warning_count": warning_count
    }


@router.get("/{user_id}/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    user_id: str,
    budget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific budget by ID.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Update spending before returning
    tracker = BudgetTracker(db)
    await tracker.update_budget_spending(budget_id)
    await db.refresh(budget)

    return budget.to_dict()


@router.put("/{user_id}/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    user_id: str,
    budget_id: int,
    budget_data: BudgetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a budget's details.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Update fields if provided
    if budget_data.amount is not None:
        budget.amount = budget_data.amount
        budget.remaining_amount = budget_data.amount - budget.spent_amount
    if budget_data.period is not None:
        budget.period = budget_data.period
    if budget_data.status is not None:
        budget.status = budget_data.status
    if budget_data.rollover_enabled is not None:
        budget.rollover_enabled = budget_data.rollover_enabled
    if budget_data.alert_threshold is not None:
        budget.alert_threshold = budget_data.alert_threshold

    await db.commit()
    await db.refresh(budget)

    # Recalculate spending
    tracker = BudgetTracker(db)
    await tracker.update_budget_spending(budget_id)
    await db.refresh(budget)

    return budget.to_dict()


@router.delete("/{user_id}/{budget_id}")
async def delete_budget(
    user_id: str,
    budget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a budget.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    await db.delete(budget)
    await db.commit()

    return {"message": "Budget deleted successfully"}


@router.post("/{user_id}/{budget_id}/refresh")
async def refresh_budget_spending(
    user_id: str,
    budget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a budget spending recalculation.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    tracker = BudgetTracker(db)
    await tracker.update_budget_spending(budget_id)
    await db.refresh(budget)

    return budget.to_dict()


@router.post("/{user_id}/auto-generate", response_model=List[BudgetResponse])
async def auto_generate_budgets(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-generate budgets based on user's spending history (last 90 days).

    Analyzes transaction patterns and creates recommended budgets.
    """
    # Check if user exists and has consent
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.consent_status:
        raise HTTPException(status_code=403, detail="User consent required")

    # Generate budgets
    generator = AutoBudgetGenerator(db)
    budgets = await generator.generate_budgets_for_user(user_id)

    return [budget.to_dict() for budget in budgets]


@router.get("/{user_id}/summary")
async def get_budget_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get budget summary for a user (total budget, total spent, etc.).
    """
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.status == "active"
        )
    )
    budgets = result.scalars().all()

    if not budgets:
        return {
            "user_id": user_id,
            "total_budgeted": 0,
            "total_spent": 0,
            "total_remaining": 0,
            "overall_percentage": 0,
            "budget_count": 0,
            "exceeded_count": 0,
            "warning_count": 0
        }

    total_budgeted = sum(b.amount for b in budgets)
    total_spent = sum(b.spent_amount for b in budgets)
    total_remaining = sum(b.remaining_amount or 0 for b in budgets)
    exceeded_count = sum(1 for b in budgets if b.status == "exceeded")
    warning_count = sum(1 for b in budgets if b.status == "warning")

    overall_percentage = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0

    return {
        "user_id": user_id,
        "total_budgeted": total_budgeted,
        "total_spent": total_spent,
        "total_remaining": total_remaining,
        "overall_percentage": round(overall_percentage, 2),
        "budget_count": len(budgets),
        "exceeded_count": exceeded_count,
        "warning_count": warning_count
    }

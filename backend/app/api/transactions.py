from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, extract
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models import Transaction, User, Account
from pydantic import BaseModel

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionResponse(BaseModel):
    transaction_id: str
    account_id: str
    user_id: str
    date: date
    amount: float
    merchant_name: Optional[str] = None
    merchant_entity_id: Optional[str] = None
    payment_channel: Optional[str] = None
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    pending: bool = False

    class Config:
        from_attributes = True


class SpendingCategoryData(BaseModel):
    category: str
    amount: float
    percentage: float
    transaction_count: int


class SpendingCategoriesResponse(BaseModel):
    categories: List[SpendingCategoryData]
    total_spending: float
    period_start: date
    period_end: date


class SavingsHistoryPoint(BaseModel):
    date: str
    balance: float
    month: str


class SavingsHistoryResponse(BaseModel):
    history: List[SavingsHistoryPoint]
    growth_rate: float
    current_balance: float
    starting_balance: float


@router.get("/{user_id}", response_model=List[TransactionResponse])
async def get_user_transactions(
    user_id: str,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transactions for a user.

    Parameters:
    - limit: Maximum number of transactions to return (default 100, max 1000)
    - offset: Number of transactions to skip (for pagination)
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get transactions ordered by date (most recent first)
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.date))
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()

    return transactions


@router.get("/{user_id}/spending-categories", response_model=SpendingCategoriesResponse)
async def get_spending_categories(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get spending breakdown by category for a user.

    Parameters:
    - days: Number of days to look back (default 30, max 365)

    Returns spending grouped by primary category with:
    - Total amount per category
    - Percentage of total spending
    - Transaction count
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get spending transactions (negative amounts = expenses)
    result = await db.execute(
        select(
            Transaction.category_primary,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.transaction_id).label('transaction_count')
        )
        .where(and_(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0,  # Only expenses (negative amounts)
            Transaction.category_primary != "INCOME"  # Exclude income
        ))
        .group_by(Transaction.category_primary)
        .order_by(desc('total_amount'))
    )

    category_data = result.all()

    # Calculate total spending
    total_spending = sum(cat.total_amount for cat in category_data)

    # Format response
    categories = []
    for cat in category_data:
        category_name = cat.category_primary or "Uncategorized"
        amount = float(cat.total_amount)
        percentage = (amount / total_spending * 100) if total_spending > 0 else 0

        categories.append(SpendingCategoryData(
            category=category_name,
            amount=round(amount, 2),
            percentage=round(percentage, 2),
            transaction_count=cat.transaction_count
        ))

    return SpendingCategoriesResponse(
        categories=categories,
        total_spending=round(total_spending, 2),
        period_start=start_date,
        period_end=end_date
    )


@router.get("/{user_id}/savings-history", response_model=SavingsHistoryResponse)
async def get_savings_history(
    user_id: str,
    months: int = Query(default=6, ge=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """
    Get savings account balance history over time.

    Parameters:
    - months: Number of months to look back (default 6, max 24)

    Returns monthly snapshots of savings account balance with growth rate.
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get savings accounts
    result = await db.execute(
        select(Account).where(and_(
            Account.user_id == user_id,
            Account.type.in_(["depository", "savings"])
        ))
    )
    savings_accounts = result.scalars().all()

    if not savings_accounts:
        return SavingsHistoryResponse(
            history=[],
            growth_rate=0.0,
            current_balance=0.0,
            starting_balance=0.0
        )

    # Get current balance
    current_balance = sum(acc.current_balance or 0 for acc in savings_accounts)

    # Calculate monthly balances by looking at transactions
    # For simplicity, we'll create a monthly snapshot based on net inflows
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    account_ids = [acc.account_id for acc in savings_accounts]

    # Get all transactions for savings accounts in the period
    result = await db.execute(
        select(Transaction)
        .where(and_(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ))
        .order_by(Transaction.date)
    )
    transactions = result.scalars().all()

    # Build monthly snapshots
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Start with an estimated beginning balance (work backwards from current)
    # Sum all transactions and subtract from current to get starting balance
    total_net_flow = sum(
        -txn.amount if txn.amount > 0 else abs(txn.amount)  # Credits increase balance
        for txn in transactions
    )
    starting_balance = max(0, current_balance - total_net_flow)

    # Create monthly data points
    history = []
    current_point_date = start_date.replace(day=1)  # Start of first month
    running_balance = starting_balance

    while current_point_date <= end_date:
        # Get transactions for this month
        month_end = (current_point_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        month_transactions = [
            txn for txn in transactions
            if current_point_date <= txn.date <= month_end
        ]

        # Calculate net flow for the month
        month_net_flow = sum(
            -txn.amount if txn.amount > 0 else abs(txn.amount)
            for txn in month_transactions
        )

        running_balance += month_net_flow

        history.append(SavingsHistoryPoint(
            date=current_point_date.strftime('%Y-%m'),
            balance=round(max(0, running_balance), 2),
            month=month_names[current_point_date.month - 1]
        ))

        # Move to next month
        current_point_date = (month_end + timedelta(days=1))

    # Calculate growth rate
    growth_rate = 0.0
    if starting_balance > 0 and len(history) > 1:
        total_months = len(history)
        growth_rate = ((current_balance - starting_balance) / starting_balance) * (12 / total_months)
        growth_rate = growth_rate * 100  # Convert to percentage

    return SavingsHistoryResponse(
        history=history,
        growth_rate=round(growth_rate, 2),
        current_balance=round(current_balance, 2),
        starting_balance=round(starting_balance, 2)
    )

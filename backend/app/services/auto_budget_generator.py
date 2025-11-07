from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List
from app.models import Budget, Transaction

class AutoBudgetGenerator:
    """
    Service to auto-generate budgets based on historical spending patterns.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_budgets_for_user(self, user_id: str) -> List[Budget]:
        """
        Generate recommended budgets based on last 90 days of spending.

        Analyzes transaction history and creates budgets with 10% buffer.
        """
        # Get spending by category for last 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)

        result = await self.db.execute(
            select(
                Transaction.category_primary,
                func.sum(func.abs(Transaction.amount)).label("total_spent")
            ).where(
                Transaction.user_id == user_id,
                Transaction.date >= ninety_days_ago.isoformat(),
                Transaction.amount < 0  # Negative = spending
            ).group_by(Transaction.category_primary)
        )

        spending_by_category = result.all()

        if not spending_by_category:
            return []

        # Create budgets with 10% buffer
        budgets = []
        period_start = datetime.now()
        period_end = period_start + timedelta(days=30)

        # Delete existing auto-generated budgets for this user
        await self.db.execute(
            Budget.__table__.delete().where(
                Budget.user_id == user_id,
                Budget.is_auto_generated == True
            )
        )

        for category, total_spent in spending_by_category:
            if not category or total_spent <= 0:
                continue

            # Calculate monthly average (90 days / 3 months)
            monthly_average = total_spent / 3

            # Add 10% buffer
            recommended_amount = monthly_average * 1.1

            # Create budget
            budget = Budget(
                user_id=user_id,
                category=category,
                amount=round(recommended_amount, 2),
                period="monthly",
                spent_amount=0.0,
                remaining_amount=round(recommended_amount, 2),
                status="active",
                is_auto_generated=True,
                rollover_enabled=False,
                alert_threshold=80.0,
                period_start_date=period_start.date().isoformat(),
                period_end_date=period_end.date().isoformat()
            )

            self.db.add(budget)
            budgets.append(budget)

        await self.db.commit()

        # Refresh all budgets to get IDs
        for budget in budgets:
            await self.db.refresh(budget)

        return budgets

    async def analyze_spending_patterns(self, user_id: str, days: int = 90) -> dict:
        """
        Analyze user's spending patterns over a period.

        Returns dictionary with insights:
        - Top spending categories
        - Average daily/monthly spending
        - Spending trends
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all spending transactions
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.date >= cutoff_date.isoformat(),
                Transaction.amount < 0  # Negative = spending
            )
        )
        transactions = result.scalars().all()

        if not transactions:
            return {
                "total_spent": 0,
                "average_daily": 0,
                "average_monthly": 0,
                "top_categories": [],
                "transaction_count": 0
            }

        # Calculate totals
        total_spent = sum(abs(t.amount) for t in transactions)
        average_daily = total_spent / days
        average_monthly = average_daily * 30

        # Calculate by category
        category_spending = {}
        for t in transactions:
            cat = t.category_primary or "Uncategorized"
            if cat not in category_spending:
                category_spending[cat] = 0
            category_spending[cat] += abs(t.amount)

        # Sort by spending
        top_categories = sorted(
            category_spending.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "total_spent": round(total_spent, 2),
            "average_daily": round(average_daily, 2),
            "average_monthly": round(average_monthly, 2),
            "top_categories": [
                {"category": cat, "amount": round(amt, 2), "percentage": round(amt / total_spent * 100, 2)}
                for cat, amt in top_categories
            ],
            "transaction_count": len(transactions)
        }

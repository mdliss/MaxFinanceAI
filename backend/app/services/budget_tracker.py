from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from app.models import Budget, Transaction

class BudgetTracker:
    """
    Service to track budget spending and update budget status.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_budget_spending(self, budget_id: int) -> Optional[Budget]:
        """
        Update spending for a specific budget based on transactions.

        Calculates:
        - Spent amount (sum of transactions in budget period and category)
        - Remaining amount
        - Status (active, warning, exceeded)
        """
        # Get the budget
        result = await self.db.execute(
            select(Budget).where(Budget.budget_id == budget_id)
        )
        budget = result.scalar_one_or_none()

        if not budget:
            return None

        # Calculate spent amount from transactions
        spent = await self._calculate_spending(
            budget.user_id,
            budget.category,
            budget.period_start_date,
            budget.period_end_date
        )

        budget.spent_amount = spent
        budget.remaining_amount = budget.amount - spent

        # Update status based on spending
        if spent >= budget.amount:
            budget.status = "exceeded"
        elif (spent / budget.amount * 100) >= budget.alert_threshold:
            budget.status = "warning"
        else:
            budget.status = "active"

        await self.db.commit()
        return budget

    async def _calculate_spending(
        self,
        user_id: str,
        category: str,
        start_date: str,
        end_date: str
    ) -> float:
        """
        Calculate total spending in a category during a period.

        Returns sum of transaction amounts (negative values = spending).
        """
        # Get all transactions in the period for this category
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category_primary == category,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Negative = spending
            )
        )
        transactions = result.scalars().all()

        # Sum absolute values (convert negative to positive)
        total_spent = sum(abs(t.amount) for t in transactions)
        return total_spent

    async def update_all_budgets_for_user(self, user_id: str) -> int:
        """
        Update spending for all active budgets for a user.

        Returns count of budgets updated.
        """
        result = await self.db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.status.in_(["active", "warning", "exceeded"])
            )
        )
        budgets = result.scalars().all()

        count = 0
        for budget in budgets:
            await self.update_budget_spending(budget.budget_id)
            count += 1

        return count

    async def check_budget_alerts(self, user_id: str) -> list:
        """
        Check which budgets have triggered alerts (warning or exceeded).

        Returns list of budget dicts with alert info.
        """
        result = await self.db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.status.in_(["warning", "exceeded"])
            )
        )
        budgets = result.scalars().all()

        alerts = []
        for budget in budgets:
            percentage = (budget.spent_amount / budget.amount * 100) if budget.amount > 0 else 0
            alerts.append({
                "budget_id": budget.budget_id,
                "category": budget.category,
                "amount": budget.amount,
                "spent_amount": budget.spent_amount,
                "remaining_amount": budget.remaining_amount,
                "percentage": round(percentage, 2),
                "status": budget.status,
                "severity": "critical" if budget.status == "exceeded" else "warning"
            })

        return alerts

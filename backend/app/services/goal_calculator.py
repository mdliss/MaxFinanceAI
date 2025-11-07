from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional
from app.models import FinancialGoal, Account, Transaction

class GoalCalculator:
    """
    Service to calculate goal progress and project completion dates.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_goal_progress(self, goal_id: int) -> Optional[FinancialGoal]:
        """
        Update progress for a specific goal based on current account balances.

        Calculates:
        - Current amount (sum of savings/checking account balances)
        - Progress percentage
        - Projected completion date based on 90-day average savings rate
        """
        # Get the goal
        result = await self.db.execute(
            select(FinancialGoal).where(FinancialGoal.goal_id == goal_id)
        )
        goal = result.scalar_one_or_none()

        if not goal:
            return None

        # Calculate current amount from account balances
        current_amount = await self._calculate_current_amount(goal.user_id, goal.goal_type)
        goal.current_amount = current_amount

        # Calculate progress percentage
        if goal.target_amount > 0:
            goal.progress_percent = min((current_amount / goal.target_amount) * 100, 100)
        else:
            goal.progress_percent = 0

        # Calculate projected completion date
        projected_date = await self._calculate_projected_completion(goal)
        goal.projected_completion_date = projected_date

        # Update status if goal is completed
        if goal.progress_percent >= 100 and goal.status == "active":
            goal.status = "completed"

        await self.db.commit()
        return goal

    async def _calculate_current_amount(self, user_id: str, goal_type: str) -> float:
        """
        Calculate current amount toward goal based on account balances.

        For most goal types, this is the sum of savings and checking account balances.
        For debt_payoff goals, it's calculated differently (debt reduction).
        """
        if goal_type == "debt_payoff":
            # For debt payoff, we'd calculate debt reduction
            # For now, return 0 (can be enhanced later)
            return 0.0

        # Get all depository accounts (savings + checking)
        result = await self.db.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.type == "depository"
            )
        )
        accounts = result.scalars().all()

        total_balance = sum(account.current_balance for account in accounts if account.current_balance)
        return max(total_balance, 0.0)

    async def _calculate_projected_completion(self, goal: FinancialGoal) -> Optional[str]:
        """
        Calculate projected completion date using 90-day average savings rate.

        Returns ISO 8601 date string or None if insufficient data.
        """
        if goal.progress_percent >= 100:
            # Goal already completed
            return datetime.now().isoformat()

        # Calculate 90-day average savings rate
        ninety_days_ago = datetime.now() - timedelta(days=90)

        # Get savings transactions (deposits to savings accounts)
        result = await self.db.execute(
            select(Transaction).join(Account).where(
                Transaction.user_id == goal.user_id,
                Transaction.date >= ninety_days_ago.isoformat(),
                Transaction.amount > 0,  # Positive = deposits
                Account.subtype.in_(["savings", "money market"])
            )
        )
        savings_transactions = result.scalars().all()

        if not savings_transactions:
            # Insufficient data to project
            return None

        # Calculate average monthly savings
        total_saved = sum(t.amount for t in savings_transactions)
        days_analyzed = 90
        daily_savings_rate = total_saved / days_analyzed
        monthly_savings_rate = daily_savings_rate * 30

        if monthly_savings_rate <= 0:
            # No positive savings rate
            return None

        # Calculate remaining amount needed
        remaining_amount = goal.target_amount - goal.current_amount

        if remaining_amount <= 0:
            return datetime.now().isoformat()

        # Calculate months to completion
        months_to_completion = remaining_amount / monthly_savings_rate

        # Calculate projected date
        projected_date = datetime.now() + timedelta(days=months_to_completion * 30)

        return projected_date.date().isoformat()

    async def update_all_goals_for_user(self, user_id: str) -> int:
        """
        Update progress for all active goals for a user.

        Returns count of goals updated.
        """
        result = await self.db.execute(
            select(FinancialGoal).where(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == "active"
            )
        )
        goals = result.scalars().all()

        count = 0
        for goal in goals:
            await self.update_goal_progress(goal.goal_id)
            count += 1

        return count

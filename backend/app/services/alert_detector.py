from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List
from app.models import Alert, Budget, FinancialGoal, Transaction, Account, Subscription

class AlertDetector:
    """
    Service to detect and generate smart alerts for users.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_alerts_for_user(self, user_id: str) -> List[Alert]:
        """
        Generate all relevant alerts for a user.

        Returns list of newly created alerts.
        """
        alerts = []

        # Check budget alerts
        budget_alerts = await self._check_budget_alerts(user_id)
        alerts.extend(budget_alerts)

        # Check goal milestone alerts
        goal_alerts = await self._check_goal_alerts(user_id)
        alerts.extend(goal_alerts)

        # Check unusual spending alerts
        spending_alerts = await self._check_unusual_spending(user_id)
        alerts.extend(spending_alerts)

        # Check low balance alerts
        balance_alerts = await self._check_low_balance(user_id)
        alerts.extend(balance_alerts)

        # Check subscription renewal alerts
        subscription_alerts = await self._check_subscription_renewals(user_id)
        alerts.extend(subscription_alerts)

        # Save all alerts to database
        for alert in alerts:
            self.db.add(alert)
        await self.db.commit()

        # Refresh all alerts
        for alert in alerts:
            await self.db.refresh(alert)

        return alerts

    async def _check_budget_alerts(self, user_id: str) -> List[Alert]:
        """
        Check for budget-related alerts (warning, exceeded).
        """
        alerts = []

        # Get all budgets with warning or exceeded status
        result = await self.db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.status.in_(["warning", "exceeded"])
            )
        )
        budgets = result.scalars().all()

        # Check if we already have alerts for these budgets
        for budget in budgets:
            # Check if alert already exists for this budget
            existing = await self.db.execute(
                select(Alert).where(
                    Alert.user_id == user_id,
                    Alert.alert_type == "budget_exceeded" if budget.status == "exceeded" else "budget_warning",
                    Alert.related_entity_id == str(budget.budget_id),
                    Alert.is_dismissed == False
                )
            )

            if existing.scalar_one_or_none():
                continue  # Alert already exists

            # Calculate percentage
            percentage = (budget.spent_amount / budget.amount * 100) if budget.amount > 0 else 0

            if budget.status == "exceeded":
                alert = Alert(
                    user_id=user_id,
                    alert_type="budget_exceeded",
                    severity="critical",
                    title=f"Budget Exceeded: {budget.category}",
                    message=f"You've exceeded your {budget.category} budget by ${abs(budget.remaining_amount):.2f}. You've spent ${budget.spent_amount:.2f} of your ${budget.amount:.2f} budget.",
                    related_entity_type="budget",
                    related_entity_id=str(budget.budget_id),
                    action_url=f"/budgets/{budget.budget_id}"
                )
                alerts.append(alert)

            elif budget.status == "warning":
                alert = Alert(
                    user_id=user_id,
                    alert_type="budget_warning",
                    severity="warning",
                    title=f"Budget Alert: {budget.category}",
                    message=f"You've used {percentage:.0f}% of your {budget.category} budget. ${budget.remaining_amount:.2f} remaining of ${budget.amount:.2f}.",
                    related_entity_type="budget",
                    related_entity_id=str(budget.budget_id),
                    action_url=f"/budgets/{budget.budget_id}"
                )
                alerts.append(alert)

        return alerts

    async def _check_goal_alerts(self, user_id: str) -> List[Alert]:
        """
        Check for goal milestone alerts (25%, 50%, 75%, 100%).
        """
        alerts = []

        # Get all active goals
        result = await self.db.execute(
            select(FinancialGoal).where(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == "active"
            )
        )
        goals = result.scalars().all()

        for goal in goals:
            # Check for milestone achievements - find highest achieved milestone
            milestones = [25, 50, 75, 100]
            highest_milestone = None
            for milestone in milestones:
                if goal.progress_percent >= milestone:
                    highest_milestone = milestone

            if highest_milestone:
                # Check if we already alerted for this milestone
                existing = await self.db.execute(
                    select(Alert).where(
                        Alert.user_id == user_id,
                        Alert.alert_type == "goal_milestone",
                        Alert.related_entity_id == str(goal.goal_id),
                        Alert.message.like(f"%{highest_milestone}%"),
                        Alert.is_dismissed == False
                    )
                )

                if not existing.scalar_one_or_none():
                    # Create milestone alert for highest achieved milestone
                    if highest_milestone == 100:
                        alert = Alert(
                            user_id=user_id,
                            alert_type="goal_milestone",
                            severity="info",
                            title=f"Goal Completed: {goal.title}! 🎉",
                            message=f"Congratulations! You've reached your goal of ${goal.target_amount:.2f}. Great job staying on track!",
                            related_entity_type="goal",
                            related_entity_id=str(goal.goal_id),
                            action_url=f"/goals/{goal.goal_id}"
                        )
                    else:
                        alert = Alert(
                            user_id=user_id,
                            alert_type="goal_milestone",
                            severity="info",
                            title=f"Goal Progress: {goal.title}",
                            message=f"You're {highest_milestone}% of the way to your goal! You've saved ${goal.current_amount:.2f} of ${goal.target_amount:.2f}.",
                            related_entity_type="goal",
                            related_entity_id=str(goal.goal_id),
                            action_url=f"/goals/{goal.goal_id}"
                        )
                    alerts.append(alert)

        return alerts

    async def _check_unusual_spending(self, user_id: str) -> List[Alert]:
        """
        Check for unusual spending patterns (spending 2x average).
        """
        alerts = []

        # Get last 30 days of spending
        thirty_days_ago = datetime.now() - timedelta(days=30)
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.date >= thirty_days_ago.date(),
                Transaction.amount < 0  # Negative = spending
            )
        )
        recent_transactions = result.scalars().all()

        if len(recent_transactions) < 10:
            return alerts  # Not enough data

        # Calculate average daily spending
        total_spent = sum(abs(t.amount) for t in recent_transactions)
        avg_daily = total_spent / 30

        # Check today's spending
        today = datetime.now().date()
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.date == today,
                Transaction.amount < 0
            )
        )
        today_transactions = result.scalars().all()
        today_spent = sum(abs(t.amount) for t in today_transactions)

        # Alert if today's spending is 2x average
        if today_spent > (avg_daily * 2) and today_spent > 100:  # At least $100
            # Check if we already have this alert today
            existing = await self.db.execute(
                select(Alert).where(
                    Alert.user_id == user_id,
                    Alert.alert_type == "unusual_spending",
                    Alert.created_at >= datetime.now().replace(hour=0, minute=0, second=0),
                    Alert.is_dismissed == False
                )
            )

            if not existing.scalar_one_or_none():
                alert = Alert(
                    user_id=user_id,
                    alert_type="unusual_spending",
                    severity="warning",
                    title="Unusual Spending Detected",
                    message=f"Your spending today (${today_spent:.2f}) is higher than usual. Your average daily spending is ${avg_daily:.2f}.",
                    related_entity_type="transaction",
                    action_url="/transactions"
                )
                alerts.append(alert)

        return alerts

    async def _check_low_balance(self, user_id: str) -> List[Alert]:
        """
        Check for low balance alerts (balance < $100).
        """
        alerts = []

        # Get all checking/savings accounts
        result = await self.db.execute(
            select(Account).where(
                Account.user_id == user_id,
                Account.type == "depository"
            )
        )
        accounts = result.scalars().all()

        for account in accounts:
            if account.current_balance and account.current_balance < 100:
                # Check if we already have this alert
                existing = await self.db.execute(
                    select(Alert).where(
                        Alert.user_id == user_id,
                        Alert.alert_type == "low_balance",
                        Alert.related_entity_id == account.account_id,
                        Alert.is_dismissed == False
                    )
                )

                if existing.scalar_one_or_none():
                    continue

                alert = Alert(
                    user_id=user_id,
                    alert_type="low_balance",
                    severity="warning" if account.current_balance < 50 else "info",
                    title="Low Balance Alert",
                    message=f"Your {account.subtype or 'account'} balance is low: ${account.current_balance:.2f}",
                    related_entity_type="account",
                    related_entity_id=account.account_id,
                    action_url=f"/accounts/{account.account_id}"
                )
                alerts.append(alert)

        return alerts

    async def _check_subscription_renewals(self, user_id: str) -> List[Alert]:
        """
        Check for upcoming subscription renewals (within 3 days).
        """
        alerts = []

        # Get all active subscriptions with upcoming renewals
        three_days_from_now = (datetime.now() + timedelta(days=3)).date()
        today = datetime.now().date()

        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.next_billing_date >= today.isoformat(),
                Subscription.next_billing_date <= three_days_from_now.isoformat()
            )
        )
        subscriptions = result.scalars().all()

        for subscription in subscriptions:
            # Check if we already have this alert
            existing = await self.db.execute(
                select(Alert).where(
                    Alert.user_id == user_id,
                    Alert.alert_type == "subscription_renewal",
                    Alert.related_entity_id == str(subscription.subscription_id),
                    Alert.is_dismissed == False
                )
            )

            if existing.scalar_one_or_none():
                continue

            days_until = (datetime.fromisoformat(subscription.next_billing_date).date() - today).days

            alert = Alert(
                user_id=user_id,
                alert_type="subscription_renewal",
                severity="info",
                title=f"Upcoming Renewal: {subscription.merchant_name}",
                message=f"Your {subscription.merchant_name} subscription (${subscription.amount:.2f}) will renew in {days_until} day{'s' if days_until != 1 else ''}.",
                related_entity_type="subscription",
                related_entity_id=str(subscription.subscription_id),
                action_url=f"/subscriptions/{subscription.subscription_id}"
            )
            alerts.append(alert)

        return alerts

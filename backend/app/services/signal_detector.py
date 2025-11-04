from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Transaction, Account, Signal


class SignalDetector:
    """Detects behavioral financial signals from transaction data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_all_signals(self, user_id: str) -> List[Signal]:
        """Detect all signals for a user"""
        signals = []

        # Get user transactions
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date)
        )
        transactions = result.scalars().all()

        # Get user accounts
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        accounts = result.scalars().all()

        if not transactions:
            return signals

        # Detect each signal type
        signals.extend(await self.detect_subscriptions(user_id, transactions))
        signals.extend(await self.detect_savings_growth(user_id, accounts, transactions))
        signals.extend(await self.detect_credit_utilization(user_id, accounts))
        signals.extend(await self.detect_income_stability(user_id, transactions))

        return signals

    async def detect_subscriptions(
        self,
        user_id: str,
        transactions: List[Transaction]
    ) -> List[Signal]:
        """
        Detect recurring subscription payments.

        Algorithm:
        - Group transactions by merchant name
        - Check for recurring patterns (monthly, weekly, etc.)
        - Identify consistent amounts and intervals
        """
        signals = []
        merchant_transactions = defaultdict(list)

        # Group by merchant
        for txn in transactions:
            if txn.amount < 0 and txn.merchant_name:  # Only outgoing payments
                merchant_transactions[txn.merchant_name].append(txn)

        # Analyze each merchant for recurring patterns
        for merchant, txns in merchant_transactions.items():
            if len(txns) < 2:
                continue

            # Sort by date
            txns.sort(key=lambda x: x.date)

            # Check for consistent intervals and amounts
            intervals = []
            amounts = []

            for i in range(1, len(txns)):
                interval = (txns[i].date - txns[i-1].date).days
                intervals.append(interval)
                amounts.append(abs(txns[i].amount))

            if not intervals:
                continue

            # Calculate average interval and amount
            avg_interval = sum(intervals) / len(intervals)
            avg_amount = sum(amounts) / len(amounts)

            # Check if it's a subscription pattern
            # Monthly: 28-32 days, Weekly: 6-8 days, Yearly: 360-370 days
            is_recurring = False
            frequency = "unknown"

            if 28 <= avg_interval <= 32:
                is_recurring = True
                frequency = "monthly"
            elif 6 <= avg_interval <= 8:
                is_recurring = True
                frequency = "weekly"
            elif 360 <= avg_interval <= 370:
                is_recurring = True
                frequency = "yearly"

            # Check amount consistency (within 10% variance)
            amount_variance = max(amounts) - min(amounts) if amounts else 0
            amount_consistent = amount_variance / avg_amount <= 0.1 if avg_amount > 0 else False

            if is_recurring and amount_consistent and len(txns) >= 2:
                signal = Signal(
                    signal_id=f"sub_{user_id}_{merchant.replace(' ', '_')}_{datetime.utcnow().timestamp()}",
                    user_id=user_id,
                    signal_type="subscription_detected",
                    value=avg_amount,
                    details={
                        "merchant": merchant,
                        "frequency": frequency,
                        "average_amount": round(avg_amount, 2),
                        "interval_days": round(avg_interval, 1),
                        "occurrences": len(txns)
                    }
                )
                signals.append(signal)

        return signals

    async def detect_savings_growth(
        self,
        user_id: str,
        accounts: List[Account],
        transactions: List[Transaction]
    ) -> List[Signal]:
        """
        Detect savings growth patterns.

        Algorithm:
        - Identify savings accounts
        - Track balance trends over time
        - Calculate growth rate
        """
        signals = []

        for account in accounts:
            if account.subtype != "savings":
                continue

            # Get transactions for this savings account
            account_txns = [t for t in transactions if t.account_id == account.account_id]

            if len(account_txns) < 2:
                continue

            # Sort by date
            account_txns.sort(key=lambda x: x.date)

            # Calculate balance progression
            deposits = [t for t in account_txns if t.amount > 0]

            if len(deposits) >= 2:
                total_deposited = sum(abs(t.amount) for t in deposits)
                days_span = (account_txns[-1].date - account_txns[0].date).days

                if days_span > 0:
                    # Calculate monthly growth rate
                    monthly_rate = (total_deposited / days_span) * 30

                    if monthly_rate > 0:
                        signal = Signal(
                            signal_id=f"sav_{user_id}_{account.account_id}_{datetime.utcnow().timestamp()}",
                            user_id=user_id,
                            signal_type="savings_growth",
                            value=monthly_rate,
                            details={
                                "account_id": account.account_id,
                                "current_balance": round(account.current_balance, 2),
                                "monthly_growth_rate": round(monthly_rate, 2),
                                "total_deposits": round(total_deposited, 2),
                                "days_tracked": days_span
                            }
                        )
                        signals.append(signal)

        return signals

    async def detect_credit_utilization(
        self,
        user_id: str,
        accounts: List[Account]
    ) -> List[Signal]:
        """
        Detect credit utilization patterns.

        Algorithm:
        - Calculate utilization rate for credit accounts
        - Flag high utilization (>30%)
        """
        signals = []

        for account in accounts:
            if account.type != "credit" or not account.credit_limit:
                continue

            if account.credit_limit <= 0:
                continue

            # Calculate utilization rate
            utilization_rate = (account.current_balance / account.credit_limit) * 100

            signal = Signal(
                signal_id=f"cred_{user_id}_{account.account_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                signal_type="credit_utilization",
                value=utilization_rate,
                details={
                    "account_id": account.account_id,
                    "current_balance": round(account.current_balance, 2),
                    "credit_limit": round(account.credit_limit, 2),
                    "utilization_percent": round(utilization_rate, 2),
                    "status": "high" if utilization_rate > 30 else "healthy"
                }
            )
            signals.append(signal)

        return signals

    async def detect_income_stability(
        self,
        user_id: str,
        transactions: List[Transaction]
    ) -> List[Signal]:
        """
        Detect income stability patterns.

        Algorithm:
        - Identify income transactions
        - Calculate regularity and variance
        - Assess stability score
        """
        signals = []

        # Find income transactions (positive amounts with "Income" category)
        income_txns = [
            t for t in transactions
            if t.amount > 0 and t.category_primary == "Income"
        ]

        if len(income_txns) < 2:
            return signals

        # Sort by date
        income_txns.sort(key=lambda x: x.date)

        # Calculate intervals between income deposits
        intervals = []
        amounts = [t.amount for t in income_txns]

        for i in range(1, len(income_txns)):
            interval = (income_txns[i].date - income_txns[i-1].date).days
            intervals.append(interval)

        if not intervals:
            return signals

        # Calculate statistics
        avg_interval = sum(intervals) / len(intervals)
        avg_amount = sum(amounts) / len(amounts)

        # Calculate variance
        interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)

        # Stability score (0-100, higher is more stable)
        # Based on interval consistency and amount consistency
        interval_consistency = max(0, 100 - (interval_variance / avg_interval * 100)) if avg_interval > 0 else 0
        amount_consistency = max(0, 100 - (amount_variance / avg_amount * 100)) if avg_amount > 0 else 0

        stability_score = (interval_consistency + amount_consistency) / 2

        signal = Signal(
            signal_id=f"inc_{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            signal_type="income_stability",
            value=stability_score,
            details={
                "average_income": round(avg_amount, 2),
                "average_interval_days": round(avg_interval, 1),
                "stability_score": round(stability_score, 2),
                "income_count": len(income_txns),
                "status": "stable" if stability_score > 70 else "variable"
            }
        )
        signals.append(signal)

        return signals

    async def save_signals(self, signals: List[Signal]) -> int:
        """Save detected signals to database"""
        if not signals:
            return 0

        # Delete old signals for this user
        if signals:
            user_id = signals[0].user_id
            await self.db.execute(
                Signal.__table__.delete().where(Signal.user_id == user_id)
            )

        # Add new signals
        for signal in signals:
            self.db.add(signal)

        await self.db.commit()
        return len(signals)

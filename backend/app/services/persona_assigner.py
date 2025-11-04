from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Signal, Persona, User


# Persona type definitions per rubric specification
PERSONA_DEFINITIONS = {
    # Persona 1: High Utilization (highest priority)
    "high_utilization": {
        "priority": 1,
        "description": "Any card utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR is_overdue = true",
        "criteria": {
            "signal_types": ["credit_utilization"],
            "min_utilization": 50  # ≥50% per rubric
        },
        "focus": "Reduce utilization and interest; payment planning and autopay education"
    },
    # Persona 2: Variable Income Budgeter
    "variable_income_budgeter": {
        "priority": 2,
        "description": "Median pay gap > 45 days AND cash-flow buffer < 1 month",
        "criteria": {
            "signal_types": ["income_stability"],
            "min_median_pay_gap": 45,  # > 45 days per rubric
            "max_cashflow_buffer": 1  # < 1 month
        },
        "focus": "Percent-based budgets, emergency fund basics, smoothing strategies"
    },
    # Persona 3: Subscription-Heavy
    "subscription_heavy": {
        "priority": 3,
        "description": "Recurring merchants ≥3 AND (monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)",
        "criteria": {
            "signal_types": ["subscription_detected"],
            "min_subscriptions": 3,
            "min_monthly_spend": 50  # ≥$50 in 30d window
        },
        "focus": "Subscription audit, cancellation/negotiation tips, bill alerts"
    },
    # Persona 4: Savings Builder
    "savings_builder": {
        "priority": 4,
        "description": "Savings growth rate ≥2% over window OR net savings inflow ≥$200/month, AND all card utilizations < 30%",
        "criteria": {
            "signal_types": ["savings_growth", "credit_utilization"],
            "min_growth_rate": 200,  # ≥$200/month per rubric
            "max_credit_utilization": 30  # < 30%
        },
        "focus": "Goal setting, automation, APY optimization (HYSA/CD basics)"
    },
    # Persona 5: Financial Wellness Achiever (custom persona)
    "financial_wellness_achiever": {
        "priority": 5,
        "description": "User with stable income, healthy credit, and active savings (all systems optimal)",
        "criteria": {
            "signal_types": ["income_stability", "credit_utilization", "savings_growth"],
            "min_stability_score": 70,
            "max_credit_utilization": 30,
            "min_growth_rate": 100
        },
        "focus": "Advanced wealth building, investment education, tax optimization, retirement planning"
    }
}


class PersonaAssigner:
    """Assigns financial personas to users based on their signals"""

    def __init__(self, db: AsyncSession, window_days: int = 180):
        self.db = db
        self.window_days = window_days

    async def assign_personas(self, user_id: str) -> List[Persona]:
        """
        Assign personas to a user based on their signals.
        Returns assigned personas in priority order.

        Per rubric: assigns personas based on signals from the specified time window.
        """
        # Check user exists and has consent
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        if not user.consent_status:
            raise ValueError(f"User {user_id} has not granted consent")

        # Get user signals for this time window only
        result = await self.db.execute(
            select(Signal).where(Signal.user_id == user_id)
        )
        all_signals = result.scalars().all()

        # Filter signals by window_days
        signals = [s for s in all_signals if s.details.get("window_days") == self.window_days]

        # Evaluate each persona
        assigned_personas = []

        for persona_type, definition in PERSONA_DEFINITIONS.items():
            if self._meets_criteria(signals, definition["criteria"]):
                persona = Persona(
                    user_id=user_id,
                    window_days=self.window_days,
                    persona_type=persona_type,
                    priority_rank=definition["priority"],
                    criteria_met=self._format_criteria_met(signals, definition["criteria"])
                )
                assigned_personas.append(persona)

        # If no personas assigned, user doesn't match any specific persona for this window
        # Don't assign default - let operator see no match

        # Sort by priority (lower number = higher priority)
        assigned_personas.sort(key=lambda p: p.priority_rank)

        return assigned_personas

    def _meets_criteria(self, signals: List[Signal], criteria: Dict) -> bool:
        """Check if signals meet persona criteria per rubric specification"""

        if "signal_types" not in criteria:
            return False

        relevant_signals = [
            s for s in signals
            if s.signal_type in criteria["signal_types"]
        ]

        if not relevant_signals:
            return False

        # Persona 1: High Utilization - any card ≥50% utilization
        if "min_utilization" in criteria:
            for signal in relevant_signals:
                if signal.signal_type == "credit_utilization":
                    if signal.value >= criteria["min_utilization"]:
                        return True
            return False

        # Persona 2: Variable Income Budgeter - median pay gap > 45 days AND cashflow < 1 month
        if "min_median_pay_gap" in criteria:
            for signal in relevant_signals:
                if signal.signal_type == "income_stability":
                    median_pay_gap = signal.details.get("median_pay_gap_days", 0)
                    # TODO: Implement cashflow buffer calculation
                    # For now, just check median pay gap
                    if median_pay_gap > criteria["min_median_pay_gap"]:
                        return True
            return False

        # Persona 3: Subscription-Heavy - ≥3 subscriptions AND ≥$50/month spend
        if "min_subscriptions" in criteria:
            subscription_signals = [s for s in relevant_signals if s.signal_type == "subscription_detected"]
            if len(subscription_signals) < criteria["min_subscriptions"]:
                return False

            # Check total monthly spend
            total_monthly_spend = sum(s.value for s in subscription_signals)
            if total_monthly_spend >= criteria.get("min_monthly_spend", 0):
                return True
            return False

        # Persona 4: Savings Builder - ≥$200/month AND all credit < 30%
        if "min_growth_rate" in criteria and "max_credit_utilization" in criteria:
            # Check savings growth
            has_good_savings = False
            for signal in signals:  # Check all signals
                if signal.signal_type == "savings_growth":
                    if signal.value >= criteria["min_growth_rate"]:
                        has_good_savings = True
                        break

            if not has_good_savings:
                return False

            # Check ALL credit cards are below 30%
            credit_signals = [s for s in signals if s.signal_type == "credit_utilization"]
            if credit_signals:
                for signal in credit_signals:
                    if signal.value >= criteria["max_credit_utilization"]:
                        return False  # Any card ≥30% disqualifies

            return True

        # Persona 5: Financial Wellness Achiever - stable income + healthy credit + active savings
        if "min_stability_score" in criteria and "max_credit_utilization" in criteria and "min_growth_rate" in criteria:
            has_stable_income = False
            has_healthy_credit = True
            has_active_savings = False

            for signal in signals:
                if signal.signal_type == "income_stability":
                    if signal.value >= criteria["min_stability_score"]:
                        has_stable_income = True

                if signal.signal_type == "credit_utilization":
                    if signal.value >= criteria["max_credit_utilization"]:
                        has_healthy_credit = False

                if signal.signal_type == "savings_growth":
                    if signal.value >= criteria["min_growth_rate"]:
                        has_active_savings = True

            return has_stable_income and has_healthy_credit and has_active_savings

        return False

    def _format_criteria_met(self, signals: List[Signal], criteria: Dict) -> str:
        """Format a human-readable string of criteria met"""
        met_criteria = []

        if "max_signals" in criteria:
            met_criteria.append(f"signals_count={len(signals)}")

        if "signal_types" in criteria:
            relevant_signals = [
                s for s in signals
                if s.signal_type in criteria["signal_types"]
            ]

            for signal in relevant_signals:
                if signal.signal_type == "subscription_detected":
                    merchant = signal.details.get("merchant", "unknown")
                    met_criteria.append(f"subscription:{merchant}")
                elif signal.signal_type == "savings_growth":
                    rate = signal.details.get("monthly_growth_rate", 0)
                    met_criteria.append(f"savings_growth:${rate:.2f}/mo")
                elif signal.signal_type == "credit_utilization":
                    util = signal.details.get("utilization_percent", 0)
                    met_criteria.append(f"credit_util:{util:.1f}%")
                elif signal.signal_type == "income_stability":
                    score = signal.details.get("stability_score", 0)
                    met_criteria.append(f"income_stability:{score:.0f}/100")

        return ", ".join(met_criteria) if met_criteria else "none"

    async def save_personas(self, user_id: str, personas: List[Persona]) -> int:
        """Save personas to database, replacing any existing ones"""
        # Delete existing personas for this user
        await self.db.execute(
            delete(Persona).where(Persona.user_id == user_id)
        )

        # Add new personas
        for persona in personas:
            self.db.add(persona)

        await self.db.commit()
        return len(personas)

    async def get_primary_persona(self, user_id: str) -> Optional[Persona]:
        """Get the highest priority persona for a user"""
        result = await self.db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.priority_rank)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_personas(self, user_id: str) -> List[Persona]:
        """Get all personas for a user, ordered by priority"""
        result = await self.db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.priority_rank)
        )
        return result.scalars().all()

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Signal, Persona, User


# Persona type definitions with criteria
PERSONA_DEFINITIONS = {
    "subscription_optimizer": {
        "priority": 1,
        "description": "User with multiple subscriptions that could be optimized",
        "criteria": {
            "min_subscriptions": 3,
            "signal_types": ["subscription_detected"]
        }
    },
    "savings_builder": {
        "priority": 2,
        "description": "User showing positive savings growth trends",
        "criteria": {
            "signal_types": ["savings_growth"],
            "min_growth_rate": 100  # $100/month minimum
        }
    },
    "credit_optimizer": {
        "priority": 3,
        "description": "User with high credit utilization that needs optimization",
        "criteria": {
            "signal_types": ["credit_utilization"],
            "min_utilization": 30  # 30% or higher
        }
    },
    "income_stable": {
        "priority": 4,
        "description": "User with stable, predictable income",
        "criteria": {
            "signal_types": ["income_stability"],
            "min_stability_score": 70
        }
    },
    "financial_newcomer": {
        "priority": 5,
        "description": "User with limited financial signals (default persona)",
        "criteria": {
            "max_signals": 1
        }
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
        """
        # Check user exists and has consent
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        if not user.consent_status:
            raise ValueError(f"User {user_id} has not granted consent")

        # Get user signals
        result = await self.db.execute(
            select(Signal).where(Signal.user_id == user_id)
        )
        signals = result.scalars().all()

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

        # If no personas assigned, assign default newcomer persona
        if not assigned_personas:
            persona = Persona(
                user_id=user_id,
                window_days=self.window_days,
                persona_type="financial_newcomer",
                priority_rank=PERSONA_DEFINITIONS["financial_newcomer"]["priority"],
                criteria_met="default_assignment"
            )
            assigned_personas.append(persona)

        # Sort by priority (lower number = higher priority)
        assigned_personas.sort(key=lambda p: p.priority_rank)

        return assigned_personas

    def _meets_criteria(self, signals: List[Signal], criteria: Dict) -> bool:
        """Check if signals meet persona criteria"""

        # Check max_signals (for newcomer persona)
        if "max_signals" in criteria:
            return len(signals) <= criteria["max_signals"]

        # Check required signal types
        if "signal_types" in criteria:
            relevant_signals = [
                s for s in signals
                if s.signal_type in criteria["signal_types"]
            ]

            if not relevant_signals:
                return False

            # Check specific criteria based on persona type
            if "min_subscriptions" in criteria:
                subscription_count = len([
                    s for s in relevant_signals
                    if s.signal_type == "subscription_detected"
                ])
                if subscription_count < criteria["min_subscriptions"]:
                    return False

            if "min_growth_rate" in criteria:
                for signal in relevant_signals:
                    if signal.signal_type == "savings_growth":
                        if signal.value >= criteria["min_growth_rate"]:
                            return True
                return False

            if "min_utilization" in criteria:
                for signal in relevant_signals:
                    if signal.signal_type == "credit_utilization":
                        if signal.value >= criteria["min_utilization"]:
                            return True
                return False

            if "min_stability_score" in criteria:
                for signal in relevant_signals:
                    if signal.signal_type == "income_stability":
                        if signal.value >= criteria["min_stability_score"]:
                            return True
                return False

            return True

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

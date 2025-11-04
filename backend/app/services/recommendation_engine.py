from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Persona, Signal, Recommendation, User
from app.services.guardrails import GuardrailsService, GuardrailViolation


# Recommendation templates by persona type
RECOMMENDATION_TEMPLATES = {
    "subscription_heavy": [
        {
            "content_type": "article",
            "title": "How to Review and Cancel Unused Subscriptions",
            "description": "Learn simple steps to identify subscriptions you don't use and how to cancel them safely.",
            "eligibility_check": lambda signals: len([s for s in signals if s.signal_type == "subscription_detected"]) >= 3,
            "rationale_template": "We noticed you have {sub_count} active subscriptions totaling ${total_amount:.2f} per month. Here's a strategy to review each one and decide which to keep."
        },
        {
            "content_type": "calculator",
            "title": "Subscription Savings Calculator",
            "description": "See how much you could save by canceling subscriptions you rarely use.",
            "eligibility_check": lambda signals: len([s for s in signals if s.signal_type == "subscription_detected"]) >= 2,
            "rationale_template": "We noticed you have {sub_count} subscriptions. This calculator could help you see your potential annual savings."
        },
        {
            "content_type": "guide",
            "title": "Alternatives to Expensive Subscriptions",
            "description": "Discover free or cheaper alternatives to popular subscription services.",
            "eligibility_check": lambda signals: any(s.value > 20 for s in signals if s.signal_type == "subscription_detected"),
            "rationale_template": "We noticed you're spending ${max_sub:.2f}/month on your most expensive subscription. Here are some options for similar free alternatives."
        },
        {
            "content_type": "video",
            "title": "Managing Multiple Subscriptions: Tips from Real People",
            "description": "Watch how others successfully cut their subscription costs without missing out.",
            "eligibility_check": lambda signals: len([s for s in signals if s.signal_type == "subscription_detected"]) >= 3,
            "rationale_template": "With {sub_count} active subscriptions, you might consider learning from others who successfully reduced their monthly costs."
        }
    ],
    "savings_builder": [
        {
            "content_type": "article",
            "title": "The 50/30/20 Budget Rule Explained Simply",
            "description": "Learn an easy budgeting method that helped millions save more money each month.",
            "eligibility_check": lambda signals: any(s.signal_type == "savings_growth" for s in signals),
            "rationale_template": "We noticed you're already saving ${growth_rate:.2f} per month. This budgeting method could help you save even more."
        },
        {
            "content_type": "calculator",
            "title": "Savings Goal Calculator",
            "description": "Figure out exactly how much to save each month to reach your goals.",
            "eligibility_check": lambda signals: any(s.signal_type == "savings_growth" for s in signals),
            "rationale_template": "At your current rate of ${growth_rate:.2f}/month, here's a strategy to see when you'll reach different savings goals."
        },
        {
            "content_type": "guide",
            "title": "High-Yield Savings Accounts: What You Need to Know",
            "description": "Discover how to earn more interest on the money you're already saving.",
            "eligibility_check": lambda signals: any(s.value >= 200 for s in signals if s.signal_type == "savings_growth"),
            "rationale_template": "We noticed your savings are growing by ${growth_rate:.2f}/month. A high-yield account could help you earn extra interest."
        },
        {
            "content_type": "article",
            "title": "Automatic Savings: Set It and Forget It",
            "description": "Learn how to automate your savings so you never have to think about it.",
            "eligibility_check": lambda signals: any(s.signal_type == "savings_growth" for s in signals),
            "rationale_template": "We noticed you're already building good savings habits. Here's an option to make saving ${growth_rate:.2f}/month even easier through automation."
        }
    ],
    "high_utilization": [
        {
            "content_type": "article",
            "title": "Understanding Credit Utilization: Why 30% Matters",
            "description": "Learn why keeping your credit card balance below 30% helps your credit score.",
            "eligibility_check": lambda signals: any(s.value >= 30 for s in signals if s.signal_type == "credit_utilization"),
            "rationale_template": "We noticed your credit card is {util_percent:.0f}% used. Here's a strategy that explains how lowering it could help improve your credit score."
        },
        {
            "content_type": "calculator",
            "title": "Credit Payoff Calculator",
            "description": "See how different payment amounts affect when you'll be debt-free.",
            "eligibility_check": lambda signals: any(s.signal_type == "credit_utilization" for s in signals),
            "rationale_template": "With a balance of ${balance:.2f}, you might consider using this calculator to see how quickly you can pay it off with different payment plans."
        },
        {
            "content_type": "guide",
            "title": "Debt Avalanche vs. Debt Snowball: Which Is Right for You?",
            "description": "Compare two popular strategies for paying off credit card debt faster.",
            "eligibility_check": lambda signals: any(s.value >= 50 for s in signals if s.signal_type == "credit_utilization"),
            "rationale_template": "With {util_percent:.0f}% credit utilization, here are some options for payoff strategies that could work best for your situation."
        },
        {
            "content_type": "article",
            "title": "How to Request a Credit Limit Increase",
            "description": "Learn when and how to ask for a higher limit to lower your utilization ratio.",
            "eligibility_check": lambda signals: any(30 <= s.value < 70 for s in signals if s.signal_type == "credit_utilization"),
            "rationale_template": "At {util_percent:.0f}% utilization, you might consider a credit limit increase, which could help improve your credit score."
        }
    ],
    "variable_income_budgeter": [
        {
            "content_type": "article",
            "title": "Building an Emergency Fund: A Beginner's Guide",
            "description": "Learn how to build a safety net for unexpected expenses.",
            "eligibility_check": lambda signals: any(s.value >= 70 for s in signals if s.signal_type == "income_stability"),
            "rationale_template": "We noticed your stable income of ${avg_income:.2f} every two weeks. Here's a strategy to start an emergency fund that could work for you."
        },
        {
            "content_type": "guide",
            "title": "Introduction to Retirement Accounts: 401(k) and IRA Basics",
            "description": "Simple explanations of retirement savings options and how they work.",
            "eligibility_check": lambda signals: any(s.value >= 80 for s in signals if s.signal_type == "income_stability"),
            "rationale_template": "With your consistent income, you have the option to contribute to retirement accounts. Here are some basics to help you get started."
        },
        {
            "content_type": "calculator",
            "title": "Net Worth Calculator",
            "description": "Calculate your net worth and track your financial progress over time.",
            "eligibility_check": lambda signals: any(s.signal_type == "income_stability" for s in signals),
            "rationale_template": "With your stable income, this could help you track your net worth and see your financial growth over time."
        },
        {
            "content_type": "article",
            "title": "Side Income Ideas for People with Regular Jobs",
            "description": "Explore realistic ways to earn extra money without quitting your day job.",
            "eligibility_check": lambda signals: any(s.value >= 70 for s in signals if s.signal_type == "income_stability"),
            "rationale_template": "We noticed your stable main income of ${avg_income:.2f}. Here are some options for building additional income streams."
        }
    ],
    "financial_wellness_achiever": [
        {
            "content_type": "article",
            "title": "Personal Finance 101: The Basics Everyone Should Know",
            "description": "Start your financial journey with these fundamental money management concepts.",
            "eligibility_check": lambda signals: True,
            "rationale_template": "As you're starting your financial journey, we'd like to share this article that covers essential basics that could help you."
        },
        {
            "content_type": "guide",
            "title": "Creating Your First Budget in 5 Easy Steps",
            "description": "A simple guide to tracking where your money goes each month.",
            "eligibility_check": lambda signals: True,
            "rationale_template": "You might consider building a budget as a first step to taking control of your finances. This guide could help make it simple."
        },
        {
            "content_type": "video",
            "title": "Banking Basics: Checking vs. Savings Accounts",
            "description": "Learn the difference between account types and which one you need.",
            "eligibility_check": lambda signals: True,
            "rationale_template": "Here's an opportunity to understand different account types, which could help you make smart banking decisions from the start."
        },
        {
            "content_type": "calculator",
            "title": "Monthly Budget Calculator",
            "description": "A simple tool to help you see where your money is going.",
            "eligibility_check": lambda signals: True,
            "rationale_template": "You might consider using this calculator to get started tracking your income and expenses each month."
        }
    ]
}


class RecommendationEngine:
    """Generates personalized educational recommendations based on user personas"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.guardrails = GuardrailsService(db)

    async def generate_recommendations(self, user_id: str, max_recommendations: int = 5) -> List[Recommendation]:
        """
        Generate personalized recommendations for a user based on their persona.
        Returns 3-5 recommendations that meet eligibility criteria.

        Applies comprehensive guardrails including:
        - User eligibility checks
        - Content safety validation
        - Rate limiting
        - Vulnerable population protections
        """
        # Validate user eligibility (includes consent, age, data sufficiency)
        is_eligible, reason = await self.guardrails.validate_user_eligibility(user_id)
        if not is_eligible:
            raise GuardrailViolation(reason, "user_eligibility")

        # Get user
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        # Get user's primary persona
        result = await self.db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.priority_rank)
            .limit(1)
        )
        persona = result.scalar_one_or_none()

        if not persona:
            raise ValueError(f"No persona assigned to user {user_id}")

        # Get user signals for eligibility checks and rationale
        result = await self.db.execute(
            select(Signal).where(Signal.user_id == user_id)
        )
        signals = result.scalars().all()

        # Get templates for this persona
        templates = RECOMMENDATION_TEMPLATES.get(persona.persona_type, [])

        # Generate recommendations as dictionaries first (for guardrail validation)
        recommendations_dict = []
        for template in templates:
            if len(recommendations_dict) >= max_recommendations:
                break

            # Check eligibility
            eligibility_met = template["eligibility_check"](signals)

            if not eligibility_met:
                continue

            # Generate rationale
            rationale = self._generate_rationale(
                template["rationale_template"],
                signals,
                persona.persona_type
            )

            rec_dict = {
                "user_id": user_id,
                "persona_type": persona.persona_type,
                "content_type": template["content_type"],
                "title": template["title"],
                "description": template["description"],
                "rationale": rationale,
                "eligibility_met": eligibility_met,
            }

            recommendations_dict.append(rec_dict)

        # Ensure we have at least 3 recommendations
        if len(recommendations_dict) < 3:
            # Add fallback recommendations without strict eligibility
            for template in templates:
                if len(recommendations_dict) >= max_recommendations:
                    break

                # Skip if already added
                if any(r["title"] == template["title"] for r in recommendations_dict):
                    continue

                rationale = self._generate_rationale(
                    template["rationale_template"],
                    signals,
                    persona.persona_type
                )

                rec_dict = {
                    "user_id": user_id,
                    "persona_type": persona.persona_type,
                    "content_type": template["content_type"],
                    "title": template["title"],
                    "description": template["description"],
                    "rationale": rationale,
                    "eligibility_met": False,
                }

                recommendations_dict.append(rec_dict)

        # Apply guardrails validation
        is_valid, reason, filtered_recs = await self.guardrails.validate_recommendation_batch(
            user_id,
            recommendations_dict
        )

        if not is_valid:
            raise GuardrailViolation(reason, "batch_validation")

        # Convert to Recommendation objects
        recommendations = []
        for rec_dict in filtered_recs[:max_recommendations]:
            recommendation = Recommendation(
                user_id=rec_dict["user_id"],
                persona_type=rec_dict["persona_type"],
                content_type=rec_dict["content_type"],
                title=rec_dict["title"],
                description=rec_dict["description"],
                rationale=rec_dict["rationale"],
                disclaimer=rec_dict.get("disclaimer"),
                eligibility_met=rec_dict["eligibility_met"],
                approval_status="approved"  # Auto-approve after guardrail validation
            )
            recommendations.append(recommendation)

        return recommendations

    def _generate_rationale(self, template: str, signals: List[Signal], persona_type: str) -> str:
        """Generate a personalized rationale based on user signals"""
        # Extract relevant data from signals
        data = {}

        if persona_type == "subscription_heavy":
            sub_signals = [s for s in signals if s.signal_type == "subscription_detected"]
            data["sub_count"] = len(sub_signals)
            data["total_amount"] = sum(s.value for s in sub_signals)
            if sub_signals:
                data["max_sub"] = max(s.value for s in sub_signals)

        elif persona_type == "savings_builder":
            savings_signals = [s for s in signals if s.signal_type == "savings_growth"]
            if savings_signals:
                data["growth_rate"] = savings_signals[0].value

        elif persona_type == "high_utilization":
            credit_signals = [s for s in signals if s.signal_type == "credit_utilization"]
            if credit_signals:
                signal = credit_signals[0]
                data["util_percent"] = signal.value
                if signal.details:
                    data["balance"] = signal.details.get("current_balance", 0)

        elif persona_type == "variable_income_budgeter":
            income_signals = [s for s in signals if s.signal_type == "income_stability"]
            if income_signals and income_signals[0].details:
                data["avg_income"] = income_signals[0].details.get("average_income", 0)

        # Format the template with available data
        try:
            return template.format(**data)
        except KeyError:
            # If data is missing, return a generic rationale
            return "This content is recommended based on your financial profile."

    async def save_recommendations(self, user_id: str, recommendations: List[Recommendation]) -> int:
        """Save recommendations to database, replacing any existing ones"""
        # Delete existing recommendations for this user
        await self.db.execute(
            delete(Recommendation).where(Recommendation.user_id == user_id)
        )

        # Add new recommendations
        for recommendation in recommendations:
            self.db.add(recommendation)

        await self.db.commit()
        return len(recommendations)

    async def get_recommendations(self, user_id: str) -> List[Recommendation]:
        """Get all recommendations for a user"""
        result = await self.db.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
        )
        return result.scalars().all()

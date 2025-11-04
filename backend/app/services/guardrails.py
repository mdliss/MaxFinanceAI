from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Recommendation, Transaction, Signal


class GuardrailViolation(Exception):
    """Raised when a guardrail check fails"""
    def __init__(self, message: str, violation_type: str):
        self.message = message
        self.violation_type = violation_type
        super().__init__(self.message)


# Content risk levels
CONTENT_RISK_LEVELS = {
    "article": "low",
    "calculator": "low",
    "guide": "low",
    "video": "low",
}

# Prohibited content patterns
PROHIBITED_PATTERNS = [
    "invest in",
    "buy stock",
    "cryptocurrency investment",
    "guaranteed returns",
    "get rich quick",
    "payday loan",
    "cash advance",
    "binary options",
    "forex trading",
    "penny stocks",
]

# Tone Guardrails - Prohibited shaming/judgmental language
PROHIBITED_TONE_PATTERNS = [
    # Shaming language
    "you're drowning in debt",
    "terrible choices",
    "bad financial habits",
    "you're overspending",
    "poor decisions",
    "irresponsible",
    "reckless spending",
    "wasting money",
    "stupid mistake",
    "foolish",

    # Judgmental phrases
    "you should have",
    "you need to stop",
    "what were you thinking",
    "you can't afford",
    "you're being careless",

    # Panic-inducing warnings
    "you're in serious trouble",
    "financial disaster",
    "you'll go broke",
    "financial ruin",
    "hopeless situation",
    "too late",
    "beyond help",

    # Condescending tone
    "obviously you",
    "anyone knows",
    "it's simple",
    "just stop",
    "clearly you don't",

    # Absolute demands
    "you must",
    "you have to",
    "you need to immediately",
    "do this now",
]

# Required empowering/supportive patterns (these are encouraged)
EMPOWERING_PATTERNS = [
    "we noticed",
    "you might consider",
    "here's a strategy",
    "opportunity to",
    "could help",
    "here are some options",
    "you have the option",
    "consider trying",
    "one approach is",
    "this could",
]

# Required disclaimers by content type
REQUIRED_DISCLAIMERS = {
    "calculator": "This calculator provides estimates only. Results may vary based on your specific situation.",
    "guide": "This is educational content only and not financial advice. Consult a licensed professional for personalized guidance.",
    "article": "This content is for educational purposes only and should not be considered financial advice.",
    "video": "Educational content only. Not a substitute for professional financial advice.",
}


class GuardrailsService:
    """Enforces safety and compliance rules for financial recommendations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_user_eligibility(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user is eligible to receive recommendations.
        Returns (is_eligible, reason_if_not)
        """
        # Get user
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False, "User not found"

        # Check consent
        if not user.consent_status:
            return False, "User has not granted consent for data processing"

        # Check age (must be 18+)
        if user.age and user.age < 18:
            return False, "User must be 18 or older to receive recommendations"

        # Check for sufficient data (at least 10 transactions)
        result = await self.db.execute(
            select(func.count(Transaction.transaction_id))
            .where(Transaction.user_id == user_id)
        )
        transaction_count = result.scalar()

        if transaction_count < 10:
            return False, f"Insufficient transaction data ({transaction_count} transactions, minimum 10 required)"

        # Check for at least one signal
        result = await self.db.execute(
            select(func.count(Signal.signal_id))
            .where(Signal.user_id == user_id)
        )
        signal_count = result.scalar()

        if signal_count < 1:
            return False, "No behavioral signals detected yet"

        return True, None

    def check_vulnerable_population(self, user: User) -> Tuple[bool, Optional[str]]:
        """
        Check if user is in a vulnerable population requiring extra protection.
        Returns (is_vulnerable, protection_message)
        """
        # Elderly users (65+) - provide simpler, more conservative recommendations
        if user.age and user.age >= 65:
            return True, "User is 65+ (senior protection active)"

        # Very low income users - avoid any debt-related content
        if user.income_level and user.income_level.lower() in ["very_low", "low"]:
            return True, "User has low income (debt avoidance protection active)"

        # Very young adults (18-21) - provide educational basics
        if user.age and 18 <= user.age <= 21:
            return True, "User is 18-21 (young adult education focus)"

        return False, None

    async def check_rate_limits(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limits for recommendations.
        Returns (is_within_limits, reason_if_not)
        """
        # Max 10 recommendations per week
        week_ago = datetime.now() - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id))
            .where(
                Recommendation.user_id == user_id,
                Recommendation.created_at >= week_ago
            )
        )
        recent_count = result.scalar()

        if recent_count >= 10:
            return False, f"Weekly recommendation limit reached ({recent_count}/10)"

        # No more than 1 recommendation generation per day
        day_ago = datetime.now() - timedelta(days=1)
        result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id))
            .where(
                Recommendation.user_id == user_id,
                Recommendation.created_at >= day_ago
            )
        )
        today_count = result.scalar()

        if today_count > 0:
            return False, "Recommendations already generated today. Please wait 24 hours."

        return True, None

    def validate_content_safety(self, title: str, description: str, content_type: str) -> Tuple[bool, Optional[str]]:
        """
        Check if content meets safety standards.
        Returns (is_safe, reason_if_not)
        """
        combined_text = f"{title} {description}".lower()

        # Check for prohibited patterns
        for pattern in PROHIBITED_PATTERNS:
            if pattern in combined_text:
                return False, f"Content contains prohibited pattern: '{pattern}'"

        # Validate content type
        if content_type not in CONTENT_RISK_LEVELS:
            return False, f"Unknown content type: {content_type}"

        # Check risk level (only allow low-risk educational content)
        risk_level = CONTENT_RISK_LEVELS[content_type]
        if risk_level != "low":
            return False, f"Content risk level too high: {risk_level}"

        return True, None

    def get_required_disclaimer(self, content_type: str) -> str:
        """Get the required disclaimer for a content type"""
        return REQUIRED_DISCLAIMERS.get(
            content_type,
            "This is educational content only and not financial advice."
        )

    def validate_tone(self, text: str) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Check if content meets tone guardrail standards.
        Returns (is_appropriate, reason_if_not, violations_list)

        Ensures content is:
        - Empowering, not shaming
        - Neutral, not judgmental
        - Supportive, not panic-inducing
        - Respectful, not condescending
        - Suggestive, not demanding
        """
        text_lower = text.lower()
        violations = []

        # Check for prohibited tone patterns
        for pattern in PROHIBITED_TONE_PATTERNS:
            if pattern in text_lower:
                violations.append(pattern)

        if violations:
            return False, f"Content contains inappropriate tone ({len(violations)} violation(s))", violations

        # Check for at least one empowering pattern (encourage good tone)
        has_empowering = any(pattern in text_lower for pattern in EMPOWERING_PATTERNS)

        if not has_empowering and len(text.split()) > 10:
            # Only warn for longer text (>10 words)
            return False, "Content lacks empowering/supportive language. Consider using phrases like 'we noticed', 'you might consider', 'here's a strategy', etc.", []

        return True, None, None

    def suggest_tone_improvements(self, text: str) -> List[str]:
        """
        Suggest improvements to make content more empowering and supportive.
        Returns list of suggestions.
        """
        suggestions = []
        text_lower = text.lower()

        # Detect patterns that could be improved
        if "you must" in text_lower or "you have to" in text_lower:
            suggestions.append("Replace 'you must' with 'you might consider' or 'one option is'")

        if "bad" in text_lower or "terrible" in text_lower or "poor" in text_lower:
            suggestions.append("Replace negative adjectives with neutral observations")

        if "stop" in text_lower and "you" in text_lower:
            suggestions.append("Replace 'stop' commands with alternative suggestions")

        if not any(pattern in text_lower for pattern in EMPOWERING_PATTERNS):
            suggestions.append("Add empowering language like 'we noticed', 'you could try', or 'here's a strategy'")

        return suggestions

    async def apply_vulnerable_population_filters(
        self,
        user: User,
        recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Filter and adjust recommendations for vulnerable populations.
        Returns filtered list of recommendations.
        """
        is_vulnerable, reason = self.check_vulnerable_population(user)

        if not is_vulnerable:
            return recommendations

        filtered = []

        for rec in recommendations:
            title_lower = rec.get("title", "").lower()
            desc_lower = rec.get("description", "").lower()

            # For elderly users: avoid complex financial instruments
            if user.age and user.age >= 65:
                if any(term in title_lower or term in desc_lower for term in ["retirement", "401k", "ira", "invest"]):
                    # Skip investment-related content for seniors
                    continue

            # For low-income users: avoid debt and credit content
            if user.income_level and user.income_level.lower() in ["very_low", "low"]:
                if any(term in title_lower or term in desc_lower for term in ["credit", "debt", "loan", "borrow"]):
                    # Skip debt-related content for low-income users
                    continue

            # For young adults (18-21): focus on basics only
            if user.age and 18 <= user.age <= 21:
                if any(term in title_lower or term in desc_lower for term in ["retirement", "investment", "stock", "401k"]):
                    # Skip advanced topics for young adults
                    continue

            filtered.append(rec)

        return filtered

    async def validate_recommendation_batch(
        self,
        user_id: str,
        recommendations: List[Dict]
    ) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        Comprehensive validation of a batch of recommendations.
        Returns (is_valid, reason_if_not, filtered_recommendations)
        """
        # 1. Check user eligibility
        is_eligible, reason = await self.validate_user_eligibility(user_id)
        if not is_eligible:
            raise GuardrailViolation(reason, "user_eligibility")

        # 2. Check rate limits
        within_limits, reason = await self.check_rate_limits(user_id)
        if not within_limits:
            raise GuardrailViolation(reason, "rate_limit")

        # 3. Get user for vulnerable population checks
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        # 4. Validate each recommendation's content safety
        for rec in recommendations:
            is_safe, reason = self.validate_content_safety(
                rec.get("title", ""),
                rec.get("description", ""),
                rec.get("content_type", "")
            )
            if not is_safe:
                raise GuardrailViolation(reason, "content_safety")

            # 4a. Validate tone guardrails
            combined_text = f"{rec.get('title', '')} {rec.get('description', '')} {rec.get('rationale', '')}"
            is_appropriate, tone_reason, violations = self.validate_tone(combined_text)
            if not is_appropriate:
                violation_details = f" Violations: {violations}" if violations else ""
                raise GuardrailViolation(
                    f"{tone_reason}{violation_details}",
                    "tone_violation"
                )

            # Add required disclaimer
            disclaimer = self.get_required_disclaimer(rec.get("content_type", ""))
            rec["disclaimer"] = disclaimer

        # 5. Apply vulnerable population filters
        filtered_recs = await self.apply_vulnerable_population_filters(user, recommendations)

        # 6. Ensure minimum recommendations
        if len(filtered_recs) < 2:
            return False, "Insufficient safe recommendations after filtering", filtered_recs

        return True, None, filtered_recs

    async def log_guardrail_check(
        self,
        user_id: str,
        check_type: str,
        passed: bool,
        details: Optional[str] = None
    ):
        """Log guardrail checks for audit purposes"""
        # This could be extended to write to AuditLog table
        # For now, just pass (logging infrastructure could be added later)
        pass

    def get_guardrail_summary(self) -> Dict:
        """Return a summary of active guardrail rules"""
        return {
            "user_eligibility_rules": {
                "minimum_age": 18,
                "requires_consent": True,
                "minimum_transactions": 10,
                "minimum_signals": 1,
            },
            "content_safety_rules": {
                "allowed_risk_levels": ["low"],
                "prohibited_patterns": PROHIBITED_PATTERNS,
                "required_disclaimers": True,
            },
            "tone_guardrails": {
                "prohibited_tone_patterns_count": len(PROHIBITED_TONE_PATTERNS),
                "requires_empowering_language": True,
                "examples_prohibited": [
                    "you're drowning in debt",
                    "terrible choices",
                    "you must",
                    "financial disaster"
                ],
                "examples_encouraged": [
                    "we noticed",
                    "you might consider",
                    "here's a strategy",
                    "opportunity to"
                ]
            },
            "rate_limits": {
                "max_per_week": 10,
                "max_per_day": 1,
            },
            "vulnerable_population_protections": {
                "seniors_65_plus": "simplified, conservative content",
                "low_income": "avoid debt-related content",
                "young_adults_18_21": "educational basics only",
            },
        }

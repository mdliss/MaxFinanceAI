"""
Risk Mitigation Tests: Inappropriate Recommendations
Tests that guardrails prevent harmful, regulated, or inappropriate content.
"""
import pytest
from app.services.guardrails import (
    check_tone_guardrails,
    check_pii_exposure,
    check_regulatory_compliance,
    GuardrailViolation
)


class TestToneGuardrails:
    """Test that tone guardrails catch inappropriate language."""

    @pytest.mark.asyncio
    async def test_rejects_shame_based_language(self):
        """Ensure shame-based language is rejected."""
        shame_content = {
            "title": "Stop Wasting Money!",
            "description": "You're terrible with money and need to fix this immediately.",
            "rationale": "Your spending is irresponsible and reckless."
        }

        result = check_tone_guardrails(shame_content)
        assert result["passed"] is False
        assert "shame" in result["reason"].lower() or "negative" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_rejects_fear_based_language(self):
        """Ensure fear-based language is rejected."""
        fear_content = {
            "title": "You're Going Bankrupt!",
            "description": "If you don't act now, you'll lose everything!",
            "rationale": "You're in serious financial danger."
        }

        result = check_tone_guardrails(fear_content)
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_rejects_judgmental_language(self):
        """Ensure judgmental language is rejected."""
        judgmental_content = {
            "title": "Your Bad Decisions",
            "description": "You should know better than to spend like this.",
            "rationale": "Anyone with common sense would see this is wrong."
        }

        result = check_tone_guardrails(judgmental_content)
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_accepts_empowering_language(self):
        """Ensure empowering, supportive language passes."""
        empowering_content = {
            "title": "Understanding Your Spending Patterns",
            "description": "We noticed some subscription charges. Here's a strategy to review them.",
            "rationale": "This information could help you optimize your monthly expenses."
        }

        result = check_tone_guardrails(empowering_content)
        assert result["passed"] is True


class TestPIIExposure:
    """Test that PII detection prevents data leaks."""

    @pytest.mark.asyncio
    async def test_rejects_ssn_in_content(self):
        """Ensure SSN is detected and blocked."""
        pii_content = {
            "title": "Account Review",
            "description": "Your SSN 123-45-6789 shows good credit history.",
            "rationale": "Based on SSN verification."
        }

        result = check_pii_exposure(pii_content)
        assert result["passed"] is False
        assert "ssn" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_rejects_account_numbers(self):
        """Ensure account numbers are detected."""
        pii_content = {
            "title": "Account Information",
            "description": "Your account 9876543210 has high activity.",
            "rationale": "Account analysis completed."
        }

        result = check_pii_exposure(pii_content)
        assert result["passed"] is False
        assert "account" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_accepts_generic_content(self):
        """Ensure generic content without PII passes."""
        clean_content = {
            "title": "Savings Strategy",
            "description": "Building an emergency fund can provide financial security.",
            "rationale": "General financial education."
        }

        result = check_pii_exposure(clean_content)
        assert result["passed"] is True


class TestRegulatoryCompliance:
    """Test that regulatory guardrails prevent illegal advice."""

    @pytest.mark.asyncio
    async def test_rejects_investment_advice(self):
        """Ensure investment recommendations are blocked."""
        investment_content = {
            "title": "Buy This Stock Now!",
            "description": "You should invest in XYZ Corp immediately.",
            "rationale": "This stock will make you rich."
        }

        result = check_regulatory_compliance(investment_content)
        assert result["passed"] is False
        assert "investment" in result["reason"].lower() or "regulated" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_rejects_guaranteed_returns(self):
        """Ensure guaranteed return claims are blocked."""
        guaranteed_content = {
            "title": "Guaranteed Profits",
            "description": "This strategy guarantees 20% annual returns.",
            "rationale": "Risk-free investment opportunity."
        }

        result = check_regulatory_compliance(guaranteed_content)
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_rejects_tax_advice(self):
        """Ensure specific tax advice is blocked."""
        tax_content = {
            "title": "Tax Deduction Strategy",
            "description": "You should claim this specific deduction to reduce your taxes.",
            "rationale": "This will save you money on taxes."
        }

        result = check_regulatory_compliance(tax_content)
        assert result["passed"] is False
        assert "tax" in result["reason"].lower() or "regulated" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_accepts_educational_content(self):
        """Ensure general educational content passes."""
        educational_content = {
            "title": "Understanding Credit Scores",
            "description": "Learn how credit utilization affects your score.",
            "rationale": "Educational information about credit basics."
        }

        result = check_regulatory_compliance(educational_content)
        assert result["passed"] is True


class TestVulnerablePopulations:
    """Test protection for vulnerable populations."""

    @pytest.mark.asyncio
    async def test_extra_scrutiny_for_elderly(self):
        """Ensure recommendations for elderly users have extra protections."""
        from app.services.guardrails import check_vulnerable_population

        # Elderly user (age > 65)
        user_data = {"date_of_birth": "1950-01-01"}

        result = check_vulnerable_population(user_data)
        assert result["is_vulnerable"] is True
        assert result["category"] == "elderly"

    @pytest.mark.asyncio
    async def test_extra_scrutiny_for_low_income(self):
        """Ensure recommendations for low-income users are carefully reviewed."""
        from app.services.guardrails import check_vulnerable_population

        # Low income user
        user_data = {"monthly_income": 1500}  # Below threshold

        result = check_vulnerable_population(user_data)
        assert result["is_vulnerable"] is True
        assert result["category"] == "low_income"

    @pytest.mark.asyncio
    async def test_extra_scrutiny_for_young_adults(self):
        """Ensure young adults get age-appropriate content."""
        from app.services.guardrails import check_vulnerable_population

        # Young adult (18-24)
        user_data = {"date_of_birth": "2002-01-01"}

        result = check_vulnerable_population(user_data)
        assert result["is_vulnerable"] is True
        assert result["category"] == "young_adult"


class TestRateLimiting:
    """Test that rate limiting prevents recommendation spam."""

    @pytest.mark.asyncio
    async def test_weekly_rate_limit_enforced(self):
        """Ensure users don't get too many recommendations per week."""
        from app.services.guardrails import check_rate_limits

        # User who already received 5 recommendations this week
        user_stats = {
            "recommendations_this_week": 5,
            "recommendations_today": 2
        }

        result = check_rate_limits(user_stats)
        assert result["passed"] is False
        assert "weekly" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_daily_rate_limit_enforced(self):
        """Ensure users don't get too many recommendations per day."""
        from app.services.guardrails import check_rate_limits

        # User who already received 3 recommendations today
        user_stats = {
            "recommendations_this_week": 3,
            "recommendations_today": 3
        }

        result = check_rate_limits(user_stats)
        assert result["passed"] is False
        assert "daily" in result["reason"].lower()

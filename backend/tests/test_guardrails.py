import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from app.services.guardrails import GuardrailsService, GuardrailViolation
from app.models import User, Transaction, Signal, Recommendation


@pytest.mark.asyncio
async def test_user_eligibility_valid_user(db_session, sample_user_with_consent):
    """Test that a valid user passes eligibility checks"""
    user = sample_user_with_consent

    # Add sufficient transactions
    for i in range(15):
        transaction = Transaction(
            transaction_id=f"txn_valid_{uuid.uuid4().hex[:8]}_{i}",
            user_id=user.user_id,
            account_id="test_account",
            amount=100.0,
            category_primary="groceries",
            date=datetime.now() - timedelta(days=i)
        )
        db_session.add(transaction)

    # Add a signal
    signal = Signal(
        signal_id=f"sig_{uuid.uuid4().hex[:8]}",
        user_id=user.user_id,
        signal_type="savings_growth",
        value=200.0
    )
    db_session.add(signal)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_eligible, reason = await guardrails.validate_user_eligibility(user.user_id)

    assert is_eligible is True
    assert reason is None


@pytest.mark.asyncio
async def test_user_eligibility_no_consent(db_session, sample_user_no_consent):
    """Test that user without consent fails eligibility"""
    guardrails = GuardrailsService(db_session)
    is_eligible, reason = await guardrails.validate_user_eligibility(sample_user_no_consent.user_id)

    assert is_eligible is False
    assert "consent" in reason.lower()


@pytest.mark.asyncio
async def test_user_eligibility_underage(db_session):
    """Test that users under 18 fail eligibility"""
    user = User(
        user_id=f"minor_user_{uuid.uuid4().hex[:8]}",
        name="Minor User",
        age=16,
        consent_status=True,
        consent_timestamp=datetime.now()
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_eligible, reason = await guardrails.validate_user_eligibility(user.user_id)

    assert is_eligible is False
    assert "18 or older" in reason

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_user_eligibility_insufficient_transactions(db_session, sample_user_with_consent):
    """Test that user with too few transactions fails eligibility"""
    user = sample_user_with_consent

    # Add only 5 transactions (less than minimum 10)
    for i in range(5):
        transaction = Transaction(
            transaction_id=f"txn_insuff_{uuid.uuid4().hex[:8]}_{i}",
            user_id=user.user_id,
            account_id="test_account",
            amount=100.0,
            category_primary="groceries",
            date=datetime.now() - timedelta(days=i)
        )
        db_session.add(transaction)

    # Add a signal
    signal = Signal(
        signal_id=f"sig_insuff_{uuid.uuid4().hex[:8]}",
        user_id=user.user_id,
        signal_type="savings_growth",
        value=200.0
    )
    db_session.add(signal)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_eligible, reason = await guardrails.validate_user_eligibility(user.user_id)

    assert is_eligible is False
    assert "Insufficient transaction data" in reason
    assert "5 transactions" in reason


@pytest.mark.asyncio
async def test_user_eligibility_no_signals(db_session, sample_user_with_consent):
    """Test that user without signals fails eligibility"""
    user = sample_user_with_consent

    # Add sufficient transactions
    for i in range(15):
        transaction = Transaction(
            transaction_id=f"txn_nosig_{uuid.uuid4().hex[:8]}_{i}",
            user_id=user.user_id,
            account_id="test_account",
            amount=100.0,
            category_primary="groceries",
            date=datetime.now() - timedelta(days=i)
        )
        db_session.add(transaction)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_eligible, reason = await guardrails.validate_user_eligibility(user.user_id)

    assert is_eligible is False
    assert "No behavioral signals" in reason


@pytest.mark.asyncio
async def test_vulnerable_population_elderly(db_session):
    """Test elderly user (65+) is identified as vulnerable"""
    user = User(
        user_id=f"elderly_user_{uuid.uuid4().hex[:8]}",
        name="Elderly User",
        age=70,
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_vulnerable, message = guardrails.check_vulnerable_population(user)

    assert is_vulnerable is True
    assert "65+" in message or "senior" in message.lower()

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_vulnerable_population_low_income(db_session):
    """Test low income user is identified as vulnerable"""
    user = User(
        user_id=f"low_income_user_{uuid.uuid4().hex[:8]}",
        name="Low Income User",
        age=30,
        income_level="low",
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_vulnerable, message = guardrails.check_vulnerable_population(user)

    assert is_vulnerable is True
    assert "low income" in message.lower()

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_vulnerable_population_young_adult(db_session):
    """Test young adult (18-21) is identified as vulnerable"""
    user = User(
        user_id=f"young_user_{uuid.uuid4().hex[:8]}",
        name="Young User",
        age=19,
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_vulnerable, message = guardrails.check_vulnerable_population(user)

    assert is_vulnerable is True
    assert "18-21" in message

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_vulnerable_population_not_vulnerable(db_session):
    """Test normal user is not identified as vulnerable"""
    user = User(
        user_id=f"normal_user_{uuid.uuid4().hex[:8]}",
        name="Normal User",
        age=35,
        income_level="medium",
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    is_vulnerable, message = guardrails.check_vulnerable_population(user)

    assert is_vulnerable is False
    assert message is None

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_rate_limit_weekly_exceeded(db_session, sample_user_with_consent):
    """Test that weekly rate limit is enforced"""
    user = sample_user_with_consent

    # Create 10 recommendations in the past week
    for i in range(10):
        rec = Recommendation(
            user_id=user.user_id,
            persona_type="savings_builder",
            content_type="article",
            title=f"Test Recommendation {i}",
            rationale="Test rationale",
            created_at=datetime.now() - timedelta(days=i % 7)
        )
        db_session.add(rec)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    within_limits, reason = await guardrails.check_rate_limits(user.user_id)

    assert within_limits is False
    assert "Weekly recommendation limit" in reason


@pytest.mark.asyncio
async def test_rate_limit_daily_exceeded(db_session, sample_user_with_consent):
    """Test that daily rate limit is enforced"""
    user = sample_user_with_consent

    # Create 1 recommendation today
    rec = Recommendation(
        user_id=user.user_id,
        persona_type="savings_builder",
        content_type="article",
        title="Test Recommendation",
        rationale="Test rationale",
        created_at=datetime.now()
    )
    db_session.add(rec)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    within_limits, reason = await guardrails.check_rate_limits(user.user_id)

    assert within_limits is False
    assert "already generated today" in reason.lower()


@pytest.mark.asyncio
async def test_rate_limit_within_limits(db_session, sample_user_with_consent):
    """Test that user within rate limits passes"""
    user = sample_user_with_consent

    # Create 3 old recommendations (more than a week ago)
    for i in range(3):
        rec = Recommendation(
            user_id=user.user_id,
            persona_type="savings_builder",
            content_type="article",
            title=f"Old Recommendation {i}",
            rationale="Test rationale",
            created_at=datetime.now() - timedelta(days=10 + i)
        )
        db_session.add(rec)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)
    within_limits, reason = await guardrails.check_rate_limits(user.user_id)

    assert within_limits is True
    assert reason is None


def test_content_safety_valid_content():
    """Test that safe educational content passes validation"""
    guardrails = GuardrailsService(None)

    is_safe, reason = guardrails.validate_content_safety(
        title="How to Save Money on Groceries",
        description="Learn simple tips to reduce your grocery bill",
        content_type="article"
    )

    assert is_safe is True
    assert reason is None


def test_content_safety_prohibited_pattern():
    """Test that content with prohibited patterns fails validation"""
    guardrails = GuardrailsService(None)

    # Test investment pattern
    is_safe, reason = guardrails.validate_content_safety(
        title="How to invest in stocks",
        description="Start investing today",
        content_type="article"
    )

    assert is_safe is False
    assert "prohibited pattern" in reason.lower()

    # Test cryptocurrency pattern
    is_safe, reason = guardrails.validate_content_safety(
        title="Bitcoin Guide",
        description="Cryptocurrency investment strategies",
        content_type="article"
    )

    assert is_safe is False
    assert "prohibited pattern" in reason.lower()


def test_content_safety_unknown_content_type():
    """Test that unknown content types fail validation"""
    guardrails = GuardrailsService(None)

    is_safe, reason = guardrails.validate_content_safety(
        title="Test Title",
        description="Test description",
        content_type="unknown_type"
    )

    assert is_safe is False
    assert "Unknown content type" in reason


def test_get_required_disclaimer():
    """Test that disclaimers are correctly assigned"""
    guardrails = GuardrailsService(None)

    # Test calculator disclaimer
    disclaimer = guardrails.get_required_disclaimer("calculator")
    assert "estimates only" in disclaimer.lower()

    # Test guide disclaimer
    disclaimer = guardrails.get_required_disclaimer("guide")
    assert "educational" in disclaimer.lower()
    assert "not financial advice" in disclaimer.lower()

    # Test article disclaimer
    disclaimer = guardrails.get_required_disclaimer("article")
    assert "educational" in disclaimer.lower()


@pytest.mark.asyncio
async def test_apply_vulnerable_population_filters_elderly(db_session):
    """Test that elderly users have investment content filtered"""
    user = User(
        user_id=f"elderly_user_filter_{uuid.uuid4().hex[:8]}",
        name="Elderly User",
        age=70,
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)

    recommendations = [
        {"title": "Retirement Planning", "description": "Plan your retirement", "content_type": "article"},
        {"title": "Budget Basics", "description": "Learn to budget", "content_type": "article"},
        {"title": "401k Guide", "description": "Understanding 401k", "content_type": "guide"},
    ]

    filtered = await guardrails.apply_vulnerable_population_filters(user, recommendations)

    # Should filter out retirement/401k content for elderly
    assert len(filtered) < len(recommendations)
    assert not any("retirement" in r["title"].lower() or "401k" in r["title"].lower() for r in filtered)

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_apply_vulnerable_population_filters_low_income(db_session):
    """Test that low income users have debt content filtered"""
    user = User(
        user_id=f"low_income_filter_{uuid.uuid4().hex[:8]}",
        name="Low Income User",
        age=30,
        income_level="low",
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)

    recommendations = [
        {"title": "Credit Card Tips", "description": "Manage credit cards", "content_type": "article"},
        {"title": "Budget Basics", "description": "Learn to budget", "content_type": "article"},
        {"title": "Debt Payoff", "description": "Pay off debt faster", "content_type": "guide"},
    ]

    filtered = await guardrails.apply_vulnerable_population_filters(user, recommendations)

    # Should filter out credit/debt content for low income
    assert len(filtered) < len(recommendations)
    assert not any("credit" in r["title"].lower() or "debt" in r["title"].lower() for r in filtered)

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_apply_vulnerable_population_filters_young_adult(db_session):
    """Test that young adults have advanced content filtered"""
    user = User(
        user_id=f"young_filter_{uuid.uuid4().hex[:8]}",
        name="Young User",
        age=19,
        consent_status=True
    )
    db_session.add(user)
    await db_session.commit()

    guardrails = GuardrailsService(db_session)

    recommendations = [
        {"title": "Investment Basics", "description": "Start investing", "content_type": "article"},
        {"title": "Budget for Beginners", "description": "Learn to budget", "content_type": "article"},
        {"title": "Stock Market 101", "description": "Understanding stocks", "content_type": "guide"},
    ]

    filtered = await guardrails.apply_vulnerable_population_filters(user, recommendations)

    # Should filter out investment/stock content for young adults
    assert len(filtered) < len(recommendations)
    assert not any("investment" in r["title"].lower() or "stock" in r["title"].lower() for r in filtered)

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


def test_get_guardrail_summary():
    """Test that guardrail summary is returned correctly"""
    guardrails = GuardrailsService(None)

    summary = guardrails.get_guardrail_summary()

    assert "user_eligibility_rules" in summary
    assert "content_safety_rules" in summary
    assert "rate_limits" in summary
    assert "vulnerable_population_protections" in summary
    assert "tone_guardrails" in summary

    assert summary["user_eligibility_rules"]["minimum_age"] == 18
    assert summary["user_eligibility_rules"]["minimum_transactions"] == 10
    assert summary["rate_limits"]["max_per_week"] == 10
    assert summary["rate_limits"]["max_per_day"] == 1


# Tone Guardrails Tests

def test_validate_tone_good_example():
    """Test that empowering, supportive language passes tone validation"""
    guardrails = GuardrailsService(None)

    # Good tone from PRD example
    good_text = "We noticed your credit utilization is high. Here are strategies that could help reduce interest charges."

    is_appropriate, reason, violations = guardrails.validate_tone(good_text)

    assert is_appropriate is True
    assert reason is None
    assert violations is None


def test_validate_tone_bad_example_shaming():
    """Test that shaming language fails tone validation"""
    guardrails = GuardrailsService(None)

    # Bad tone from PRD example
    bad_text = "You're drowning in debt and making terrible choices."

    is_appropriate, reason, violations = guardrails.validate_tone(bad_text)

    assert is_appropriate is False
    assert reason is not None
    assert violations is not None
    assert len(violations) >= 2  # "you're drowning in debt" and "terrible choices"


def test_validate_tone_judgmental_language():
    """Test that judgmental phrases fail tone validation"""
    guardrails = GuardrailsService(None)

    bad_texts = [
        "You should have saved more money earlier.",
        "What were you thinking with those purchases?",
        "You're being careless with your finances."
    ]

    for text in bad_texts:
        is_appropriate, reason, violations = guardrails.validate_tone(text)
        assert is_appropriate is False, f"Expected '{text}' to fail tone validation"
        assert violations is not None


def test_validate_tone_panic_inducing():
    """Test that panic-inducing warnings fail tone validation"""
    guardrails = GuardrailsService(None)

    panic_texts = [
        "You're in serious trouble financially",
        "This is a financial disaster waiting to happen",
        "It's too late to fix this",
        "You'll go broke if you continue"
    ]

    for text in panic_texts:
        is_appropriate, reason, violations = guardrails.validate_tone(text)
        assert is_appropriate is False, f"Expected '{text}' to fail tone validation"


def test_validate_tone_condescending():
    """Test that condescending tone fails validation"""
    guardrails = GuardrailsService(None)

    condescending_texts = [
        "Obviously you should budget better",
        "Anyone knows that's irresponsible spending",
        "It's simple - just stop buying things"
    ]

    for text in condescending_texts:
        is_appropriate, reason, violations = guardrails.validate_tone(text)
        assert is_appropriate is False, f"Expected '{text}' to fail tone validation"


def test_validate_tone_absolute_demands():
    """Test that absolute demands fail validation"""
    guardrails = GuardrailsService(None)

    demand_texts = [
        "You must stop spending immediately",
        "You have to cut your budget now",
        "You need to immediately cancel these subscriptions"
    ]

    for text in demand_texts:
        is_appropriate, reason, violations = guardrails.validate_tone(text)
        assert is_appropriate is False, f"Expected '{text}' to fail tone validation"


def test_validate_tone_empowering_patterns():
    """Test that various empowering patterns pass validation"""
    guardrails = GuardrailsService(None)

    empowering_texts = [
        "We noticed you might benefit from reviewing your subscriptions",
        "You might consider setting up automatic savings",
        "Here's a strategy that could help with debt reduction",
        "This approach could improve your credit utilization",
        "Here are some options to reduce monthly expenses"
    ]

    for text in empowering_texts:
        is_appropriate, reason, violations = guardrails.validate_tone(text)
        assert is_appropriate is True, f"Expected '{text}' to pass tone validation"


def test_validate_tone_short_text():
    """Test that short text without empowering language still passes"""
    guardrails = GuardrailsService(None)

    # Short text (≤10 words) should pass even without empowering language
    short_text = "Review your budget monthly"

    is_appropriate, reason, violations = guardrails.validate_tone(short_text)

    assert is_appropriate is True


def test_validate_tone_long_text_no_empowering():
    """Test that long text without empowering language fails"""
    guardrails = GuardrailsService(None)

    # Long text (>10 words) without empowering patterns should fail
    long_text = "Review your budget every month to ensure you stay on track with your financial goals and spending"

    is_appropriate, reason, violations = guardrails.validate_tone(long_text)

    assert is_appropriate is False
    assert "empowering" in reason.lower() or "supportive" in reason.lower()


def test_suggest_tone_improvements():
    """Test that tone improvement suggestions are helpful"""
    guardrails = GuardrailsService(None)

    # Text with "you must"
    text1 = "You must reduce your credit card spending"
    suggestions1 = guardrails.suggest_tone_improvements(text1)
    assert len(suggestions1) > 0
    assert any("you must" in s.lower() for s in suggestions1)

    # Text with negative adjectives
    text2 = "Your bad spending habits are causing problems"
    suggestions2 = guardrails.suggest_tone_improvements(text2)
    assert len(suggestions2) > 0
    assert any("negative" in s.lower() for s in suggestions2)

    # Text without empowering language
    text3 = "Cancel your unused subscriptions right away"
    suggestions3 = guardrails.suggest_tone_improvements(text3)
    assert len(suggestions3) > 0


def test_validate_tone_combined_title_description_rationale():
    """Test tone validation on combined recommendation text"""
    guardrails = GuardrailsService(None)

    # Test complete recommendation with good tone
    title = "Subscription Audit Opportunity"
    description = "Review your monthly subscriptions"
    rationale = "We noticed you have several recurring charges. Here's a strategy to identify services you no longer use."

    combined = f"{title} {description} {rationale}"
    is_appropriate, reason, violations = guardrails.validate_tone(combined)

    assert is_appropriate is True

    # Test complete recommendation with bad tone
    title_bad = "Stop Wasting Money"
    description_bad = "You must cancel subscriptions"
    rationale_bad = "You're drowning in debt from terrible choices and need to fix this immediately"

    combined_bad = f"{title_bad} {description_bad} {rationale_bad}"
    is_appropriate, reason, violations = guardrails.validate_tone(combined_bad)

    assert is_appropriate is False
    assert len(violations) >= 2

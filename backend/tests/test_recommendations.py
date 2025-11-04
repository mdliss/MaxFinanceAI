import pytest
from sqlalchemy import select
from app.models import User, Signal, Persona, Recommendation
from app.services.recommendation_engine import RecommendationEngine


@pytest.mark.asyncio
async def test_generate_recommendations_subscription_optimizer(async_db):
    """Test generating recommendations for subscription optimizer persona"""
    # Get a user with consent
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing data
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))
    await async_db.execute(Recommendation.__table__.delete().where(Recommendation.user_id == user.user_id))

    # Add subscription signals
    for i in range(3):
        signal = Signal(
            signal_id=f"test_sub_{i}_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=15.0 + i * 5,
            details={"merchant": f"Service_{i}", "frequency": "monthly"}
        )
        async_db.add(signal)

    # Add persona
    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="subscription_optimizer",
        priority_rank=1,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should have 3-5 recommendations
    assert 3 <= len(recommendations) <= 5

    # All should be for subscription_optimizer
    for rec in recommendations:
        assert rec.persona_type == "subscription_optimizer"
        assert rec.user_id == user.user_id
        assert rec.title
        assert rec.description
        assert rec.rationale
        assert rec.content_type in ["article", "calculator", "guide", "video"]


@pytest.mark.asyncio
async def test_generate_recommendations_savings_builder(async_db):
    """Test generating recommendations for savings builder persona"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing data
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))

    # Add savings growth signal
    signal = Signal(
        signal_id=f"test_savings_{user.user_id}",
        user_id=user.user_id,
        signal_type="savings_growth",
        value=250.0,
        details={"monthly_growth_rate": 250.0}
    )
    async_db.add(signal)

    # Add persona
    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="savings_builder",
        priority_rank=2,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should have recommendations
    assert 3 <= len(recommendations) <= 5

    # All should be for savings_builder
    for rec in recommendations:
        assert rec.persona_type == "savings_builder"


@pytest.mark.asyncio
async def test_generate_recommendations_credit_optimizer(async_db):
    """Test generating recommendations for credit optimizer persona"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing data
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))

    # Add credit utilization signal
    signal = Signal(
        signal_id=f"test_credit_{user.user_id}",
        user_id=user.user_id,
        signal_type="credit_utilization",
        value=65.0,
        details={"utilization_percent": 65.0, "current_balance": 3250.0}
    )
    async_db.add(signal)

    # Add persona
    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="credit_optimizer",
        priority_rank=3,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should have recommendations
    assert 3 <= len(recommendations) <= 5

    # All should be for credit_optimizer
    for rec in recommendations:
        assert rec.persona_type == "credit_optimizer"


@pytest.mark.asyncio
async def test_generate_recommendations_financial_newcomer(async_db):
    """Test generating recommendations for financial newcomer persona"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing data
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))

    # Add a minimal signal (guardrails require at least 1 signal)
    signal = Signal(
        signal_id=f"test_newcomer_{user.user_id}",
        user_id=user.user_id,
        signal_type="income_stability",
        value=50.0,
        details={"average_income": 1000.0}
    )
    async_db.add(signal)

    # Add persona
    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="financial_newcomer",
        priority_rank=5,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should have recommendations
    assert 3 <= len(recommendations) <= 5

    # All should be for financial_newcomer
    for rec in recommendations:
        assert rec.persona_type == "financial_newcomer"


@pytest.mark.asyncio
async def test_recommendation_rationale_contains_data(async_db):
    """Test that rationales cite specific user data"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing data
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))

    # Add subscription signals
    for i in range(3):
        signal = Signal(
            signal_id=f"test_sub_{i}_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=15.0,
            details={"merchant": f"Service_{i}"}
        )
        async_db.add(signal)

    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="subscription_optimizer",
        priority_rank=1,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # At least one rationale should mention the number of subscriptions
    rationales = [r.rationale for r in recommendations]
    assert any("3" in r or "three" in r.lower() for r in rationales)


@pytest.mark.asyncio
async def test_save_recommendations(async_db):
    """Test saving recommendations to database"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear and setup
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))
    await async_db.execute(Recommendation.__table__.delete().where(Recommendation.user_id == user.user_id))
    await async_db.execute(Recommendation.__table__.delete().where(Recommendation.user_id == user.user_id))

    # Add a minimal signal (guardrails require at least 1 signal)
    signal = Signal(
        signal_id=f"test_save_{user.user_id}",
        user_id=user.user_id,
        signal_type="income_stability",
        value=50.0,
        details={"average_income": 1000.0}
    )
    async_db.add(signal)

    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="financial_newcomer",
        priority_rank=5,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate and save
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)
    saved_count = await engine.save_recommendations(user.user_id, recommendations)

    assert saved_count == len(recommendations)

    # Verify in database
    result = await async_db.execute(
        select(Recommendation).where(Recommendation.user_id == user.user_id)
    )
    db_recommendations = result.scalars().all()

    assert len(db_recommendations) == len(recommendations)


@pytest.mark.asyncio
async def test_recommendation_content_types(async_db):
    """Test that recommendations include various content types"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear and setup
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))
    await async_db.execute(Recommendation.__table__.delete().where(Recommendation.user_id == user.user_id))

    # Add a minimal signal (guardrails require at least 1 signal)
    signal = Signal(
        signal_id=f"test_content_{user.user_id}",
        user_id=user.user_id,
        signal_type="income_stability",
        value=50.0,
        details={"average_income": 1000.0}
    )
    async_db.add(signal)

    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="financial_newcomer",
        priority_rank=5,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should have variety of content types
    content_types = {r.content_type for r in recommendations}
    assert len(content_types) >= 2  # At least 2 different types


@pytest.mark.asyncio
async def test_recommendations_auto_approved(async_db):
    """Test that educational recommendations are auto-approved"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear and setup
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))
    await async_db.execute(Recommendation.__table__.delete().where(Recommendation.user_id == user.user_id))

    # Add a minimal signal (guardrails require at least 1 signal)
    signal = Signal(
        signal_id=f"test_approved_{user.user_id}",
        user_id=user.user_id,
        signal_type="income_stability",
        value=50.0,
        details={"average_income": 1000.0}
    )
    async_db.add(signal)

    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="financial_newcomer",
        priority_rank=5,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # All should be auto-approved
    for rec in recommendations:
        assert rec.approval_status == "approved"


@pytest.mark.asyncio
async def test_recommendation_eligibility_check(async_db):
    """Test that eligibility checks work correctly"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear and setup with minimal signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))

    # Add only 1 subscription signal (less than required for some recommendations)
    signal = Signal(
        signal_id=f"test_sub_{user.user_id}",
        user_id=user.user_id,
        signal_type="subscription_detected",
        value=15.0,
        details={"merchant": "Service"}
    )
    async_db.add(signal)

    persona = Persona(
        user_id=user.user_id,
        window_days=180,
        persona_type="subscription_optimizer",
        priority_rank=1,
        criteria_met="test"
    )
    async_db.add(persona)
    await async_db.commit()

    # Generate recommendations
    engine = RecommendationEngine(async_db)
    recommendations = await engine.generate_recommendations(user.user_id)

    # Should still get recommendations (some may have eligibility_met=False)
    assert len(recommendations) >= 3

    # Check that eligibility_met field is set
    for rec in recommendations:
        assert isinstance(rec.eligibility_met, bool)

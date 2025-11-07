import pytest
from sqlalchemy import select
from app.models import User, Signal, Persona
from app.services.persona_assigner import PersonaAssigner, PERSONA_DEFINITIONS


@pytest.mark.asyncio
async def test_assign_personas_no_signals(async_db):
    """Test that users with no signals get the financial_newcomer persona"""
    # Get a user with consent
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear any existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))
    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should get newcomer persona
    assert len(personas) == 1
    assert personas[0].persona_type == "financial_newcomer"
    assert personas[0].priority_rank == PERSONA_DEFINITIONS["financial_newcomer"]["priority"]


@pytest.mark.asyncio
async def test_assign_subscription_optimizer_persona(async_db):
    """Test subscription optimizer persona assignment"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))

    # Add 3 subscription signals (total spend $60 to exceed min of $50)
    for i in range(3):
        signal = Signal(
            signal_id=f"test_sub_{i}_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=20.0,  # 3 * 20 = 60, which exceeds minimum of 50
            details={"merchant": f"Service_{i}", "frequency": "monthly"}
        )
        async_db.add(signal)

    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should have subscription_optimizer
    persona_types = [p.persona_type for p in personas]
    assert "subscription_optimizer" in persona_types

    # Check priority
    sub_persona = next(p for p in personas if p.persona_type == "subscription_optimizer")
    assert sub_persona.priority_rank == PERSONA_DEFINITIONS["subscription_optimizer"]["priority"]


@pytest.mark.asyncio
async def test_assign_savings_builder_persona(async_db):
    """Test savings builder persona assignment"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))

    # Add savings growth signal
    signal = Signal(
        signal_id=f"test_savings_{user.user_id}",
        user_id=user.user_id,
        signal_type="savings_growth",
        value=250.0,  # $250/month growth
        details={"monthly_growth_rate": 250.0}
    )
    async_db.add(signal)
    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should have savings_builder
    persona_types = [p.persona_type for p in personas]
    assert "savings_builder" in persona_types


@pytest.mark.asyncio
async def test_assign_credit_optimizer_persona(async_db):
    """Test credit optimizer persona assignment"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))

    # Add high credit utilization signal
    signal = Signal(
        signal_id=f"test_credit_{user.user_id}",
        user_id=user.user_id,
        signal_type="credit_utilization",
        value=65.0,  # 65% utilization
        details={"utilization_percent": 65.0, "status": "high"}
    )
    async_db.add(signal)
    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should have credit_optimizer
    persona_types = [p.persona_type for p in personas]
    assert "credit_optimizer" in persona_types


@pytest.mark.asyncio
async def test_assign_income_stable_persona(async_db):
    """Test income stable persona assignment"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))

    # Add stable income signal
    signal = Signal(
        signal_id=f"test_income_{user.user_id}",
        user_id=user.user_id,
        signal_type="income_stability",
        value=85.0,  # 85/100 stability score
        details={"stability_score": 85.0, "status": "stable"}
    )
    async_db.add(signal)
    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should have income_stable
    persona_types = [p.persona_type for p in personas]
    assert "income_stable" in persona_types


@pytest.mark.asyncio
async def test_multiple_personas_prioritization(async_db):
    """Test that multiple personas are prioritized correctly"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing signals
    await async_db.execute(Signal.__table__.delete().where(Signal.user_id == user.user_id))

    # Add multiple signals
    signals = [
        Signal(
            signal_id=f"test_sub_1_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=10.0,
            details={"merchant": "Netflix", "frequency": "monthly"}
        ),
        Signal(
            signal_id=f"test_sub_2_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=15.0,
            details={"merchant": "Spotify", "frequency": "monthly"}
        ),
        Signal(
            signal_id=f"test_sub_3_{user.user_id}",
            user_id=user.user_id,
            signal_type="subscription_detected",
            value=80.0,
            details={"merchant": "Internet", "frequency": "monthly"}
        ),
        Signal(
            signal_id=f"test_credit_{user.user_id}",
            user_id=user.user_id,
            signal_type="credit_utilization",
            value=65.0,  # Must be ≥50% for credit_optimizer
            details={"utilization_percent": 65.0, "status": "high"}
        ),
    ]

    for signal in signals:
        async_db.add(signal)

    await async_db.commit()

    # Assign personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)

    # Should have both subscription_optimizer and credit_optimizer
    persona_types = [p.persona_type for p in personas]
    assert "subscription_optimizer" in persona_types
    assert "credit_optimizer" in persona_types

    # credit_optimizer should be first (priority 1), subscription_optimizer second (priority 3)
    assert personas[0].persona_type == "credit_optimizer"
    assert personas[0].priority_rank < personas[1].priority_rank


@pytest.mark.asyncio
async def test_save_personas(async_db):
    """Test saving personas to database"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Clear existing personas
    await async_db.execute(Persona.__table__.delete().where(Persona.user_id == user.user_id))
    await async_db.commit()

    # Assign and save personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)
    saved_count = await assigner.save_personas(user.user_id, personas)

    assert saved_count == len(personas)

    # Verify personas in database
    result = await async_db.execute(
        select(Persona).where(Persona.user_id == user.user_id)
    )
    db_personas = result.scalars().all()

    assert len(db_personas) == len(personas)


@pytest.mark.asyncio
async def test_get_primary_persona(async_db):
    """Test getting the primary (highest priority) persona"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Assign and save personas
    assigner = PersonaAssigner(async_db)
    personas = await assigner.assign_personas(user.user_id)
    await assigner.save_personas(user.user_id, personas)

    # Get primary persona
    primary = await assigner.get_primary_persona(user.user_id)

    # Should match the first persona in the sorted list
    assert primary.persona_type == personas[0].persona_type
    assert primary.priority_rank == personas[0].priority_rank


@pytest.mark.asyncio
async def test_persona_assignment_deterministic(async_db):
    """Test that persona assignment is deterministic"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Assign personas twice
    assigner = PersonaAssigner(async_db)
    personas1 = await assigner.assign_personas(user.user_id)
    personas2 = await assigner.assign_personas(user.user_id)

    # Should be identical
    assert len(personas1) == len(personas2)

    for p1, p2 in zip(personas1, personas2):
        assert p1.persona_type == p2.persona_type
        assert p1.priority_rank == p2.priority_rank

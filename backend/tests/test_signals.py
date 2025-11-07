import pytest
from sqlalchemy import select
from app.models import User, Signal
from app.services.signal_detector import SignalDetector


@pytest.mark.asyncio
async def test_detect_all_signals(async_db):
    """Test detecting all signal types for a user"""
    # Get a user with consent
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    # Detect signals
    detector = SignalDetector(async_db)
    signals = await detector.detect_all_signals(user.user_id)

    # Should detect at least 1 signal
    assert len(signals) >= 1

    # All signals should have required fields
    for signal in signals:
        assert signal.signal_id
        assert signal.user_id == user.user_id
        assert signal.signal_type in [
            "subscription_detected",
            "savings_growth",
            "credit_utilization",
            "income_stability"
        ]
        assert isinstance(signal.value, (int, float))
        assert signal.details is not None


@pytest.mark.asyncio
async def test_subscription_detection(async_db):
    """Test subscription detection algorithm"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    detector = SignalDetector(async_db)

    # Get user transactions
    from app.models import Transaction
    result = await async_db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.user_id)
        .order_by(Transaction.date)
    )
    transactions = result.scalars().all()

    signals = await detector.detect_subscriptions(user.user_id, transactions)

    # Check signal structure if any subscriptions detected
    if signals:
        for signal in signals:
            assert signal.signal_type == "subscription_detected"
            assert "merchant" in signal.details
            assert "frequency" in signal.details
            assert signal.details["frequency"] in ["monthly", "weekly", "yearly"]
            assert signal.value > 0


@pytest.mark.asyncio
async def test_credit_utilization_detection(async_db):
    """Test credit utilization detection"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    detector = SignalDetector(async_db)

    # Get user accounts
    from app.models import Account
    result = await async_db.execute(
        select(Account).where(Account.user_id == user.user_id)
    )
    accounts = result.scalars().all()

    signals = await detector.detect_credit_utilization(user.user_id, accounts)

    # Check credit signals
    credit_accounts = [a for a in accounts if a.type == "credit"]
    assert len(signals) == len(credit_accounts)

    for signal in signals:
        assert signal.signal_type == "credit_utilization"
        assert 0 <= signal.value <= 100
        assert "status" in signal.details
        assert signal.details["status"] in ["healthy", "high", "critical"]


@pytest.mark.asyncio
async def test_income_stability_detection(async_db):
    """Test income stability detection"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    detector = SignalDetector(async_db)

    # Get user transactions
    from app.models import Transaction
    result = await async_db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.user_id)
        .order_by(Transaction.date)
    )
    transactions = result.scalars().all()

    signals = await detector.detect_income_stability(user.user_id, transactions)

    # Check income stability signals
    if signals:
        for signal in signals:
            assert signal.signal_type == "income_stability"
            assert 0 <= signal.value <= 100
            assert "stability_score" in signal.details
            assert "status" in signal.details


@pytest.mark.asyncio
async def test_save_signals(async_db):
    """Test saving signals to database"""
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    detector = SignalDetector(async_db)

    # Detect and save signals
    signals = await detector.detect_all_signals(user.user_id)
    saved_count = await detector.save_signals(signals)

    assert saved_count == len(signals)

    # Verify signals in database
    result = await async_db.execute(
        select(Signal).where(Signal.user_id == user.user_id)
    )
    db_signals = result.scalars().all()

    assert len(db_signals) == len(signals)


@pytest.mark.asyncio
async def test_signal_detection_performance(async_db):
    """Test that signal detection meets performance requirements (<1s per user)"""
    import time

    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one()

    detector = SignalDetector(async_db)

    # Measure detection time
    start = time.time()
    signals = await detector.detect_all_signals(user.user_id)
    elapsed = time.time() - start

    # Should complete in under 1 second
    assert elapsed < 1.0, f"Signal detection took {elapsed:.3f}s, should be <1s"

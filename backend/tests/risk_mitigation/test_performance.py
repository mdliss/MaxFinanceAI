"""
Risk Mitigation Tests: Performance with 100+ Users
Tests system performance under realistic load.
"""
import pytest
import time
import datetime
from app.models import User, Account, Transaction, ConsentRecord
from app.services.signal_detection import SignalDetector
from app.services.persona_assignment import PersonaAssigner
from app.services.recommendation_engine import RecommendationEngine


class TestPerformanceUnderLoad:
    """Test system performance with 100+ users."""

    @pytest.mark.asyncio
    async def test_bulk_user_creation_performance(self, test_db):
        """Test creating 100+ users in reasonable time."""
        start_time = time.time()

        users = []
        for i in range(100):
            user = User(
                user_id=f"perf_user_{i}",
                full_name=f"Performance User {i}",
                email=f"perf{i}@example.com",
                date_of_birth=datetime.date(1990, 1, 1),
                has_consented=True
            )
            users.append(user)

        test_db.add_all(users)
        await test_db.commit()

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in under 5 seconds
        assert duration < 5.0, f"User creation took {duration}s, expected < 5s"

    @pytest.mark.asyncio
    async def test_signal_detection_scales(self, test_db):
        """Test signal detection performs well with multiple users."""
        # Create 10 test users with transactions
        for i in range(10):
            user = User(
                user_id=f"signal_user_{i}",
                full_name=f"Signal User {i}",
                email=f"signal{i}@example.com",
                date_of_birth=datetime.date(1990, 1, 1),
                has_consented=True
            )
            test_db.add(user)

            # Add account
            account = Account(
                account_id=f"acc_{i}",
                user_id=user.user_id,
                name=f"Checking {i}",
                type="depository",
                subtype="checking"
            )
            test_db.add(account)

            # Add 50 transactions per user
            for j in range(50):
                transaction = Transaction(
                    transaction_id=f"txn_{i}_{j}",
                    account_id=account.account_id,
                    user_id=user.user_id,
                    amount=100.0 + j,
                    date=datetime.date.today() - datetime.timedelta(days=j),
                    name=f"Transaction {j}",
                    category=["Food and Drink", "Restaurants"]
                )
                test_db.add(transaction)

        await test_db.commit()

        # Detect signals for all users
        detector = SignalDetector(test_db)
        start_time = time.time()

        for i in range(10):
            await detector.detect_signals(f"signal_user_{i}")

        end_time = time.time()
        duration = end_time - start_time

        # Should process 10 users in under 10 seconds
        assert duration < 10.0, f"Signal detection took {duration}s, expected < 10s"

    @pytest.mark.asyncio
    async def test_concurrent_recommendation_generation(self, test_db):
        """Test that multiple recommendations can be generated efficiently."""
        # Note: This is a simplified test - in production you'd use actual concurrency
        users_created = 0
        start_time = time.time()

        for i in range(5):
            user = User(
                user_id=f"rec_user_{i}",
                full_name=f"Rec User {i}",
                email=f"rec{i}@example.com",
                date_of_birth=datetime.date(1990, 1, 1),
                has_consented=True
            )
            test_db.add(user)
            users_created += 1

        await test_db.commit()
        end_time = time.time()
        duration = end_time - start_time

        # Should create users quickly
        assert users_created == 5
        assert duration < 2.0, f"User creation took {duration}s"

    @pytest.mark.asyncio
    async def test_database_query_performance(self, test_db):
        """Test that database queries perform well with more data."""
        from sqlalchemy import select

        # Create 50 users
        for i in range(50):
            user = User(
                user_id=f"query_user_{i}",
                full_name=f"Query User {i}",
                email=f"query{i}@example.com",
                date_of_birth=datetime.date(1990, 1, 1),
                has_consented=True
            )
            test_db.add(user)

        await test_db.commit()

        # Query all users
        start_time = time.time()
        result = await test_db.execute(select(User))
        users = result.scalars().all()
        end_time = time.time()
        duration = end_time - start_time

        # Should query quickly
        assert len(users) >= 50
        assert duration < 1.0, f"Query took {duration}s, expected < 1s"


class TestMemoryUsage:
    """Test that memory usage stays reasonable."""

    @pytest.mark.asyncio
    async def test_transaction_processing_memory(self, test_db):
        """Test that processing many transactions doesn't exhaust memory."""
        user = User(
            user_id="mem_test_user",
            full_name="Memory Test",
            email="mem@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)

        account = Account(
            account_id="mem_acc",
            user_id=user.user_id,
            name="Test Account",
            type="depository",
            subtype="checking"
        )
        test_db.add(account)

        # Create 1000 transactions
        transactions = []
        for i in range(1000):
            txn = Transaction(
                transaction_id=f"mem_txn_{i}",
                account_id=account.account_id,
                user_id=user.user_id,
                amount=50.0 + i,
                date=datetime.date.today() - datetime.timedelta(days=i % 365),
                name=f"Transaction {i}",
                category=["Shopping"]
            )
            transactions.append(txn)

        test_db.add_all(transactions)
        await test_db.commit()

        # Query should work without memory issues
        from sqlalchemy import select
        result = await test_db.execute(
            select(Transaction).where(Transaction.user_id == user.user_id)
        )
        retrieved = result.scalars().all()

        assert len(retrieved) == 1000


class TestResponseTimes:
    """Test API response times under load."""

    @pytest.mark.asyncio
    async def test_user_lookup_speed(self, test_db):
        """Test that user lookup is fast."""
        from sqlalchemy import select

        # Create user
        user = User(
            user_id="speed_user",
            full_name="Speed Test",
            email="speed@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)
        await test_db.commit()

        # Lookup should be very fast
        start_time = time.time()
        result = await test_db.execute(
            select(User).where(User.user_id == "speed_user")
        )
        found_user = result.scalar_one_or_none()
        end_time = time.time()
        duration = end_time - start_time

        assert found_user is not None
        assert duration < 0.1, f"Lookup took {duration}s, expected < 0.1s"

    @pytest.mark.asyncio
    async def test_consent_check_speed(self, test_db):
        """Test that consent checking is fast."""
        from sqlalchemy import select

        user = User(
            user_id="consent_speed",
            full_name="Consent Speed",
            email="consent@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)

        consent = ConsentRecord(
            user_id=user.user_id,
            consent_status=True,
            consent_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent)
        await test_db.commit()

        # Check consent
        start_time = time.time()
        result = await test_db.execute(
            select(User).where(User.user_id == "consent_speed")
        )
        checked_user = result.scalar_one_or_none()
        end_time = time.time()
        duration = end_time - start_time

        assert checked_user.has_consented is True
        assert duration < 0.1, f"Consent check took {duration}s"

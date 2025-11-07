import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import User, Recommendation
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db():
    """Create a test database session"""
    # Use the main database for tests
    from app.config import settings
    engine = create_async_engine(settings.database_url, echo=False)

    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session():
    """Alias for async_db to match test naming"""
    from app.config import settings
    engine = create_async_engine(settings.database_url, echo=False)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def sample_user_with_consent(db_session):
    """Create a sample user with consent granted"""
    import uuid
    unique_id = f"test_user_consent_{uuid.uuid4().hex[:8]}"
    user = User(
        user_id=unique_id,
        name="Test User With Consent",
        age=30,
        income_level="medium",
        consent_status=True,
        consent_timestamp=datetime.now()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    # Cleanup after test
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def sample_user_no_consent(db_session):
    """Create a sample user without consent"""
    import uuid
    unique_id = f"test_user_no_consent_{uuid.uuid4().hex[:8]}"
    user = User(
        user_id=unique_id,
        name="Test User No Consent",
        age=35,
        income_level="medium",
        consent_status=False,
        consent_timestamp=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    # Cleanup after test
    await db_session.delete(user)
    await db_session.commit()


# New fixtures for additional endpoint tests

@pytest.fixture
async def client():
    """Create async HTTP client for testing"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_with_consent(db_session):
    """Create a test user with consent granted"""
    import uuid
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    user = User(
        user_id=unique_id,
        name="Test User With Consent",
        age=30,
        income_level="medium",
        consent_status=True,
        consent_timestamp=datetime.now()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def test_user_no_consent(db_session):
    """Create a test user without consent"""
    import uuid
    unique_id = f"test_user_no_consent_{uuid.uuid4().hex[:8]}"
    user = User(
        user_id=unique_id,
        name="Test User No Consent",
        age=35,
        income_level="low",
        consent_status=False,
        consent_timestamp=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def test_recommendation(db_session, test_user_with_consent):
    """Create a test recommendation"""
    recommendation = Recommendation(
        user_id=test_user_with_consent.user_id,
        persona_type="high_utilization",
        content_type="education",
        title="Test Recommendation",
        description="This is a test recommendation",
        rationale="This is a test rationale with specific data",
        eligibility_met=True,
        approval_status="pending"
    )
    db_session.add(recommendation)
    await db_session.commit()
    await db_session.refresh(recommendation)

    yield recommendation

    # Cleanup
    await db_session.delete(recommendation)
    await db_session.commit()


@pytest.fixture
def add_sufficient_transactions():
    """Helper fixture to add sufficient transactions to a user"""
    from app.models import Transaction, Account
    from datetime import datetime, timedelta

    async def _add_transactions(db_session, user_id: str, count: int = 12):
        """Add transactions to a user (default 12 to exceed minimum of 10)"""
        import uuid
        # Create an account for the user with unique ID
        account_unique_id = f"test_account_{user_id}_{uuid.uuid4().hex[:8]}"
        account = Account(
            account_id=account_unique_id,
            user_id=user_id,
            type="depository",
            subtype="checking",
            available_balance=5000.0,
            current_balance=5000.0
        )
        db_session.add(account)
        await db_session.commit()

        # Add transactions
        for i in range(count):
            transaction = Transaction(
                transaction_id=f"test_txn_{user_id}_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                account_id=account.account_id,
                date=datetime.now() - timedelta(days=i),
                amount=-50.0 - (i * 10),  # Varying amounts
                merchant_name=f"Test Merchant {i}",
                category_primary="Shopping",
                pending=False
            )
            db_session.add(transaction)

        await db_session.commit()
        return account

    return _add_transactions

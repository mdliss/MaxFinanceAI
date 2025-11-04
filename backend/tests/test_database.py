import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import User, Account, Transaction

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield async_session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(test_db):
    """Test creating a user."""
    async with test_db() as session:
        user = User(
            user_id="user_123",
            name="Test User",
            age=30,
            income_level="50000",
            consent_status=True,
            consent_timestamp=datetime.now()
        )
        session.add(user)
        await session.commit()

        assert user.user_id == "user_123"
        assert user.consent_status is True

@pytest.mark.asyncio
async def test_create_account_with_user(test_db):
    """Test creating an account linked to a user."""
    async with test_db() as session:
        user = User(
            user_id="user_456",
            name="Test User 2",
            consent_status=False
        )
        session.add(user)

        account = Account(
            account_id="acct_789",
            user_id="user_456",
            type="checking",
            current_balance=1000.00,
            available_balance=950.00
        )
        session.add(account)
        await session.commit()

        assert account.user_id == "user_456"
        assert account.current_balance == 1000.00

@pytest.mark.asyncio
async def test_create_transaction(test_db):
    """Test creating a transaction."""
    async with test_db() as session:
        user = User(user_id="user_789", name="Test User 3", consent_status=True)
        account = Account(
            account_id="acct_999",
            user_id="user_789",
            type="checking",
            current_balance=500.00
        )
        session.add_all([user, account])

        transaction = Transaction(
            transaction_id="txn_001",
            account_id="acct_999",
            user_id="user_789",
            date=date.today(),
            amount=-25.50,
            merchant_name="Coffee Shop",
            category_primary="Food and Drink"
        )
        session.add(transaction)
        await session.commit()

        assert transaction.amount == -25.50
        assert transaction.merchant_name == "Coffee Shop"

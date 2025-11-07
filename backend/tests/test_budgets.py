import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from app.main import app
from app.models import User, Budget, Transaction, Account

@pytest.mark.asyncio
async def test_create_budget(async_db):
    """Test creating a budget"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        # Grant consent
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create a budget
        response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Dining",
                "amount": 500.0,
                "period": "monthly",
                "alert_threshold": 80.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == unique_id
        assert data["category"] == "Dining"
        assert data["amount"] == 500.0
        assert data["status"] == "active"
        assert data["spent_amount"] == 0.0
        assert data["remaining_amount"] == 500.0


@pytest.mark.asyncio
async def test_create_budget_without_consent(async_db):
    """Test that creating a budget without consent fails"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user without consent
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Try to create a budget (should fail)
        response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Shopping",
                "amount": 300.0
            }
        )

        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_budgets(async_db):
    """Test listing all budgets for a user"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create multiple budgets
        await client.post(
            "/api/v1/budgets/",
            json={"user_id": unique_id, "category": "Dining", "amount": 500.0}
        )
        await client.post(
            "/api/v1/budgets/",
            json={"user_id": unique_id, "category": "Transportation", "amount": 200.0}
        )

        # List all budgets
        response = await client.get(f"/api/v1/budgets/{unique_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(budget["user_id"] == unique_id for budget in data)


@pytest.mark.asyncio
async def test_get_budget(async_db):
    """Test getting a specific budget"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create a budget
        create_response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Entertainment",
                "amount": 250.0
            }
        )
        budget_id = create_response.json()["budget_id"]

        # Get the budget
        response = await client.get(f"/api/v1/budgets/{unique_id}/{budget_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["budget_id"] == budget_id
        assert data["category"] == "Entertainment"


@pytest.mark.asyncio
async def test_update_budget(async_db):
    """Test updating a budget"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create a budget
        create_response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Shopping",
                "amount": 400.0
            }
        )
        budget_id = create_response.json()["budget_id"]

        # Update the budget
        response = await client.put(
            f"/api/v1/budgets/{unique_id}/{budget_id}",
            json={"amount": 600.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 600.0


@pytest.mark.asyncio
async def test_delete_budget(async_db):
    """Test deleting a budget"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create a budget
        create_response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Groceries",
                "amount": 700.0
            }
        )
        budget_id = create_response.json()["budget_id"]

        # Delete the budget
        response = await client.delete(f"/api/v1/budgets/{unique_id}/{budget_id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = await client.get(f"/api/v1/budgets/{unique_id}/{budget_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_budget_spending_calculation(async_db):
    """Test that budget spending is calculated correctly from transactions"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user in database
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create account
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="checking",
        current_balance=5000.0,
        available_balance=5000.0
    )
    async_db.add(account)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a budget
        response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Dining",
                "amount": 500.0
            }
        )
        budget_id = response.json()["budget_id"]

        # Add some transactions
        today = datetime.now().date()
        for i in range(3):
            transaction = Transaction(
                transaction_id=f"test_txn_{uuid.uuid4().hex[:8]}",
                user_id=unique_id,
                account_id=account.account_id,
                date=today,
                amount=-50.0,  # Negative = spending
                merchant_name=f"Restaurant {i}",
                category_primary="Dining",
                pending=False
            )
            async_db.add(transaction)
        await async_db.commit()

        # Refresh budget spending
        response = await client.post(f"/api/v1/budgets/{unique_id}/{budget_id}/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["spent_amount"] == 150.0  # 3 * 50
        assert data["remaining_amount"] == 350.0  # 500 - 150


@pytest.mark.asyncio
async def test_budget_status_warning(async_db):
    """Test that budget status changes to warning when threshold is exceeded"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create account
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="checking",
        current_balance=5000.0,
        available_balance=5000.0
    )
    async_db.add(account)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a budget with 80% threshold
        response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Shopping",
                "amount": 100.0,
                "alert_threshold": 80.0
            }
        )
        budget_id = response.json()["budget_id"]

        # Add transactions totaling $85 (85% of budget)
        today = datetime.now().date()
        transaction = Transaction(
            transaction_id=f"test_txn_{uuid.uuid4().hex[:8]}",
            user_id=unique_id,
            account_id=account.account_id,
            date=today,
            amount=-85.0,
            merchant_name="Store",
            category_primary="Shopping",
            pending=False
        )
        async_db.add(transaction)
        await async_db.commit()

        # Refresh budget
        response = await client.post(f"/api/v1/budgets/{unique_id}/{budget_id}/refresh")
        data = response.json()
        assert data["spent_amount"] == 85.0
        assert data["status"] == "warning"  # Should be in warning status


@pytest.mark.asyncio
async def test_budget_status_exceeded(async_db):
    """Test that budget status changes to exceeded when over budget"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create account
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="checking",
        current_balance=5000.0,
        available_balance=5000.0
    )
    async_db.add(account)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a budget
        response = await client.post(
            "/api/v1/budgets/",
            json={
                "user_id": unique_id,
                "category": "Dining",
                "amount": 200.0
            }
        )
        budget_id = response.json()["budget_id"]

        # Add transactions totaling $250 (over budget)
        today = datetime.now().date()
        transaction = Transaction(
            transaction_id=f"test_txn_{uuid.uuid4().hex[:8]}",
            user_id=unique_id,
            account_id=account.account_id,
            date=today,
            amount=-250.0,
            merchant_name="Restaurant",
            category_primary="Dining",
            pending=False
        )
        async_db.add(transaction)
        await async_db.commit()

        # Refresh budget
        response = await client.post(f"/api/v1/budgets/{unique_id}/{budget_id}/refresh")
        data = response.json()
        assert data["spent_amount"] == 250.0
        assert data["remaining_amount"] == -50.0
        assert data["status"] == "exceeded"


@pytest.mark.asyncio
async def test_auto_generate_budgets(async_db):
    """Test auto-generating budgets from spending history"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create account
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="checking",
        current_balance=5000.0,
        available_balance=5000.0
    )
    async_db.add(account)
    await async_db.commit()

    # Add historical transactions (last 90 days)
    categories = ["Dining", "Transportation", "Shopping"]
    for i in range(30):  # 30 days of transactions
        days_ago = i
        date = (datetime.now() - timedelta(days=days_ago)).date()
        for category in categories:
            transaction = Transaction(
                transaction_id=f"test_txn_{uuid.uuid4().hex[:8]}",
                user_id=unique_id,
                account_id=account.account_id,
                date=date,
                amount=-50.0,  # $50/day per category
                merchant_name=f"Merchant {i}",
                category_primary=category,
                pending=False
            )
            async_db.add(transaction)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Auto-generate budgets
        response = await client.post(f"/api/v1/budgets/{unique_id}/auto-generate")
        assert response.status_code == 200
        data = response.json()

        # Should have budgets for all 3 categories
        assert len(data) == 3
        assert all(b["is_auto_generated"] for b in data)

        # Each category had $1500 spending over 90 days = $500/month average
        # With 10% buffer = $550
        for budget in data:
            assert budget["amount"] >= 500  # At least the monthly average


@pytest.mark.asyncio
async def test_budget_summary(async_db):
    """Test getting budget summary for a user"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})
        await client.post("/api/v1/consent/", json={"user_id": unique_id, "consent_status": True})

        # Create multiple budgets
        await client.post(
            "/api/v1/budgets/",
            json={"user_id": unique_id, "category": "Dining", "amount": 500.0}
        )
        await client.post(
            "/api/v1/budgets/",
            json={"user_id": unique_id, "category": "Shopping", "amount": 300.0}
        )

        # Get summary
        response = await client.get(f"/api/v1/budgets/{unique_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_budgeted"] == 800.0
        assert data["budget_count"] == 2

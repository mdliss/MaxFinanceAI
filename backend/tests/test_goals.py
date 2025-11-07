import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import User, FinancialGoal, Account
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_goal(async_db):
    """Test creating a financial goal"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create a goal
        response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "emergency_fund",
                "title": "Build Emergency Fund",
                "description": "Save 6 months of expenses",
                "target_amount": 10000.0,
                "target_date": "2025-12-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == unique_id
        assert data["goal_type"] == "emergency_fund"
        assert data["title"] == "Build Emergency Fund"
        assert data["target_amount"] == 10000.0
        assert data["status"] == "active"
        assert data["progress_percent"] == 0.0


@pytest.mark.asyncio
async def test_create_goal_without_consent(async_db):
    """Test that creating a goal without consent fails"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user without consent
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )

        # Try to create a goal (should fail)
        response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "vacation",
                "title": "Summer Vacation",
                "target_amount": 5000.0
            }
        )

        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_goals(async_db):
    """Test listing all goals for a user"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create multiple goals
        await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "emergency_fund",
                "title": "Emergency Fund",
                "target_amount": 10000.0
            }
        )
        await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "vacation",
                "title": "Vacation",
                "target_amount": 3000.0
            }
        )

        # List all goals
        response = await client.get(f"/api/v1/goals/{unique_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(goal["user_id"] == unique_id for goal in data)


@pytest.mark.asyncio
async def test_get_goal(async_db):
    """Test getting a specific goal"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create a goal
        create_response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "retirement",
                "title": "Retirement Savings",
                "target_amount": 100000.0
            }
        )
        goal_id = create_response.json()["goal_id"]

        # Get the goal
        response = await client.get(f"/api/v1/goals/{unique_id}/{goal_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["goal_id"] == goal_id
        assert data["title"] == "Retirement Savings"


@pytest.mark.asyncio
async def test_update_goal(async_db):
    """Test updating a goal"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create a goal
        create_response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "major_purchase",
                "title": "New Car",
                "target_amount": 20000.0
            }
        )
        goal_id = create_response.json()["goal_id"]

        # Update the goal
        response = await client.put(
            f"/api/v1/goals/{unique_id}/{goal_id}",
            json={
                "title": "Used Car",
                "target_amount": 15000.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Used Car"
        assert data["target_amount"] == 15000.0


@pytest.mark.asyncio
async def test_delete_goal(async_db):
    """Test deleting a goal"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create a goal
        create_response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "debt_payoff",
                "title": "Pay Off Credit Card",
                "target_amount": 5000.0
            }
        )
        goal_id = create_response.json()["goal_id"]

        # Delete the goal
        response = await client.delete(f"/api/v1/goals/{unique_id}/{goal_id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = await client.get(f"/api/v1/goals/{unique_id}/{goal_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_goal_progress_calculation(async_db):
    """Test that goal progress is calculated correctly"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user in database
    user = User(
        user_id=unique_id,
        name="Test User",
        consent_status=True
    )
    async_db.add(user)

    # Create savings account with balance
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="savings",
        current_balance=5000.0,
        available_balance=5000.0
    )
    async_db.add(account)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a goal
        response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "emergency_fund",
                "title": "Emergency Fund",
                "target_amount": 10000.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Progress should be calculated based on account balance
        assert data["current_amount"] == 5000.0
        assert data["progress_percent"] == 50.0


@pytest.mark.asyncio
async def test_filter_goals_by_status(async_db):
    """Test filtering goals by status"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User"}
        )
        # Grant consent
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Create active goal
        await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "emergency_fund",
                "title": "Active Goal",
                "target_amount": 10000.0
            }
        )

        # Create paused goal
        create_response = await client.post(
            "/api/v1/goals/",
            json={
                "user_id": unique_id,
                "goal_type": "vacation",
                "title": "Paused Goal",
                "target_amount": 5000.0
            }
        )
        paused_goal_id = create_response.json()["goal_id"]

        # Update to paused
        await client.put(
            f"/api/v1/goals/{unique_id}/{paused_goal_id}",
            json={"status": "paused"}
        )

        # Filter by active
        response = await client.get(f"/api/v1/goals/{unique_id}?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"

        # Filter by paused
        response = await client.get(f"/api/v1/goals/{unique_id}?status=paused")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "paused"

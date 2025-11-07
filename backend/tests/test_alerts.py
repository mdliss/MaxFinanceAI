import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from app.main import app
from app.models import User, Alert, Budget, FinancialGoal, Account, Transaction, Subscription

@pytest.mark.asyncio
async def test_create_alert(async_db):
    """Test creating an alert"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create an alert
        response = await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "budget_warning",
                "severity": "warning",
                "title": "Budget Alert",
                "message": "You've reached 80% of your dining budget"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == unique_id
        assert data["alert_type"] == "budget_warning"
        assert data["severity"] == "warning"
        assert data["is_read"] is False
        assert data["is_dismissed"] is False


@pytest.mark.asyncio
async def test_list_alerts(async_db):
    """Test listing alerts for a user"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create multiple alerts
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "budget_warning",
                "severity": "warning",
                "title": "Budget Alert",
                "message": "Budget warning"
            }
        )
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "goal_milestone",
                "severity": "info",
                "title": "Goal Progress",
                "message": "You reached 50% of your goal"
            }
        )

        # List all alerts
        response = await client.get(f"/api/v1/alerts/{unique_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.asyncio
async def test_filter_alerts_by_severity(async_db):
    """Test filtering alerts by severity"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create alerts with different severities
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "budget_exceeded",
                "severity": "critical",
                "title": "Budget Exceeded",
                "message": "Critical alert"
            }
        )
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "goal_milestone",
                "severity": "info",
                "title": "Goal Update",
                "message": "Info alert"
            }
        )

        # Filter by critical
        response = await client.get(f"/api/v1/alerts/{unique_id}?severity=critical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_get_unread_count(async_db):
    """Test getting unread alert count"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create unread alerts
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "budget_warning",
                "severity": "warning",
                "title": "Alert 1",
                "message": "Message 1"
            }
        )
        await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "low_balance",
                "severity": "critical",
                "title": "Alert 2",
                "message": "Message 2"
            }
        )

        # Get unread count
        response = await client.get(f"/api/v1/alerts/{unique_id}/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 2
        assert data["by_severity"]["warning"] == 1
        assert data["by_severity"]["critical"] == 1


@pytest.mark.asyncio
async def test_mark_alert_as_read(async_db):
    """Test marking an alert as read"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create alert
        create_response = await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "goal_milestone",
                "severity": "info",
                "title": "Goal Alert",
                "message": "Goal reached"
            }
        )
        alert_id = create_response.json()["alert_id"]

        # Mark as read
        response = await client.put(
            f"/api/v1/alerts/{unique_id}/{alert_id}",
            json={"is_read": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        assert data["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_all_as_read(async_db):
    """Test marking all alerts as read"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create multiple unread alerts
        for i in range(3):
            await client.post(
                "/api/v1/alerts/",
                json={
                    "user_id": unique_id,
                    "alert_type": "info",
                    "severity": "info",
                    "title": f"Alert {i}",
                    "message": f"Message {i}"
                }
            )

        # Mark all as read
        response = await client.post(f"/api/v1/alerts/{unique_id}/mark-all-read")
        assert response.status_code == 200

        # Verify all are read
        unread_response = await client.get(f"/api/v1/alerts/{unique_id}/unread-count")
        data = unread_response.json()
        assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_delete_alert(async_db):
    """Test deleting an alert"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create alert
        create_response = await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "test",
                "severity": "info",
                "title": "Test Alert",
                "message": "Test message"
            }
        )
        alert_id = create_response.json()["alert_id"]

        # Delete the alert
        response = await client.delete(f"/api/v1/alerts/{unique_id}/{alert_id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = await client.get(f"/api/v1/alerts/{unique_id}/{alert_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_budget_alerts(async_db):
    """Test auto-generating budget alerts"""
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

    # Create budget that's exceeded
    budget = Budget(
        user_id=unique_id,
        category="Dining",
        amount=500.0,
        period="monthly",
        spent_amount=600.0,
        remaining_amount=-100.0,
        status="exceeded",
        period_start_date=datetime.now().date().isoformat(),
        period_end_date=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    async_db.add(budget)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate alerts
        response = await client.post(f"/api/v1/alerts/{unique_id}/generate")
        assert response.status_code == 200
        data = response.json()
        assert data["alerts_generated"] >= 1

        # Verify budget exceeded alert was created
        alerts = data["alerts"]
        budget_alerts = [a for a in alerts if a["alert_type"] == "budget_exceeded"]
        assert len(budget_alerts) >= 1


@pytest.mark.asyncio
async def test_generate_goal_milestone_alerts(async_db):
    """Test auto-generating goal milestone alerts"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create goal at 50% completion
    goal = FinancialGoal(
        user_id=unique_id,
        goal_type="emergency_fund",
        title="Emergency Fund",
        target_amount=10000.0,
        current_amount=5000.0,
        progress_percent=50.0,
        status="active"
    )
    async_db.add(goal)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate alerts
        response = await client.post(f"/api/v1/alerts/{unique_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # Verify goal milestone alert was created
        alerts = data["alerts"]
        goal_alerts = [a for a in alerts if a["alert_type"] == "goal_milestone"]
        assert len(goal_alerts) >= 1
        assert "50%" in goal_alerts[0]["message"]


@pytest.mark.asyncio
async def test_generate_low_balance_alerts(async_db):
    """Test auto-generating low balance alerts"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create account with low balance
    account = Account(
        account_id=f"test_account_{uuid.uuid4().hex[:8]}",
        user_id=unique_id,
        type="depository",
        subtype="checking",
        current_balance=50.0,  # Low balance
        available_balance=50.0
    )
    async_db.add(account)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate alerts
        response = await client.post(f"/api/v1/alerts/{unique_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # Verify low balance alert was created
        alerts = data["alerts"]
        balance_alerts = [a for a in alerts if a["alert_type"] == "low_balance"]
        assert len(balance_alerts) >= 1


@pytest.mark.asyncio
async def test_generate_subscription_renewal_alerts(async_db):
    """Test auto-generating subscription renewal alerts"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create user
    user = User(user_id=unique_id, name="Test User", consent_status=True)
    async_db.add(user)

    # Create subscription renewing in 2 days
    two_days_from_now = (datetime.now() + timedelta(days=2)).date().isoformat()
    subscription = Subscription(
        user_id=unique_id,
        merchant_name="Netflix",
        amount=15.99,
        frequency="monthly",
        status="active",
        next_billing_date=two_days_from_now
    )
    async_db.add(subscription)
    await async_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate alerts
        response = await client.post(f"/api/v1/alerts/{unique_id}/generate")
        assert response.status_code == 200
        data = response.json()

        # Verify subscription renewal alert was created
        alerts = data["alerts"]
        sub_alerts = [a for a in alerts if a["alert_type"] == "subscription_renewal"]
        assert len(sub_alerts) >= 1
        assert "Netflix" in sub_alerts[0]["message"]


@pytest.mark.asyncio
async def test_dismiss_alert(async_db):
    """Test dismissing an alert"""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post("/api/v1/users/", json={"user_id": unique_id, "name": "Test User"})

        # Create alert
        create_response = await client.post(
            "/api/v1/alerts/",
            json={
                "user_id": unique_id,
                "alert_type": "test",
                "severity": "info",
                "title": "Test Alert",
                "message": "Test message"
            }
        )
        alert_id = create_response.json()["alert_id"]

        # Dismiss the alert
        response = await client.put(
            f"/api/v1/alerts/{unique_id}/{alert_id}",
            json={"is_dismissed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_dismissed"] is True
        assert data["dismissed_at"] is not None

        # Verify it doesn't appear in list (dismissed alerts are filtered)
        list_response = await client.get(f"/api/v1/alerts/{unique_id}")
        alerts = list_response.json()
        assert len(alerts) == 0

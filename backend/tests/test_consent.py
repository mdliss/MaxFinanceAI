import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_user_without_consent():
    """Test creating a user - should default to no consent."""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users/",
            json={
                "user_id": unique_id,
                "name": "Test User",
                "age": 30,
                "income_level": "50000"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == unique_id
        assert data["consent_status"] is False
        assert data["consent_timestamp"] is None

@pytest.mark.asyncio
async def test_grant_consent():
    """Test granting user consent."""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user first
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User 2"}
        )

        # Grant consent
        response = await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consent_status"] is True
        assert data["consent_timestamp"] is not None
        assert "granted successfully" in data["message"]

@pytest.mark.asyncio
async def test_revoke_consent():
    """Test revoking user consent."""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user and grant consent
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User 3"}
        )
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Revoke consent
        response = await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consent_status"] is False
        assert data["consent_timestamp"] is None
        assert "revoked successfully" in data["message"]

@pytest.mark.asyncio
async def test_get_consent_status():
    """Test checking consent status."""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User 4"}
        )

        # Check consent status
        response = await client.get(f"/api/v1/consent/{unique_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["consent_status"] is False
        assert "has not granted consent" in data["message"]

@pytest.mark.asyncio
async def test_revoke_consent_via_delete():
    """Test revoking consent via DELETE endpoint."""
    unique_id = f"test_user_{uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user and grant consent
        await client.post(
            "/api/v1/users/",
            json={"user_id": unique_id, "name": "Test User 5"}
        )
        await client.post(
            "/api/v1/consent/",
            json={"user_id": unique_id, "consent_status": True}
        )

        # Revoke via DELETE
        response = await client.delete(f"/api/v1/consent/{unique_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["consent_status"] is False

@pytest.mark.asyncio
async def test_consent_nonexistent_user():
    """Test granting consent to non-existent user."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/consent/",
            json={"user_id": "nonexistent", "consent_status": True}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

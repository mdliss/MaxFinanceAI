import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Recommendation, Feedback


class TestProfileEndpoint:
    """Tests for GET /profile/{user_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, client: AsyncClient, test_user_with_consent):
        """Test getting comprehensive user profile"""
        response = await client.get(f"/api/v1/profile/{test_user_with_consent.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user_with_consent.user_id
        assert data["name"] == test_user_with_consent.name
        assert data["consent_status"] is True
        assert "signals" in data
        assert "personas" in data
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_get_profile_no_consent(self, client: AsyncClient, test_user_no_consent):
        """Test that profile access is denied without consent"""
        response = await client.get(f"/api/v1/profile/{test_user_no_consent.user_id}")

        assert response.status_code == 403
        assert "consent required" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_profile_user_not_found(self, client: AsyncClient):
        """Test getting profile for non-existent user"""
        response = await client.get("/api/v1/profile/nonexistent_user")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestFeedbackEndpoint:
    """Tests for POST /feedback endpoint"""

    @pytest.mark.asyncio
    async def test_submit_feedback_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_consent,
        test_recommendation
    ):
        """Test submitting feedback on a recommendation"""
        feedback_data = {
            "user_id": test_user_with_consent.user_id,
            "recommendation_id": test_recommendation.recommendation_id,
            "rating": 5,
            "comment": "Very helpful recommendation!",
            "feedback_type": "helpful"
        }

        response = await client.post("/api/v1/recommendations/feedback", json=feedback_data)

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user_with_consent.user_id
        assert data["recommendation_id"] == test_recommendation.recommendation_id
        assert data["rating"] == 5
        assert data["comment"] == "Very helpful recommendation!"
        assert data["feedback_type"] == "helpful"

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(
        self,
        client: AsyncClient,
        test_user_with_consent,
        test_recommendation
    ):
        """Test submitting feedback with invalid rating (outside 1-5 range)"""
        feedback_data = {
            "user_id": test_user_with_consent.user_id,
            "recommendation_id": test_recommendation.recommendation_id,
            "rating": 6,  # Invalid: must be 1-5
            "feedback_type": "helpful"
        }

        response = await client.post("/api/v1/recommendations/feedback", json=feedback_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_submit_feedback_user_not_found(self, client: AsyncClient):
        """Test submitting feedback for non-existent user"""
        feedback_data = {
            "user_id": "nonexistent_user",
            "recommendation_id": 1,
            "rating": 5,
            "feedback_type": "helpful"
        }

        response = await client.post("/api/v1/recommendations/feedback", json=feedback_data)

        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_feedback_recommendation_not_found(
        self,
        client: AsyncClient,
        test_user_with_consent
    ):
        """Test submitting feedback for non-existent recommendation"""
        feedback_data = {
            "user_id": test_user_with_consent.user_id,
            "recommendation_id": 99999,  # Non-existent
            "rating": 5,
            "feedback_type": "helpful"
        }

        response = await client.post("/api/v1/recommendations/feedback", json=feedback_data)

        assert response.status_code == 404
        assert "recommendation not found" in response.json()["detail"].lower()


class TestOperatorApproveEndpoint:
    """Tests for POST /operator/approve/{recommendation_id}"""

    @pytest.mark.asyncio
    async def test_approve_recommendation_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_recommendation
    ):
        """Test approving a recommendation"""
        approve_data = {
            "operator_id": "operator_001",
            "notes": "Looks good, approved"
        }

        response = await client.post(
            f"/api/v1/operator/approve/{test_recommendation.recommendation_id}",
            json=approve_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["operator_notes"] == "Looks good, approved"
        assert "approved successfully" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_approve_recommendation_not_found(self, client: AsyncClient):
        """Test approving non-existent recommendation"""
        approve_data = {
            "operator_id": "operator_001",
            "notes": "Test"
        }

        response = await client.post(
            "/api/v1/operator/approve/99999",
            json=approve_data
        )

        assert response.status_code == 404


class TestOperatorOverrideEndpoint:
    """Tests for POST /operator/override/{recommendation_id}"""

    @pytest.mark.asyncio
    async def test_override_recommendation_success(
        self,
        client: AsyncClient,
        test_recommendation
    ):
        """Test overriding a recommendation"""
        override_data = {
            "operator_id": "operator_001",
            "new_title": "Updated Title",
            "new_description": "Updated description",
            "notes": "Content needed improvement"
        }

        response = await client.post(
            f"/api/v1/operator/override/{test_recommendation.recommendation_id}",
            json=override_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert "original_values" in data
        assert "overridden successfully" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_override_recommendation_partial(
        self,
        client: AsyncClient,
        test_recommendation
    ):
        """Test partial override (only some fields)"""
        override_data = {
            "operator_id": "operator_001",
            "new_title": "Only Title Changed",
            "notes": "Just updating the title"
        }

        response = await client.post(
            f"/api/v1/operator/override/{test_recommendation.recommendation_id}",
            json=override_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"

    @pytest.mark.asyncio
    async def test_override_recommendation_not_found(self, client: AsyncClient):
        """Test overriding non-existent recommendation"""
        override_data = {
            "operator_id": "operator_001",
            "notes": "Test"
        }

        response = await client.post(
            "/api/v1/operator/override/99999",
            json=override_data
        )

        assert response.status_code == 404


class TestOperatorFlagEndpoint:
    """Tests for POST /operator/flag/{recommendation_id}"""

    @pytest.mark.asyncio
    async def test_flag_recommendation_success(
        self,
        client: AsyncClient,
        test_recommendation
    ):
        """Test flagging a recommendation"""
        flag_data = {
            "operator_id": "operator_001",
            "reason": "Potentially inappropriate tone",
            "severity": "high",
            "notes": "Needs review by senior operator"
        }

        response = await client.post(
            f"/api/v1/operator/flag/{test_recommendation.recommendation_id}",
            json=flag_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "review"
        assert data["severity"] == "high"
        assert data["reason"] == "Potentially inappropriate tone"
        assert "flagged for review" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_flag_recommendation_invalid_severity(
        self,
        client: AsyncClient,
        test_recommendation
    ):
        """Test flagging with invalid severity level"""
        flag_data = {
            "operator_id": "operator_001",
            "reason": "Test",
            "severity": "critical",  # Invalid: must be low, medium, or high
            "notes": "Test"
        }

        response = await client.post(
            f"/api/v1/operator/flag/{test_recommendation.recommendation_id}",
            json=flag_data
        )

        assert response.status_code == 400
        assert "invalid severity" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_flag_recommendation_not_found(self, client: AsyncClient):
        """Test flagging non-existent recommendation"""
        flag_data = {
            "operator_id": "operator_001",
            "reason": "Test",
            "severity": "low",
            "notes": "Test"
        }

        response = await client.post(
            "/api/v1/operator/flag/99999",
            json=flag_data
        )

        assert response.status_code == 404

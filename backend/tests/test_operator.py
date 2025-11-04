import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from app.models import User, Recommendation, AuditLog, Signal, Persona


@pytest.mark.asyncio
async def test_get_dashboard_stats(async_db):
    """Test getting dashboard statistics"""
    from app.api.operator import get_dashboard_stats

    stats = await get_dashboard_stats(db=async_db)

    # Should have all required fields
    assert hasattr(stats, "total_users")
    assert hasattr(stats, "users_with_consent")
    assert hasattr(stats, "total_recommendations")
    assert hasattr(stats, "pending_recommendations")
    assert hasattr(stats, "approved_recommendations")
    assert hasattr(stats, "total_signals")
    assert hasattr(stats, "total_personas")
    assert hasattr(stats, "total_transactions")
    assert hasattr(stats, "recent_consent_changes")

    # All should be non-negative integers
    assert stats.total_users >= 0
    assert stats.users_with_consent >= 0
    assert stats.total_recommendations >= 0


@pytest.mark.asyncio
async def test_get_all_recommendations(async_db):
    """Test getting all recommendations with pagination"""
    from app.api.operator import get_all_recommendations

    result = await get_all_recommendations(
        status=None,
        persona_type=None,
        limit=10,
        offset=0,
        db=async_db
    )

    assert "recommendations" in result
    assert "total" in result
    assert "limit" in result
    assert "offset" in result
    assert isinstance(result["recommendations"], list)
    assert result["limit"] == 10
    assert result["offset"] == 0


@pytest.mark.asyncio
async def test_get_recommendations_filtered_by_status(async_db):
    """Test filtering recommendations by approval status"""
    from app.api.operator import get_all_recommendations

    # Get approved recommendations
    result = await get_all_recommendations(
        status="approved",
        persona_type=None,
        limit=50,
        offset=0,
        db=async_db
    )

    # All recommendations should be approved
    for rec in result["recommendations"]:
        assert rec["approval_status"] == "approved"


@pytest.mark.asyncio
async def test_update_recommendation_status(async_db):
    """Test updating recommendation approval status"""
    from app.api.operator import update_recommendation_status, RecommendationUpdate
    from fastapi import HTTPException

    # Get a recommendation
    result = await async_db.execute(select(Recommendation).limit(1))
    recommendation = result.scalar_one_or_none()

    if recommendation:
        # Update status
        update = RecommendationUpdate(
            approval_status="review",
            operator_notes="Needs further review"
        )

        response = await update_recommendation_status(
            recommendation_id=recommendation.recommendation_id,
            update=update,
            db=async_db
        )

        assert response["approval_status"] == "review"
        assert response["operator_notes"] == "Needs further review"

        # Verify in database
        await async_db.refresh(recommendation)
        assert recommendation.approval_status == "review"
        assert recommendation.operator_notes == "Needs further review"


@pytest.mark.asyncio
async def test_update_nonexistent_recommendation(async_db):
    """Test updating a recommendation that doesn't exist"""
    from app.api.operator import update_recommendation_status, RecommendationUpdate
    from fastapi import HTTPException

    update = RecommendationUpdate(approval_status="approved")

    with pytest.raises(HTTPException) as exc_info:
        await update_recommendation_status(
            recommendation_id=999999,
            update=update,
            db=async_db
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_recommendation_invalid_status(async_db):
    """Test updating recommendation with invalid status"""
    from app.api.operator import update_recommendation_status, RecommendationUpdate
    from fastapi import HTTPException

    # Get a recommendation
    result = await async_db.execute(select(Recommendation).limit(1))
    recommendation = result.scalar_one_or_none()

    if recommendation:
        update = RecommendationUpdate(approval_status="invalid_status")

        with pytest.raises(HTTPException) as exc_info:
            await update_recommendation_status(
                recommendation_id=recommendation.recommendation_id,
                update=update,
                db=async_db
            )

        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_audit_logs(async_db):
    """Test getting audit logs"""
    from app.api.operator import get_audit_logs

    result = await get_audit_logs(
        user_id=None,
        action=None,
        days=7,
        limit=100,
        offset=0,
        db=async_db
    )

    assert "logs" in result
    assert "total" in result
    assert "limit" in result
    assert "offset" in result
    assert isinstance(result["logs"], list)


@pytest.mark.asyncio
async def test_get_audit_logs_filtered(async_db):
    """Test getting audit logs with filters"""
    from app.api.operator import get_audit_logs

    # Get consent-related logs
    result = await get_audit_logs(
        user_id=None,
        action="consent_granted",
        days=30,
        limit=50,
        offset=0,
        db=async_db
    )

    # All logs should be consent_granted
    for log in result["logs"]:
        assert log["action"] == "consent_granted"


@pytest.mark.asyncio
async def test_get_users_summary(async_db):
    """Test getting users summary"""
    from app.api.operator import get_users_summary

    result = await get_users_summary(
        consent_status=None,
        limit=50,
        offset=0,
        db=async_db
    )

    assert "users" in result
    assert "total" in result
    assert "limit" in result
    assert "offset" in result
    assert isinstance(result["users"], list)

    # Check user structure
    if result["users"]:
        user = result["users"][0]
        assert "user_id" in user
        assert "name" in user
        assert "consent_status" in user
        assert "signal_count" in user
        assert "persona_count" in user
        assert "recommendation_count" in user


@pytest.mark.asyncio
async def test_get_users_summary_filtered_by_consent(async_db):
    """Test getting users summary filtered by consent"""
    from app.api.operator import get_users_summary

    # Get only users with consent
    result = await get_users_summary(
        consent_status=True,
        limit=50,
        offset=0,
        db=async_db
    )

    # All users should have consent
    for user in result["users"]:
        assert user["consent_status"] == True


@pytest.mark.asyncio
async def test_get_user_details(async_db):
    """Test getting detailed user information"""
    from app.api.operator import get_user_details

    # Get a user
    result = await async_db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if user:
        details = await get_user_details(user_id=user.user_id, db=async_db)

        assert "user" in details
        assert "transaction_count" in details
        assert "signals" in details
        assert "personas" in details
        assert "recommendations" in details
        assert "audit_logs" in details

        # User info should match
        assert details["user"]["user_id"] == user.user_id
        assert details["user"]["name"] == user.name


@pytest.mark.asyncio
async def test_get_user_details_not_found(async_db):
    """Test getting details for non-existent user"""
    from app.api.operator import get_user_details
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_user_details(user_id="nonexistent_user", db=async_db)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_recommendations_by_persona(async_db):
    """Test getting recommendation counts by persona"""
    from app.api.operator import get_recommendations_by_persona

    result = await get_recommendations_by_persona(db=async_db)

    assert "persona_stats" in result
    assert isinstance(result["persona_stats"], list)

    # Each stat should have persona_type and count
    for stat in result["persona_stats"]:
        assert "persona_type" in stat
        assert "count" in stat
        assert stat["count"] >= 0


@pytest.mark.asyncio
async def test_get_consent_trends(async_db):
    """Test getting consent trends over time"""
    from app.api.operator import get_consent_trends

    result = await get_consent_trends(days=30, db=async_db)

    assert "period_days" in result
    assert "grants" in result
    assert "revocations" in result
    assert result["period_days"] == 30
    assert isinstance(result["grants"], dict)
    assert isinstance(result["revocations"], dict)


@pytest.mark.asyncio
async def test_pagination_recommendations(async_db):
    """Test pagination for recommendations list"""
    from app.api.operator import get_all_recommendations

    # Get first page
    page1 = await get_all_recommendations(
        status=None,
        persona_type=None,
        limit=5,
        offset=0,
        db=async_db
    )

    # Get second page
    page2 = await get_all_recommendations(
        status=None,
        persona_type=None,
        limit=5,
        offset=5,
        db=async_db
    )

    # Pages should have different recommendations (if enough exist)
    if len(page1["recommendations"]) == 5 and len(page2["recommendations"]) > 0:
        page1_ids = {r["recommendation_id"] for r in page1["recommendations"]}
        page2_ids = {r["recommendation_id"] for r in page2["recommendations"]}
        assert page1_ids != page2_ids


@pytest.mark.asyncio
async def test_pagination_audit_logs(async_db):
    """Test pagination for audit logs"""
    from app.api.operator import get_audit_logs

    # Get first page
    page1 = await get_audit_logs(
        user_id=None,
        action=None,
        days=30,
        limit=10,
        offset=0,
        db=async_db
    )

    # Get second page
    page2 = await get_audit_logs(
        user_id=None,
        action=None,
        days=30,
        limit=10,
        offset=10,
        db=async_db
    )

    # Both should have metadata
    assert page1["limit"] == 10
    assert page1["offset"] == 0
    assert page2["offset"] == 10


@pytest.mark.asyncio
async def test_pagination_users(async_db):
    """Test pagination for users summary"""
    from app.api.operator import get_users_summary

    # Get first page
    page1 = await get_users_summary(
        consent_status=None,
        limit=10,
        offset=0,
        db=async_db
    )

    # Get second page
    page2 = await get_users_summary(
        consent_status=None,
        limit=10,
        offset=10,
        db=async_db
    )

    # Pages should have different users (if enough exist)
    if len(page1["users"]) == 10 and len(page2["users"]) > 0:
        page1_ids = {u["user_id"] for u in page1["users"]}
        page2_ids = {u["user_id"] for u in page2["users"]}
        assert page1_ids != page2_ids

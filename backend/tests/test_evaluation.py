import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_
from app.models import User, Account, Transaction, Signal, Persona, Recommendation
from app.services.evaluation import EvaluationService


@pytest.mark.asyncio
async def test_calculate_quality_metrics(async_db):
    """Test quality metrics calculation"""
    service = EvaluationService(async_db)
    metrics = await service._calculate_quality_metrics(180)  # Last 180 days

    # Should have metrics structure
    assert "relevance_score" in metrics
    assert "diversity_score" in metrics
    assert "coverage_rate" in metrics
    assert "personalization_score" in metrics
    assert "total_recommendations" in metrics
    assert "avg_recommendations_per_user" in metrics
    assert "content_type_distribution" in metrics

    # Metrics should be between 0 and 1
    assert 0 <= metrics["relevance_score"] <= 1
    assert 0 <= metrics["diversity_score"] <= 1
    assert 0 <= metrics["coverage_rate"] <= 1
    assert 0 <= metrics["personalization_score"] <= 1


@pytest.mark.asyncio
async def test_calculate_performance_metrics(async_db):
    """Test system performance metrics"""
    service = EvaluationService(async_db)
    metrics = await service._calculate_performance_metrics(180)

    # Should have all required fields
    assert "total_signals_detected" in metrics
    assert "total_personas_assigned" in metrics
    assert "total_recommendations_generated" in metrics
    assert "throughput_signals_per_day" in metrics
    assert "throughput_personas_per_day" in metrics
    assert "throughput_recommendations_per_day" in metrics
    assert "unique_users_processed" in metrics
    assert metrics["time_period_days"] == 180

    # Counts should be non-negative
    assert metrics["total_signals_detected"] >= 0
    assert metrics["total_personas_assigned"] >= 0
    assert metrics["total_recommendations_generated"] >= 0
    assert metrics["unique_users_processed"] >= 0


@pytest.mark.asyncio
async def test_calculate_outcome_metrics(async_db):
    """Test user outcome metrics"""
    service = EvaluationService(async_db)
    metrics = await service._calculate_outcome_metrics(180)

    # Should have all required fields
    assert "approval_rate" in metrics
    assert "rejection_rate" in metrics
    assert "pending_count" in metrics
    assert "total_approved" in metrics
    assert "total_rejected" in metrics
    assert "persona_distribution" in metrics
    assert "signal_detection_rate" in metrics
    assert "consent_rate" in metrics
    assert "total_users" in metrics
    assert "users_with_signals" in metrics

    # Rates should be between 0 and 1
    assert 0 <= metrics["approval_rate"] <= 1
    assert 0 <= metrics["rejection_rate"] <= 1
    assert 0 <= metrics["signal_detection_rate"] <= 1
    assert 0 <= metrics["consent_rate"] <= 1

    # Counts should be non-negative
    assert metrics["total_users"] >= 0
    assert metrics["users_with_signals"] >= 0


@pytest.mark.asyncio
async def test_calculate_guardrail_metrics(async_db):
    """Test guardrail effectiveness metrics"""
    service = EvaluationService(async_db)
    metrics = await service._calculate_guardrail_metrics(180)

    # Should have all required fields
    assert "eligibility_rate" in metrics
    assert "eligible_users" in metrics
    assert "total_users_checked" in metrics
    assert "ineligibility_reasons" in metrics
    assert "vulnerable_populations" in metrics
    assert "rate_limit_violations" in metrics
    assert "content_safety_enabled" in metrics

    # Check ineligibility reasons structure
    assert "no_consent" in metrics["ineligibility_reasons"]
    assert "under_age" in metrics["ineligibility_reasons"]
    assert "insufficient_transactions" in metrics["ineligibility_reasons"]
    assert "no_signals" in metrics["ineligibility_reasons"]

    # Check vulnerable populations structure
    assert "seniors_65_plus" in metrics["vulnerable_populations"]
    assert "low_income_under_30k" in metrics["vulnerable_populations"]
    assert "young_adults_18_21" in metrics["vulnerable_populations"]

    # Eligibility rate should be between 0 and 1
    assert 0 <= metrics["eligibility_rate"] <= 1

    # Content safety should always be enabled
    assert metrics["content_safety_enabled"] is True


@pytest.mark.asyncio
async def test_evaluate_recommendation_batch(async_db):
    """Test batch evaluation of users"""
    # Get 3 existing users
    result = await async_db.execute(
        select(User.user_id).limit(3)
    )
    user_ids = [row[0] for row in result.all()]

    if not user_ids:
        pytest.skip("No users in database")

    service = EvaluationService(async_db)
    results = await service.evaluate_recommendation_batch(user_ids)

    assert results["total_users"] == len(user_ids)
    assert results["successful"] + results["failed"] == len(user_ids)
    assert "metrics" in results
    assert "avg_signals_per_user" in results["metrics"]
    assert "avg_personas_per_user" in results["metrics"]
    assert "avg_recommendations_per_user" in results["metrics"]
    assert "users_with_signals" in results["metrics"]
    assert "users_with_personas" in results["metrics"]
    assert "users_with_recommendations" in results["metrics"]


@pytest.mark.asyncio
async def test_evaluate_batch_with_nonexistent_users(async_db):
    """Test batch evaluation with non-existent users"""
    service = EvaluationService(async_db)
    results = await service.evaluate_recommendation_batch(
        ["nonexistent_user_1", "nonexistent_user_2"]
    )

    assert results["total_users"] == 2
    assert results["failed"] == 2
    assert len(results["errors"]) == 2


@pytest.mark.asyncio
async def test_get_quality_report_existing_user(async_db):
    """Test quality report for an existing user"""
    # Get a user with consent
    result = await async_db.execute(
        select(User.user_id).where(User.consent_status == True).limit(1)
    )
    user_id = result.scalar_one_or_none()

    if not user_id:
        pytest.skip("No consented users in database")

    service = EvaluationService(async_db)
    report = await service.get_quality_report(user_id)

    assert report["user_id"] == user_id
    assert "timestamp" in report
    assert "pipeline_status" in report
    assert "details" in report
    assert "issues" in report
    assert "overall_status" in report

    # Check pipeline status structure
    assert "user_exists" in report["pipeline_status"]
    assert "has_consent" in report["pipeline_status"]
    assert "has_transactions" in report["pipeline_status"]
    assert "has_signals" in report["pipeline_status"]
    assert "has_personas" in report["pipeline_status"]
    assert "has_recommendations" in report["pipeline_status"]

    assert report["pipeline_status"]["user_exists"] is True


@pytest.mark.asyncio
async def test_get_quality_report_nonexistent_user(async_db):
    """Test quality report for non-existent user"""
    service = EvaluationService(async_db)
    report = await service.get_quality_report("nonexistent_user_xyz")

    assert report["user_id"] == "nonexistent_user_xyz"
    assert report["pipeline_status"]["user_exists"] is False
    assert "User not found" in report["issues"]


@pytest.mark.asyncio
async def test_calculate_all_metrics(async_db):
    """Test comprehensive metrics calculation"""
    service = EvaluationService(async_db)
    metrics = await service.calculate_all_metrics(time_period_days=180)

    # Verify metrics object structure
    metrics_dict = metrics.to_dict()
    assert "timestamp" in metrics_dict
    assert "recommendation_quality" in metrics_dict
    assert "system_performance" in metrics_dict
    assert "user_outcomes" in metrics_dict
    assert "guardrail_effectiveness" in metrics_dict

    # Verify each category has data
    assert isinstance(metrics_dict["recommendation_quality"], dict)
    assert isinstance(metrics_dict["system_performance"], dict)
    assert isinstance(metrics_dict["user_outcomes"], dict)
    assert isinstance(metrics_dict["guardrail_effectiveness"], dict)


@pytest.mark.asyncio
async def test_quality_metrics_with_recommendations(async_db):
    """Test quality metrics when recommendations exist"""
    # Get a user with consent and create test recommendation
    result = await async_db.execute(
        select(User).where(User.consent_status == True).limit(1)
    )
    user = result.scalar_one_or_none()

    if not user:
        pytest.skip("No consented users in database")

    # Create test persona (persona_id autoincrements, don't set it)
    test_persona = Persona(
        user_id=user.user_id,
        window_days=180,  # Required field
        persona_type="savings_builder",
        priority_rank=2,
        criteria_met=json.dumps({"test": "data"}),  # Convert dict to JSON string
        assigned_at=datetime.utcnow()
    )
    async_db.add(test_persona)

    # Create test recommendation (created_at and recommendation_id will be auto-set by database)
    test_rec = Recommendation(
        user_id=user.user_id,
        persona_type="savings_builder",
        content_type="article",
        title="Test Article for Evaluation",
        description="This is a test article for evaluation metrics",
        rationale="You are saving consistently each month, this article will help you optimize your savings strategy.",
        disclaimer="Educational content only",
        eligibility_met=True,  # Boolean, not integer
        approval_status="pending"
    )
    async_db.add(test_rec)
    await async_db.commit()

    try:
        # Calculate metrics
        service = EvaluationService(async_db)
        metrics = await service._calculate_quality_metrics(1)  # Last 1 day

        # Should include our test recommendation
        assert metrics["total_recommendations"] >= 1
        assert "article" in metrics["content_type_distribution"]

    finally:
        # Cleanup
        await async_db.execute(
            delete(Recommendation).where(
                Recommendation.recommendation_id == test_rec.recommendation_id
            )
        )
        # Persona persona_id is auto-generated, use user_id and type to find it
        await async_db.execute(
            delete(Persona).where(
                and_(
                    Persona.user_id == user.user_id,
                    Persona.persona_type == "savings_builder",
                    Persona.window_days == 180
                )
            )
        )
        await async_db.commit()


@pytest.mark.asyncio
async def test_batch_evaluation_with_mixed_users(async_db):
    """Test batch evaluation with mix of existing and non-existent users"""
    # Get one existing user
    result = await async_db.execute(
        select(User.user_id).limit(1)
    )
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        pytest.skip("No users in database")

    # Mix existing and non-existent users
    user_ids = [existing_user, "nonexistent_user_test_1", "nonexistent_user_test_2"]

    service = EvaluationService(async_db)
    results = await service.evaluate_recommendation_batch(user_ids)

    assert results["total_users"] == 3
    assert results["successful"] >= 1  # At least the existing user
    assert results["failed"] >= 2  # At least the two non-existent users


@pytest.mark.asyncio
async def test_guardrail_metrics_detects_vulnerable_populations(async_db):
    """Test that guardrail metrics correctly identify vulnerable populations"""
    service = EvaluationService(async_db)
    metrics = await service._calculate_guardrail_metrics(180)

    # The synthetic data should have some vulnerable populations
    vulnerable = metrics["vulnerable_populations"]

    # Counts should be non-negative
    assert vulnerable["seniors_65_plus"] >= 0
    assert vulnerable["low_income_under_30k"] >= 0
    assert vulnerable["young_adults_18_21"] >= 0

    # Total vulnerable should not exceed total users
    total_vulnerable = (
        vulnerable["seniors_65_plus"] +
        vulnerable["low_income_under_30k"] +
        vulnerable["young_adults_18_21"]
    )
    assert total_vulnerable <= metrics["total_users_checked"]

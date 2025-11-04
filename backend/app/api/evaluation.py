from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.services.evaluation import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/metrics/all")
async def get_all_metrics(
    time_period_days: int = Query(default=30, ge=1, le=365, description="Time period in days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive system metrics

    Returns:
    - Recommendation quality metrics (relevance, diversity, coverage)
    - System performance metrics (throughput, processing stats)
    - User outcome metrics (approval rates, persona distribution)
    - Guardrail effectiveness metrics (eligibility, protections)
    """
    service = EvaluationService(db)
    metrics = await service.calculate_all_metrics(time_period_days)
    return metrics.to_dict()


@router.get("/metrics/quality")
async def get_quality_metrics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recommendation quality metrics only

    Metrics include:
    - Relevance score: % of recommendations matching user personas
    - Diversity score: Distribution across content types
    - Coverage rate: % of eligible users receiving recommendations
    - Personalization score: % with detailed rationales
    """
    service = EvaluationService(db)
    quality_metrics = await service._calculate_quality_metrics(time_period_days)
    return {
        "time_period_days": time_period_days,
        "metrics": quality_metrics
    }


@router.get("/metrics/performance")
async def get_performance_metrics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system performance metrics

    Metrics include:
    - Total operations (signals, personas, recommendations)
    - Throughput rates (per day)
    - Unique users processed
    """
    service = EvaluationService(db)
    performance_metrics = await service._calculate_performance_metrics(time_period_days)
    return {
        "time_period_days": time_period_days,
        "metrics": performance_metrics
    }


@router.get("/metrics/outcomes")
async def get_outcome_metrics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user outcome metrics

    Metrics include:
    - Approval/rejection rates
    - Persona distribution
    - Signal detection rates
    - Consent rates
    """
    service = EvaluationService(db)
    outcome_metrics = await service._calculate_outcome_metrics(time_period_days)
    return {
        "time_period_days": time_period_days,
        "metrics": outcome_metrics
    }


@router.get("/metrics/guardrails")
async def get_guardrail_metrics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get guardrail effectiveness metrics

    Metrics include:
    - Eligibility rates
    - Ineligibility reasons breakdown
    - Vulnerable population counts
    - Rate limiting violations
    """
    service = EvaluationService(db)
    guardrail_metrics = await service._calculate_guardrail_metrics(time_period_days)
    return {
        "time_period_days": time_period_days,
        "metrics": guardrail_metrics
    }


@router.post("/batch/evaluate")
async def evaluate_user_batch(
    user_ids: List[str],
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate a batch of users through the full pipeline

    Useful for:
    - Testing specific user cohorts
    - Quality assurance
    - Debugging pipeline issues

    Returns metrics for:
    - Average signals/personas/recommendations per user
    - Success/failure counts
    - Error details
    """
    if not user_ids:
        raise HTTPException(status_code=400, detail="user_ids list cannot be empty")

    if len(user_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 users per batch evaluation"
        )

    service = EvaluationService(db)
    results = await service.evaluate_recommendation_batch(user_ids)
    return results


@router.get("/user/{user_id}/quality-report")
async def get_user_quality_report(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate detailed quality report for a specific user

    Shows:
    - Pipeline status (each step of the recommendation flow)
    - Detailed counts (transactions, signals, personas, recommendations)
    - Quality validation (persona matching, disclaimers, etc.)
    - Issues detected

    Useful for debugging and quality assurance
    """
    service = EvaluationService(db)
    report = await service.get_quality_report(user_id)
    return report


@router.get("/health-check")
async def evaluation_health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    Quick health check for the evaluation system
    Returns basic stats to verify system is operational
    """
    service = EvaluationService(db)

    # Quick metrics for last 7 days
    metrics = await service.calculate_all_metrics(time_period_days=7)

    return {
        "status": "healthy",
        "timestamp": metrics.timestamp.isoformat(),
        "quick_stats": {
            "total_recommendations_7d": metrics.recommendation_quality.get("total_recommendations", 0),
            "coverage_rate": metrics.recommendation_quality.get("coverage_rate", 0),
            "approval_rate": metrics.user_outcomes.get("approval_rate", 0),
            "eligibility_rate": metrics.guardrail_effectiveness.get("eligibility_rate", 0)
        }
    }

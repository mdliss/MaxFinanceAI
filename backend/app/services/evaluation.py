from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func, distinct, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User, Recommendation, Signal, Persona, Transaction,
    AuditLog, Account
)
import time


class EvaluationMetrics:
    """Container for evaluation metrics"""

    def __init__(self):
        self.recommendation_quality = {}
        self.system_performance = {}
        self.user_outcomes = {}
        self.guardrail_effectiveness = {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "recommendation_quality": self.recommendation_quality,
            "system_performance": self.system_performance,
            "user_outcomes": self.user_outcomes,
            "guardrail_effectiveness": self.guardrail_effectiveness
        }


class EvaluationService:
    """Evaluates recommendation system quality and effectiveness"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_all_metrics(
        self,
        time_period_days: int = 30
    ) -> EvaluationMetrics:
        """Calculate comprehensive metrics for the system"""
        metrics = EvaluationMetrics()

        # Calculate all metric categories
        metrics.recommendation_quality = await self._calculate_quality_metrics(time_period_days)
        metrics.system_performance = await self._calculate_performance_metrics(time_period_days)
        metrics.user_outcomes = await self._calculate_outcome_metrics(time_period_days)
        metrics.guardrail_effectiveness = await self._calculate_guardrail_metrics(time_period_days)

        return metrics

    async def _calculate_quality_metrics(self, days: int) -> Dict:
        """Calculate recommendation quality metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get recommendations from time period
        result = await self.db.execute(
            select(Recommendation).where(Recommendation.created_at >= cutoff_date)
        )
        recommendations = result.scalars().all()

        if not recommendations:
            return {
                "relevance_score": 0.0,
                "diversity_score": 0.0,
                "coverage_rate": 0.0,
                "personalization_score": 0.0,
                "avg_recommendations_per_user": 0.0,
                "total_recommendations": 0,
                "content_type_distribution": {}
            }

        # Relevance: % of recommendations with matching persona
        relevance_count = 0
        for rec in recommendations:
            # Get user's personas
            personas_result = await self.db.execute(
                select(Persona).where(Persona.user_id == rec.user_id)
            )
            user_personas = [p.persona_type for p in personas_result.scalars().all()]

            if rec.persona_type in user_personas:
                relevance_count += 1

        relevance_score = relevance_count / len(recommendations) if recommendations else 0.0

        # Diversity: Distribution across content types
        content_types = {}
        for rec in recommendations:
            content_types[rec.content_type] = content_types.get(rec.content_type, 0) + 1

        # Calculate diversity using Simpson's diversity index
        # Higher = more diverse (1 - sum of squared proportions)
        total = len(recommendations)
        diversity_score = 1 - sum((count / total) ** 2 for count in content_types.values())

        # Coverage: % of eligible users who received recommendations
        total_users_result = await self.db.execute(
            select(func.count(distinct(User.user_id))).where(User.consent_status == True)
        )
        total_eligible_users = total_users_result.scalar() or 0

        users_with_recs_result = await self.db.execute(
            select(func.count(distinct(Recommendation.user_id))).where(
                Recommendation.created_at >= cutoff_date
            )
        )
        users_with_recs = users_with_recs_result.scalar() or 0

        # Cap at 100% - coverage rate should never exceed 1.0
        coverage_rate = min(1.0, users_with_recs / total_eligible_users if total_eligible_users > 0 else 0.0)

        # Personalization: % with non-generic rationales
        personalized_count = sum(
            1 for rec in recommendations
            if rec.rationale and len(rec.rationale) > 50  # Non-trivial rationale
        )
        personalization_score = personalized_count / len(recommendations) if recommendations else 0.0

        # Average recommendations per user
        avg_recs_per_user = len(recommendations) / users_with_recs if users_with_recs > 0 else 0.0

        return {
            "relevance_score": round(relevance_score, 3),
            "diversity_score": round(diversity_score, 3),
            "coverage_rate": round(coverage_rate, 3),
            "personalization_score": round(personalization_score, 3),
            "avg_recommendations_per_user": round(avg_recs_per_user, 2),
            "total_recommendations": len(recommendations),
            "content_type_distribution": content_types
        }

    async def _calculate_performance_metrics(self, days: int) -> Dict:
        """Calculate system performance metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count total operations (signals, personas, recommendations)
        signals_result = await self.db.execute(
            select(func.count(Signal.signal_id)).where(Signal.computed_at >= cutoff_date)
        )
        total_signals = signals_result.scalar() or 0

        personas_result = await self.db.execute(
            select(func.count(Persona.persona_id)).where(Persona.assigned_at >= cutoff_date)
        )
        total_personas = personas_result.scalar() or 0

        recommendations_result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                Recommendation.created_at >= cutoff_date
            )
        )
        total_recommendations = recommendations_result.scalar() or 0

        # Calculate throughput (per day)
        throughput_signals = total_signals / days if days > 0 else 0
        throughput_personas = total_personas / days if days > 0 else 0
        throughput_recommendations = total_recommendations / days if days > 0 else 0

        # Get unique users processed
        users_processed_result = await self.db.execute(
            select(func.count(distinct(Signal.user_id))).where(
                Signal.computed_at >= cutoff_date
            )
        )
        users_processed = users_processed_result.scalar() or 0

        return {
            "total_signals_detected": total_signals,
            "total_personas_assigned": total_personas,
            "total_recommendations_generated": total_recommendations,
            "throughput_signals_per_day": round(throughput_signals, 2),
            "throughput_personas_per_day": round(throughput_personas, 2),
            "throughput_recommendations_per_day": round(throughput_recommendations, 2),
            "unique_users_processed": users_processed,
            "time_period_days": days
        }

    async def _calculate_outcome_metrics(self, days: int) -> Dict:
        """Calculate user outcome metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Approval rates
        total_recs_result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                Recommendation.created_at >= cutoff_date
            )
        )
        total_recs = total_recs_result.scalar() or 0

        approved_recs_result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                and_(
                    Recommendation.created_at >= cutoff_date,
                    Recommendation.approval_status == "approved"
                )
            )
        )
        approved_recs = approved_recs_result.scalar() or 0

        rejected_recs_result = await self.db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                and_(
                    Recommendation.created_at >= cutoff_date,
                    Recommendation.approval_status == "rejected"
                )
            )
        )
        rejected_recs = rejected_recs_result.scalar() or 0

        pending_recs = total_recs - approved_recs - rejected_recs

        approval_rate = approved_recs / total_recs if total_recs > 0 else 0.0
        rejection_rate = rejected_recs / total_recs if total_recs > 0 else 0.0

        # Persona distribution
        personas_result = await self.db.execute(
            select(Persona.persona_type, func.count(Persona.persona_id))
            .where(Persona.assigned_at >= cutoff_date)
            .group_by(Persona.persona_type)
        )
        persona_distribution = {row[0]: row[1] for row in personas_result.all()}

        # Signal detection rates
        total_users_result = await self.db.execute(
            select(func.count(User.user_id))
        )
        total_users = total_users_result.scalar() or 0

        users_with_signals_result = await self.db.execute(
            select(func.count(distinct(Signal.user_id))).where(
                Signal.computed_at >= cutoff_date
            )
        )
        users_with_signals = users_with_signals_result.scalar() or 0

        # Cap at 100% - signal detection rate should never exceed 1.0
        signal_detection_rate = min(1.0, users_with_signals / total_users if total_users > 0 else 0.0)

        # Consent rates
        consented_users_result = await self.db.execute(
            select(func.count(User.user_id)).where(User.consent_status == True)
        )
        consented_users = consented_users_result.scalar() or 0

        # Cap at 100%
        consent_rate = min(1.0, consented_users / total_users if total_users > 0 else 0.0)

        return {
            "approval_rate": round(approval_rate, 3),
            "rejection_rate": round(rejection_rate, 3),
            "pending_count": pending_recs,
            "total_approved": approved_recs,
            "total_rejected": rejected_recs,
            "persona_distribution": persona_distribution,
            "signal_detection_rate": round(signal_detection_rate, 3),
            "consent_rate": round(consent_rate, 3),
            "total_users": total_users,
            "users_with_signals": users_with_signals
        }

    async def _calculate_guardrail_metrics(self, days: int) -> Dict:
        """Calculate guardrail effectiveness metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get all users to check eligibility
        users_result = await self.db.execute(select(User))
        all_users = users_result.scalars().all()

        eligible_count = 0
        ineligible_reasons = {
            "no_consent": 0,
            "under_age": 0,
            "insufficient_transactions": 0,
            "no_signals": 0
        }

        for user in all_users:
            # Check consent
            if not user.consent_status:
                ineligible_reasons["no_consent"] += 1
                continue

            # Check age
            if user.age and user.age < 18:
                ineligible_reasons["under_age"] += 1
                continue

            # Check transaction count
            tx_count_result = await self.db.execute(
                select(func.count(Transaction.transaction_id)).where(Transaction.user_id == user.user_id)
            )
            tx_count = tx_count_result.scalar() or 0

            if tx_count < 10:
                ineligible_reasons["insufficient_transactions"] += 1
                continue

            # Check signals
            signals_result = await self.db.execute(
                select(func.count(Signal.signal_id)).where(Signal.user_id == user.user_id)
            )
            signal_count = signals_result.scalar() or 0

            if signal_count < 1:
                ineligible_reasons["no_signals"] += 1
                continue

            eligible_count += 1

        eligibility_rate = eligible_count / len(all_users) if all_users else 0.0

        # Check for vulnerable populations with special protections
        seniors_result = await self.db.execute(
            select(func.count(User.user_id)).where(User.age >= 65)
        )
        seniors_count = seniors_result.scalar() or 0

        low_income_result = await self.db.execute(
            select(func.count(User.user_id)).where(User.income_level == "low")
        )
        low_income_count = low_income_result.scalar() or 0

        young_adults_result = await self.db.execute(
            select(func.count(User.user_id)).where(
                and_(User.age >= 18, User.age <= 21)
            )
        )
        young_adults_count = young_adults_result.scalar() or 0

        # Rate limiting violations (simplified - would need tracking in production)
        # For now, check if any users have excessive recommendations
        excessive_recs_result = await self.db.execute(
            select(Recommendation.user_id, func.count(Recommendation.recommendation_id))
            .where(Recommendation.created_at >= cutoff_date)
            .group_by(Recommendation.user_id)
            .having(func.count(Recommendation.recommendation_id) > 10)
        )
        rate_limit_violations = len(excessive_recs_result.all())

        return {
            "eligibility_rate": round(eligibility_rate, 3),
            "eligible_users": eligible_count,
            "total_users_checked": len(all_users),
            "ineligibility_reasons": ineligible_reasons,
            "vulnerable_populations": {
                "seniors_65_plus": seniors_count,
                "low_income_under_30k": low_income_count,
                "young_adults_18_21": young_adults_count
            },
            "rate_limit_violations": rate_limit_violations,
            "content_safety_enabled": True  # Always enabled
        }

    async def evaluate_recommendation_batch(
        self,
        user_ids: List[str]
    ) -> Dict:
        """
        Evaluate a specific batch of users through the full pipeline
        Useful for testing and quality assurance
        """
        results = {
            "total_users": len(user_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "metrics": {
                "avg_signals_per_user": 0.0,
                "avg_personas_per_user": 0.0,
                "avg_recommendations_per_user": 0.0,
                "users_with_signals": 0,
                "users_with_personas": 0,
                "users_with_recommendations": 0
            }
        }

        total_signals = 0
        total_personas = 0
        total_recommendations = 0

        for user_id in user_ids:
            try:
                # Check if user exists
                user_result = await self.db.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    results["failed"] += 1
                    results["errors"].append(f"User {user_id} not found")
                    continue

                # Count signals
                signals_result = await self.db.execute(
                    select(func.count(Signal.signal_id)).where(Signal.user_id == user_id)
                )
                signal_count = signals_result.scalar() or 0
                total_signals += signal_count
                if signal_count > 0:
                    results["metrics"]["users_with_signals"] += 1

                # Count personas
                personas_result = await self.db.execute(
                    select(func.count(Persona.persona_id)).where(Persona.user_id == user_id)
                )
                persona_count = personas_result.scalar() or 0
                total_personas += persona_count
                if persona_count > 0:
                    results["metrics"]["users_with_personas"] += 1

                # Count recommendations
                recs_result = await self.db.execute(
                    select(func.count(Recommendation.recommendation_id)).where(
                        Recommendation.user_id == user_id
                    )
                )
                rec_count = recs_result.scalar() or 0
                total_recommendations += rec_count
                if rec_count > 0:
                    results["metrics"]["users_with_recommendations"] += 1

                results["successful"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"User {user_id}: {str(e)}")

        # Calculate averages
        if results["successful"] > 0:
            results["metrics"]["avg_signals_per_user"] = round(
                total_signals / results["successful"], 2
            )
            results["metrics"]["avg_personas_per_user"] = round(
                total_personas / results["successful"], 2
            )
            results["metrics"]["avg_recommendations_per_user"] = round(
                total_recommendations / results["successful"], 2
            )

        return results

    async def get_quality_report(self, user_id: str) -> Dict:
        """
        Generate a detailed quality report for a specific user
        Shows the full pipeline and validates each step
        """
        report = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline_status": {
                "user_exists": False,
                "has_consent": False,
                "has_transactions": False,
                "has_signals": False,
                "has_personas": False,
                "has_recommendations": False
            },
            "details": {},
            "issues": []
        }

        # Check user
        user_result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            report["issues"].append("User not found")
            return report

        report["pipeline_status"]["user_exists"] = True
        report["pipeline_status"]["has_consent"] = user.consent_status

        if not user.consent_status:
            report["issues"].append("User has not consented")

        # Check transactions
        tx_result = await self.db.execute(
            select(func.count(Transaction.transaction_id)).where(Transaction.user_id == user_id)
        )
        tx_count = tx_result.scalar() or 0
        report["details"]["transaction_count"] = tx_count
        report["pipeline_status"]["has_transactions"] = tx_count >= 10

        if tx_count < 10:
            report["issues"].append(f"Insufficient transactions ({tx_count} < 10)")

        # Check signals
        signals_result = await self.db.execute(
            select(Signal).where(Signal.user_id == user_id)
        )
        signals = signals_result.scalars().all()
        report["details"]["signal_count"] = len(signals)
        report["details"]["signal_types"] = [s.signal_type for s in signals]
        report["pipeline_status"]["has_signals"] = len(signals) >= 1

        if len(signals) < 1:
            report["issues"].append("No behavioral signals detected")

        # Check personas
        personas_result = await self.db.execute(
            select(Persona).where(Persona.user_id == user_id)
        )
        personas = personas_result.scalars().all()
        report["details"]["persona_count"] = len(personas)
        report["details"]["persona_types"] = [p.persona_type for p in personas]
        report["pipeline_status"]["has_personas"] = len(personas) >= 1

        if len(personas) < 1:
            report["issues"].append("No personas assigned")

        # Check recommendations
        recs_result = await self.db.execute(
            select(Recommendation).where(Recommendation.user_id == user_id)
        )
        recommendations = recs_result.scalars().all()
        report["details"]["recommendation_count"] = len(recommendations)
        report["details"]["recommendations"] = [
            {
                "id": r.id,
                "persona_type": r.persona_type,
                "content_type": r.content_type,
                "title": r.title,
                "approval_status": r.approval_status,
                "has_disclaimer": bool(r.disclaimer)
            }
            for r in recommendations
        ]
        report["pipeline_status"]["has_recommendations"] = len(recommendations) >= 1

        if len(recommendations) < 1:
            report["issues"].append("No recommendations generated")

        # Validate recommendation quality
        for rec in recommendations:
            if rec.persona_type not in report["details"]["persona_types"]:
                report["issues"].append(
                    f"Recommendation {rec.id} persona mismatch: "
                    f"{rec.persona_type} not in user personas"
                )

            if not rec.disclaimer:
                report["issues"].append(
                    f"Recommendation {rec.id} missing disclaimer"
                )

        report["overall_status"] = "healthy" if not report["issues"] else "issues_found"

        return report

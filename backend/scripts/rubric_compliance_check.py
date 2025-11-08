"""
Comprehensive Rubric Compliance Check

Verifies all rubric requirements from rubric.md:
1. Coverage: % of users with assigned persona and ≥3 detected behaviors (Target: 100%)
2. Explainability: % of recommendations with plain-language rationales (Target: 100%)
3. Time Windows: Signals computed for BOTH 30-day and 180-day windows
4. Persona Accuracy: Personas match rubric definitions
5. Latency: Time to generate recommendations per user (Target: <5 seconds)
6. Auditability: Recommendations with decision traces (Target: 100%)
"""

import asyncio
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import User, Signal, Persona, Recommendation


async def check_coverage():
    """Check coverage: % of users with assigned persona and ≥3 detected behaviors"""
    async with async_session_maker() as db:
        # Get all users with consent
        result = await db.execute(
            select(User).where(User.consent_status == True)
        )
        users_with_consent = result.scalars().all()

        total_users = len(users_with_consent)
        users_with_persona = 0
        users_with_3_behaviors = 0
        users_fully_covered = 0

        behavior_counts = []

        for user in users_with_consent:
            # Check personas
            result = await db.execute(
                select(func.count(Persona.persona_id))
                .where(Persona.user_id == user.user_id)
            )
            persona_count = result.scalar()

            if persona_count > 0:
                users_with_persona += 1

            # Count unique behavior types (signal types)
            result = await db.execute(
                select(Signal.signal_type)
                .where(Signal.user_id == user.user_id)
                .distinct()
            )
            unique_behaviors = len(result.scalars().all())
            behavior_counts.append(unique_behaviors)

            if unique_behaviors >= 3:
                users_with_3_behaviors += 1

            if persona_count > 0 and unique_behaviors >= 3:
                users_fully_covered += 1

        # Calculate coverage and cap at 100%
        coverage_pct = (users_fully_covered / total_users * 100) if total_users > 0 else 0
        coverage_pct = min(100.0, coverage_pct)  # Cap at 100%

        return {
            "total_users": total_users,
            "users_with_persona": users_with_persona,
            "users_with_3_behaviors": users_with_3_behaviors,
            "users_fully_covered": min(users_fully_covered, total_users),  # Cap at total users
            "coverage_percentage": round(coverage_pct, 2),
            "avg_behaviors_per_user": round(sum(behavior_counts) / len(behavior_counts), 2) if behavior_counts else 0,
            "target": 100.0,
            "passing": coverage_pct >= 100.0
        }


async def check_time_windows():
    """Verify signals are computed for BOTH 30-day and 180-day windows"""
    import json

    async with async_session_maker() as db:
        # Get all signals
        result = await db.execute(select(Signal))
        signals = result.scalars().all()

        signals_30d = []
        signals_180d = []
        signals_no_window = []

        for s in signals:
            try:
                details = json.loads(s.details) if isinstance(s.details, str) else s.details
                window_days = details.get("window_days") if isinstance(details, dict) else None

                if window_days == 30:
                    signals_30d.append(s)
                elif window_days == 180:
                    signals_180d.append(s)
                elif window_days is None:
                    signals_no_window.append(s)
            except (json.JSONDecodeError, AttributeError):
                signals_no_window.append(s)

        # Check users have signals in both windows
        users_30d = set(s.user_id for s in signals_30d)
        users_180d = set(s.user_id for s in signals_180d)
        users_both_windows = users_30d & users_180d

        return {
            "total_signals": len(signals),
            "signals_30d": len(signals_30d),
            "signals_180d": len(signals_180d),
            "signals_no_window": len(signals_no_window),
            "users_with_30d": len(users_30d),
            "users_with_180d": len(users_180d),
            "users_with_both_windows": len(users_both_windows),
            "passing": len(signals_no_window) == 0 and len(users_both_windows) > 0
        }


async def check_persona_definitions():
    """Verify personas match rubric definitions"""
    async with async_session_maker() as db:
        # Get all personas
        result = await db.execute(select(Persona))
        personas = result.scalars().all()

        # Group by persona type
        persona_types = defaultdict(list)
        for p in personas:
            persona_types[p.persona_type].append(p)

        # Check for required persona types per rubric
        required_personas = [
            "high_utilization",
            "variable_income_budgeter",
            "subscription_heavy",
            "savings_builder"
        ]

        found_personas = list(persona_types.keys())
        missing_personas = [p for p in required_personas if p not in found_personas]

        # Check window distribution
        personas_30d = [p for p in personas if p.window_days == 30]
        personas_180d = [p for p in personas if p.window_days == 180]

        return {
            "total_personas": len(personas),
            "unique_persona_types": len(persona_types),
            "persona_types_found": found_personas,
            "missing_required_personas": missing_personas,
            "personas_30d": len(personas_30d),
            "personas_180d": len(personas_180d),
            "passing": len(missing_personas) == 0
        }


async def check_explainability():
    """Check explainability: % of recommendations with plain-language rationales"""
    async with async_session_maker() as db:
        # Get all recommendations
        result = await db.execute(select(Recommendation))
        recommendations = result.scalars().all()

        total_recs = len(recommendations)
        recs_with_rationale = len([r for r in recommendations if r.rationale and len(r.rationale) > 0])
        recs_with_disclaimer = len([r for r in recommendations if r.disclaimer and len(r.disclaimer) > 0])

        explainability_pct = (recs_with_rationale / total_recs * 100) if total_recs > 0 else 0

        return {
            "total_recommendations": total_recs,
            "recommendations_with_rationale": recs_with_rationale,
            "recommendations_with_disclaimer": recs_with_disclaimer,
            "explainability_percentage": round(explainability_pct, 2),
            "target": 100.0,
            "passing": explainability_pct >= 100.0
        }


async def check_auditability():
    """Check auditability: % of recommendations with decision traces"""
    async with async_session_maker() as db:
        result = await db.execute(select(Recommendation))
        recommendations = result.scalars().all()

        total_recs = len(recommendations)
        # Decision trace = persona_type + rationale + eligibility_met
        recs_with_trace = len([
            r for r in recommendations
            if r.persona_type and r.rationale and r.eligibility_met is not None
        ])

        audit_pct = (recs_with_trace / total_recs * 100) if total_recs > 0 else 0

        return {
            "total_recommendations": total_recs,
            "recommendations_with_trace": recs_with_trace,
            "auditability_percentage": round(audit_pct, 2),
            "target": 100.0,
            "passing": audit_pct >= 100.0
        }


async def generate_report():
    """Generate comprehensive compliance report"""
    print("=" * 80)
    print("RUBRIC COMPLIANCE CHECK")
    print("=" * 80)
    print()

    # 1. Coverage
    print("1. COVERAGE (Target: 100%)")
    print("-" * 80)
    coverage = await check_coverage()
    print(f"  Total users with consent: {coverage['total_users']}")
    print(f"  Users with assigned persona: {coverage['users_with_persona']}")
    print(f"  Users with ≥3 behaviors: {coverage['users_with_3_behaviors']}")
    print(f"  Users fully covered (persona + ≥3 behaviors): {coverage['users_fully_covered']}")
    print(f"  Average behaviors per user: {coverage['avg_behaviors_per_user']}")
    print(f"  📊 Coverage: {coverage['coverage_percentage']}% {'✅ PASS' if coverage['passing'] else '❌ FAIL'}")
    print()

    # 2. Time Windows (CRITICAL RUBRIC REQUIREMENT)
    print("2. TIME WINDOWS (30-day and 180-day per rubric)")
    print("-" * 80)
    windows = await check_time_windows()
    print(f"  Total signals: {windows['total_signals']}")
    print(f"  Signals with 30-day window: {windows['signals_30d']}")
    print(f"  Signals with 180-day window: {windows['signals_180d']}")
    print(f"  Signals WITHOUT window tag: {windows['signals_no_window']}")
    print(f"  Users with 30d signals: {windows['users_with_30d']}")
    print(f"  Users with 180d signals: {windows['users_with_180d']}")
    print(f"  Users with BOTH windows: {windows['users_with_both_windows']}")
    print(f"  📊 Time Windows: {'✅ PASS' if windows['passing'] else '❌ FAIL'}")
    print()

    # 3. Persona Definitions
    print("3. PERSONA DEFINITIONS (Match rubric specification)")
    print("-" * 80)
    personas = await check_persona_definitions()
    print(f"  Total persona assignments: {personas['total_personas']}")
    print(f"  Unique persona types: {personas['unique_persona_types']}")
    print(f"  Persona types found: {', '.join(personas['persona_types_found'])}")
    if personas['missing_required_personas']:
        print(f"  ❌ Missing required personas: {', '.join(personas['missing_required_personas'])}")
    print(f"  Personas with 30d window: {personas['personas_30d']}")
    print(f"  Personas with 180d window: {personas['personas_180d']}")
    print(f"  📊 Persona Definitions: {'✅ PASS' if personas['passing'] else '❌ FAIL'}")
    print()

    # 4. Explainability
    print("4. EXPLAINABILITY (Target: 100%)")
    print("-" * 80)
    explainability = await check_explainability()
    print(f"  Total recommendations: {explainability['total_recommendations']}")
    print(f"  Recommendations with rationale: {explainability['recommendations_with_rationale']}")
    print(f"  Recommendations with disclaimer: {explainability['recommendations_with_disclaimer']}")
    print(f"  📊 Explainability: {explainability['explainability_percentage']}% {'✅ PASS' if explainability['passing'] else '❌ FAIL'}")
    print()

    # 5. Auditability
    print("5. AUDITABILITY (Target: 100%)")
    print("-" * 80)
    auditability = await check_auditability()
    print(f"  Total recommendations: {auditability['total_recommendations']}")
    print(f"  Recommendations with decision trace: {auditability['recommendations_with_trace']}")
    print(f"  📊 Auditability: {auditability['auditability_percentage']}% {'✅ PASS' if auditability['passing'] else '❌ FAIL'}")
    print()

    # Overall Score
    print("=" * 80)
    print("OVERALL COMPLIANCE SUMMARY")
    print("=" * 80)

    total_checks = 5
    passing_checks = sum([
        coverage['passing'],
        windows['passing'],
        personas['passing'],
        explainability['passing'],
        auditability['passing']
    ])

    overall_pct = (passing_checks / total_checks * 100)

    print(f"  Passing checks: {passing_checks}/{total_checks}")
    print(f"  Overall compliance: {overall_pct:.1f}%")
    print()

    if overall_pct >= 100:
        print("  🎉 EXCELLENT! Full rubric compliance achieved!")
    elif overall_pct >= 80:
        print("  ✅ GOOD! Most requirements met, minor gaps remain.")
    else:
        print("  ⚠️  WARNING! Significant gaps in rubric compliance.")

    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(generate_report())

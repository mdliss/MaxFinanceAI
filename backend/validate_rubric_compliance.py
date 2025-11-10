#!/usr/bin/env python3
"""
Validate that the generated dataset meets all rubric requirements.
"""

import asyncio
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from app.models import (
    User, BehavioralSignal, PersonaAssignment,
    Recommendation, Transaction, Account
)
from sqlalchemy import select, func


async def validate_rubric():
    """Run all validation checks."""

    print("=" * 80)
    print("RUBRIC COMPLIANCE VALIDATION")
    print("=" * 80)
    print()

    results = {}
    async with async_session_maker() as db:

        # 1. User Count (50-100 users)
        print("📊 Checking User Count...")
        result = await db.execute(select(func.count(User.user_id)))
        user_count = result.scalar()
        results['user_count'] = user_count
        status = "✅" if 50 <= user_count <= 100 else "❌"
        print(f"  {status} Total users: {user_count} (target: 50-100)")
        print()

        # 2. Consent (all users should have consent)
        print("📊 Checking Consent Status...")
        result = await db.execute(select(func.count(User.user_id)).where(User.consent_status == True))
        consented_count = result.scalar()
        consent_percentage = (consented_count / user_count * 100) if user_count > 0 else 0
        results['consent_percentage'] = consent_percentage
        status = "✅" if consent_percentage == 100 else "❌"
        print(f"  {status} Users with consent: {consented_count}/{user_count} ({consent_percentage:.1f}%)")
        print()

        # 3. Coverage: Users with assigned persona + ≥3 behaviors
        print("📊 Checking Coverage (Persona + ≥3 Behaviors)...")
        result = await db.execute(select(User))
        users = result.scalars().all()

        users_with_coverage = 0
        for user in users:
            # Check persona
            result = await db.execute(
                select(PersonaAssignment).where(PersonaAssignment.user_id == user.user_id)
            )
            personas = result.scalars().all()

            # Check signals
            result = await db.execute(
                select(BehavioralSignal).where(BehavioralSignal.user_id == user.user_id)
            )
            signals = result.scalars().all()

            if len(personas) > 0 and len(signals) >= 3:
                users_with_coverage += 1

        coverage_percentage = (users_with_coverage / user_count * 100) if user_count > 0 else 0
        results['coverage_percentage'] = coverage_percentage
        status = "✅" if coverage_percentage == 100 else "❌"
        print(f"  {status} Users with persona + ≥3 behaviors: {users_with_coverage}/{user_count} ({coverage_percentage:.1f}%)")
        print()

        # 4. Explainability: Recommendations with rationales
        print("📊 Checking Explainability (Recommendations with Rationales)...")
        result = await db.execute(select(Recommendation))
        recommendations = result.scalars().all()

        recs_with_rationale = sum(1 for rec in recommendations if rec.rationale and len(rec.rationale) > 10)
        explainability_percentage = (recs_with_rationale / len(recommendations) * 100) if len(recommendations) > 0 else 0
        results['explainability_percentage'] = explainability_percentage
        status = "✅" if explainability_percentage == 100 else "❌"
        print(f"  {status} Recommendations with rationales: {recs_with_rationale}/{len(recommendations)} ({explainability_percentage:.1f}%)")
        print()

        # 5. Persona Distribution
        print("📊 Checking Persona Distribution...")
        result = await db.execute(select(PersonaAssignment))
        persona_assignments = result.scalars().all()

        persona_counts = Counter(p.persona_type for p in persona_assignments)
        print(f"  Total persona assignments: {len(persona_assignments)}")
        for persona_type, count in sorted(persona_counts.items(), key=lambda x: -x[1]):
            print(f"    - {persona_type}: {count}")

        # Check if all 5 personas are represented
        unique_personas = len(persona_counts)
        status = "✅" if unique_personas >= 5 else "❌"
        print(f"  {status} Unique personas: {unique_personas} (target: 5+)")
        print()

        # 6. Signal Types
        print("📊 Checking Signal Types...")
        result = await db.execute(select(BehavioralSignal))
        signals = result.scalars().all()

        signal_types = Counter(s.signal_type for s in signals)
        print(f"  Total signals: {len(signals)}")
        for signal_type, count in sorted(signal_types.items(), key=lambda x: -x[1]):
            print(f"    - {signal_type}: {count}")

        required_signal_types = [
            "credit_utilization", "savings_growth", "recurring_merchants",
            "income_stability", "subscription_spend"
        ]
        detected_types = set(signal_types.keys())
        missing_types = [t for t in required_signal_types if t not in detected_types]

        status = "✅" if len(missing_types) == 0 else "⚠️"
        print(f"  {status} Required signal types detected: {len(detected_types)}/{len(required_signal_types)}")
        if missing_types:
            print(f"    Missing: {', '.join(missing_types)}")
        print()

        # 7. Transaction Data Quality
        print("📊 Checking Transaction Data Quality...")
        result = await db.execute(select(Transaction))
        transactions = result.scalars().all()

        # Check diversity
        merchants = set(t.merchant_name for t in transactions if t.merchant_name)
        categories = set(t.category_primary for t in transactions if t.category_primary)

        print(f"  Total transactions: {len(transactions)}")
        print(f"  Unique merchants: {len(merchants)}")
        print(f"  Unique categories: {len(categories)}")
        print(f"  Avg transactions per user: {len(transactions) / user_count:.1f}")

        status = "✅" if len(transactions) / user_count > 100 else "⚠️"
        print(f"  {status} Transaction density (target: >100 per user)")
        print()

        # 8. Account Types
        print("📊 Checking Account Diversity...")
        result = await db.execute(select(Account))
        accounts = result.scalars().all()

        account_types = Counter(f"{a.type}/{a.subtype}" for a in accounts)
        print(f"  Total accounts: {len(accounts)}")
        for account_type, count in sorted(account_types.items(), key=lambda x: -x[1]):
            print(f"    - {account_type}: {count}")

        required_account_types = ["depository/checking", "depository/savings", "credit/credit card"]
        detected_account_types = set(account_types.keys())
        missing_account_types = [t for t in required_account_types if t not in detected_account_types]

        status = "✅" if len(missing_account_types) == 0 else "❌"
        print(f"  {status} Required account types present")
        print()

        # 9. Recommendation Types
        print("📊 Checking Recommendation Diversity...")
        recommendation_types = Counter(r.recommendation_type for r in recommendations)
        print(f"  Total recommendations: {len(recommendations)}")
        for rec_type, count in sorted(recommendation_types.items(), key=lambda x: -x[1]):
            print(f"    - {rec_type}: {count}")
        print()

        # 10. Data Freshness
        print("📊 Checking Data Freshness...")
        from datetime import datetime, timedelta

        recent_transactions = [t for t in transactions if t.date >= (datetime.now() - timedelta(days=30)).date()]
        recent_percentage = (len(recent_transactions) / len(transactions) * 100) if len(transactions) > 0 else 0

        status = "✅" if recent_percentage > 15 else "⚠️"
        print(f"  {status} Recent transactions (last 30 days): {len(recent_transactions)}/{len(transactions)} ({recent_percentage:.1f}%)")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    checks = {
        "User Count (50-100)": 50 <= results['user_count'] <= 100,
        "Consent (100%)": results['consent_percentage'] == 100,
        "Coverage (100%)": results['coverage_percentage'] == 100,
        "Explainability (100%)": results['explainability_percentage'] == 100,
    }

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    for check_name, passed_check in checks.items():
        status = "✅" if passed_check else "❌"
        print(f"{status} {check_name}")

    print()
    print(f"Rubric Compliance: {passed}/{total} critical checks passed")

    if passed == total:
        print("✅ Dataset meets all rubric requirements!")
    else:
        print("⚠️  Some requirements not met. Review above for details.")

    print()


if __name__ == "__main__":
    asyncio.run(validate_rubric())

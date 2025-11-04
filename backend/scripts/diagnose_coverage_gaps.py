"""
Diagnose coverage gaps to achieve 100% rubric compliance.

Identifies:
1. Users without personas
2. Users with < 3 behavior types
3. Recommendations for data fixes
"""

import asyncio
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import User, Signal, Persona

async def diagnose():
    """Identify coverage gaps and recommend fixes."""
    async with async_session_maker() as db:
        print("=" * 80)
        print("COVERAGE GAP DIAGNOSIS")
        print("=" * 80)

        # Get all consenting users
        result = await db.execute(
            select(User).where(User.consent_status == True)
        )
        users = result.scalars().all()

        print(f"\nTotal users with consent: {len(users)}")

        # Analyze each user
        users_without_persona = []
        users_with_insufficient_behaviors = []

        for user in users:
            # Check persona
            persona_count = await db.execute(
                select(func.count(Persona.persona_id)).where(Persona.user_id == user.user_id)
            )
            has_persona = persona_count.scalar() > 0

            # Check behavior count
            behavior_result = await db.execute(
                select(Signal.signal_type).where(Signal.user_id == user.user_id).distinct()
            )
            behavior_types = [row[0] for row in behavior_result]
            behavior_count = len(behavior_types)

            if not has_persona:
                users_without_persona.append({
                    'user_id': user.user_id,
                    'name': user.name,
                    'behaviors': behavior_count,
                    'behavior_types': behavior_types
                })

            if behavior_count < 3:
                users_with_insufficient_behaviors.append({
                    'user_id': user.user_id,
                    'name': user.name,
                    'has_persona': has_persona,
                    'behaviors': behavior_count,
                    'behavior_types': behavior_types
                })

        print(f"\n{'=' * 80}")
        print(f"USERS WITHOUT PERSONA: {len(users_without_persona)}")
        print(f"{'=' * 80}")

        if users_without_persona:
            print("\nSample users without persona (first 10):")
            for user_info in users_without_persona[:10]:
                print(f"\n  {user_info['name']} ({user_info['user_id']})")
                print(f"    Behaviors: {user_info['behaviors']}")
                print(f"    Types: {user_info['behavior_types']}")

        print(f"\n{'=' * 80}")
        print(f"USERS WITH < 3 BEHAVIORS: {len(users_with_insufficient_behaviors)}")
        print(f"{'=' * 80}")

        if users_with_insufficient_behaviors:
            # Group by behavior count
            by_count = defaultdict(list)
            for user_info in users_with_insufficient_behaviors:
                by_count[user_info['behaviors']].append(user_info)

            for count in sorted(by_count.keys()):
                print(f"\n  Users with {count} behavior type(s): {len(by_count[count])}")
                if count == 0:
                    print(f"    Sample users (first 5):")
                    for user_info in by_count[count][:5]:
                        print(f"      - {user_info['name']} ({user_info['user_id']})")

        # Analyze signal distribution
        print(f"\n{'=' * 80}")
        print("SIGNAL TYPE DISTRIBUTION")
        print(f"{'=' * 80}")

        signal_counts = await db.execute(
            select(Signal.signal_type, func.count(Signal.signal_id))
            .group_by(Signal.signal_type)
        )

        for signal_type, count in signal_counts:
            print(f"  {signal_type}: {count} signals")

        # Recommendations
        print(f"\n{'=' * 80}")
        print("RECOMMENDATIONS")
        print(f"{'=' * 80}")

        print("\n1. Users without personas:")
        print(f"   - Total: {len(users_without_persona)}")
        print(f"   - Action: Regenerate personas (may need more data to trigger persona logic)")

        print("\n2. Users with insufficient behaviors:")
        print(f"   - Total: {len(users_with_insufficient_behaviors)}")
        print(f"   - Action: Enrich transaction data to generate more signal types")

        # Specific recommendations based on missing signal types
        all_behavior_types = set()
        for user_info in users_with_insufficient_behaviors:
            all_behavior_types.update(user_info['behavior_types'])

        possible_signals = {'subscription_detected', 'savings_growth', 'credit_utilization', 'income_stability'}

        print("\n3. Signal type coverage:")
        for signal_type in possible_signals:
            if signal_type not in all_behavior_types:
                print(f"   - Missing: {signal_type}")

        return {
            'users_without_persona': len(users_without_persona),
            'users_with_insufficient_behaviors': len(users_with_insufficient_behaviors),
            'total_users': len(users)
        }

if __name__ == "__main__":
    result = asyncio.run(diagnose())
    print(f"\n{'=' * 80}")
    print(f"Coverage: {((result['total_users'] - max(result['users_without_persona'], result['users_with_insufficient_behaviors'])) / result['total_users'] * 100):.1f}%")
    print(f"{'=' * 80}")

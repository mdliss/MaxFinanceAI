#!/usr/bin/env python3
"""
Process all users with consent:
1. Detect signals from transactions
2. Assign personas based on signals
3. Users are now ready for recommendation generation
"""

import asyncio
import sys
from sqlalchemy import select
from app.database import async_session_maker
from app.models import User
from app.services.signal_detector import SignalDetector
from app.services.persona_assigner import PersonaAssigner

async def process_all_users():
    """Process all users who have granted consent"""
    print("\n" + "=" * 70)
    print("🚀 PROCESSING ALL USERS WITH CONSENT")
    print("=" * 70)

    async with async_session_maker() as db:
        try:
            # Get all users with consent
            result = await db.execute(
                select(User).where(User.consent_status == True)
            )
            users = result.scalars().all()

            if not users:
                print("\n❌ No users with consent found!")
                return

            print(f"\n📊 Found {len(users)} users with consent")
            print("-" * 70)

            signal_detector = SignalDetector(db)
            persona_assigner = PersonaAssigner(db, window_days=180)

            success_count = 0
            failed_count = 0

            for i, user in enumerate(users, 1):
                print(f"\n[{i}/{len(users)}] Processing: {user.name} ({user.user_id})")

                try:
                    # Step 1: Detect signals
                    print(f"  ├─ Detecting signals...", end=" ")
                    signals = await signal_detector.detect_all_signals(user.user_id)
                    await signal_detector.save_signals(signals)
                    print(f"✅ {len(signals)} signals detected")

                    if signals:
                        for signal in signals:
                            print(f"  │   • {signal.signal_type}: {signal.value:.2f}")

                    # Step 2: Assign personas
                    print(f"  ├─ Assigning personas...", end=" ")
                    personas = await persona_assigner.assign_personas(user.user_id)
                    await persona_assigner.save_personas(user.user_id, personas)
                    print(f"✅ {len(personas)} personas assigned")

                    if personas:
                        for persona in personas:
                            print(f"  │   • {persona.persona_type} (priority: {persona.priority_rank})")

                    print(f"  └─ ✅ User processing complete")
                    success_count += 1

                except Exception as e:
                    print(f"  └─ ❌ Error: {e}")
                    failed_count += 1
                    continue

            # Summary
            print("\n" + "=" * 70)
            print("✅ PROCESSING COMPLETE!")
            print("-" * 70)
            print(f"  Total Users Processed: {len(users)}")
            print(f"  ✅ Successful: {success_count}")
            print(f"  ❌ Failed: {failed_count}")
            print("=" * 70)

            print("\n📝 Next Steps:")
            print("  1. Visit http://localhost:3001/operator")
            print("  2. Search for any user to see their profile")
            print("  3. Recommendations will be generated on-demand")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\n❌ Fatal Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(process_all_users())

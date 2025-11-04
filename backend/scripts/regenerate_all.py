"""
Regenerate all signals and personas for all consenting users.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.database import async_session_maker
from app.models import User
from app.services.signal_detector import SignalDetector
from app.services.persona_assigner import PersonaAssigner

async def regenerate_all():
    """Regenerate signals and personas for all users."""
    async with async_session_maker() as db:
        print("=" * 80)
        print("REGENERATING SIGNALS AND PERSONAS")
        print("=" * 80)

        # Get all consenting users
        result = await db.execute(select(User).where(User.consent_status == True))
        users = result.scalars().all()

        print(f"\nProcessing {len(users)} users...")

        # Step 1: Regenerate signals for both 30d and 180d windows
        print("\n[1/3] Detecting signals...")
        detector_30 = SignalDetector(db)
        detector_180 = SignalDetector(db)

        signals_30d = 0
        signals_180d = 0

        for i, user in enumerate(users, 1):
            if i % 20 == 0:
                print(f"  Processed {i}/{len(users)} users...")

            # Detect signals for both windows
            signals_30 = await detector_30.detect_all_signals(user.user_id, window_days=30)
            signals_30d += len(signals_30)

            signals_180 = await detector_180.detect_all_signals(user.user_id, window_days=180)
            signals_180d += len(signals_180)

            # Combine and save all signals at once (to avoid deletion)
            all_signals = signals_30 + signals_180
            await detector_180.save_signals(all_signals)

        await db.commit()
        print(f"  ✅ Signals detected:")
        print(f"     - 30-day window: {signals_30d} signals")
        print(f"     - 180-day window: {signals_180d} signals")

        # Step 2: Regenerate personas
        print("\n[2/3] Assigning personas...")
        assigner = PersonaAssigner(db, window_days=180)

        personas_assigned = 0

        for i, user in enumerate(users, 1):
            if i % 20 == 0:
                print(f"  Processed {i}/{len(users)} users...")

            personas = await assigner.assign_personas(user.user_id)
            if personas:
                # Save personas to database
                await assigner.save_personas(user.user_id, personas)
                personas_assigned += 1

        await db.commit()
        print(f"  ✅ Personas assigned to {personas_assigned} users")

        # Step 3: Summary
        print("\n[3/3] Summary:")
        print(f"  - Total users: {len(users)}")
        print(f"  - Users with personas: {personas_assigned}")
        print(f"  - Coverage: {personas_assigned / len(users) * 100:.1f}%")

        return {
            'total_users': len(users),
            'personas_assigned': personas_assigned,
            'signals_30d': signals_30d,
            'signals_180d': signals_180d
        }

if __name__ == "__main__":
    result = asyncio.run(regenerate_all())
    print(f"\n✅ Regeneration complete!")

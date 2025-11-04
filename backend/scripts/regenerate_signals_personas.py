"""
Regenerate signals and personas for all users with both 30-day and 180-day time windows.

This script:
1. Detects signals for both 30-day and 180-day windows
2. Assigns personas for both time windows
3. Updates the database with new data

Per rubric requirement: Compute signals per time window (30-day and 180-day)
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.database import async_session_maker
from app.models import User
from app.services.signal_detector import SignalDetector
from app.services.persona_assigner import PersonaAssigner


async def regenerate_all():
    """Regenerate signals and personas for all consenting users"""
    async with async_session_maker() as db:
        # Get all users with consent
        result = await db.execute(
            select(User).where(User.consent_status == True)
        )
        users = result.scalars().all()

        print(f"Found {len(users)} users with consent")
        print("=" * 60)

        for idx, user in enumerate(users, 1):
            print(f"\n[{idx}/{len(users)}] Processing user: {user.name} ({user.user_id})")

            try:
                # Detect signals for BOTH time windows
                detector = SignalDetector(db)

                print("  - Detecting 30-day signals...")
                signals_30d = await detector.detect_all_signals(user.user_id, window_days=30)

                print("  - Detecting 180-day signals...")
                signals_180d = await detector.detect_all_signals(user.user_id, window_days=180)

                all_signals = signals_30d + signals_180d

                print(f"  - Detected {len(signals_30d)} signals (30d) + {len(signals_180d)} signals (180d)")

                # Save signals
                await detector.save_signals(all_signals)

                # Assign personas for BOTH time windows
                print("  - Assigning personas for 30-day window...")
                assigner_30d = PersonaAssigner(db, window_days=30)
                personas_30d = await assigner_30d.assign_personas(user.user_id)

                print("  - Assigning personas for 180-day window...")
                assigner_180d = PersonaAssigner(db, window_days=180)
                personas_180d = await assigner_180d.assign_personas(user.user_id)

                all_personas = personas_30d + personas_180d

                print(f"  - Assigned {len(personas_30d)} personas (30d) + {len(personas_180d)} personas (180d)")

                # Save personas
                await assigner_30d.save_personas(user.user_id, all_personas)

                # Show summary
                if personas_30d:
                    print(f"  - 30d personas: {', '.join([p.persona_type for p in personas_30d])}")
                if personas_180d:
                    print(f"  - 180d personas: {', '.join([p.persona_type for p in personas_180d])}")

                print("  ✓ Success")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

        print("\n" + "=" * 60)
        print("Regeneration complete!")


if __name__ == "__main__":
    asyncio.run(regenerate_all())

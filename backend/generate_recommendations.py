#!/usr/bin/env python3
"""
Generate recommendations for all users with personas and consent.
"""

import asyncio
import sys
from sqlalchemy import select
from app.database import async_session_maker
from app.models import User, Persona
from app.services.recommendation_engine import RecommendationEngine

async def generate_all_recommendations():
    """Generate recommendations for all users with personas"""
    print("\n" + "=" * 70)
    print("🎯 GENERATING RECOMMENDATIONS FOR ALL USERS")
    print("=" * 70)

    async with async_session_maker() as db:
        try:
            # Get all users with consent and personas
            result = await db.execute(
                select(User.user_id)
                .join(Persona, User.user_id == Persona.user_id)
                .where(User.consent_status == True)
                .distinct()
            )
            user_ids = [row[0] for row in result.all()]

            if not user_ids:
                print("\n❌ No users with consent and personas found!")
                return

            print(f"\n📊 Found {len(user_ids)} users with personas")
            print("-" * 70)

            engine = RecommendationEngine(db)
            success_count = 0
            failed_count = 0

            for i, user_id in enumerate(user_ids, 1):
                # Get user info
                result = await db.execute(select(User).where(User.user_id == user_id))
                user = result.scalar_one_or_none()

                if not user:
                    continue

                print(f"\n[{i}/{len(user_ids)}] {user.name} ({user_id})")

                try:
                    # Generate recommendations
                    recommendations = await engine.generate_recommendations(user_id)

                    # Save recommendations
                    count = await engine.save_recommendations(user_id, recommendations)

                    print(f"  ✅ Generated {count} recommendations")
                    for rec in recommendations:
                        print(f"     • {rec.content_type}: {rec.title}")

                    success_count += 1

                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    failed_count += 1
                    continue

            # Summary
            print("\n" + "=" * 70)
            print("✅ RECOMMENDATION GENERATION COMPLETE!")
            print("-" * 70)
            print(f"  Total Users Processed: {len(user_ids)}")
            print(f"  ✅ Successful: {success_count}")
            print(f"  ❌ Failed: {failed_count}")
            print("=" * 70)

            # Show sample recommendations
            print("\n📝 Sample Recommendations Generated:")
            result = await db.execute(
                select(User.name, Persona.persona_type)
                .join(Persona, User.user_id == Persona.user_id)
                .where(Persona.priority_rank == 1)
                .limit(5)
            )
            for name, persona in result.all():
                print(f"  • {name}: {persona}")

            print("\n✨ Visit http://localhost:3001/operator to see recommendations!\n")

        except Exception as e:
            print(f"\n❌ Fatal Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(generate_all_recommendations())

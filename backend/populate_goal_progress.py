#!/usr/bin/env python3
"""
Populate goal progress data for demo user
"""
import asyncio
from sqlalchemy import select
from app.database import get_db
from app.models import FinancialGoal

async def populate_goal_progress():
    user_id = "demo"

    async for db in get_db():
        try:
            print("=" * 60)
            print("Populating Goal Progress Data")
            print("=" * 60)

            # Get all goals for demo user
            result = await db.execute(
                select(FinancialGoal).where(FinancialGoal.user_id == user_id)
            )
            goals = result.scalars().all()

            if not goals:
                print("No goals found for demo user")
                return

            # Update progress for each goal
            for goal in goals:
                if goal.goal_type == "emergency_fund":
                    # Emergency Fund: $15,000 target, $3,200 saved (21.3%)
                    goal.current_amount = 3200.00
                    goal.progress_percent = (3200.00 / 15000.00) * 100

                elif goal.goal_type == "vacation":
                    # Summer Vacation: $5,000 target, $1,850 saved (37%)
                    goal.current_amount = 1850.00
                    goal.progress_percent = (1850.00 / 5000.00) * 100

                elif goal.goal_type == "major_purchase":
                    # New Laptop: $2,500 target, $650 saved (26%)
                    goal.current_amount = 650.00
                    goal.progress_percent = (650.00 / 2500.00) * 100

                print(f"\n{goal.title}:")
                print(f"  Target: ${goal.target_amount:,.2f}")
                print(f"  Current: ${goal.current_amount:,.2f}")
                print(f"  Progress: {goal.progress_percent:.1f}%")
                print(f"  Remaining: ${goal.target_amount - goal.current_amount:,.2f}")

            await db.commit()

            print("\n" + "=" * 60)
            print("✅ GOAL PROGRESS DATA UPDATED!")
            print("=" * 60)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(populate_goal_progress())

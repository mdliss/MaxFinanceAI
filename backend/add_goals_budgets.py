#!/usr/bin/env python3
"""
Add goals and budgets to existing user
"""

import asyncio
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/app')

from app.database import async_session_maker
from app.models import User, FinancialGoal, Budget
from sqlalchemy import select

USER_ID = "user_05559915742f"

async def main():
    async with async_session_maker() as db:
        try:
            # Check if goals already exist
            result = await db.execute(
                select(FinancialGoal).where(FinancialGoal.user_id == USER_ID)
            )
            existing_goals = result.scalars().all()

            if not existing_goals:
                print("Creating financial goals...")
                goals = [
                    FinancialGoal(
                        user_id=USER_ID,
                        name="Emergency Fund",
                        target_amount=10000.00,
                        current_amount=6500.00,
                        deadline=(datetime.now() + timedelta(days=180)).date(),
                        category="savings",
                        status="active"
                    ),
                    FinancialGoal(
                        user_id=USER_ID,
                        name="Vacation to Hawaii",
                        target_amount=5000.00,
                        current_amount=1200.00,
                        deadline=(datetime.now() + timedelta(days=270)).date(),
                        category="savings",
                        status="active"
                    ),
                    FinancialGoal(
                        user_id=USER_ID,
                        name="Pay Off Credit Card",
                        target_amount=2500.00,
                        current_amount=1800.00,
                        deadline=(datetime.now() + timedelta(days=90)).date(),
                        category="debt_payoff",
                        status="active"
                    ),
                    FinancialGoal(
                        user_id=USER_ID,
                        name="New Laptop Fund",
                        target_amount=2000.00,
                        current_amount=450.00,
                        deadline=(datetime.now() + timedelta(days=150)).date(),
                        category="purchase",
                        status="active"
                    )
                ]

                for goal in goals:
                    db.add(goal)
                await db.commit()
                print(f"✅ Created {len(goals)} financial goals")
            else:
                print(f"✅ User already has {len(existing_goals)} goals")

            # Check if budgets already exist
            result = await db.execute(
                select(Budget).where(Budget.user_id == USER_ID)
            )
            existing_budgets = result.scalars().all()

            if not existing_budgets:
                print("Creating budgets...")
                budgets = [
                    Budget(
                        user_id=USER_ID,
                        category="groceries",
                        limit=600.00,
                        spent=485.50,
                        period="monthly",
                        start_date=datetime.now().replace(day=1).date(),
                        status="active"
                    ),
                    Budget(
                        user_id=USER_ID,
                        category="dining",
                        limit=300.00,
                        spent=340.25,
                        period="monthly",
                        start_date=datetime.now().replace(day=1).date(),
                        status="active"
                    ),
                    Budget(
                        user_id=USER_ID,
                        category="entertainment",
                        limit=150.00,
                        spent=95.00,
                        period="monthly",
                        start_date=datetime.now().replace(day=1).date(),
                        status="active"
                    ),
                    Budget(
                        user_id=USER_ID,
                        category="transportation",
                        limit=200.00,
                        spent=125.75,
                        period="monthly",
                        start_date=datetime.now().replace(day=1).date(),
                        status="active"
                    ),
                    Budget(
                        user_id=USER_ID,
                        category="utilities",
                        limit=250.00,
                        spent=210.00,
                        period="monthly",
                        start_date=datetime.now().replace(day=1).date(),
                        status="active"
                    )
                ]

                for budget in budgets:
                    db.add(budget)
                await db.commit()
                print(f"✅ Created {len(budgets)} budgets")
            else:
                print(f"✅ User already has {len(existing_budgets)} budgets")

            print("\n✅ Done! Visit http://localhost:3001/goals and http://localhost:3001/budgets")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

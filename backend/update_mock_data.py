#!/usr/bin/env python3
"""
Update goals and budgets with realistic progress
"""

import asyncio
import sys
sys.path.insert(0, '/app')

from app.database import async_session_maker
from app.models import FinancialGoal, Budget
from sqlalchemy import select, update

USER_ID = "user_05559915742f"

async def main():
    async with async_session_maker() as db:
        try:
            # Update goals with progress
            print("Updating goals with progress...")

            await db.execute(
                update(FinancialGoal)
                .where(FinancialGoal.user_id == USER_ID)
                .where(FinancialGoal.goal_type == "emergency_fund")
                .values(current_amount=6500.0)
            )

            await db.execute(
                update(FinancialGoal)
                .where(FinancialGoal.user_id == USER_ID)
                .where(FinancialGoal.goal_type == "vacation")
                .values(current_amount=1200.0)
            )

            await db.execute(
                update(FinancialGoal)
                .where(FinancialGoal.user_id == USER_ID)
                .where(FinancialGoal.goal_type == "debt_payoff")
                .values(current_amount=800.0)
            )

            await db.execute(
                update(FinancialGoal)
                .where(FinancialGoal.user_id == USER_ID)
                .where(FinancialGoal.goal_type == "home_purchase")
                .values(current_amount=12000.0)
            )

            await db.commit()
            print("✅ Updated 4 goals with progress")

            # Update budgets with spending
            print("Updating budgets with spending...")

            await db.execute(
                update(Budget)
                .where(Budget.user_id == USER_ID)
                .where(Budget.category == "groceries")
                .values(spent_amount=485.50, remaining_amount=114.50)
            )

            await db.execute(
                update(Budget)
                .where(Budget.user_id == USER_ID)
                .where(Budget.category == "dining")
                .values(spent_amount=340.25, remaining_amount=59.75)
            )

            await db.execute(
                update(Budget)
                .where(Budget.user_id == USER_ID)
                .where(Budget.category == "entertainment")
                .values(spent_amount=95.00, remaining_amount=55.00)
            )

            await db.execute(
                update(Budget)
                .where(Budget.user_id == USER_ID)
                .where(Budget.category == "transportation")
                .values(spent_amount=125.75, remaining_amount=74.25)
            )

            await db.execute(
                update(Budget)
                .where(Budget.user_id == USER_ID)
                .where(Budget.category == "utilities")
                .values(spent_amount=210.00, remaining_amount=40.00)
            )

            await db.commit()
            print("✅ Updated 5 budgets with spending")

            print("\n✅ Done! Refresh the dashboard to see updated data")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

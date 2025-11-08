#!/usr/bin/env python3
"""
Add goals and budgets to the demo user
"""
import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import FinancialGoal, Budget

async def add_demo_goals_and_budgets():
    user_id = "demo"

    async for db in get_db():
        try:
            print("=" * 60)
            print("Adding Goals and Budgets for Demo User")
            print("=" * 60)

            # Create goals
            goals = [
                FinancialGoal(
                    user_id=user_id,
                    goal_type="emergency_fund",
                    title="Emergency Fund",
                    description="Build a 6-month emergency fund for unexpected expenses",
                    target_amount=15000.00,
                    current_amount=0.00,
                    target_date=(datetime.now() + timedelta(days=266)).date(),
                    status="active"
                ),
                FinancialGoal(
                    user_id=user_id,
                    goal_type="vacation",
                    title="Summer Vacation",
                    description="Save for a summer vacation to Hawaii",
                    target_amount=5000.00,
                    current_amount=0.00,
                    target_date=(datetime.now() + timedelta(days=250)).date(),
                    status="active"
                ),
                FinancialGoal(
                    user_id=user_id,
                    goal_type="major_purchase",
                    title="New Laptop",
                    description="Save for a new MacBook Pro",
                    target_amount=2500.00,
                    current_amount=0.00,
                    target_date=(datetime.now() + timedelta(days=120)).date(),
                    status="active"
                ),
            ]

            for goal in goals:
                db.add(goal)

            await db.commit()
            print(f"✓ Created {len(goals)} financial goals")

            # Create budgets
            budgets = [
                Budget(
                    user_id=user_id,
                    category="Groceries",
                    amount=600.00,
                    period="monthly",
                    spent_amount=0.00,
                    status="active",
                    is_auto_generated=False,
                    rollover_enabled=False,
                    alert_threshold=80.0,
                    period_start_date=datetime.now().replace(day=1).date(),
                    period_end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1)
                ),
                Budget(
                    user_id=user_id,
                    category="Dining",
                    amount=400.00,
                    period="monthly",
                    spent_amount=0.00,
                    status="active",
                    is_auto_generated=False,
                    rollover_enabled=False,
                    alert_threshold=80.0,
                    period_start_date=datetime.now().replace(day=1).date(),
                    period_end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1)
                ),
                Budget(
                    user_id=user_id,
                    category="Entertainment",
                    amount=200.00,
                    period="monthly",
                    spent_amount=0.00,
                    status="active",
                    is_auto_generated=False,
                    rollover_enabled=False,
                    alert_threshold=80.0,
                    period_start_date=datetime.now().replace(day=1).date(),
                    period_end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1)
                ),
                Budget(
                    user_id=user_id,
                    category="Transportation",
                    amount=300.00,
                    period="monthly",
                    spent_amount=0.00,
                    status="active",
                    is_auto_generated=False,
                    rollover_enabled=False,
                    alert_threshold=80.0,
                    period_start_date=datetime.now().replace(day=1).date(),
                    period_end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1)
                ),
                Budget(
                    user_id=user_id,
                    category="Shopping",
                    amount=250.00,
                    period="monthly",
                    spent_amount=0.00,
                    status="active",
                    is_auto_generated=False,
                    rollover_enabled=False,
                    alert_threshold=80.0,
                    period_start_date=datetime.now().replace(day=1).date(),
                    period_end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date() - timedelta(days=1)
                ),
            ]

            for budget in budgets:
                db.add(budget)

            await db.commit()
            print(f"✓ Created {len(budgets)} budgets")

            print("\n" + "=" * 60)
            print("✅ GOALS AND BUDGETS ADDED!")
            print("=" * 60)
            print(f"\nGoals added:")
            for goal in goals:
                print(f"  - {goal.title}: ${goal.target_amount:,.2f}")
            print(f"\nBudgets added:")
            for budget in budgets:
                print(f"  - {budget.category}: ${budget.amount:,.2f}/month")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            sys.exit(1)
        finally:
            break

if __name__ == "__main__":
    asyncio.run(add_demo_goals_and_budgets())

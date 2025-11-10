#!/usr/bin/env python3
"""
Combined initialization script that creates tables and demo user in single event loop.
This solves the async SQLite engine disposal issue.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, async_session_maker
from app.models import User, Account, Transaction, Liability
from app.services.signal_detector import SignalDetector
from app.services.persona_assigner import PersonaAssigner
from app.services.recommendation_engine import RecommendationEngine
from sqlalchemy import select, delete


async def create_tables():
    """Create all database tables"""
    print("🚀 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully\n")


async def create_demo_user():
    """Create demo user with complete data"""
    user_id = "demo"

    print("=" * 60)
    print("Creating Demo User with Complete Financial Data")
    print("=" * 60)
    print()

    async with async_session_maker() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.user_id == user_id))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✓ User '{user_id}' already exists")
        else:
            # Create user
            user = User(
                user_id=user_id,
                name="Demo User",
                age=30,
                income_level="medium",
                consent_status=True,
                consent_timestamp=datetime.now()
            )
            db.add(user)
            await db.commit()
            print(f"✓ Created user '{user_id}'")

        # Delete existing financial data for clean slate
        print("\nCleaning existing data...")
        await db.execute(delete(Transaction).where(Transaction.user_id == user_id))
        await db.execute(delete(Liability).where(Liability.user_id == user_id))
        await db.execute(delete(Account).where(Account.user_id == user_id))
        await db.commit()
        print("✓ Cleaned existing data")

        # Create accounts
        print("\nCreating accounts...")

        # Checking account
        checking = Account(
            account_id=f"{user_id}_checking",
            user_id=user_id,
            type="depository",
            subtype="checking",
            current_balance=2500.00,
            available_balance=2500.00,
            iso_currency_code="USD"
        )
        db.add(checking)

        # Savings account
        savings = Account(
            account_id=f"{user_id}_savings",
            user_id=user_id,
            type="depository",
            subtype="savings",
            current_balance=8500.00,
            available_balance=8500.00,
            iso_currency_code="USD"
        )
        db.add(savings)

        # Credit card
        credit = Account(
            account_id=f"{user_id}_credit",
            user_id=user_id,
            type="credit",
            subtype="credit card",
            current_balance=1200.00,
            available_balance=3800.00,
            credit_limit=5000.00,
            iso_currency_code="USD"
        )
        db.add(credit)

        # Credit liability
        liability = Liability(
            liability_id=f"{user_id}_credit_liability",
            account_id=credit.account_id,
            user_id=user_id,
            type="credit",
            apr_percentage=18.99,
            minimum_payment_amount=35.00,
            last_payment_amount=150.00,
            is_overdue=False,
            next_payment_due_date=(datetime.now() + timedelta(days=15)).date()
        )
        db.add(liability)

        await db.commit()
        print("✓ Created 3 accounts (checking, savings, credit)")

        # Create transactions for last 180 days
        print("\nCreating transaction history...")
        transactions = []

        for days_ago in range(180):
            date = (datetime.now() - timedelta(days=days_ago)).date()

            # Income (bi-weekly)
            if days_ago % 14 == 0:
                transactions.append(Transaction(
                    transaction_id=f"{user_id}_income_{date.isoformat()}",
                    account_id=checking.account_id,
                    user_id=user_id,
                    date=date,
                    amount=2000.00,
                    merchant_name="Employer Payroll",
                    payment_channel="other",
                    category_primary="INCOME",
                    category_detailed="Paycheck",
                    pending=False
                ))

            # Subscriptions (monthly on 1st)
            if date.day == 1:
                for sub_name, amount in [
                    ("Netflix", 15.99),
                    ("Spotify", 10.99),
                    ("Amazon Prime", 14.99)
                ]:
                    transactions.append(Transaction(
                        transaction_id=f"{user_id}_sub_{sub_name}_{date.isoformat()}",
                        account_id=credit.account_id,
                        user_id=user_id,
                        date=date,
                        amount=-amount,
                        merchant_name=sub_name,
                        payment_channel="online",
                        category_primary="GENERAL_SERVICES",
                        category_detailed="Subscription",
                        pending=False
                    ))

            # Savings transfer (monthly on 5th)
            if date.day == 5:
                transactions.append(Transaction(
                    transaction_id=f"{user_id}_savings_{date.isoformat()}",
                    account_id=checking.account_id,
                    user_id=user_id,
                    date=date,
                    amount=-400.00,
                    merchant_name="Savings Transfer",
                    payment_channel="other",
                    category_primary="TRANSFER_OUT",
                    category_detailed="Savings",
                    pending=False
                ))

            # Daily spending (2-5 transactions per day)
            for i in range(random.randint(2, 5)):
                categories = [
                    ("FOOD_AND_DRINK", "Groceries", (25, 80), "Safeway"),
                    ("FOOD_AND_DRINK", "Restaurants", (12, 45), "Restaurant"),
                    ("TRANSPORTATION", "Gas", (35, 65), "Shell"),
                    ("GENERAL_MERCHANDISE", "Shopping", (20, 150), "Amazon"),
                ]

                primary, detailed, (min_amt, max_amt), merchant = random.choice(categories)
                amount = random.uniform(min_amt, max_amt)

                transactions.append(Transaction(
                    transaction_id=f"{user_id}_{date.isoformat()}_{i}_{random.randint(1000, 9999)}",
                    account_id=credit.account_id if random.random() < 0.6 else checking.account_id,
                    user_id=user_id,
                    date=date,
                    amount=-amount,
                    merchant_name=merchant,
                    payment_channel="in store" if random.random() < 0.5 else "online",
                    category_primary=primary,
                    category_detailed=detailed,
                    pending=False
                ))

        # Add all transactions
        for txn in transactions:
            db.add(txn)

        await db.commit()
        print(f"✓ Created {len(transactions)} transactions")

        # Run the pipeline
        print("\nRunning detection pipeline...")

        signal_detector = SignalDetector(db)
        persona_assigner = PersonaAssigner(db)
        rec_engine = RecommendationEngine(db)

        # Detect signals for both windows
        signals_30 = await signal_detector.detect_all_signals(user_id, window_days=30)
        await signal_detector.save_signals(signals_30)
        signals_180 = await signal_detector.detect_all_signals(user_id, window_days=180)
        await signal_detector.save_signals(signals_180)
        print(f"✓ Detected behavioral signals ({len(signals_30)} 30-day, {len(signals_180)} 180-day)")

        # Assign personas
        personas = await persona_assigner.assign_personas(user_id)
        await persona_assigner.save_personas(user_id, personas)
        print(f"✓ Assigned personas ({len(personas)} personas)")

        # Generate recommendations
        recommendations = await rec_engine.generate_recommendations(user_id)
        await rec_engine.save_recommendations(user_id, recommendations)
        await db.commit()
        print("✓ Generated recommendations")

        print("\n" + "=" * 60)
        print("✅ DEMO USER SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nUser ID: demo")
        print(f"\nThe demo user now has:")
        print("  - 3 accounts (checking, savings, credit)")
        print("  - 180 days of transaction history")
        print("  - Behavioral signals detected")
        print("  - Personas assigned")
        print("  - Personalized recommendations")
        print()


async def create_demo_goals_budgets():
    """Add goals and budgets to demo user"""
    user_id = "demo"

    print("\n" + "=" * 60)
    print("Adding Goals and Budgets for Demo User")
    print("=" * 60)

    async with async_session_maker() as db:
        # Import here to avoid circular imports
        from app.models import FinancialGoal, Budget

        # Create goals
        goals = [
            FinancialGoal(
                user_id=user_id,
                goal_type="emergency_fund",
                title="Emergency Fund",
                description="Build a 6-month emergency fund for unexpected expenses",
                target_amount=15000.00,
                current_amount=0.00,
                target_date=(datetime.now() + timedelta(days=266)).date().isoformat(),
                status="active"
            ),
            FinancialGoal(
                user_id=user_id,
                goal_type="vacation",
                title="Summer Vacation",
                description="Save for a summer vacation to Hawaii",
                target_amount=5000.00,
                current_amount=0.00,
                target_date=(datetime.now() + timedelta(days=250)).date().isoformat(),
                status="active"
            ),
            FinancialGoal(
                user_id=user_id,
                goal_type="major_purchase",
                title="New Laptop",
                description="Save for a new MacBook Pro",
                target_amount=2500.00,
                current_amount=0.00,
                target_date=(datetime.now() + timedelta(days=120)).date().isoformat(),
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
                period_start_date=datetime.now().replace(day=1).date().isoformat(),
                period_end_date=((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).date().isoformat()
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
                period_start_date=datetime.now().replace(day=1).date().isoformat(),
                period_end_date=((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).date().isoformat()
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
                period_start_date=datetime.now().replace(day=1).date().isoformat(),
                period_end_date=((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).date().isoformat()
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
                period_start_date=datetime.now().replace(day=1).date().isoformat(),
                period_end_date=((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).date().isoformat()
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
                period_start_date=datetime.now().replace(day=1).date().isoformat(),
                period_end_date=((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).date().isoformat()
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
        print()


async def main():
    """Main initialization function"""
    # Create tables first
    await create_tables()

    # Then create demo user in same event loop
    await create_demo_user()

    # Add goals and budgets in same event loop
    await create_demo_goals_budgets()

    # Dispose engine to ensure all writes are flushed
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Bootstrap script executed during Railway startup.

Responsibilities:
  * Create database tables if they do not exist
  * Ensure the production demo user (with budgets/goals) is present
  * Optionally trigger full synthetic dataset generation (>=150 users)
  * Provide readiness checks so deployments can short-circuit when data exists
"""

import argparse
import asyncio
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

from sqlalchemy import delete, func, select

from app.database import Base, async_session_maker, engine
from app.models import (
    Account,
    Budget,
    FinancialGoal,
    Persona,
    Recommendation,
    Signal,
    Transaction,
    User,
)
from app.services.persona_assigner import PersonaAssigner
from app.services.recommendation_engine import RecommendationEngine
from app.services.signal_detector import SignalDetector
from populate_full_dataset import generate_full_dataset

DEFAULT_USER_COUNT = int(os.getenv("DATASET_USER_COUNT", "150"))
FLAG_PATH = Path(os.getenv("DATASET_FLAG_PATH", "/app/data/full_dataset.flag"))


# ---------------------------------------------------------------------------
# Demo user provisioning
# ---------------------------------------------------------------------------

async def delete_existing_demo(db) -> None:
    """Remove any existing demo user data to allow clean recreation."""
    await db.execute(delete(Transaction).where(Transaction.user_id == "demo"))
    await db.execute(delete(Recommendation).where(Recommendation.user_id == "demo"))
    await db.execute(delete(Persona).where(Persona.user_id == "demo"))
    await db.execute(delete(Signal).where(Signal.user_id == "demo"))
    await db.execute(delete(Budget).where(Budget.user_id == "demo"))
    await db.execute(delete(FinancialGoal).where(FinancialGoal.user_id == "demo"))
    await db.execute(delete(Account).where(Account.user_id == "demo"))
    await db.execute(delete(User).where(User.user_id == "demo"))
    await db.commit()


async def create_demo_user(force_refresh: bool = False) -> None:
    """Create (or refresh) the production demo user with full data."""
    async with async_session_maker() as db:
        existing = await db.execute(select(User).where(User.user_id == "demo"))
        demo_user = existing.scalar_one_or_none()

        if demo_user and not force_refresh:
            txn_count = await db.scalar(
                select(func.count(Transaction.transaction_id)).where(Transaction.user_id == "demo")
            )
            if txn_count and txn_count >= 150:
                print("✅ Demo user already populated; skipping refresh.")
                return
            print("ℹ️  Demo user exists but incomplete. Refreshing...")
            await delete_existing_demo(db)
        else:
            await delete_existing_demo(db)

        now = datetime.utcnow()

        user = User(
            user_id="demo",
            name="Demo User",
            age=35,
            income_level="medium",
            consent_status=True,
            consent_timestamp=now,
            created_at=now,
        )
        db.add(user)

        checking = Account(
            account_id="demo_checking",
            user_id="demo",
            type="depository",
            subtype="checking",
            available_balance=3500.0,
            current_balance=3500.0,
            iso_currency_code="USD",
            holder_category="personal",
        )
        savings = Account(
            account_id="demo_savings",
            user_id="demo",
            type="depository",
            subtype="savings",
            available_balance=12000.0,
            current_balance=12000.0,
            iso_currency_code="USD",
            holder_category="personal",
        )
        credit = Account(
            account_id="demo_credit",
            user_id="demo",
            type="credit",
            subtype="credit card",
            available_balance=2750.0,
            current_balance=2250.0,
            credit_limit=5000.0,
            iso_currency_code="USD",
            holder_category="personal",
        )
        db.add_all([checking, savings, credit])
        await db.flush()

        # Build 180 days of transactions (payroll, subscriptions, transfers, expenses)
        transactions = []
        for day_offset in range(0, 180):
            txn_date = (now - timedelta(days=day_offset)).date()

            # Bi-weekly paycheck
            if day_offset % 14 == 0:
                transactions.append(
                    Transaction(
                        transaction_id=f"demo_income_{day_offset}",
                        account_id=checking.account_id,
                        user_id="demo",
                        date=txn_date,
                        amount=2000.0,
                        merchant_name="Employer Payroll",
                        merchant_entity_id="employer_payroll",
                        payment_channel="other",
                        category_primary="INCOME",
                        category_detailed="Paycheck",
                        pending=False,
                    )
                )

            # Monthly subscriptions on the 1st
            if txn_date.day == 1:
                for merchant, amount in [
                    ("Netflix", -15.99),
                    ("Spotify", -9.99),
                    ("Amazon Prime", -14.99),
                    ("Microsoft 365", -12.99),
                ]:
                    transactions.append(
                        Transaction(
                            transaction_id=f"demo_sub_{merchant.lower()}_{txn_date.isoformat()}",
                            account_id=credit.account_id,
                            user_id="demo",
                            date=txn_date,
                            amount=amount,
                            merchant_name=merchant,
                            merchant_entity_id=f"{merchant.lower().replace(' ', '_')}_entity",
                            payment_channel="online",
                            category_primary="GENERAL_SERVICES",
                            category_detailed="Subscription",
                            pending=False,
                        )
                    )

            # Monthly savings transfer on the 5th
            if txn_date.day == 5:
                amount = 500.0
                transactions.append(
                    Transaction(
                        transaction_id=f"demo_savings_out_{txn_date.isoformat()}",
                        account_id=checking.account_id,
                        user_id="demo",
                        date=txn_date,
                        amount=-amount,
                        merchant_name="Savings Transfer",
                        merchant_entity_id="savings_transfer_out",
                        payment_channel="other",
                        category_primary="TRANSFER_OUT",
                        category_detailed="Savings",
                        pending=False,
                    )
                )
                transactions.append(
                    Transaction(
                        transaction_id=f"demo_savings_in_{txn_date.isoformat()}",
                        account_id=savings.account_id,
                        user_id="demo",
                        date=txn_date,
                        amount=amount,
                        merchant_name="Savings Transfer",
                        merchant_entity_id="savings_transfer_in",
                        payment_channel="other",
                        category_primary="TRANSFER_IN",
                        category_detailed="Savings",
                        pending=False,
                    )
                )

            # Daily expenses (restaurants, groceries, transport)
            category_choices = [
                ("Whole Foods", -random.uniform(45, 120), "FOOD_AND_DRINK", "Groceries"),
                ("Trader Joe's", -random.uniform(30, 90), "FOOD_AND_DRINK", "Groceries"),
                ("Starbucks", -random.uniform(5, 15), "FOOD_AND_DRINK", "Coffee Shop"),
                ("Chipotle", -random.uniform(15, 35), "FOOD_AND_DRINK", "Restaurants"),
                ("Shell", -random.uniform(35, 70), "TRANSPORTATION", "Gas"),
                ("Amazon", -random.uniform(25, 150), "GENERAL_MERCHANDISE", "Shopping"),
            ]
            for merchant_name, amount, cat_primary, cat_detailed in random.sample(category_choices, k=3):
                account = credit if random.random() < 0.65 else checking
                transactions.append(
                    Transaction(
                        transaction_id=f"demo_{merchant_name.lower().replace(' ', '_')}_{day_offset}_{random.randint(1000, 9999)}",
                        account_id=account.account_id,
                        user_id="demo",
                        date=txn_date,
                        amount=round(amount, 2),
                        merchant_name=merchant_name,
                        merchant_entity_id=f"{merchant_name.lower().replace(' ', '_')}_entity",
                        payment_channel="in_store" if random.random() < 0.5 else "online",
                        category_primary=cat_primary,
                        category_detailed=cat_detailed,
                        pending=False,
                    )
                )

        db.add_all(transactions)
        await db.commit()

        # Run behavioral pipeline
        detector = SignalDetector(db)
        assigner = PersonaAssigner(db, window_days=180)
        recommender = RecommendationEngine(db)

        signals = await detector.detect_all_signals("demo", window_days=180)
        await detector.save_signals(signals)

        personas = await assigner.assign_personas("demo")
        await assigner.save_personas("demo", personas)

        recommendations = await recommender.generate_recommendations("demo")
        await recommender.save_recommendations("demo", recommendations)

        # Goals & budgets
        goals = [
            FinancialGoal(
                user_id="demo",
                goal_type="emergency_fund",
                title="Emergency Fund",
                description="Build a 6-month emergency fund",
                target_amount=30000,
                current_amount=12000,
                target_date=(now + timedelta(days=365)).date().isoformat(),
                status="active",
                progress_percent=40.0,
            ),
            FinancialGoal(
                user_id="demo",
                goal_type="vacation",
                title="Summer Vacation",
                description="Plan a family vacation to Hawaii",
                target_amount=5000,
                current_amount=2500,
                target_date=(now + timedelta(days=210)).date().isoformat(),
                status="active",
                progress_percent=50.0,
            ),
            FinancialGoal(
                user_id="demo",
                goal_type="major_purchase",
                title="New Car",
                description="Save for a new hybrid SUV",
                target_amount=15000,
                current_amount=4500,
                target_date=(now + timedelta(days=300)).date().isoformat(),
                status="active",
                progress_percent=30.0,
            ),
        ]
        budgets = [
            Budget(
                user_id="demo",
                category="Groceries",
                amount=600,
                period="monthly",
                spent_amount=420,
                remaining_amount=180,
                status="active",
                period_start_date=(now - timedelta(days=15)).date().isoformat(),
                period_end_date=(now + timedelta(days=15)).date().isoformat(),
            ),
            Budget(
                user_id="demo",
                category="Dining Out",
                amount=300,
                period="monthly",
                spent_amount=260,
                remaining_amount=40,
                status="warning",
                period_start_date=(now - timedelta(days=15)).date().isoformat(),
                period_end_date=(now + timedelta(days=15)).date().isoformat(),
            ),
            Budget(
                user_id="demo",
                category="Entertainment",
                amount=200,
                period="monthly",
                spent_amount=120,
                remaining_amount=80,
                status="active",
                period_start_date=(now - timedelta(days=15)).date().isoformat(),
                period_end_date=(now + timedelta(days=15)).date().isoformat(),
            ),
            Budget(
                user_id="demo",
                category="Transportation",
                amount=350,
                period="monthly",
                spent_amount=280,
                remaining_amount=70,
                status="active",
                period_start_date=(now - timedelta(days=15)).date().isoformat(),
                period_end_date=(now + timedelta(days=15)).date().isoformat(),
            ),
        ]
        db.add_all(goals + budgets)
        await db.commit()

        print("✅ Demo user ready with transactions, signals, personas, goals, and budgets.")


# ---------------------------------------------------------------------------
# Dataset readiness checks
# ---------------------------------------------------------------------------

async def dataset_metrics(min_users: int) -> Tuple[bool, Dict[str, float]]:
    async with async_session_maker() as db:
        user_count = await db.scalar(select(func.count(User.user_id)))
        consented = await db.scalar(
            select(func.count(User.user_id)).where(User.consent_status.is_(True))
        )
        signal_counts = await db.execute(
            select(Signal.user_id, func.count(func.distinct(Signal.signal_type)))
            .group_by(Signal.user_id)
        )
        persona_counts = await db.execute(
            select(Persona.user_id, func.count(Persona.persona_id)).group_by(Persona.user_id)
        )
        users_with_signals = sum(1 for _, count in signal_counts if count >= 3)
        users_with_persona = sum(1 for _, count in persona_counts if count >= 1)

        ready = (
            user_count >= min_users
            and users_with_signals >= min_users
            and users_with_persona >= min_users
        )
        coverage = {
            "users_total": float(user_count or 0),
            "users_with_signals": float(users_with_signals),
            "users_with_personas": float(users_with_persona),
            "consented_users": float(consented or 0),
        }
        return ready, coverage


# ---------------------------------------------------------------------------
# CLI + control flow
# ---------------------------------------------------------------------------

async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def async_main(args) -> None:
    await ensure_tables()
    await create_demo_user(force_refresh=args.refresh_demo)

    if args.check_only:
        ready, coverage = await dataset_metrics(args.user_count)
        status = "READY" if ready else "NOT READY"
        print(f"Dataset status: {status}")
        for key, value in coverage.items():
            print(f"{key}: {int(value)}")
        return

    if args.ensure_dataset:
        ready, coverage = await dataset_metrics(args.user_count)
        if ready and not args.force_dataset:
            print(
                f"✅ Dataset already meets requirements (>= {args.user_count} users with full coverage)."
            )
            return

        print("🚀 Generating synthetic dataset...")
        stats = await generate_full_dataset(
            user_count=args.user_count,
            force=args.force_dataset,
            purge_existing=args.purge_before_dataset,
        )
        print("Synthetic dataset stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Verify post-generation
        ready, coverage = await dataset_metrics(args.user_count)
        status = "READY" if ready else "NOT READY"
        print(f"Dataset status after generation: {status}")
        for key, value in coverage.items():
            print(f"  {key}: {int(value)}")


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize MaxFinanceAI dataset.")
    parser.add_argument(
        "--user-count",
        type=int,
        default=DEFAULT_USER_COUNT,
        help="Minimum synthetic user count for readiness checks (default: %(default)s).",
    )
    parser.add_argument(
        "--ensure-dataset",
        action="store_true",
        help="Run dataset generation if minimum user count/coverage is not met.",
    )
    parser.add_argument(
        "--force-dataset",
        action="store_true",
        help="Regenerate dataset even if it appears ready and the flag file exists.",
    )
    parser.add_argument(
        "--purge-before-dataset",
        action="store_true",
        help="Delete existing synthetic users (except demo) before generating new data.",
    )
    parser.add_argument(
        "--refresh-demo",
        action="store_true",
        help="Force refresh of the demo user even if it already exists.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only report readiness metrics; do not mutate data.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()

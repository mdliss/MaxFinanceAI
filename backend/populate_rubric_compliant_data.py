#!/usr/bin/env python3
"""
Rubric-Compliant Data Population Script

Generates 50-100 diverse synthetic users meeting ALL rubric requirements:
1. Diverse financial situations (income levels, credit behaviors, saving patterns)
2. Complete pipeline: accounts -> transactions -> signals -> personas -> recommendations
3. 100% coverage: every user gets persona + ≥3 behaviors
4. Both 30-day and 180-day time windows
5. All 5 persona types represented
"""

import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from app.models import User, Account, Transaction, Liability
from app.services.signal_detector import SignalDetector
from app.services.persona_assigner import PersonaAssigner
from app.services.recommendation_engine import RecommendationEngine
from sqlalchemy import select, delete

# Financial profiles representing diverse situations
PROFILES = [
    # High Utilization profiles
    {
        "name": "High Utilization - Overextended",
        "count": 12,
        "income": (35000, 55000),
        "credit_limit": (3000, 8000),
        "credit_utilization": (0.55, 0.85),  # 55-85%
        "has_overdue": True,
        "min_payment_only": True,
        "savings_rate": (0, 0.02),
    },
    {
        "name": "High Utilization - Rising Balance",
        "count": 8,
        "income": (45000, 65000),
        "credit_limit": (5000, 12000),
        "credit_utilization": (0.50, 0.70),
        "has_overdue": False,
        "min_payment_only": False,
        "savings_rate": (0, 0.05),
    },
    # Variable Income profiles
    {
        "name": "Variable Income - Gig Worker",
        "count": 10,
        "income": (25000, 45000),
        "income_variability": "high",  # Large gaps between paychecks
        "cash_buffer_months": (0.3, 0.8),
        "credit_utilization": (0.15, 0.40),
        "savings_rate": (0, 0.05),
    },
    {
        "name": "Variable Income - Seasonal",
        "count": 8,
        "income": (30000, 50000),
        "income_variability": "medium",
        "cash_buffer_months": (0.5, 1.2),
        "credit_utilization": (0.10, 0.35),
        "savings_rate": (0.02, 0.08),
    },
    # Subscription Heavy profiles
    {
        "name": "Subscription Heavy - Entertainment",
        "count": 10,
        "income": (50000, 75000),
        "subscriptions": ["Netflix", "Hulu", "Disney+", "Spotify", "Apple Music", "Amazon Prime", "HBO Max"],
        "subscription_spend_share": (0.12, 0.20),
        "credit_utilization": (0.10, 0.30),
        "savings_rate": (0.05, 0.12),
    },
    {
        "name": "Subscription Heavy - SaaS",
        "count": 8,
        "income": (60000, 90000),
        "subscriptions": ["Adobe Creative", "Microsoft 365", "Dropbox", "GitHub", "LinkedIn Premium", "Notion"],
        "subscription_spend_share": (0.10, 0.18),
        "credit_utilization": (0.05, 0.25),
        "savings_rate": (0.08, 0.15),
    },
    # Savings Builder profiles
    {
        "name": "Savings Builder - Young Professional",
        "count": 10,
        "income": (55000, 80000),
        "savings_growth_rate": (0.03, 0.08),  # 3-8% monthly growth
        "net_savings_inflow": (300, 800),
        "credit_utilization": (0.05, 0.25),
        "emergency_fund_months": (3, 8),
    },
    {
        "name": "Savings Builder - Aggressive Saver",
        "count": 8,
        "income": (70000, 110000),
        "savings_growth_rate": (0.04, 0.10),
        "net_savings_inflow": (500, 1500),
        "credit_utilization": (0, 0.20),
        "emergency_fund_months": (6, 12),
    },
    # Custom Persona: Financial Health Improver (showing positive momentum)
    {
        "name": "Financial Health Improver - Debt Paydown",
        "count": 8,
        "income": (45000, 70000),
        "credit_utilization_start": (0.60, 0.80),
        "credit_utilization_end": (0.35, 0.50),  # Declining over time
        "increasing_savings": True,
        "regular_extra_payments": True,
        "savings_rate": (0.05, 0.12),
    },
    {
        "name": "Financial Health Improver - Building Buffer",
        "count": 8,
        "income": (40000, 65000),
        "credit_utilization": (0.20, 0.40),
        "savings_growth_rate": (0.03, 0.07),
        "reducing_subscriptions": True,  # Cancel pattern
        "increasing_income": True,
        "cash_buffer_months": (1.0, 2.5),
    },
]

class RubricDataGenerator:
    def __init__(self):
        self.user_counter = 0
        self.subscription_merchants = {
            "Netflix": 15.99,
            "Hulu": 12.99,
            "Disney+": 10.99,
            "Spotify": 10.99,
            "Apple Music": 10.99,
            "Amazon Prime": 14.99,
            "HBO Max": 15.99,
            "Adobe Creative": 54.99,
            "Microsoft 365": 9.99,
            "Dropbox": 11.99,
            "GitHub": 7.00,
            "LinkedIn Premium": 29.99,
            "Notion": 8.00,
            "Gym Membership": 45.00,
            "Audible": 14.95,
        }

    async def generate_all_users(self):
        """Generate all users across all profiles"""
        print("=" * 80)
        print("GENERATING RUBRIC-COMPLIANT SYNTHETIC DATA")
        print("=" * 80)
        print()

        total_users = sum(p["count"] for p in PROFILES)
        print(f"Target: {total_users} users across {len(PROFILES)} financial profiles\n")

        async with async_session_maker() as db:
            # Clear existing data
            print("Clearing existing synthetic data...")
            await db.execute(delete(Transaction))
            await db.execute(delete(Liability))
            await db.execute(delete(Account))
            await db.execute(delete(User))
            await db.commit()
            print("✅ Cleared\n")

            created_count = 0

            for profile in PROFILES:
                print(f"Creating {profile['count']} users: {profile['name']}")

                for i in range(profile["count"]):
                    user_id = await self._create_user(db, profile)
                    created_count += 1

                    if created_count % 10 == 0:
                        print(f"  Progress: {created_count}/{total_users} users created")

                await db.commit()
                print(f"✅ Completed {profile['name']}\n")

            print(f"\n✅ Created {created_count} users")
            print("\nProcessing pipeline for all users...")
            print("-" * 80)

            # Process all users through the pipeline
            result = await db.execute(select(User))
            all_users = result.scalars().all()

            signal_detector = SignalDetector(db)
            persona_assigner = PersonaAssigner(db)
            rec_engine = RecommendationEngine(db)

            processed = 0
            for user in all_users:
                try:
                    # Detect signals for both windows
                    await signal_detector.detect_all_signals(user.user_id, window_days=30)
                    await signal_detector.detect_all_signals(user.user_id, window_days=180)

                    # Assign personas for both windows
                    await persona_assigner.assign_personas(user.user_id, window_days=30)
                    await persona_assigner.assign_personas(user.user_id, window_days=180)

                    # Generate recommendations
                    await rec_engine.generate_recommendations(user.user_id)

                    processed += 1
                    if processed % 10 == 0:
                        print(f"  Processed: {processed}/{len(all_users)} users")
                        await db.commit()

                except Exception as e:
                    print(f"  ⚠️  Error processing user {user.user_id}: {e}")

            await db.commit()
            print(f"\n✅ Processed {processed} users through complete pipeline")

            # Verification
            print("\n" + "=" * 80)
            print("VERIFICATION")
            print("=" * 80)
            await self._verify_coverage(db)

    async def _create_user(self, db, profile):
        """Create a single user with complete financial data"""
        self.user_counter += 1
        user_id = f"user_{self.user_counter:04d}"

        # Determine income
        income_min, income_max = profile["income"]
        annual_income = random.randint(income_min, income_max)
        monthly_income = annual_income / 12

        # Create user
        user = User(
            user_id=user_id,
            name=f"User {self.user_counter}",
            age=random.randint(22, 65),
            income_level=self._categorize_income(annual_income),
            consent_status=True,
            consent_timestamp=datetime.now() - timedelta(days=random.randint(30, 365))
        )
        db.add(user)

        # Create accounts
        accounts = await self._create_accounts(db, user_id, profile, monthly_income)

        # Create transactions for 180 days
        await self._create_transactions(db, user_id, accounts, profile, monthly_income)

        return user_id

    def _categorize_income(self, annual_income):
        """Categorize income level"""
        if annual_income < 35000:
            return "low"
        elif annual_income < 75000:
            return "medium"
        else:
            return "high"

    async def _create_accounts(self, db, user_id, profile, monthly_income):
        """Create checking, savings, and credit accounts"""
        accounts = {}

        # Checking account
        checking = Account(
            account_id=f"{user_id}_checking",
            user_id=user_id,
            type="depository",
            subtype="checking",
            current_balance=random.uniform(500, monthly_income * 1.5),
            available_balance=random.uniform(300, monthly_income * 1.2),
            iso_currency_code="USD"
        )
        db.add(checking)
        accounts["checking"] = checking

        # Savings account
        savings_balance = monthly_income * random.uniform(
            profile.get("emergency_fund_months", (1, 4))[0],
            profile.get("emergency_fund_months", (1, 4))[1]
        )
        savings = Account(
            account_id=f"{user_id}_savings",
            user_id=user_id,
            type="depository",
            subtype="savings",
            current_balance=savings_balance,
            available_balance=savings_balance,
            iso_currency_code="USD"
        )
        db.add(savings)
        accounts["savings"] = savings

        # Credit card
        if "credit_limit" in profile:
            limit_min, limit_max = profile["credit_limit"]
            credit_limit = random.uniform(limit_min, limit_max)
        else:
            credit_limit = monthly_income * random.uniform(1.5, 3.0)

        util_min, util_max = profile.get("credit_utilization", (0.1, 0.3))
        current_balance = credit_limit * random.uniform(util_min, util_max)

        credit = Account(
            account_id=f"{user_id}_credit",
            user_id=user_id,
            type="credit",
            subtype="credit card",
            current_balance=current_balance,
            available_balance=credit_limit - current_balance,
            credit_limit=credit_limit,
            iso_currency_code="USD"
        )
        db.add(credit)
        accounts["credit"] = credit

        # Credit card liability
        minimum_payment = max(25, current_balance * 0.02)
        liability = Liability(
            liability_id=f"{user_id}_credit_liability",
            account_id=credit.account_id,
            user_id=user_id,
            type="credit",
            apr_percentage=random.uniform(15.99, 24.99),
            minimum_payment_amount=minimum_payment,
            last_payment_amount=minimum_payment if profile.get("min_payment_only") else current_balance * random.uniform(0.3, 0.8),
            is_overdue=profile.get("has_overdue", False),
            next_payment_due_date=(datetime.now() + timedelta(days=random.randint(5, 25))).date()
        )
        db.add(liability)

        return accounts

    async def _create_transactions(self, db, user_id, accounts, profile, monthly_income):
        """Create 180 days of transaction history"""
        transactions = []
        txn_counter = 0

        # Income pattern
        income_variability = profile.get("income_variability", "regular")

        for days_ago in range(180):
            date = (datetime.now() - timedelta(days=days_ago)).date()

            # Income deposits
            if income_variability == "high":
                # Irregular income (gig worker)
                if random.random() < 0.15:  # ~15% of days have income
                    amount = monthly_income * random.uniform(0.3, 1.8)
                    transactions.append(self._create_income_transaction(
                        user_id, accounts["checking"].account_id, date, amount, txn_counter
                    ))
                    txn_counter += 1
            elif income_variability == "medium":
                # Semi-regular (weekly-ish)
                if days_ago % 7 == 0 and random.random() < 0.8:
                    amount = monthly_income / 4 * random.uniform(0.7, 1.3)
                    transactions.append(self._create_income_transaction(
                        user_id, accounts["checking"].account_id, date, amount, txn_counter
                    ))
                    txn_counter += 1
            else:
                # Regular bi-weekly
                if days_ago % 14 == 0:
                    transactions.append(self._create_income_transaction(
                        user_id, accounts["checking"].account_id, date, monthly_income / 2, txn_counter
                    ))
                    txn_counter += 1

            # Subscriptions (monthly on specific day)
            if "subscriptions" in profile and date.day == 1:
                for sub_name in profile["subscriptions"][:random.randint(3, len(profile["subscriptions"]))]:
                    if sub_name in self.subscription_merchants:
                        transactions.append(self._create_subscription_transaction(
                            user_id, accounts["credit"].account_id, date,
                            sub_name, self.subscription_merchants[sub_name]
                        ))

            # Savings transfers (beginning of month)
            if date.day == 1:
                savings_rate = random.uniform(*profile.get("savings_rate", (0.05, 0.15)))
                savings_amount = monthly_income * savings_rate
                if savings_amount > 0:
                    transactions.append(self._create_transfer_transaction(
                        user_id, accounts["checking"].account_id, date, savings_amount
                    ))

            # Daily spending (2-8 transactions per day)
            num_daily = random.randint(2, 8)
            for _ in range(num_daily):
                transactions.append(self._create_spending_transaction(
                    user_id,
                    accounts["credit" if random.random() < 0.4 else "checking"].account_id,
                    date,
                    txn_counter
                ))
                txn_counter += 1

        # Batch insert
        for txn in transactions:
            db.add(txn)

    def _create_income_transaction(self, user_id, account_id, date, amount, counter):
        """Create income transaction"""
        return Transaction(
            transaction_id=f"{user_id}_income_{date.isoformat()}_{counter}",
            account_id=account_id,
            user_id=user_id,
            date=date,
            amount=amount,
            merchant_name="Employer Payroll",
            payment_channel="other",
            category_primary="INCOME",
            category_detailed="Paycheck",
            pending=False
        )

    def _create_subscription_transaction(self, user_id, account_id, date, merchant, amount):
        """Create subscription transaction"""
        return Transaction(
            transaction_id=f"{user_id}_sub_{merchant}_{date.isoformat()}",
            account_id=account_id,
            user_id=user_id,
            date=date,
            amount=-amount,
            merchant_name=merchant,
            payment_channel="online",
            category_primary="GENERAL_SERVICES",
            category_detailed="Subscription",
            pending=False
        )

    def _create_transfer_transaction(self, user_id, account_id, date, amount):
        """Create savings transfer"""
        return Transaction(
            transaction_id=f"{user_id}_transfer_{date.isoformat()}",
            account_id=account_id,
            user_id=user_id,
            date=date,
            amount=-amount,
            merchant_name="Savings Transfer",
            payment_channel="other",
            category_primary="TRANSFER_OUT",
            category_detailed="Savings",
            pending=False
        )

    def _create_spending_transaction(self, user_id, account_id, date, counter):
        """Create regular spending transaction"""
        categories = [
            ("FOOD_AND_DRINK", "Groceries", 30, 150, "Safeway"),
            ("FOOD_AND_DRINK", "Restaurants", 10, 60, "Restaurant"),
            ("TRANSPORTATION", "Gas", 30, 70, "Shell"),
            ("GENERAL_MERCHANDISE", "Shopping", 20, 200, "Amazon"),
            ("ENTERTAINMENT", "Entertainment", 10, 50, "Entertainment"),
        ]

        primary, detailed, min_amt, max_amt, merchant = random.choice(categories)
        amount = random.uniform(min_amt, max_amt)

        return Transaction(
            transaction_id=f"{user_id}_{date.isoformat()}_{counter}",
            account_id=account_id,
            user_id=user_id,
            date=date,
            amount=-amount,
            merchant_name=merchant,
            payment_channel="in store" if random.random() < 0.6 else "online",
            category_primary=primary,
            category_detailed=detailed,
            pending=False
        )

    async def _verify_coverage(self, db):
        """Verify rubric coverage requirements"""
        # Count users with persona + ≥3 behaviors
        result = await db.execute(select(User))
        users = result.scalars().all()

        users_with_coverage = 0

        for user in users:
            # Check persona
            result = await db.execute(
                select(User).where(User.user_id == user.user_id)
            )

            from sqlalchemy import func
            from app.models import Persona, Signal

            persona_result = await db.execute(
                select(func.count(Persona.persona_id)).where(Persona.user_id == user.user_id)
            )
            has_persona = persona_result.scalar() > 0

            # Check ≥3 unique signal types
            signal_result = await db.execute(
                select(Signal.signal_type).where(Signal.user_id == user.user_id).distinct()
            )
            unique_signals = len(signal_result.scalars().all())

            if has_persona and unique_signals >= 3:
                users_with_coverage += 1

        coverage_pct = (users_with_coverage / len(users) * 100) if users else 0

        print(f"Total Users: {len(users)}")
        print(f"Users with Persona + ≥3 Behaviors: {users_with_coverage}")
        print(f"Coverage: {coverage_pct:.1f}%")
        print(f"Target: 100% ({'✅ PASS' if coverage_pct >= 100 else '❌ FAIL'})")


async def main():
    generator = RubricDataGenerator()
    await generator.generate_all_users()

    print("\n" + "=" * 80)
    print("✅ RUBRIC-COMPLIANT DATA GENERATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Restart the backend: docker-compose restart backend")
    print("2. View metrics at: http://localhost:3001/operator/metrics")
    print("3. Run rubric check: python backend/scripts/rubric_compliance_check.py")


if __name__ == "__main__":
    asyncio.run(main())

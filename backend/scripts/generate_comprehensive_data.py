"""
Comprehensive Synthetic Data Generator

Creates 100+ diverse users with realistic edge cases to showcase application functionality:
- High credit utilization users (50-95%)
- Variable income patterns (gig workers, contractors, seasonal)
- Strong savings builders
- Subscription-heavy users
- Edge cases and multiple persona matches
"""

import asyncio
import sys
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, delete
from app.database import async_session_maker
from app.models import User, Account, Transaction, Liability

random.seed(42)  # Deterministic

def generate_id(prefix: str) -> str:
    """Generate a unique ID"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def generate_transaction_id() -> str:
    """Generate transaction ID in Plaid format"""
    return f"txn_{uuid.uuid4().hex[:20]}"

# User archetypes for diverse scenarios - create list of individual users
def get_user_archetypes():
    """Generate a list of user archetypes (1 dict per user)"""
    archetypes = []

    # HIGH UTILIZATION (30 users)
    archetypes.extend([{"type": "high_util_struggling"} for _ in range(10)])
    archetypes.extend([{"type": "high_util_recovering"} for _ in range(10)])
    archetypes.extend([{"type": "high_util_extreme"} for _ in range(10)])

    # VARIABLE INCOME (30 users)
    archetypes.extend([{"type": "gig_worker"} for _ in range(10)])
    archetypes.extend([{"type": "contractor"} for _ in range(10)])
    archetypes.extend([{"type": "seasonal_worker"} for _ in range(10)])

    # SUBSCRIPTION HEAVY (25 users)
    archetypes.extend([{"type": "subscription_moderate"} for _ in range(10)])
    archetypes.extend([{"type": "subscription_extreme"} for _ in range(15)])

    # SAVINGS BUILDERS (30 users)
    archetypes.extend([{"type": "consistent_saver"} for _ in range(15)])
    archetypes.extend([{"type": "aggressive_saver"} for _ in range(15)])

    # EDGE CASES (20 users)
    archetypes.extend([{"type": "multiple_personas"} for _ in range(5)])
    archetypes.extend([{"type": "borderline_cases"} for _ in range(5)])
    archetypes.extend([{"type": "recent_changes"} for _ in range(5)])
    archetypes.extend([{"type": "financial_recovery"} for _ in range(5)])

    return archetypes

USER_ARCHETYPES = get_user_archetypes()

SUBSCRIPTION_MERCHANTS = [
    "Netflix", "Spotify", "Apple Music", "Disney+", "HBO Max",
    "Amazon Prime", "Hulu", "YouTube Premium", "Audible", "NYT Digital",
    "Adobe Creative Cloud", "Microsoft 365", "Dropbox", "Planet Fitness",
    "ClassPass", "Blue Apron", "HelloFresh", "Dollar Shave Club"
]

REGULAR_MERCHANTS = [
    ("Whole Foods", "Food and Drink", 40, 150),
    ("Safeway", "Food and Drink", 50, 200),
    ("Target", "Shops", 30, 200),
    ("Amazon", "Shops", 20, 300),
    ("Shell Gas Station", "Travel", 40, 80),
    ("Uber", "Travel", 15, 45),
    ("Starbucks", "Food and Drink", 4, 12),
    ("CVS Pharmacy", "Medical", 10, 80),
]

async def create_user(db, archetype: str, index: int) -> User:
    """Create a user based on archetype"""
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
                   "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]

    user = User(
        user_id=generate_id("user"),
        name=f"{random.choice(first_names)} {random.choice(last_names)}",
        age=random.randint(22, 65),
        income_level=random.choice(["low", "medium", "high"]),
        consent_status=True,
        consent_timestamp=datetime.utcnow()
    )
    db.add(user)
    await db.flush()
    return user

async def create_accounts(db, user: User, archetype: str) -> List[Account]:
    """Create accounts based on archetype"""
    accounts = []

    # Checking account (everyone)
    checking = Account(
        account_id=generate_id("acc"),
        user_id=user.user_id,
        type="depository",
        subtype="checking",
        available_balance=random.uniform(500, 5000),
        current_balance=random.uniform(500, 5000),
        iso_currency_code="USD",
        holder_category="personal"
    )
    accounts.append(checking)

    # Savings account (most users)
    if "saver" in archetype or "multiple" in archetype or random.random() > 0.3:
        savings = Account(
            account_id=generate_id("acc"),
            user_id=user.user_id,
            type="depository",
            subtype="savings",
            available_balance=random.uniform(1000, 20000),
            current_balance=random.uniform(1000, 20000),
            iso_currency_code="USD",
            holder_category="personal"
        )
        accounts.append(savings)

    # Credit card (most users)
    if "util" in archetype or random.random() > 0.2:
        credit_limit = random.uniform(2000, 15000)

        # Set utilization based on archetype
        if "high_util_extreme" in archetype:
            utilization = random.uniform(0.85, 0.95)
        elif "high_util_struggling" in archetype:
            utilization = random.uniform(0.60, 0.80)
        elif "high_util_recovering" in archetype:
            utilization = random.uniform(0.50, 0.65)
        elif "saver" in archetype:
            utilization = random.uniform(0.05, 0.25)
        else:
            utilization = random.uniform(0.10, 0.40)

        current_balance = credit_limit * utilization

        credit = Account(
            account_id=generate_id("acc"),
            user_id=user.user_id,
            type="credit",
            subtype="credit card",
            available_balance=credit_limit - current_balance,
            current_balance=current_balance,
            credit_limit=credit_limit,
            iso_currency_code="USD",
            holder_category="personal"
        )
        accounts.append(credit)

        # Add liability for credit card
        liability = Liability(
            liability_id=generate_id("liab"),
            account_id=credit.account_id,
            user_id=user.user_id,
            type="credit_card",
            apr_percentage=random.uniform(15.99, 24.99),
            apr_type="variable",
            minimum_payment_amount=current_balance * 0.02,
            last_payment_amount=random.uniform(50, 200),
            is_overdue="high_util_struggling" in archetype and random.random() > 0.7,
            last_statement_balance=current_balance * random.uniform(0.9, 1.1)
        )
        db.add(liability)

    for account in accounts:
        db.add(account)

    await db.flush()
    return accounts

async def create_income_transactions(db, user: User, checking: Account, archetype: str) -> List[Transaction]:
    """Create income transactions based on archetype"""
    transactions = []
    end_date = datetime(2025, 11, 4)

    if "gig_worker" in archetype:
        # Highly variable income, irregular intervals
        for i in range(25):  # ~6 months of gig payments
            days_back = random.randint(0, 180)
            date = end_date - timedelta(days=days_back)
            amount = random.uniform(100, 800)  # Highly variable

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=checking.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name=random.choice(["Uber", "DoorDash", "Instacart", "Upwork"]),
                payment_channel="ach",
                category_primary="INCOME",
                category_detailed="GIG_ECONOMY",
                pending=False
            )
            transactions.append(txn)

    elif "contractor" in archetype:
        # Monthly or bi-monthly, moderate variability
        for i in range(8):  # 6-8 months
            days_back = i * random.randint(25, 35)  # Irregular monthly
            date = end_date - timedelta(days=days_back)
            amount = random.uniform(3000, 7000)  # Good income but variable

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=checking.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="Contract Payment",
                payment_channel="ach",
                category_primary="INCOME",
                category_detailed="PAYROLL",
                pending=False
            )
            transactions.append(txn)

    elif "seasonal" in archetype:
        # Heavy income certain months, light others
        for i in range(15):
            days_back = i * 14
            if days_back > 180:
                break

            # Simulate seasonal variation (summer = high, winter = low)
            date = end_date - timedelta(days=days_back)
            month = date.month
            is_high_season = month in [6, 7, 8]  # Summer
            amount = random.uniform(2500, 4000) if is_high_season else random.uniform(800, 1500)

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=checking.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="Seasonal Employer",
                payment_channel="ach",
                category_primary="INCOME",
                category_detailed="PAYROLL",
                pending=False
            )
            transactions.append(txn)

    else:
        # Regular biweekly income (stable)
        base_income = random.uniform(2500, 6000)
        for i in range(13):  # 6 months biweekly
            days_back = i * 14
            date = end_date - timedelta(days=days_back)
            amount = base_income * random.uniform(0.98, 1.02)  # Minimal variation

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=checking.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="Employer Payroll",
                payment_channel="ach",
                category_primary="INCOME",
                category_detailed="PAYROLL",
                pending=False
            )
            transactions.append(txn)

    for txn in transactions:
        db.add(txn)

    return transactions

async def create_savings_transactions(db, user: User, savings: Account, archetype: str) -> List[Transaction]:
    """Create savings deposit transactions"""
    transactions = []
    end_date = datetime(2025, 11, 4)

    if "aggressive_saver" in archetype:
        # $400-800/month savings
        for i in range(6):
            date = end_date - timedelta(days=i*30)
            amount = random.uniform(400, 800)

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=savings.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="Automatic Transfer",
                payment_channel="ach",
                category_primary="TRANSFER",
                category_detailed="SAVINGS",
                pending=False
            )
            transactions.append(txn)

    elif "consistent_saver" in archetype or "multiple" in archetype:
        # $200-400/month savings
        for i in range(6):
            date = end_date - timedelta(days=i*30)
            amount = random.uniform(200, 400)

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=savings.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="Automatic Transfer",
                payment_channel="ach",
                category_primary="TRANSFER",
                category_detailed="SAVINGS",
                pending=False
            )
            transactions.append(txn)

    # Add some withdrawals for realism
    if random.random() > 0.5:
        for i in range(random.randint(1, 3)):
            date = end_date - timedelta(days=random.randint(0, 180))
            amount = -random.uniform(100, 300)

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=savings.account_id,
                user_id=user.user_id,
                date=date,
                amount=amount,
                merchant_name="ATM Withdrawal",
                payment_channel="withdrawal",
                category_primary="TRANSFER",
                category_detailed="WITHDRAWAL",
                pending=False
            )
            transactions.append(txn)

    for txn in transactions:
        db.add(txn)

    return transactions

async def create_subscription_transactions(db, user: User, checking: Account, archetype: str) -> List[Transaction]:
    """Create subscription transactions"""
    transactions = []
    end_date = datetime(2025, 11, 4)

    if "subscription_extreme" in archetype:
        num_subs = random.randint(8, 12)
    elif "subscription_moderate" in archetype:
        num_subs = random.randint(4, 6)
    else:
        num_subs = random.randint(0, 2)

    selected_subs = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subs, len(SUBSCRIPTION_MERCHANTS)))

    for merchant in selected_subs:
        # Create recurring transactions
        monthly_cost = random.uniform(9.99, 49.99)

        # Go back 6 months
        for i in range(6):
            date = end_date - timedelta(days=i*30 + random.randint(-2, 2))

            txn = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=checking.account_id,
                user_id=user.user_id,
                date=date,
                amount=-monthly_cost,
                merchant_name=merchant,
                payment_channel="online",
                category_primary="Services",
                category_detailed="SUBSCRIPTION",
                pending=False
            )
            transactions.append(txn)

    for txn in transactions:
        db.add(txn)

    return transactions

async def create_regular_transactions(db, user: User, checking: Account, num_months: int = 6) -> List[Transaction]:
    """Create regular spending transactions"""
    transactions = []
    end_date = datetime(2025, 11, 4)

    # Create realistic spending patterns
    for merchant, category, min_amt, max_amt in REGULAR_MERCHANTS:
        # Random frequency for this merchant
        times_per_month = random.randint(2, 8)

        for month in range(num_months):
            for _ in range(times_per_month):
                days_back = month * 30 + random.randint(0, 30)
                date = end_date - timedelta(days=days_back)
                amount = -random.uniform(min_amt, max_amt)

                txn = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=checking.account_id,
                    user_id=user.user_id,
                    date=date,
                    amount=amount,
                    merchant_name=merchant,
                    payment_channel=random.choice(["in store", "online"]),
                    category_primary=category,
                    category_detailed=category.upper(),
                    pending=False
                )
                transactions.append(txn)

    for txn in transactions:
        db.add(txn)

    return transactions

async def generate_all_data():
    """Generate comprehensive synthetic data"""
    async with async_session_maker() as db:
        print("=" * 80)
        print("COMPREHENSIVE SYNTHETIC DATA GENERATION")
        print("=" * 80)

        # Clear existing synthetic data (keep test users)
        print("\n1. Clearing existing synthetic data...")
        await db.execute(
            delete(Transaction).where(~Transaction.user_id.like('test_%'))
        )
        await db.execute(
            delete(Liability).where(~Liability.user_id.like('test_%'))
        )
        await db.execute(
            delete(Account).where(~Account.user_id.like('test_%'))
        )
        await db.execute(
            delete(User).where(~User.user_id.like('test_%'))
        )
        await db.commit()
        print("   ✓ Cleared")

        # Track statistics
        stats = {
            "users": 0,
            "accounts": 0,
            "transactions": 0,
            "high_util": 0,
            "variable_income": 0,
            "subscription_heavy": 0,
            "savers": 0,
            "edge_cases": 0
        }

        print("\n2. Generating users and accounts...")
        print(f"   Planned: {len(USER_ARCHETYPES)} users\n")

        for archetype_def in USER_ARCHETYPES:
            archetype = archetype_def["type"]

            # Create user
            user = await create_user(db, archetype, stats["users"])
            stats["users"] += 1

            # Create accounts
            accounts = await create_accounts(db, user, archetype)
            stats["accounts"] += len(accounts)

            # Find specific account types
            checking = next((a for a in accounts if a.subtype == "checking"), None)
            savings = next((a for a in accounts if a.subtype == "savings"), None)

            # Create transactions based on archetype
            if checking:
                # Income
                income_txns = await create_income_transactions(db, user, checking, archetype)
                stats["transactions"] += len(income_txns)

                # Subscriptions
                sub_txns = await create_subscription_transactions(db, user, checking, archetype)
                stats["transactions"] += len(sub_txns)

                # Regular spending
                regular_txns = await create_regular_transactions(db, user, checking)
                stats["transactions"] += len(regular_txns)

            # Savings
            if savings:
                savings_txns = await create_savings_transactions(db, user, savings, archetype)
                stats["transactions"] += len(savings_txns)

            # Update archetype stats
            if "high_util" in archetype:
                stats["high_util"] += 1
            if "gig" in archetype or "contractor" in archetype or "seasonal" in archetype:
                stats["variable_income"] += 1
            if "subscription" in archetype:
                stats["subscription_heavy"] += 1
            if "saver" in archetype:
                stats["savers"] += 1
            if "multiple" in archetype or "borderline" in archetype or "recent" in archetype or "recovery" in archetype:
                stats["edge_cases"] += 1

            # Progress indicator
            if stats["users"] % 10 == 0:
                print(f"   Generated {stats['users']} users...")

        await db.commit()

        print("\n" + "=" * 80)
        print("GENERATION COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Statistics:")
        print(f"   Total Users: {stats['users']}")
        print(f"   Total Accounts: {stats['accounts']}")
        print(f"   Total Transactions: {stats['transactions']}")
        print(f"\n👥 User Archetypes:")
        print(f"   High Utilization: {stats['high_util']}")
        print(f"   Variable Income: {stats['variable_income']}")
        print(f"   Subscription Heavy: {stats['subscription_heavy']}")
        print(f"   Savers: {stats['savers']}")
        print(f"   Edge Cases: {stats['edge_cases']}")

        return stats

if __name__ == "__main__":
    result = asyncio.run(generate_all_data())

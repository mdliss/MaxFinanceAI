"""
Enrich synthetic data to meet rubric coverage requirements.

Adds:
1. Monthly deposits to savings accounts (to generate savings_growth signals)
2. Biweekly/monthly income transactions (to generate income_stability signals)

This will ensure users have ≥3 behavioral signals as required by the rubric.
"""

import asyncio
import sys
import os
import random
import uuid
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.database import get_db
from app.models import Account, Transaction

random.seed(42)  # Deterministic behavior

def generate_transaction_id():
    """Generate a transaction ID in the format txn_<random_hex>"""
    return f"txn_{uuid.uuid4().hex[:20]}"

async def enrich_data():
    """Add missing transactions to synthetic data."""
    async for db in get_db():
        # Get all savings accounts
        savings_accounts = await db.execute(
            select(Account).where(Account.subtype.in_(['savings', 'money market', 'cd', 'hsa']))
        )
        savings_accounts = savings_accounts.scalars().all()

        print(f"Found {len(savings_accounts)} savings accounts")

        # Add monthly deposits to savings accounts (last 6 months)
        deposits_added = 0
        for account in savings_accounts:
            # Add 6 monthly deposits
            for month_offset in range(6):
                deposit_date = datetime(2025, 11, 1) - timedelta(days=30 * month_offset)
                # Random deposit amount between $100-$500
                amount = round(random.uniform(100, 500), 2)

                transaction = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=account.account_id,
                    user_id=account.user_id,
                    date=deposit_date,
                    amount=amount,
                    merchant_name="Direct Deposit",
                    payment_channel="ach",
                    category_primary="INCOME",
                    category_detailed="PAYROLL",
                    pending=False
                )
                db.add(transaction)
                deposits_added += 1

        print(f"Added {deposits_added} savings deposits")

        # Get all checking accounts (for income)
        checking_accounts = await db.execute(
            select(Account).where(Account.subtype == 'checking')
        )
        checking_accounts = checking_accounts.scalars().all()

        print(f"Found {len(checking_accounts)} checking accounts")

        # Add biweekly income for half the users, monthly for the other half
        income_added = 0
        for i, account in enumerate(checking_accounts):
            is_biweekly = i % 2 == 0
            frequency_days = 14 if is_biweekly else 30
            num_paychecks = 12 if is_biweekly else 6  # Last 6 months

            # Vary income amounts to create variable vs stable income
            base_amount = random.uniform(2000, 6000)
            is_variable = i % 3 == 0  # 1/3 of users have variable income

            for paycheck_num in range(num_paychecks):
                income_date = datetime(2025, 11, 1) - timedelta(days=frequency_days * paycheck_num)

                # Add variability for some users
                if is_variable:
                    amount = round(base_amount * random.uniform(0.7, 1.3), 2)
                else:
                    amount = round(base_amount * random.uniform(0.98, 1.02), 2)

                transaction = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=account.account_id,
                    user_id=account.user_id,
                    date=income_date,
                    amount=amount,
                    merchant_name="Employer Payroll",
                    payment_channel="ach",
                    category_primary="INCOME",
                    category_detailed="PAYROLL",
                    pending=False
                )
                db.add(transaction)
                income_added += 1

        print(f"Added {income_added} income transactions")

        # Commit all changes
        await db.commit()
        print("\n✅ Data enrichment complete!")
        print(f"Total new transactions: {deposits_added + income_added}")

        return {
            "deposits_added": deposits_added,
            "income_added": income_added,
            "total": deposits_added + income_added
        }

if __name__ == "__main__":
    result = asyncio.run(enrich_data())
    print(f"\n📊 Summary: {result}")
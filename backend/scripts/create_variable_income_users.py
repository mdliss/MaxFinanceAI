"""
Create users with variable income patterns to trigger variable_income_budgeter persona.

Per rubric: Median pay gap > 45 days AND cash-flow buffer < 1 month
"""

import asyncio
import sys
import os
import uuid
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.database import async_session_maker
from app.models import User, Account, Transaction

random.seed(43)

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def generate_transaction_id() -> str:
    return f"txn_{uuid.uuid4().hex[:20]}"

async def create_variable_income_users():
    """Create 10 users with highly variable income (median pay gap > 45 days)"""
    async with async_session_maker() as db:
        print("Creating variable income users...")

        users_created = 0
        end_date = datetime(2025, 11, 4)

        for i in range(10):
            # Create user
            user = User(
                user_id=generate_id("user"),
                name=f"Freelancer {i+1}",
                age=random.randint(25, 55),
                income_level="medium",
                consent_status=True,
                consent_timestamp=datetime.utcnow()
            )
            db.add(user)
            await db.flush()

            # Create checking account
            checking = Account(
                account_id=generate_id("acc"),
                user_id=user.user_id,
                type="depository",
                subtype="checking",
                available_balance=random.uniform(200, 800),  # Low buffer
                current_balance=random.uniform(200, 800),
                iso_currency_code="USD",
                holder_category="personal"
            )
            db.add(checking)
            await db.flush()

            # Create very irregular income pattern (payments every 50-90 days)
            num_payments = random.randint(3, 5)  # Only 3-5 payments in 180 days
            dates = []

            for j in range(num_payments):
                # Start 180 days ago and space payments irregularly
                days_back = 180 - (j * random.randint(50, 90))
                if days_back < 0:
                    break

                payment_date = end_date - timedelta(days=days_back)
                dates.append(payment_date)

                # Large but irregular amounts
                amount = random.uniform(3000, 8000)

                txn = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=checking.account_id,
                    user_id=user.user_id,
                    date=payment_date,
                    amount=amount,
                    merchant_name="Freelance Client",
                    payment_channel="ach",
                    category_primary="INCOME",
                    category_detailed="PAYROLL",
                    pending=False
                )
                db.add(txn)

            # Add some expenses to reduce cash-flow buffer
            for k in range(random.randint(20, 40)):
                expense_date = end_date - timedelta(days=random.randint(0, 180))
                expense_amount = -random.uniform(30, 200)

                txn = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=checking.account_id,
                    user_id=user.user_id,
                    date=expense_date,
                    amount=expense_amount,
                    merchant_name=random.choice(["Whole Foods", "Amazon", "Uber", "Rent"]),
                    payment_channel=random.choice(["in store", "online"]),
                    category_primary=random.choice(["Food and Drink", "Shops", "Travel", "Payment"]),
                    category_detailed="EXPENSE",
                    pending=False
                )
                db.add(txn)

            # Calculate median pay gap for verification
            dates.sort()
            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            median_gap = sorted(gaps)[len(gaps)//2] if gaps else 0

            users_created += 1
            print(f"  Created {user.name}: {num_payments} payments, median gap: {median_gap} days")

        await db.commit()

        print(f"\n✅ Created {users_created} variable income users")
        return users_created

if __name__ == "__main__":
    result = asyncio.run(create_variable_income_users())

import random
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import async_session_maker
from app.models import User, Account, Transaction

# Financial personas with distinct spending patterns
PERSONAS = [
    {
        "name": "High Spender",
        "age_range": (28, 45),
        "income": "high",
        "income_range": (120000, 200000),
        "spending_multiplier": 1.8,
        "savings_rate": 0.15
    },
    {
        "name": "Smart Saver",
        "age_range": (25, 35),
        "income": "medium",
        "income_range": (60000, 90000),
        "spending_multiplier": 0.6,
        "savings_rate": 0.40
    },
    {
        "name": "Investor",
        "age_range": (30, 50),
        "income": "medium_high",
        "income_range": (90000, 140000),
        "spending_multiplier": 0.8,
        "savings_rate": 0.30
    },
    {
        "name": "Debt Heavy",
        "age_range": (22, 32),
        "income": "medium",
        "income_range": (50000, 75000),
        "spending_multiplier": 1.4,
        "savings_rate": 0.05
    },
    {
        "name": "Budget Conscious",
        "age_range": (23, 40),
        "income": "low_medium",
        "income_range": (40000, 65000),
        "spending_multiplier": 0.7,
        "savings_rate": 0.25
    },
]

MERCHANT_DATA = {
    "FOOD_AND_DRINK": {
        "primary": "Food and Drink",
        "merchants": [
            ("Whole Foods", 45, 180),
            ("Trader Joe's", 30, 120),
            ("Starbucks", 4, 8),
            ("Chipotle", 10, 15),
            ("Sweetgreen", 12, 18),
        ],
        "channel": "in store"
    },
    "GENERAL_MERCHANDISE": {
        "primary": "Shops",
        "merchants": [
            ("Amazon", 20, 300),
            ("Target", 30, 150),
            ("Apple Store", 100, 1200),
            ("Best Buy", 50, 400),
        ],
        "channel": "online"
    },
    "RENT_AND_UTILITIES": {
        "primary": "Payment",
        "merchants": [
            ("Property Management", 1500, 3500),
            ("PG&E", 80, 200),
            ("Comcast", 60, 120),
        ],
        "channel": "other"
    },
    "TRANSPORTATION": {
        "primary": "Travel",
        "merchants": [
            ("Shell", 35, 70),
            ("Uber", 12, 45),
            ("Tesla Supercharger", 15, 40),
        ],
        "channel": "in store"
    },
    "ENTERTAINMENT": {
        "primary": "Recreation",
        "merchants": [
            ("Netflix", 15, 20),
            ("Spotify", 10, 15),
            ("AMC Theaters", 25, 60),
            ("Peloton", 39, 44),
        ],
        "channel": "online"
    },
}

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
    "Lucas", "Harper", "Henry", "Evelyn", "Alexander"
]

LAST_NAMES = [
    "Chen", "Patel", "Kim", "Garcia", "Rodriguez", "Nguyen", "Martinez",
    "Anderson", "Taylor", "Moore", "Jackson", "Lee", "Harris", "Clark",
    "Lewis", "Robinson", "Walker", "Young", "Allen", "King"
]

def generate_user_id():
    return f"user_{uuid.uuid4().hex[:12]}"

def generate_account_id():
    return f"acc_{uuid.uuid4().hex[:16]}"

def generate_transaction_id():
    return f"txn_{uuid.uuid4().hex[:20]}"

async def create_diverse_users(db, num_users: int = 20):
    """Create diverse users with different financial personas"""
    users = []
    for i in range(num_users):
        persona = PERSONAS[i % len(PERSONAS)]
        user = User(
            user_id=generate_user_id(),
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            age=random.randint(*persona["age_range"]),
            income_level=persona["income"],
            consent_status=True,  # ALL new users have consent
            consent_timestamp=datetime.utcnow(),
        )
        db.add(user)
        users.append((user, persona))

    await db.commit()
    print(f"✅ Created {len(users)} diverse users (all with consent granted)")
    return users

async def create_accounts(db, users):
    """Create bank accounts for users based on their persona"""
    accounts = []
    for user, persona in users:
        income_monthly = random.uniform(*persona["income_range"]) / 12

        # Checking account
        checking_balance = income_monthly * random.uniform(0.5, 2.0)
        checking = Account(
            account_id=generate_account_id(),
            user_id=user.user_id,
            type="depository",
            subtype="checking",
            available_balance=checking_balance,
            current_balance=checking_balance,
            iso_currency_code="USD",
            holder_category="personal",
        )
        db.add(checking)
        accounts.append((checking, user, persona))

        # Savings (based on savings rate)
        if persona["savings_rate"] > 0.15:
            savings_balance = income_monthly * 6 * persona["savings_rate"]
            savings = Account(
                account_id=generate_account_id(),
                user_id=user.user_id,
                type="depository",
                subtype="savings",
                available_balance=savings_balance,
                current_balance=savings_balance,
                iso_currency_code="USD",
                holder_category="personal",
            )
            db.add(savings)
            accounts.append((savings, user, persona))

        # Credit card (more likely for debt-heavy personas)
        credit_probability = 0.9 if persona["name"] == "Debt Heavy" else 0.7
        if random.random() < credit_probability:
            credit_limit = random.uniform(5000, 25000)
            utilization = random.uniform(0.6, 0.85) if persona["name"] == "Debt Heavy" else random.uniform(0.1, 0.4)
            current_balance = credit_limit * utilization

            credit = Account(
                account_id=generate_account_id(),
                user_id=user.user_id,
                type="credit",
                subtype="credit card",
                available_balance=credit_limit - current_balance,
                current_balance=current_balance,
                credit_limit=credit_limit,
                iso_currency_code="USD",
                holder_category="personal",
            )
            db.add(credit)
            accounts.append((credit, user, persona))

    await db.commit()
    print(f"✅ Created {len(accounts)} accounts")
    return accounts

async def create_realistic_transactions(db, accounts, days=90):
    """Generate realistic transaction patterns based on persona"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    transaction_count = 0

    for account, user, persona in accounts:
        current_date = start_date
        income_monthly = random.uniform(*persona["income_range"]) / 12
        spending_budget = income_monthly * persona["spending_multiplier"]

        while current_date <= end_date:
            # Bi-weekly paycheck for checking accounts
            if account.subtype == "checking" and current_date.day in [1, 15]:
                transaction = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=account.account_id,
                    user_id=user.user_id,
                    date=current_date,
                    amount=income_monthly / 2,
                    merchant_name="Direct Deposit",
                    payment_channel="other",
                    category_primary="Income",
                    category_detailed="Paycheck",
                    pending=False,
                )
                db.add(transaction)
                transaction_count += 1

            # Monthly rent/mortgage
            if current_date.day == 1 and account.subtype == "checking":
                rent = random.uniform(1500, 3500)
                transaction = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=account.account_id,
                    user_id=user.user_id,
                    date=current_date,
                    amount=-rent,
                    merchant_name="Property Management",
                    payment_channel="other",
                    category_primary="Payment",
                    category_detailed="Rent",
                    pending=False,
                )
                db.add(transaction)
                transaction_count += 1

            # Weekly spending based on persona
            if random.random() > 0.2:
                daily_budget = spending_budget / 30
                num_purchases = random.randint(4, 12) if persona["spending_multiplier"] > 1.2 else random.randint(2, 6)

                for _ in range(num_purchases):
                    category_key = random.choice(list(MERCHANT_DATA.keys()))
                    merchant_data = MERCHANT_DATA[category_key]
                    merchant_name, min_amt, max_amt = random.choice(merchant_data["merchants"])

                    amount = random.uniform(min_amt, max_amt) * persona["spending_multiplier"]

                    transaction = Transaction(
                        transaction_id=generate_transaction_id(),
                        account_id=account.account_id,
                        user_id=user.user_id,
                        date=current_date + timedelta(days=random.randint(0, 6)),
                        amount=-amount,
                        merchant_name=merchant_name,
                        payment_channel=merchant_data["channel"],
                        category_primary=merchant_data["primary"],
                        category_detailed=category_key.replace("_", " ").title(),
                        pending=random.random() > 0.97,
                    )
                    db.add(transaction)
                    transaction_count += 1

            current_date += timedelta(days=7)

    await db.commit()
    print(f"✅ Generated {transaction_count:,} transactions")
    return transaction_count

async def main():
    print("\n🚀 Adding diverse test users to SpendSense...")
    print("=" * 60)

    async with async_session_maker() as db:
        try:
            # Check existing users
            result = await db.execute(select(User))
            existing_users = len(result.scalars().all())
            print(f"📊 Current users in database: {existing_users}")

            # Create 20 diverse users
            print("\n👥 Creating 20 diverse users with different financial personas...")
            users = await create_diverse_users(db, num_users=20)

            print("\n🏦 Setting up bank accounts...")
            accounts = await create_accounts(db, users)

            print("\n💳 Generating 90 days of realistic transactions...")
            transaction_count = await create_realistic_transactions(db, accounts, days=90)

            # Final summary
            result = await db.execute(select(User))
            total_users = len(result.scalars().all())

            print("\n" + "=" * 60)
            print("✅ COMPLETE! Summary:")
            print(f"  New Users Added: {len(users)}")
            print(f"  Total Users Now: {total_users}")
            print(f"  New Accounts: {len(accounts)}")
            print(f"  New Transactions: {transaction_count:,}")
            print(f"  All new users have CONSENT ✅")
            print("\nPersonas included:")
            for persona in PERSONAS:
                print(f"  • {persona['name']}")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(main())

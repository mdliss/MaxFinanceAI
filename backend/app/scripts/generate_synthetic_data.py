import random
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import async_session_maker, engine, Base
from app.models import User, Account, Transaction

# Merchant categories with realistic names and amounts
MERCHANT_DATA = {
    "FOOD_AND_DRINK": {
        "primary": "Food and Drink",
        "merchants": [
            ("Whole Foods", 45, 180),
            ("Trader Joe's", 30, 120),
            ("Starbucks", 4, 8),
            ("Chipotle", 10, 15),
            ("McDonald's", 6, 12),
            ("Local Cafe", 5, 15),
            ("Panera Bread", 8, 16),
            ("Subway", 7, 12),
        ],
        "channel": "in store"
    },
    "GENERAL_MERCHANDISE": {
        "primary": "Shops",
        "merchants": [
            ("Amazon", 20, 300),
            ("Target", 30, 150),
            ("Walmart", 40, 180),
            ("Costco", 80, 250),
            ("Home Depot", 35, 200),
            ("CVS Pharmacy", 15, 60),
        ],
        "channel": "online"
    },
    "RENT_AND_UTILITIES": {
        "primary": "Payment",
        "merchants": [
            ("Property Management", 1500, 2500),
            ("PG&E", 80, 200),
            ("AT&T Internet", 60, 100),
            ("Water District", 30, 80),
        ],
        "channel": "other"
    },
    "TRANSPORTATION": {
        "primary": "Travel",
        "merchants": [
            ("Shell Gas Station", 35, 70),
            ("Chevron", 40, 75),
            ("Uber", 12, 35),
            ("Lyft", 10, 30),
        ],
        "channel": "in store"
    },
    "ENTERTAINMENT": {
        "primary": "Recreation",
        "merchants": [
            ("Netflix", 15, 20),
            ("Spotify", 10, 15),
            ("AMC Theaters", 15, 30),
            ("Apple Music", 10, 11),
        ],
        "channel": "online"
    },
    "HEALTHCARE": {
        "primary": "Medical",
        "merchants": [
            ("Kaiser Permanente", 30, 150),
            ("CVS Pharmacy", 10, 80),
            ("Walgreens", 15, 60),
        ],
        "channel": "in store"
    },
}

# Recurring bills configuration
RECURRING_BILLS = [
    ("Netflix", 15.99, "ENTERTAINMENT", 1),
    ("Spotify", 9.99, "ENTERTAINMENT", 1),
    ("AT&T Internet", 79.99, "RENT_AND_UTILITIES", 1),
    ("PG&E", 120.0, "RENT_AND_UTILITIES", 1),
    ("Property Management", 1800.0, "RENT_AND_UTILITIES", 1),
]

# User profiles with realistic demographics
USER_PROFILES = [
    {"age_range": (22, 28), "income": "low", "income_range": (35000, 55000)},
    {"age_range": (28, 35), "income": "medium", "income_range": (55000, 85000)},
    {"age_range": (35, 45), "income": "medium_high", "income_range": (85000, 125000)},
    {"age_range": (45, 60), "income": "high", "income_range": (125000, 200000)},
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Nancy", "Matthew", "Lisa",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
]


def generate_user_id():
    return f"user_{uuid.uuid4().hex[:12]}"


def generate_account_id():
    return f"acc_{uuid.uuid4().hex[:16]}"


def generate_transaction_id():
    return f"txn_{uuid.uuid4().hex[:20]}"


async def create_users(db, num_users: int = 75):
    users = []
    for _ in range(num_users):
        profile = random.choice(USER_PROFILES)
        user = User(
            user_id=generate_user_id(),
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            age=random.randint(*profile["age_range"]),
            income_level=profile["income"],
            consent_status=random.choice([True, True, True, False]),  # 75% consent
            consent_timestamp=datetime.utcnow() if random.random() > 0.25 else None,
        )
        db.add(user)
        users.append((user, profile))
    await db.commit()
    return users


async def create_accounts(db, users):
    accounts = []
    for user, profile in users:
        # Everyone gets a checking account
        checking = Account(
            account_id=generate_account_id(),
            user_id=user.user_id,
            type="depository",
            subtype="checking",
            available_balance=random.uniform(500, 5000),
            current_balance=random.uniform(500, 5000),
            iso_currency_code="USD",
            holder_category="personal",
        )
        db.add(checking)
        accounts.append((checking, user, profile))

        # 70% get savings
        if random.random() > 0.3:
            savings = Account(
                account_id=generate_account_id(),
                user_id=user.user_id,
                type="depository",
                subtype="savings",
                available_balance=random.uniform(1000, 20000),
                current_balance=random.uniform(1000, 20000),
                iso_currency_code="USD",
                holder_category="personal",
            )
            db.add(savings)
            accounts.append((savings, user, profile))

        # 60% get credit card
        if random.random() > 0.4:
            credit_limit = random.uniform(2000, 15000)
            current_balance = random.uniform(100, credit_limit * 0.5)
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
            accounts.append((credit, user, profile))

    await db.commit()
    return accounts


async def create_transactions(db, accounts, days=180):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    for account, user, profile in accounts:
        current_date = start_date
        income_monthly = random.uniform(*profile["income_range"])

        # Generate recurring bills
        while current_date <= end_date:
            # Paycheck every 2 weeks for checking accounts
            if account.subtype == "checking" and current_date.day in [1, 15]:
                transaction = Transaction(
                    transaction_id=generate_transaction_id(),
                    account_id=account.account_id,
                    user_id=user.user_id,
                    date=current_date,
                    amount=income_monthly / 2,  # Bi-weekly pay
                    merchant_name="Direct Deposit - Employer",
                    payment_channel="other",
                    category_primary="Income",
                    category_detailed="Paycheck",
                    pending=False,
                )
                db.add(transaction)

            # Monthly bills on first of month
            if current_date.day == 1 and account.subtype in ["checking", "credit card"]:
                for bill_name, amount, category, day_of_month in RECURRING_BILLS:
                    if random.random() > 0.3:  # Not everyone has all subscriptions
                        merchant_data = MERCHANT_DATA[category]
                        transaction = Transaction(
                            transaction_id=generate_transaction_id(),
                            account_id=account.account_id,
                            user_id=user.user_id,
                            date=current_date,
                            amount=-amount,
                            merchant_name=bill_name,
                            payment_channel=merchant_data["channel"],
                            category_primary=merchant_data["primary"],
                            category_detailed=category.replace("_", " ").title(),
                            pending=False,
                        )
                        db.add(transaction)

            # Random purchases (3-8 per week)
            if random.random() > 0.3:
                num_purchases = random.randint(3, 8)
                for _ in range(num_purchases):
                    category_key = random.choice(list(MERCHANT_DATA.keys()))
                    merchant_data = MERCHANT_DATA[category_key]
                    merchant_name, min_amt, max_amt = random.choice(merchant_data["merchants"])

                    transaction = Transaction(
                        transaction_id=generate_transaction_id(),
                        account_id=account.account_id,
                        user_id=user.user_id,
                        date=current_date + timedelta(days=random.randint(0, 6)),
                        amount=-random.uniform(min_amt, max_amt),
                        merchant_name=merchant_name,
                        merchant_entity_id=f"ent_{uuid.uuid4().hex[:8]}",
                        payment_channel=merchant_data["channel"],
                        category_primary=merchant_data["primary"],
                        category_detailed=category_key.replace("_", " ").title(),
                        pending=random.random() > 0.95,  # 5% pending
                    )
                    db.add(transaction)

            current_date += timedelta(days=7)  # Move week by week

    await db.commit()


async def main():
    print("🏗️  Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        try:
            # Check if data already exists
            result = await db.execute(select(User))
            existing_users = len(result.scalars().all())

            if existing_users > 0:
                print(f"⚠️  Database already has {existing_users} users.")
                print("🗑️  Clearing existing data...")
                await db.execute(Transaction.__table__.delete())
                await db.execute(Account.__table__.delete())
                await db.execute(User.__table__.delete())
                await db.commit()

            print("👥 Generating users...")
            num_users = random.randint(50, 100)
            users = await create_users(db, num_users)
            print(f"✅ Created {len(users)} users")

            print("🏦 Creating accounts...")
            accounts = await create_accounts(db, users)
            print(f"✅ Created {len(accounts)} accounts")

            print("💳 Generating 180 days of transactions...")
            await create_transactions(db, accounts, days=180)

            # Get final counts
            result = await db.execute(select(Transaction))
            total_transactions = len(result.scalars().all())
            print(f"✅ Generated {total_transactions:,} transactions")

            print("\n📊 Summary:")
            print(f"  Users: {len(users)}")
            print(f"  Accounts: {len(accounts)}")
            print(f"  Transactions: {total_transactions:,}")
            print(f"  Date Range: 180 days")
            print("\n✅ Synthetic data generation complete!")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

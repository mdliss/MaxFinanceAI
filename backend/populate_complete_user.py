#!/usr/bin/env python3
"""
Populate COMPLETE user data for MaxFinanceAI including V1 and V2 features
This creates accounts, transactions, signals, personas, recommendations, goals, budgets, and alerts
"""

import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the backend to path
import sys
sys.path.insert(0, '/app')

from app.database import async_session_maker
from app.models import User, Account, Transaction, Signal, Persona, Recommendation, FinancialGoal, Budget

USER_ID = "user_05559915742f"

async def populate_accounts(db: AsyncSession):
    """Create realistic bank accounts"""
    print("Creating accounts...")

    accounts = [
        Account(
            account_id="acc_checking_demo",
            user_id=USER_ID,
            type="depository",
            subtype="checking",
            available_balance=3200.00,
            current_balance=3500.00,
            iso_currency_code="USD",
            holder_category="personal"
        ),
        Account(
            account_id="acc_savings_demo",
            user_id=USER_ID,
            type="depository",
            subtype="savings",
            available_balance=12000.00,
            current_balance=12000.00,
            iso_currency_code="USD",
            holder_category="personal"
        ),
        Account(
            account_id="acc_credit_demo",
            user_id=USER_ID,
            type="credit",
            subtype="credit card",
            available_balance=7500.00,
            current_balance=2500.00,
            credit_limit=10000.00,
            iso_currency_code="USD",
            holder_category="personal"
        )
    ]

    for account in accounts:
        db.add(account)

    await db.commit()
    print(f"✅ Created {len(accounts)} accounts")
    return accounts

async def populate_transactions(db: AsyncSession, accounts):
    """Create realistic transaction history (90 days)"""
    print("Creating transactions...")

    # Transaction templates
    merchants = {
        "groceries": ["Whole Foods", "Trader Joe's", "Safeway", "Target"],
        "dining": ["Chipotle", "Starbucks", "Panera", "Local Restaurant"],
        "gas": ["Shell", "Chevron", "Costco Gas"],
        "entertainment": ["Netflix", "Spotify", "AMC Theaters", "Amazon Prime"],
        "utilities": ["PG&E", "Water District", "Comcast"],
        "shopping": ["Amazon", "Target", "Macy's", "Best Buy"]
    }

    categories = [
        ("groceries", "Food and Drink", "Groceries", 40, 150),
        ("dining", "Food and Drink", "Restaurants", 10, 50),
        ("gas", "Travel", "Gas Stations", 30, 70),
        ("entertainment", "Recreation", "Entertainment", 5, 30),
        ("utilities", "Payment", "Utilities", 50, 200),
        ("shopping", "Shops", "General Merchandise", 20, 200)
    ]

    transactions = []
    checking_account = next(a for a in accounts if a.subtype == "checking")
    credit_account = next(a for a in accounts if a.type == "credit")

    # Generate 90 days of transactions
    for days_ago in range(90):
        date = datetime.now().date() - timedelta(days=days_ago)

        # 2-4 transactions per day
        num_txns = random.randint(2, 4)

        for _ in range(num_txns):
            cat_type, primary, detailed, min_amt, max_amt = random.choice(categories)
            merchant_list = merchants.get(cat_type, ["Generic Merchant"])
            merchant = random.choice(merchant_list)
            amount = round(random.uniform(min_amt, max_amt), 2)

            # 70% checking, 30% credit
            account = checking_account if random.random() < 0.7 else credit_account

            txn = Transaction(
                transaction_id=f"txn_{USER_ID}_{date.isoformat()}_{random.randint(1000, 9999)}",
                account_id=account.account_id,
                user_id=USER_ID,
                date=date,
                amount=-amount,  # Negative for expenses
                merchant_name=merchant,
                merchant_entity_id=f"ent_{random.randint(100000, 999999)}",
                payment_channel="in store" if random.random() < 0.6 else "online",
                category_primary=primary,
                category_detailed=detailed,
                pending=False
            )
            transactions.append(txn)

    # Add some income transactions
    for i in range(3):  # 3 paychecks
        date = datetime.now().date() - timedelta(days=i*15)
        txn = Transaction(
            transaction_id=f"txn_{USER_ID}_{date.isoformat()}_income_{i}",
            account_id=checking_account.account_id,
            user_id=USER_ID,
            date=date,
            amount=2800.00,  # Positive for income
            merchant_name="Employer Payroll",
            payment_channel="other",
            category_primary="Income",
            category_detailed="Paycheck",
            pending=False
        )
        transactions.append(txn)

    for txn in transactions:
        db.add(txn)

    await db.commit()
    print(f"✅ Created {len(transactions)} transactions over 90 days")

async def populate_signals(db: AsyncSession):
    """Create behavioral signals"""
    print("Creating signals...")

    signals = [
        Signal(
            signal_id=f"sig_{USER_ID}_credit_util",
            user_id=USER_ID,
            signal_type="credit_utilization",
            value=25.0,
            details='{"message": "Credit utilization is healthy at 25%"}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_savings_rate",
            user_id=USER_ID,
            signal_type="savings_rate",
            value=15.5,
            details='{"message": "Saving 15.5% of income"}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_monthly_spend",
            user_id=USER_ID,
            signal_type="monthly_spending",
            value=2350.00,
            details='{"message": "Average monthly spending: $2,350"}'
        )
    ]

    for signal in signals:
        db.add(signal)

    await db.commit()
    print(f"✅ Created {len(signals)} signals")

async def populate_personas(db: AsyncSession):
    """Assign user personas"""
    print("Creating personas...")

    persona = Persona(
        user_id=USER_ID,
        window_days=180,
        persona_type="budget_conscious",
        priority_rank=1,
        criteria_met="Consistent savings pattern, tracks spending"
    )

    db.add(persona)
    await db.commit()
    print("✅ Created persona: budget_conscious")

async def populate_recommendations(db: AsyncSession):
    """Create personalized recommendations"""
    print("Creating recommendations...")

    recommendations = [
        Recommendation(
            user_id=USER_ID,
            persona_type="budget_conscious",
            content_type="budgeting_tip",
            title="Review Your Entertainment Spending",
            description="You're spending consistently on subscriptions. Consider reviewing which ones you actively use.",
            rationale="Based on your transaction history, you have multiple recurring entertainment charges.",
            eligibility_met=True,
            approval_status="approved"
        ),
        Recommendation(
            user_id=USER_ID,
            persona_type="budget_conscious",
            content_type="savings_tip",
            title="Increase Emergency Fund Contributions",
            description="Great job saving! Consider automating transfers to reach your goal faster.",
            rationale="You have steady income and room in your budget for increased savings.",
            eligibility_met=True,
            approval_status="approved"
        )
    ]

    for rec in recommendations:
        db.add(rec)

    await db.commit()
    print(f"✅ Created {len(recommendations)} recommendations")

async def populate_goals(db: AsyncSession):
    """Create financial goals"""
    print("Creating financial goals...")

    goals = [
        FinancialGoal(
            user_id=USER_ID,
            name="Emergency Fund",
            target_amount=10000.00,
            current_amount=6500.00,
            deadline=(datetime.now() + timedelta(days=180)).date(),
            category="savings",
            status="active"
        ),
        FinancialGoal(
            user_id=USER_ID,
            name="Vacation to Hawaii",
            target_amount=5000.00,
            current_amount=1200.00,
            deadline=(datetime.now() + timedelta(days=270)).date(),
            category="savings",
            status="active"
        ),
        FinancialGoal(
            user_id=USER_ID,
            name="Pay Off Credit Card",
            target_amount=2500.00,
            current_amount=1800.00,
            deadline=(datetime.now() + timedelta(days=90)).date(),
            category="debt_payoff",
            status="active"
        ),
        FinancialGoal(
            user_id=USER_ID,
            name="New Laptop Fund",
            target_amount=2000.00,
            current_amount=450.00,
            deadline=(datetime.now() + timedelta(days=150)).date(),
            category="purchase",
            status="active"
        )
    ]

    for goal in goals:
        db.add(goal)

    await db.commit()
    print(f"✅ Created {len(goals)} financial goals")

async def populate_budgets(db: AsyncSession):
    """Create monthly budgets"""
    print("Creating budgets...")

    budgets = [
        Budget(
            user_id=USER_ID,
            category="groceries",
            limit=600.00,
            spent=485.50,
            period="monthly",
            start_date=datetime.now().replace(day=1).date(),
            status="active"
        ),
        Budget(
            user_id=USER_ID,
            category="dining",
            limit=300.00,
            spent=340.25,
            period="monthly",
            start_date=datetime.now().replace(day=1).date(),
            status="active"
        ),
        Budget(
            user_id=USER_ID,
            category="entertainment",
            limit=150.00,
            spent=95.00,
            period="monthly",
            start_date=datetime.now().replace(day=1).date(),
            status="active"
        ),
        Budget(
            user_id=USER_ID,
            category="transportation",
            limit=200.00,
            spent=125.75,
            period="monthly",
            start_date=datetime.now().replace(day=1).date(),
            status="active"
        ),
        Budget(
            user_id=USER_ID,
            category="utilities",
            limit=250.00,
            spent=210.00,
            period="monthly",
            start_date=datetime.now().replace(day=1).date(),
            status="active"
        )
    ]

    for budget in budgets:
        db.add(budget)

    await db.commit()
    print(f"✅ Created {len(budgets)} budgets")

async def main():
    print("=" * 70)
    print("Creating COMPLETE user profile with V1 + V2 data")
    print("=" * 70)
    print(f"User: {USER_ID}\n")

    async with async_session_maker() as db:
        try:
            # Check if user exists
            result = await db.execute(select(User).where(User.user_id == USER_ID))
            user = result.scalar_one_or_none()

            if not user:
                print(f"❌ Error: User {USER_ID} not found!")
                print("Run create_rich_test_user.py first!")
                return

            print(f"✅ Found user: {user.name}\n")

            # Create V1 data (accounts, transactions, signals, personas, recommendations)
            accounts = await populate_accounts(db)
            await populate_transactions(db, accounts)
            await populate_signals(db)
            await populate_personas(db)
            await populate_recommendations(db)

            # Create V2 data (goals, budgets)
            await populate_goals(db)
            await populate_budgets(db)

            print("\n" + "=" * 70)
            print("✅ Complete! User now has:")
            print("=" * 70)

            # Verify data
            result = await db.execute(
                select(Account).where(Account.user_id == USER_ID)
            )
            account_count = len(result.scalars().all())

            result = await db.execute(
                select(Transaction).where(Transaction.user_id == USER_ID)
            )
            txn_count = len(result.scalars().all())

            result = await db.execute(
                select(FinancialGoal).where(FinancialGoal.user_id == USER_ID)
            )
            goal_count = len(result.scalars().all())

            result = await db.execute(
                select(Budget).where(Budget.user_id == USER_ID)
            )
            budget_count = len(result.scalars().all())

            print(f"V1 Data:")
            print(f"  - {account_count} Accounts")
            print(f"  - {txn_count} Transactions")
            print(f"  - 3 Behavioral Signals")
            print(f"  - 1 Persona Assignment")
            print(f"  - 2 Recommendations")

            print(f"\nV2 Data:")
            print(f"  - {goal_count} Financial Goals")
            print(f"  - {budget_count} Monthly Budgets")

            print(f"\n🎉 Dashboard should now show complete data!")
            print(f"Visit: http://localhost:3001/dashboard")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

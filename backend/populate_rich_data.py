#!/usr/bin/env python3
"""
Populate comprehensive, realistic financial data for demo user
Creates a full 6-month history with realistic patterns
"""

import asyncio
from datetime import datetime, timedelta
import random
import sys
sys.path.insert(0, '/app')

from app.database import async_session_maker
from app.models import User, Account, Transaction, Signal, Persona, Recommendation, FinancialGoal, Budget, Alert
from sqlalchemy import select, delete

USER_ID = "user_05559915742f"

# Realistic spending patterns
MERCHANTS = {
    "groceries": [
        ("Whole Foods", 45, 120),
        ("Trader Joe's", 30, 80),
        ("Safeway", 40, 100),
        ("Target", 50, 150),
        ("Costco", 100, 300)
    ],
    "dining": [
        ("Chipotle", 8, 15),
        ("Starbucks", 4, 8),
        ("Panera Bread", 10, 18),
        ("Local Restaurant", 25, 60),
        ("Olive Garden", 30, 70),
        ("McDonald's", 6, 12)
    ],
    "gas": [
        ("Shell", 35, 65),
        ("Chevron", 40, 70),
        ("Costco Gas", 30, 60)
    ],
    "entertainment": [
        ("Netflix", 15, 20),
        ("Spotify", 10, 15),
        ("AMC Theaters", 15, 40),
        ("Amazon Prime", 12, 15),
        ("Disney+", 8, 10)
    ],
    "utilities": [
        ("PG&E", 80, 180),
        ("Water District", 50, 120),
        ("Comcast", 90, 130),
        ("AT&T", 70, 100)
    ],
    "shopping": [
        ("Amazon", 20, 200),
        ("Target", 25, 150),
        ("Macy's", 40, 180),
        ("Best Buy", 50, 300),
        ("Apple Store", 100, 800)
    ],
    "transportation": [
        ("Uber", 12, 35),
        ("Lyft", 10, 30),
        ("BART", 5, 8),
        ("Parking", 10, 25)
    ],
    "healthcare": [
        ("CVS Pharmacy", 15, 50),
        ("Walgreens", 10, 40),
        ("Dr. Office", 50, 200)
    ]
}

async def clear_existing_data(db):
    """Clear existing transactional data but keep user and accounts"""
    print("Clearing existing data...")

    await db.execute(delete(Transaction).where(Transaction.user_id == USER_ID))
    await db.execute(delete(Signal).where(Signal.user_id == USER_ID))
    await db.execute(delete(Recommendation).where(Recommendation.user_id == USER_ID))
    await db.execute(delete(Persona).where(Persona.user_id == USER_ID))
    await db.execute(delete(Alert).where(Alert.user_id == USER_ID))

    await db.commit()
    print("✅ Cleared existing transactional data")

async def create_realistic_transactions(db, accounts, days=180):
    """Create 6 months of realistic transaction history"""
    print(f"Creating {days} days of transaction history...")

    checking_account = next(a for a in accounts if a.subtype == "checking")
    credit_account = next(a for a in accounts if a.type == "credit")
    savings_account = next(a for a in accounts if a.subtype == "savings")

    transactions = []
    transaction_count = 0

    # Generate transactions for each day
    for days_ago in range(days):
        date = datetime.now().date() - timedelta(days=days_ago)

        # Bi-weekly paycheck (every 14 days)
        if days_ago % 14 == 0:
            transactions.append(Transaction(
                transaction_id=f"txn_{USER_ID}_{date.isoformat()}_income_{days_ago}",
                account_id=checking_account.account_id,
                user_id=USER_ID,
                date=date,
                amount=2800.00,
                merchant_name="Employer Payroll",
                payment_channel="other",
                category_primary="Income",
                category_detailed="Paycheck",
                pending=False
            ))
            transaction_count += 1

        # Monthly savings transfer (first of month)
        if date.day == 1:
            transactions.append(Transaction(
                transaction_id=f"txn_{USER_ID}_{date.isoformat()}_savings",
                account_id=checking_account.account_id,
                user_id=USER_ID,
                date=date,
                amount=-400.00,
                merchant_name="Savings Transfer",
                payment_channel="other",
                category_primary="Transfer",
                category_detailed="Savings",
                pending=False
            ))
            transaction_count += 1

        # Daily transactions (2-6 per day)
        num_transactions = random.randint(2, 6)

        for _ in range(num_transactions):
            category_type = random.choice(list(MERCHANTS.keys()))
            merchant_data = random.choice(MERCHANTS[category_type])
            merchant_name, min_amt, max_amt = merchant_data
            amount = round(random.uniform(min_amt, max_amt), 2)

            # 60% checking, 40% credit
            account = checking_account if random.random() < 0.6 else credit_account

            # Map to proper categories
            category_map = {
                "groceries": ("Food and Drink", "Groceries"),
                "dining": ("Food and Drink", "Restaurants"),
                "gas": ("Transportation", "Gas Stations"),
                "entertainment": ("Recreation", "Entertainment"),
                "utilities": ("Payment", "Utilities"),
                "shopping": ("Shops", "General Merchandise"),
                "transportation": ("Transportation", "Public Transportation"),
                "healthcare": ("Healthcare", "Pharmacies")
            }

            primary, detailed = category_map.get(category_type, ("Other", "Other"))

            txn_id = f"txn_{USER_ID}_{date.isoformat()}_{transaction_count}_{random.randint(1000, 9999)}"
            transactions.append(Transaction(
                transaction_id=txn_id,
                account_id=account.account_id,
                user_id=USER_ID,
                date=date,
                amount=-amount,
                merchant_name=merchant_name,
                merchant_entity_id=f"ent_{random.randint(100000, 999999)}",
                payment_channel="in store" if random.random() < 0.6 else "online",
                category_primary=primary,
                category_detailed=detailed,
                pending=False
            ))
            transaction_count += 1

    # Batch insert
    for txn in transactions:
        db.add(txn)

    await db.commit()
    print(f"✅ Created {transaction_count} transactions over {days} days")
    return transaction_count

async def create_signals(db):
    """Create behavioral signals based on transaction data"""
    print("Creating behavioral signals...")

    signals = [
        Signal(
            signal_id=f"sig_{USER_ID}_credit_util",
            user_id=USER_ID,
            signal_type="credit_utilization",
            value=25.0,
            details='{"message": "Credit utilization at 25%", "limit": 10000, "balance": 2500}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_savings_rate",
            user_id=USER_ID,
            signal_type="savings_rate",
            value=15.5,
            details='{"message": "Saving 15.5% of income monthly", "monthly_income": 5600, "monthly_savings": 868}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_monthly_spend",
            user_id=USER_ID,
            signal_type="monthly_spending",
            value=3200.00,
            details='{"message": "Average monthly spending: $3,200", "categories": {"groceries": 520, "dining": 380, "gas": 180}}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_recurring_netflix",
            user_id=USER_ID,
            signal_type="subscription_detected",
            value=15.99,
            details='{"merchant": "Netflix", "average_amount": 15.99, "frequency": "monthly"}'
        ),
        Signal(
            signal_id=f"sig_{USER_ID}_recurring_spotify",
            user_id=USER_ID,
            signal_type="subscription_detected",
            value=10.99,
            details='{"merchant": "Spotify", "average_amount": 10.99, "frequency": "monthly"}'
        )
    ]

    for signal in signals:
        db.add(signal)

    await db.commit()
    print(f"✅ Created {len(signals)} behavioral signals")

async def create_personas_and_recommendations(db):
    """Create persona and recommendations"""
    print("Creating persona and recommendations...")

    persona = Persona(
        user_id=USER_ID,
        window_days=180,
        persona_type="budget_conscious",
        priority_rank=1,
        criteria_met="Consistent savings pattern, tracks spending, maintains emergency fund"
    )
    db.add(persona)

    recommendations = [
        Recommendation(
            user_id=USER_ID,
            persona_type="budget_conscious",
            content_type="budgeting_tip",
            title="Review Your Entertainment Spending",
            description="You have multiple streaming subscriptions. Consider consolidating to save $20-30/month.",
            rationale="Analysis shows you're subscribed to Netflix, Spotify, Disney+, and Amazon Prime.",
            eligibility_met=True,
            approval_status="approved"
        ),
        Recommendation(
            user_id=USER_ID,
            persona_type="budget_conscious",
            content_type="savings_tip",
            title="Increase Emergency Fund Target",
            description="Great progress on your emergency fund! Consider increasing your target to 8 months of expenses.",
            rationale="You're consistently saving 15% of income and have stable employment.",
            eligibility_met=True,
            approval_status="approved"
        ),
        Recommendation(
            user_id=USER_ID,
            persona_type="budget_conscious",
            content_type="credit_tip",
            title="Excellent Credit Utilization",
            description="Your credit utilization is at a healthy 25%. Keep it below 30% to maintain a strong credit score.",
            rationale="Current utilization: $2,500 of $10,000 available credit.",
            eligibility_met=True,
            approval_status="approved"
        )
    ]

    for rec in recommendations:
        db.add(rec)

    await db.commit()
    print(f"✅ Created persona and {len(recommendations)} recommendations")

async def create_alerts(db):
    """Create active alerts"""
    print("Creating alerts...")

    alerts = [
        Alert(
            user_id=USER_ID,
            alert_type="budget_exceeded",
            severity="high",
            title="Dining Budget Exceeded",
            message="You've spent $340 of your $300 dining budget this month",
            is_read=False,
            meta_data='{"category": "dining", "spent": 340, "limit": 300}'
        ),
        Alert(
            user_id=USER_ID,
            alert_type="goal_milestone",
            severity="info",
            title="Goal Milestone Reached",
            message="You're 50% of the way to your Hawaii vacation goal!",
            is_read=False,
            meta_data='{"goal": "Vacation to Hawaii", "progress": 50}'
        ),
        Alert(
            user_id=USER_ID,
            alert_type="budget_warning",
            severity="medium",
            title="Groceries Budget Warning",
            message="You've used 81% of your groceries budget with 10 days remaining",
            is_read=False,
            meta_data='{"category": "groceries", "spent": 485.50, "limit": 600}'
        )
    ]

    for alert in alerts:
        db.add(alert)

    await db.commit()
    print(f"✅ Created {len(alerts)} alerts")

async def update_account_balances(db, accounts):
    """Update account balances to reflect transaction history"""
    print("Updating account balances...")

    checking = next(a for a in accounts if a.subtype == "checking")
    credit = next(a for a in accounts if a.type == "credit")
    savings = next(a for a in accounts if a.subtype == "savings")

    # Update with realistic balances
    checking.current_balance = 3847.25
    checking.available_balance = 3547.25

    credit.current_balance = 2486.50
    credit.available_balance = 7513.50

    savings.current_balance = 14200.00
    savings.available_balance = 14200.00

    await db.commit()
    print("✅ Updated account balances")

async def main():
    print("=" * 80)
    print("POPULATING COMPREHENSIVE DEMO DATA")
    print("=" * 80)
    print(f"User: {USER_ID}\n")

    async with async_session_maker() as db:
        try:
            # Verify user exists
            result = await db.execute(select(User).where(User.user_id == USER_ID))
            user = result.scalar_one_or_none()

            if not user:
                print(f"❌ Error: User {USER_ID} not found!")
                return

            print(f"✅ Found user: {user.name}\n")

            # Get existing accounts
            result = await db.execute(select(Account).where(Account.user_id == USER_ID))
            accounts = result.scalars().all()

            if len(accounts) < 3:
                print("❌ Error: Expected 3 accounts (checking, savings, credit)")
                return

            print(f"✅ Found {len(accounts)} accounts\n")

            # Clear old data
            await clear_existing_data(db)

            # Create new comprehensive data
            print("\nPopulating new data...")
            print("-" * 80)

            txn_count = await create_realistic_transactions(db, accounts, days=180)
            await create_signals(db)
            await create_personas_and_recommendations(db)
            await create_alerts(db)
            await update_account_balances(db, accounts)

            print("\n" + "=" * 80)
            print("✅ DATA POPULATION COMPLETE!")
            print("=" * 80)
            print(f"\nSummary:")
            print(f"  • {txn_count} transactions over 180 days")
            print(f"  • 5 behavioral signals")
            print(f"  • 1 persona assignment")
            print(f"  • 3 recommendations")
            print(f"  • 3 active alerts")
            print(f"  • 4 financial goals (existing)")
            print(f"  • 5 monthly budgets (existing)")
            print(f"\n🎉 Dashboard at: http://localhost:3001/dashboard")
            print(f"📊 Full transaction history with realistic spending patterns")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Populate budget spending data for demo user based on actual transactions
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.database import get_db
from app.models import Budget, Transaction

# Map transaction categories to budget categories
CATEGORY_MAPPING = {
    'Groceries': ['FOOD_AND_DRINK'],
    'Dining': ['FOOD_AND_DRINK'],
    'Entertainment': ['GENERAL_SERVICES', 'GENERAL_MERCHANDISE'],
    'Transportation': ['TRANSPORTATION'],
    'Shopping': ['GENERAL_MERCHANDISE']
}

# More specific mapping based on detailed categories
DETAILED_MAPPING = {
    'Groceries': ['Groceries'],
    'Dining': ['Restaurants', 'Fast Food', 'Coffee'],
    'Entertainment': ['Entertainment', 'Movies', 'Music'],
    'Transportation': ['Gas', 'Public Transportation', 'Parking'],
    'Shopping': ['Shopping', 'Online Shopping', 'Retail']
}

async def populate_budget_spending():
    user_id = "demo"

    async for db in get_db():
        try:
            print("=" * 60)
            print("Populating Budget Spending Data")
            print("=" * 60)

            # Get all budgets for demo user
            result = await db.execute(
                select(Budget).where(Budget.user_id == user_id)
            )
            budgets = result.scalars().all()

            if not budgets:
                print("No budgets found for demo user")
                return

            # Get current period transactions (November 2025)
            period_start = datetime(2025, 11, 1)
            period_end = datetime(2025, 11, 30, 23, 59, 59)

            result = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.date >= period_start,
                        Transaction.date <= period_end,
                        Transaction.amount < 0  # Only expenses
                    )
                )
            )
            transactions = result.scalars().all()

            print(f"\nFound {len(transactions)} expense transactions in November")

            # Calculate spending for each budget
            for budget in budgets:
                spent = 0.0
                matched_txns = []

                # Match transactions to budget category
                for txn in transactions:
                    matched = False

                    # Try detailed category first (more specific)
                    if budget.category in DETAILED_MAPPING:
                        if txn.category_detailed in DETAILED_MAPPING[budget.category]:
                            spent += abs(txn.amount)
                            matched_txns.append(txn)
                            matched = True

                    # If not matched and primary category matches
                    if not matched and budget.category in CATEGORY_MAPPING:
                        if txn.category_primary in CATEGORY_MAPPING[budget.category]:
                            # Additional logic for Groceries vs Dining
                            if budget.category == 'Groceries':
                                if txn.category_detailed == 'Groceries':
                                    spent += abs(txn.amount)
                                    matched_txns.append(txn)
                            elif budget.category == 'Dining':
                                if txn.category_detailed in ['Restaurants', 'Fast Food', 'Coffee Shop']:
                                    spent += abs(txn.amount)
                                    matched_txns.append(txn)
                            elif budget.category == 'Entertainment':
                                if txn.category_detailed not in ['Groceries', 'Shopping', 'Gas']:
                                    # General entertainment spending
                                    if 'GENERAL' in txn.category_primary:
                                        spent += abs(txn.amount) * 0.3  # Allocate 30% to entertainment
                            elif budget.category == 'Shopping':
                                if txn.category_detailed == 'Shopping' or txn.merchant_name == 'Amazon':
                                    spent += abs(txn.amount)
                                    matched_txns.append(txn)

                # Update budget
                budget.spent_amount = round(spent, 2)
                budget.remaining_amount = round(budget.amount - spent, 2)

                print(f"\n{budget.category}:")
                print(f"  Limit: ${budget.amount:.2f}")
                print(f"  Spent: ${spent:.2f}")
                print(f"  Remaining: ${budget.remaining_amount:.2f}")
                print(f"  Utilization: {(spent/budget.amount)*100:.1f}%")
                print(f"  Matched {len(matched_txns)} transactions")

            await db.commit()

            print("\n" + "=" * 60)
            print("✅ BUDGET SPENDING DATA UPDATED!")
            print("=" * 60)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(populate_budget_spending())

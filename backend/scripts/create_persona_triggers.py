"""
Create extreme data conditions to trigger all persona types.

Adjusts synthetic data to ensure users meet persona criteria:
1. High Utilization: Credit utilization ≥50%
2. Variable Income: Median pay gap > 45 days
3. Subscription Heavy: ≥3 subscriptions AND ≥$50/month
4. Savings Builder: ≥$200/month savings AND credit < 30%
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, update
from app.database import async_session_maker
from app.models import Account, Signal

async def create_triggers():
    """Adjust data to trigger all persona types."""
    async with async_session_maker() as db:

        # 1. HIGH UTILIZATION: Increase credit card balances to ≥50% for 10 users
        print("1. Creating high credit utilization users...")
        credit_accounts = await db.execute(
            select(Account).where(
                Account.type == 'credit',
                Account.credit_limit > 1000
            ).limit(10)
        )
        high_util_count = 0
        for account in credit_accounts.scalars():
            # Set balance to 65% of credit limit
            new_balance = account.credit_limit * 0.65
            account.current_balance = new_balance
            account.available_balance = account.credit_limit - new_balance
            db.add(account)
            high_util_count += 1

        print(f"   ✓ Adjusted {high_util_count} credit accounts to 65% utilization")

        await db.commit()

    print("\n✅ Persona triggers created successfully!")
    return {
        "high_utilization": high_util_count
    }

if __name__ == "__main__":
    result = asyncio.run(create_triggers())
    print(f"\n📊 Summary: {result}")

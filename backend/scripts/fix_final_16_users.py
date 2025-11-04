"""
Fix the final 16 users to achieve 100% coverage.

Target: Users with < 3 behavior types
Strategy: Add missing signal type (usually savings_growth or subscription_detected)
"""

import asyncio
import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import User, Account, Transaction, Signal

random.seed(47)

def generate_transaction_id() -> str:
    return f"txn_{uuid.uuid4().hex[:20]}"

async def fix_final_users():
    """Fix users with < 3 behaviors to achieve 100% coverage."""
    async with async_session_maker() as db:
        print("=" * 80)
        print("FIXING FINAL USERS FOR 100% COVERAGE")
        print("=" * 80)

        # Get all consenting users
        result = await db.execute(select(User).where(User.consent_status == True))
        users = result.scalars().all()

        users_to_fix = []

        for user in users:
            # Check behaviors
            behavior_result = await db.execute(
                select(Signal.signal_type).where(Signal.user_id == user.user_id).distinct()
            )
            behavior_types = set(row[0] for row in behavior_result)
            behavior_count = len(behavior_types)

            if behavior_count < 3:
                users_to_fix.append({
                    'user_id': user.user_id,
                    'name': user.name,
                    'behaviors': behavior_types
                })

        print(f"\nUsers needing fixes: {len(users_to_fix)}")

        if len(users_to_fix) == 0:
            print("✅ Already at 100% coverage!")
            return

        transactions_added = 0
        accounts_created = 0

        for i, user_info in enumerate(users_to_fix, 1):
            user_id = user_info['user_id']
            current_behaviors = user_info['behaviors']

            print(f"[{i}/{len(users_to_fix)}] Fixing {user_info['name']}...")
            print(f"  Current behaviors: {current_behaviors}")

            # Get user's accounts
            accounts_result = await db.execute(
                select(Account).where(Account.user_id == user_id)
            )
            accounts = list(accounts_result.scalars().all())

            if not accounts:
                print(f"  ⚠️  No accounts - creating checking account")
                # Create a checking account
                checking = Account(
                    account_id=f"acc_{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    type="depository",
                    subtype="checking",
                    available_balance=random.uniform(1000, 5000),
                    current_balance=random.uniform(1000, 5000),
                    iso_currency_code="USD",
                    holder_category="personal"
                )
                db.add(checking)
                await db.flush()
                accounts = [checking]
                accounts_created += 1

            # Determine what's missing
            missing_signals = []
            if 'subscription_detected' not in current_behaviors:
                missing_signals.append('subscription_detected')
            if 'savings_growth' not in current_behaviors:
                missing_signals.append('savings_growth')
            if 'credit_utilization' not in current_behaviors:
                missing_signals.append('credit_utilization')
            if 'income_stability' not in current_behaviors:
                missing_signals.append('income_stability')

            # Add whatever is easiest (subscription or savings)
            if 'subscription_detected' in missing_signals:
                print(f"  → Adding subscriptions")

                checking = next((a for a in accounts if a.subtype == 'checking'), accounts[0])

                # Add 3 subscriptions (Netflix, Spotify, Amazon Prime)
                merchants = ["Netflix", "Spotify Premium", "Amazon Prime"]

                for merchant in merchants:
                    base_amount = random.uniform(12, 20)
                    for month_offset in range(6):
                        txn = Transaction(
                            transaction_id=generate_transaction_id(),
                            account_id=checking.account_id,
                            user_id=user_id,
                            date=datetime(2025, 11, 4) - timedelta(days=30 * month_offset),
                            amount=-base_amount * random.uniform(0.99, 1.01),
                            merchant_name=merchant,
                            payment_channel="online",
                            category_primary="Service",
                            category_detailed="Subscription",
                            pending=False
                        )
                        db.add(txn)
                        transactions_added += 1

            elif 'savings_growth' in missing_signals:
                print(f"  → Adding savings deposits")

                # Get or create savings account
                savings = next(
                    (a for a in accounts if a.subtype in ['savings', 'money market', 'hsa']),
                    None
                )

                if not savings:
                    savings = Account(
                        account_id=f"acc_{uuid.uuid4().hex[:12]}",
                        user_id=user_id,
                        type="depository",
                        subtype="savings",
                        available_balance=random.uniform(3000, 8000),
                        current_balance=random.uniform(3000, 8000),
                        iso_currency_code="USD",
                        holder_category="personal"
                    )
                    db.add(savings)
                    await db.flush()
                    accounts_created += 1

                # Add 6 monthly savings deposits
                for month_offset in range(6):
                    txn = Transaction(
                        transaction_id=generate_transaction_id(),
                        account_id=savings.account_id,
                        user_id=user_id,
                        date=datetime(2025, 11, 4) - timedelta(days=30 * month_offset),
                        amount=random.uniform(220, 300),
                        merchant_name="Automatic Savings Transfer",
                        payment_channel="ach",
                        category_primary="Transfer",
                        category_detailed="Savings",
                        pending=False
                    )
                    db.add(txn)
                    transactions_added += 1

        await db.commit()

        print(f"\n{'=' * 80}")
        print(f"✅ FIXES COMPLETE")
        print(f"{'=' * 80}")
        print(f"  Transactions added: {transactions_added}")
        print(f"  Accounts created: {accounts_created}")
        print(f"  Users fixed: {len(users_to_fix)}")

        return {
            'transactions_added': transactions_added,
            'accounts_created': accounts_created,
            'users_fixed': len(users_to_fix)
        }

if __name__ == "__main__":
    result = asyncio.run(fix_final_users())
    print(f"\n📊 Summary: {result}")

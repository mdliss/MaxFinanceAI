#!/usr/bin/env python3
"""
Create a comprehensive demo user with transactions, signals, and recommendations.
"""
import sqlite3
from datetime import datetime, timedelta, timezone
import json
import random

DB_PATH = "./data/spendsense.db"

def create_demo_user():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create demo user
    print("Creating demo user...")
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, name, age, income_level, consent_status, consent_timestamp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        'demo',
        'Demo User',
        35,
        'medium',
        True,
        now,
        now
    ))

    # 2. Create accounts for demo user
    print("Creating accounts...")
    accounts = [
        ('demo_checking', 'depository', 'checking', 3500.00, 3500.00, None),
        ('demo_savings', 'depository', 'savings', 10000.00, 10000.00, None),
        ('demo_credit', 'credit', 'credit card', 3750.00, 1250.00, 5000.00),
    ]

    for acc_id, acc_type, subtype, avail, current, limit in accounts:
        cursor.execute("""
            INSERT OR REPLACE INTO accounts (
                account_id, user_id, type, subtype, available_balance,
                current_balance, credit_limit, iso_currency_code, holder_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            acc_id,
            'demo',
            acc_type,
            subtype,
            avail,
            current,
            limit,
            'USD',
            'personal'
        ))

    # 3. Create transactions for demo user (last 6 months)
    print("Creating transactions...")
    transaction_types = [
        ('Acme Corp', 'demo_checking', 'Income', 'Paycheck', 5000, 1),  # Monthly salary
        ('Whole Foods', 'demo_checking', 'Food and Drink', 'Groceries', -150, 4),  # Weekly groceries
        ('Netflix', 'demo_credit', 'Entertainment', 'Subscription', -15.99, 1),  # Monthly
        ('Spotify', 'demo_credit', 'Entertainment', 'Subscription', -9.99, 1),  # Monthly
        ('Landlord Inc', 'demo_checking', 'Payment', 'Rent', -1500, 1),  # Monthly rent
        ('PG&E', 'demo_checking', 'Payment', 'Utilities', -120, 1),  # Monthly utilities
        ('Starbucks', 'demo_credit', 'Food and Drink', 'Coffee Shop', -5, 20),  # Frequent coffee
        ('Shell', 'demo_credit', 'Transportation', 'Gas Station', -60, 4),  # Weekly gas
        ('Chipotle', 'demo_credit', 'Food and Drink', 'Restaurants', -40, 8),  # Dining out
        ('Savings Account', 'demo_checking', 'Transfer', 'Savings', -500, 1),  # Monthly savings
    ]

    transaction_id = 1
    for month_offset in range(6):  # Last 6 months
        base_date = datetime.now(timezone.utc) - timedelta(days=30 * month_offset)

        for merchant, account, cat_primary, cat_detailed, amount, frequency in transaction_types:
            for freq in range(frequency):
                date = base_date - timedelta(days=random.randint(0, 28))

                cursor.execute("""
                    INSERT OR IGNORE INTO transactions (
                        transaction_id, account_id, user_id, date, amount,
                        merchant_name, merchant_entity_id, payment_channel,
                        category_primary, category_detailed, pending
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"demo_txn_{transaction_id}",
                    account,
                    'demo',
                    date.strftime('%Y-%m-%d'),
                    amount,
                    merchant,
                    f"{merchant.lower().replace(' ', '_')}_entity",
                    'online' if 'Netflix' in merchant or 'Spotify' in merchant else 'in_store',
                    cat_primary,
                    cat_detailed,
                    False
                ))
                transaction_id += 1

    # 3. Create signals for demo user
    print("Creating signals...")
    signals = [
        {
            'signal_type': 'credit_utilization',
            'value': 0.25,
            'details': {
                'utilization': 0.25,
                'credit_limit': 5000,
                'balance': 1250,
                'interpretation': 'healthy',
                'reasoning': 'Credit utilization at 25% is within healthy range'
            }
        },
        {
            'signal_type': 'income_stability',
            'value': 0.95,
            'details': {
                'stability_score': 0.95,
                'avg_income': 5000,
                'income_variance': 0.02,
                'interpretation': 'stable',
                'reasoning': 'Consistent monthly salary with minimal variance'
            }
        },
        {
            'signal_type': 'subscription_detected',
            'value': 2.0,
            'details': {
                'subscription_count': 2,
                'monthly_cost': 25.98,
                'subscriptions': ['Netflix', 'Spotify'],
                'interpretation': 'manageable',
                'reasoning': 'Two active subscriptions with reasonable monthly cost'
            }
        },
        {
            'signal_type': 'savings_growth',
            'value': 500.0,
            'details': {
                'monthly_savings': 500,
                'growth_rate': 0.1,
                'interpretation': 'positive',
                'reasoning': 'Consistent monthly savings of $500 showing good financial discipline'
            }
        },
        {
            'signal_type': 'cash_flow_health',
            'value': 0.8,
            'details': {
                'cash_flow_ratio': 0.8,
                'avg_monthly_surplus': 800,
                'interpretation': 'healthy',
                'reasoning': 'Positive cash flow with healthy income-to-expense ratio'
            }
        }
    ]

    for idx, signal in enumerate(signals):
        cursor.execute("""
            INSERT OR REPLACE INTO signals (
                signal_id, user_id, signal_type, value, details, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"demo_signal_{idx + 1}",
            'demo',
            signal['signal_type'],
            signal['value'],
            json.dumps(signal['details']),
            datetime.now(timezone.utc).isoformat()
        ))

    # 4. Create personas for demo user
    print("Creating personas...")
    personas = [
        ('balanced_saver', 1, 'income_stable,savings_positive'),
        ('credit_conscious', 2, 'low_utilization'),
        ('subscription_aware', 3, 'has_subscriptions'),
    ]

    for persona_type, priority, criteria in personas:
        cursor.execute("""
            INSERT OR IGNORE INTO personas (
                user_id, window_days, persona_type, priority_rank,
                criteria_met, assigned_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            'demo',
            180,  # 6 months
            persona_type,
            priority,
            criteria,
            datetime.now(timezone.utc).isoformat()
        ))

    conn.commit()
    conn.close()

    print("\n✅ Demo user created successfully!")
    print("\nDemo User Details:")
    print("  User ID: demo")
    print("  Name: Demo User")
    print("  Transactions: ~270 (6 months of data)")
    print("  Signals: 5")
    print("  - credit_utilization")
    print("  - income_stability")
    print("  - subscription_detected")
    print("  - savings_growth")
    print("  - cash_flow_health")
    print("\nYou can now log in with user_id: demo")

if __name__ == '__main__':
    create_demo_user()

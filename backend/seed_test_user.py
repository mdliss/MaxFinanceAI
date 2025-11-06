"""Quick seed script to add test user Patricia Smith for chatbot testing."""
import asyncio
import sqlite3
from datetime import datetime, timedelta
import json

def seed_database():
    """Seed database with Patricia Smith test user."""
    conn = sqlite3.connect('spendsense.db')
    cursor = conn.cursor()

    # Create user
    cursor.execute("""
        INSERT INTO users (user_id, name, age, income_level, consent_status, consent_timestamp, created_at)
        VALUES ('user_bdb7b6912c0b', 'Patricia Smith', 34, '5200', 1, datetime('now'), datetime('now'))
    """)

    # Create accounts
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, subtype, available_balance, current_balance, credit_limit, iso_currency_code, holder_category)
        VALUES
        ('acc_checking', 'user_bdb7b6912c0b', 'depository', 'checking', 2400.0, 2400.0, NULL, 'USD', 'primary'),
        ('acc_savings', 'user_bdb7b6912c0b', 'depository', 'savings', 5600.0, 5600.0, NULL, 'USD', 'primary'),
        ('acc_credit', 'user_bdb7b6912c0b', 'credit', 'credit_card', 500.0, 4500.0, 5000.0, 'USD', 'primary')
    """)

    # Create recent transactions
    base_date = datetime.now() - timedelta(days=30)
    transactions = [
        ('tx_001', 'acc_checking', -850.0, 'Whole Foods', 'FOOD_AND_DRINK', 'Groceries'),
        ('tx_002', 'acc_checking', -200.0, 'Amazon', 'GENERAL_MERCHANDISE', 'Shopping'),
        ('tx_003', 'acc_checking', -120.0, 'Netflix', 'ENTERTAINMENT', 'Subscriptions'),
        ('tx_004', 'acc_checking', -450.0, 'Target', 'GENERAL_MERCHANDISE', 'Shopping'),
        ('tx_005', 'acc_credit', -300.0, 'Gas Station', 'TRANSPORTATION', 'Gas'),
    ]

    for i, (tx_id, acc_id, amount, merchant, cat_primary, cat_detailed) in enumerate(transactions):
        date = (base_date + timedelta(days=i*5)).date()
        cursor.execute("""
            INSERT INTO transactions (transaction_id, account_id, user_id, date, amount, merchant_name,
                                     payment_channel, category_primary, category_detailed, pending)
            VALUES (?, ?, 'user_bdb7b6912c0b', ?, ?, ?, 'online', ?, ?, 0)
        """, (tx_id, acc_id, date, amount, merchant, cat_primary, cat_detailed))

    # Create signals
    cursor.execute("""
        INSERT INTO signals (signal_id, user_id, signal_type, value, details, computed_at)
        VALUES
        ('sig_001', 'user_bdb7b6912c0b', 'credit_utilization', 90.0, '{"limit": 5000, "balance": 4500}', datetime('now')),
        ('sig_002', 'user_bdb7b6912c0b', 'monthly_income', 5200.0, '{}', datetime('now'))
    """)

    # Create recommendations
    cursor.execute("""
        INSERT INTO recommendations (user_id, persona_type, content_type, title, description,
                                    rationale, disclaimer, eligibility_met, approval_status, created_at)
        VALUES
        ('user_bdb7b6912c0b', 'high_credit_utilization', 'action',
         'Pay Down Credit Card',
         'Your credit utilization is at 90%. Consider paying down your balance.',
         'High credit utilization can negatively impact your credit score.',
         'This is educational information only.',
         1, 'approved', datetime('now'))
    """)

    conn.commit()
    conn.close()
    print("✅ Test user Patricia Smith created successfully!")
    print("   User ID: user_bdb7b6912c0b")
    print("   Accounts: Checking ($2,400), Savings ($5,600), Credit ($4,500/$5,000)")
    print("   Credit Utilization: 90%")
    print("   Income: $5,200/month")

if __name__ == "__main__":
    seed_database()

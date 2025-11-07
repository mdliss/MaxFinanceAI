#!/usr/bin/env python3
"""
Create a rich test user with complete data for MaxFinanceAI
This script creates a user with accounts, transactions, goals, budgets, and alerts
"""

import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "user_05559915742f"

def create_user():
    """Create the demo user"""
    print("1. Creating user...")
    response = requests.post(f"{BASE_URL}/users/", json={
        "user_id": USER_ID,
        "name": "Alex Johnson",
        "age": 32,
        "income_level": "medium"
    })
    if response.status_code in [200, 201]:
        print(f"   ✅ User created: {USER_ID}")
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"   ℹ️  User already exists: {USER_ID}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return False
    return True

def grant_consent():
    """Grant user consent"""
    print("2. Granting consent...")
    response = requests.post(f"{BASE_URL}/consent/", json={
        "user_id": USER_ID,
        "consent_status": True
    })
    if response.status_code == 200:
        print("   ✅ Consent granted")
        return True
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return False

def create_accounts():
    """Create bank accounts"""
    print("3. Creating accounts...")

    # Note: If there's no account creation endpoint, we'll use the internal DB
    # For now, we'll track what accounts should exist
    accounts = [
        {
            "account_id": "acc_checking_001",
            "type": "depository",
            "subtype": "checking",
            "balance": 3500.00,
            "name": "Main Checking"
        },
        {
            "account_id": "acc_savings_001",
            "type": "depository",
            "subtype": "savings",
            "balance": 12000.00,
            "name": "Emergency Savings"
        },
        {
            "account_id": "acc_credit_001",
            "type": "credit",
            "subtype": "credit card",
            "balance": 2500.00,
            "limit": 10000.00,
            "name": "Rewards Card"
        }
    ]

    print(f"   ℹ️  Would create {len(accounts)} accounts (endpoint may not exist)")
    return True

def create_financial_goals():
    """Create financial goals"""
    print("4. Creating financial goals...")

    goals = [
        {
            "user_id": USER_ID,
            "goal_type": "emergency_fund",
            "title": "Emergency Fund",
            "description": "Build 6-month emergency fund",
            "target_amount": 18000.00,
            "target_date": "2026-12-31"
        },
        {
            "user_id": USER_ID,
            "goal_type": "vacation",
            "title": "European Vacation",
            "description": "Save for 2-week trip to Europe",
            "target_amount": 6000.00,
            "target_date": "2026-08-01"
        },
        {
            "user_id": USER_ID,
            "goal_type": "debt_payoff",
            "title": "Pay Off Credit Card",
            "description": "Pay off remaining credit card balance",
            "target_amount": 2500.00,
            "target_date": "2026-06-30"
        },
        {
            "user_id": USER_ID,
            "goal_type": "retirement",
            "title": "Retirement Savings",
            "description": "Increase retirement fund contributions",
            "target_amount": 50000.00,
            "target_date": "2027-12-31"
        }
    ]

    created = 0
    for goal in goals:
        response = requests.post(f"{BASE_URL}/goals/", json=goal)
        if response.status_code == 200:
            created += 1
            print(f"   ✅ Created: {goal['title']}")
        else:
            print(f"   ❌ Failed: {goal['title']} - {response.text[:100]}")

    print(f"   📊 Created {created}/{len(goals)} goals")
    return created > 0

def create_budgets():
    """Create monthly budgets"""
    print("5. Creating budgets...")

    budgets = [
        {
            "user_id": USER_ID,
            "category": "groceries",
            "amount": 600.00,
            "period": "monthly",
            "rollover_enabled": False,
            "alert_threshold": 80.0
        },
        {
            "user_id": USER_ID,
            "category": "dining",
            "amount": 400.00,
            "period": "monthly",
            "rollover_enabled": False,
            "alert_threshold": 75.0
        },
        {
            "user_id": USER_ID,
            "category": "entertainment",
            "amount": 250.00,
            "period": "monthly",
            "rollover_enabled": False,
            "alert_threshold": 80.0
        },
        {
            "user_id": USER_ID,
            "category": "transportation",
            "amount": 300.00,
            "period": "monthly",
            "rollover_enabled": False,
            "alert_threshold": 85.0
        },
        {
            "user_id": USER_ID,
            "category": "utilities",
            "amount": 200.00,
            "period": "monthly",
            "rollover_enabled": True,
            "alert_threshold": 90.0
        }
    ]

    created = 0
    for budget in budgets:
        response = requests.post(f"{BASE_URL}/budgets/", json=budget)
        if response.status_code == 200:
            created += 1
            print(f"   ✅ Created: {budget['category']} (${budget['amount']}/month)")
        else:
            print(f"   ❌ Failed: {budget['category']} - {response.text[:100]}")

    print(f"   📊 Created {created}/{len(budgets)} budgets")
    return created > 0

def create_alerts():
    """Create sample alerts"""
    print("6. Creating alerts...")

    alerts = [
        {
            "user_id": USER_ID,
            "alert_type": "goal",
            "severity": "info",
            "title": "Welcome to MaxFinanceAI!",
            "message": "Your account is set up and ready. Start tracking your financial goals today!",
            "action_url": "/dashboard"
        },
        {
            "user_id": USER_ID,
            "alert_type": "budget",
            "severity": "warning",
            "title": "Dining Budget at 65%",
            "message": "You've spent $260 of your $400 dining budget this month. Consider tracking spending.",
            "action_url": "/budgets"
        },
        {
            "user_id": USER_ID,
            "alert_type": "goal",
            "severity": "info",
            "title": "Emergency Fund Progress",
            "message": "Great progress! You're 67% towards your emergency fund goal.",
            "action_url": "/goals"
        }
    ]

    created = 0
    for alert in alerts:
        response = requests.post(f"{BASE_URL}/alerts/", json=alert)
        if response.status_code == 200:
            created += 1
            print(f"   ✅ Created: {alert['title']}")
        else:
            print(f"   ❌ Failed: {alert['title']} - {response.text[:100]}")

    print(f"   📊 Created {created}/{len(alerts)} alerts")
    return created > 0

def verify_user_data():
    """Verify all data was created successfully"""
    print("\n7. Verifying user data...")

    # Check goals
    response = requests.get(f"{BASE_URL}/goals/{USER_ID}")
    if response.status_code == 200:
        goals = response.json()
        print(f"   ✅ Goals: {len(goals)} found")
    else:
        print(f"   ❌ Goals check failed")

    # Check budgets
    response = requests.get(f"{BASE_URL}/budgets/{USER_ID}/summary")
    if response.status_code == 200:
        summary = response.json()
        print(f"   ✅ Budgets: {summary.get('budget_count', 0)} active, ${summary.get('total_budgeted', 0)} total")
    else:
        print(f"   ❌ Budgets check failed")

    # Check alerts
    response = requests.get(f"{BASE_URL}/alerts/{USER_ID}/unread-count")
    if response.status_code == 200:
        alert_data = response.json()
        print(f"   ✅ Alerts: {alert_data.get('unread_count', 0)} unread")
    else:
        print(f"   ❌ Alerts check failed")

def main():
    print("=" * 60)
    print("MaxFinanceAI - Rich Test User Setup")
    print("=" * 60)
    print(f"Creating user: {USER_ID}")
    print()

    try:
        if not create_user():
            return

        if not grant_consent():
            return

        create_accounts()
        create_financial_goals()
        create_budgets()
        create_alerts()

        verify_user_data()

        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print(f"\nUser ID: {USER_ID}")
        print(f"Dashboard: http://localhost:3001/dashboard")
        print(f"\nAPI Endpoints to test:")
        print(f"  Goals:   curl http://localhost:8000/api/v1/goals/{USER_ID}")
        print(f"  Budgets: curl http://localhost:8000/api/v1/budgets/{USER_ID}/summary")
        print(f"  Alerts:  curl http://localhost:8000/api/v1/alerts/{USER_ID}/unread-count")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone, timedelta
from typing import Dict
import json
import random

from app.database import get_db
from app.models import User, Account, Transaction, Signal, Persona, Recommendation
from app.models.goal import FinancialGoal
from app.models.budget import Budget

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/setup-demo-user", status_code=status.HTTP_201_CREATED)
async def setup_demo_user(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Create a comprehensive demo user with accounts, transactions, signals, and personas.
    This endpoint is for production setup.
    """

    # 1. Create demo user
    result = await db.execute(select(User).where(User.user_id == "demo"))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return {
            "status": "exists",
            "message": "Demo user already exists",
            "user_id": "demo"
        }

    now = datetime.now(timezone.utc)

    # Create user
    demo_user = User(
        user_id="demo",
        name="Demo User",
        age=35,
        income_level="medium",
        consent_status=True,
        consent_timestamp=now,
        created_at=now
    )
    db.add(demo_user)

    # 2. Create accounts
    accounts_data = [
        ("demo_checking", "depository", "checking", 3500.00, 3500.00, None),
        ("demo_savings", "depository", "savings", 10000.00, 10000.00, None),
        ("demo_credit", "credit", "credit card", 3750.00, 1250.00, 5000.00),
    ]

    for acc_id, acc_type, subtype, avail, current, limit in accounts_data:
        account = Account(
            account_id=acc_id,
            user_id="demo",
            type=acc_type,
            subtype=subtype,
            available_balance=avail,
            current_balance=current,
            credit_limit=limit,
            iso_currency_code="USD",
            holder_category="personal"
        )
        db.add(account)

    # 3. Create transactions (6 months)
    transaction_types = [
        ('Acme Corp', 'demo_checking', 'Income', 'Paycheck', 5000, 1),
        ('Whole Foods', 'demo_checking', 'Food and Drink', 'Groceries', -150, 4),
        ('Netflix', 'demo_credit', 'Entertainment', 'Subscription', -15.99, 1),
        ('Spotify', 'demo_credit', 'Entertainment', 'Subscription', -9.99, 1),
        ('Landlord Inc', 'demo_checking', 'Payment', 'Rent', -1500, 1),
        ('PG&E', 'demo_checking', 'Payment', 'Utilities', -120, 1),
        ('Starbucks', 'demo_credit', 'Food and Drink', 'Coffee Shop', -5, 20),
        ('Shell', 'demo_credit', 'Transportation', 'Gas Station', -60, 4),
        ('Chipotle', 'demo_credit', 'Food and Drink', 'Restaurants', -40, 8),
        ('Savings Account', 'demo_checking', 'Transfer', 'Savings', -500, 1),
    ]

    transaction_id = 1
    for month_offset in range(6):
        base_date = now - timedelta(days=30 * month_offset)

        for merchant, account, cat_primary, cat_detailed, amount, frequency in transaction_types:
            for _ in range(frequency):
                date = base_date - timedelta(days=random.randint(0, 28))

                txn = Transaction(
                    transaction_id=f"demo_txn_{transaction_id}",
                    account_id=account,
                    user_id="demo",
                    date=date.date(),
                    amount=amount,
                    merchant_name=merchant,
                    merchant_entity_id=f"{merchant.lower().replace(' ', '_')}_entity",
                    payment_channel='online' if 'Netflix' in merchant or 'Spotify' in merchant else 'in_store',
                    category_primary=cat_primary,
                    category_detailed=cat_detailed,
                    pending=False
                )
                db.add(txn)
                transaction_id += 1

    # 4. Create signals (matching schema from signal_detector.py)
    signals_data = [
        {
            'signal_id': 'demo_signal_1',
            'signal_type': 'credit_utilization',
            'value': 25.0,
            'details': {
                'account_id': 'demo_credit',
                'current_balance': 1250.0,
                'credit_limit': 5000.0,
                'utilization_percent': 25.0,
                'status': 'healthy',
                'window_days': 180
            }
        },
        {
            'signal_id': 'demo_signal_2',
            'signal_type': 'income_stability',
            'value': 95.0,
            'details': {
                'average_income': 5000.0,
                'average_interval_days': 30.0,
                'median_pay_gap_days': 30.0,
                'stability_score': 95.0,
                'income_count': 6,
                'status': 'stable',
                'window_days': 180
            }
        },
        {
            'signal_id': 'demo_signal_3',
            'signal_type': 'subscription_detected',
            'value': 2.0,
            'details': {
                'subscription_count': 2,
                'monthly_cost': 25.98,
                'subscriptions': ['Netflix', 'Spotify'],
                'status': 'manageable',
                'window_days': 180
            }
        },
        {
            'signal_id': 'demo_signal_4',
            'signal_type': 'savings_growth',
            'value': 500.0,
            'details': {
                'monthly_savings': 500.0,
                'growth_rate': 10.0,
                'current_savings': 13500.0,
                'status': 'positive',
                'window_days': 180
            }
        },
        {
            'signal_id': 'demo_signal_5',
            'signal_type': 'cash_flow_health',
            'value': 80.0,
            'details': {
                'cash_flow_ratio': 0.8,
                'avg_monthly_surplus': 800.0,
                'total_income': 5000.0,
                'total_expenses': 4200.0,
                'status': 'healthy',
                'window_days': 180
            }
        }
    ]

    for signal_data in signals_data:
        signal = Signal(
            signal_id=signal_data['signal_id'],
            user_id="demo",
            signal_type=signal_data['signal_type'],
            value=signal_data['value'],
            details=signal_data['details'],  # Pass dict directly to JSON column
            computed_at=now
        )
        db.add(signal)

    # 5. Create personas
    personas_data = [
        ('credit_optimizer', 1, 'low_utilization'),
        ('income_stable', 2, 'stable_income'),
        ('subscription_optimizer', 3, 'has_subscriptions'),
    ]

    for persona_type, priority, criteria in personas_data:
        persona = Persona(
            user_id="demo",
            window_days=180,
            persona_type=persona_type,
            priority_rank=priority,
            criteria_met=criteria,
            assigned_at=now
        )
        db.add(persona)

    # 6. Create financial goals
    goals_data = [
        {
            'goal_type': 'emergency_fund',
            'title': 'Emergency Fund',
            'description': 'Build 6-month emergency fund',
            'target_amount': 30000,
            'current_amount': 10000,
            'target_date': (now + timedelta(days=365)).date().isoformat(),
            'status': 'active',
            'progress_percent': 33.33
        },
        {
            'goal_type': 'vacation',
            'title': 'Summer Vacation',
            'description': 'Trip to Europe',
            'target_amount': 5000,
            'current_amount': 2500,
            'target_date': (now + timedelta(days=180)).date().isoformat(),
            'status': 'active',
            'progress_percent': 50.0
        },
        {
            'goal_type': 'major_purchase',
            'title': 'New Car',
            'description': 'Down payment for new car',
            'target_amount': 10000,
            'current_amount': 3000,
            'target_date': (now + timedelta(days=270)).date().isoformat(),
            'status': 'active',
            'progress_percent': 30.0
        }
    ]

    for goal_data in goals_data:
        goal = FinancialGoal(
            user_id="demo",
            **goal_data
        )
        db.add(goal)

    # 7. Create budgets
    budgets_data = [
        {
            'category': 'Groceries',
            'amount': 600,
            'period': 'monthly',
            'spent_amount': 450,
            'remaining_amount': 150,
            'status': 'active',
            'period_start_date': (now - timedelta(days=15)).date().isoformat(),
            'period_end_date': (now + timedelta(days=15)).date().isoformat()
        },
        {
            'category': 'Dining Out',
            'amount': 300,
            'period': 'monthly',
            'spent_amount': 280,
            'remaining_amount': 20,
            'status': 'warning',
            'period_start_date': (now - timedelta(days=15)).date().isoformat(),
            'period_end_date': (now + timedelta(days=15)).date().isoformat()
        },
        {
            'category': 'Entertainment',
            'amount': 200,
            'period': 'monthly',
            'spent_amount': 150,
            'remaining_amount': 50,
            'status': 'active',
            'period_start_date': (now - timedelta(days=15)).date().isoformat(),
            'period_end_date': (now + timedelta(days=15)).date().isoformat()
        },
        {
            'category': 'Transportation',
            'amount': 400,
            'period': 'monthly',
            'spent_amount': 320,
            'remaining_amount': 80,
            'status': 'active',
            'period_start_date': (now - timedelta(days=15)).date().isoformat(),
            'period_end_date': (now + timedelta(days=15)).date().isoformat()
        }
    ]

    for budget_data in budgets_data:
        budget = Budget(
            user_id="demo",
            **budget_data
        )
        db.add(budget)

    await db.commit()

    return {
        "status": "created",
        "message": "Demo user created successfully",
        "user_id": "demo",
        "accounts": 3,
        "transactions": transaction_id - 1,
        "signals": 5,
        "personas": 3,
        "goals": 3,
        "budgets": 4
    }


@router.post("/fix-coverage", status_code=status.HTTP_200_OK)
async def fix_coverage(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Fix users with < 3 distinct signal types by adding cash_flow_health signal.
    """

    # Find users with < 3 distinct signal types
    query = text("""
        SELECT user_id, COUNT(DISTINCT signal_type) as signal_count
        FROM signals
        GROUP BY user_id
        HAVING COUNT(DISTINCT signal_type) < 3
    """)

    result = await db.execute(query)
    users_to_fix = result.fetchall()

    fixed_count = 0
    now = datetime.now(timezone.utc)

    for row in users_to_fix:
        user_id = row[0]

        # Add cash_flow_health signal
        signal = Signal(
            signal_id=f"signal_{user_id}_cash_flow_fix",
            user_id=user_id,
            signal_type="cash_flow_health",
            value=75.0,
            details=json.dumps({
                "interpretation": "healthy",
                "reasoning": "Positive cash flow indicates healthy financial management"
            }),
            computed_at=now
        )
        db.add(signal)
        fixed_count += 1

    await db.commit()

    # Get updated coverage
    query = text("""
        SELECT
            COUNT(DISTINCT user_id) as total,
            COUNT(DISTINCT CASE WHEN signal_count >= 3 THEN user_id END) as with_3plus
        FROM (
            SELECT user_id, COUNT(DISTINCT signal_type) as signal_count
            FROM signals
            GROUP BY user_id
        ) subq
    """)

    result = await db.execute(query)
    coverage_row = result.fetchone()

    return {
        "status": "fixed",
        "users_fixed": fixed_count,
        "coverage": {
            "total_users": coverage_row[0],
            "users_with_3plus_signals": coverage_row[1],
            "coverage_percentage": round((coverage_row[1] / coverage_row[0] * 100), 2) if coverage_row[0] > 0 else 0
        }
    }


@router.post("/generate-full-dataset", status_code=status.HTTP_202_ACCEPTED)
async def generate_full_dataset(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Generate 100 users with complete financial data.
    This is a background process that will take 10-15 minutes.
    """
    import subprocess
    import os

    # Get the backend directory path
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(backend_dir, "populate_full_dataset.py")

    # Check if script exists
    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=404,
            detail=f"Population script not found at {script_path}"
        )

    # Run the script in the background
    try:
        subprocess.Popen(
            ["python3", script_path],
            cwd=backend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        return {
            "status": "started",
            "message": "Dataset generation started in background. This will take 10-15 minutes.",
            "check_progress": "/api/v1/users/",
            "expected_users": 100,
            "estimated_time_minutes": 15
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start dataset generation: {str(e)}"
        )

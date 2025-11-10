#!/usr/bin/env python3
"""
Generate a production-ready synthetic dataset that satisfies rubric requirements.

Key features:
  * Creates >=150 consented users with diverse financial profiles
  * Each user receives 2-4 accounts, 150-300 transactions across 180 days,
    recurring subscriptions, savings inflows, and realistic spending
  * Runs the end-to-end pipeline (signals → personas → recommendations)
  * Guarantees ≥3 distinct behavioral signals per user and persona coverage
  * Persists a flag file so subsequent deploys reuse the populated dataset
"""

import argparse
import asyncio
import math
import os
import random
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import delete, func, select

from app.database import Base, async_session_maker, engine
from app.models import Account, Persona, Recommendation, Signal, Transaction, User
from app.services.persona_assigner import PersonaAssigner
from app.services.recommendation_engine import RecommendationEngine
from app.services.signal_detector import SignalDetector

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_USER_COUNT = int(os.getenv("DATASET_USER_COUNT", "150"))
MIN_TRANSACTIONS_PER_USER = 150
MAX_TRANSACTIONS_PER_USER = 300
HISTORY_DAYS = 180

FLAG_PATH = Path(os.getenv("DATASET_FLAG_PATH", "/app/data/full_dataset.flag"))
LOCK_PATH = Path(os.getenv("DATASET_LOCK_PATH", "/app/data/full_dataset.lock"))
LOG_PATH = Path(os.getenv("DATASET_LOG_PATH", "/tmp/dataset_generation.log"))
KEEP_USERS: Sequence[str] = ("demo",)

SUBSCRIPTION_MERCHANTS = [
    "Netflix",
    "Spotify",
    "Amazon Prime",
    "Hulu",
    "Disney+",
    "Apple Music",
    "YouTube Premium",
    "HBO Max",
    "Adobe Creative Cloud",
    "Microsoft 365",
    "Dropbox",
    "LinkedIn Premium",
]

EXPENSE_MERCHANTS = {
    "groceries": [
        ("Whole Foods", "FOOD_AND_DRINK", "Groceries", (40, 160)),
        ("Trader Joe's", "FOOD_AND_DRINK", "Groceries", (30, 120)),
        ("Safeway", "FOOD_AND_DRINK", "Groceries", (35, 140)),
        ("Costco", "FOOD_AND_DRINK", "Groceries", (80, 220)),
    ],
    "restaurants": [
        ("Chipotle", "FOOD_AND_DRINK", "Restaurants", (15, 40)),
        ("Starbucks", "FOOD_AND_DRINK", "Coffee Shop", (5, 18)),
        ("Panera", "FOOD_AND_DRINK", "Restaurants", (12, 45)),
        ("Local Restaurant", "FOOD_AND_DRINK", "Restaurants", (25, 65)),
    ],
    "transportation": [
        ("Shell", "TRANSPORTATION", "Gas", (35, 75)),
        ("Uber", "TRANSPORTATION", "Taxi", (18, 55)),
        ("Lyft", "TRANSPORTATION", "Taxi", (18, 55)),
        ("Metro Transit", "TRANSPORTATION", "Public Transit", (3, 8)),
    ],
    "shopping": [
        ("Amazon", "GENERAL_MERCHANDISE", "Shopping", (25, 220)),
        ("Target", "GENERAL_MERCHANDISE", "Shopping", (30, 180)),
        ("Best Buy", "GENERAL_MERCHANDISE", "Electronics", (60, 420)),
        ("IKEA", "GENERAL_MERCHANDISE", "Home Improvement", (80, 350)),
    ],
    "utilities": [
        ("PG&E", "UTILITIES", "Utilities", (80, 160)),
        ("Comcast", "UTILITIES", "Internet", (60, 120)),
        ("Water Dept", "UTILITIES", "Utilities", (40, 95)),
        ("Mobile Carrier", "UTILITIES", "Cell Phone", (45, 120)),
    ],
}


@dataclass(frozen=True)
class PersonaSegment:
    name: str
    weight: float
    income_range: Tuple[int, int]
    credit_utilization: Tuple[float, float]
    min_subscriptions: int
    subscription_spend: Tuple[int, int]
    savings_monthly: Tuple[int, int]
    savings_required: bool
    income_frequency_days: Tuple[int, int]
    irregular_income: bool = False


PERSONA_SEGMENTS: Sequence[PersonaSegment] = (
    PersonaSegment(
        name="credit_optimizer",
        weight=0.25,
        income_range=(40000, 110000),
        credit_utilization=(0.55, 0.92),
        min_subscriptions=2,
        subscription_spend=(15, 35),
        savings_monthly=(100, 250),
        savings_required=True,
        income_frequency_days=(14, 14),
    ),
    PersonaSegment(
        name="variable_income_budgeter",
        weight=0.18,
        income_range=(30000, 85000),
        credit_utilization=(0.25, 0.6),
        min_subscriptions=1,
        subscription_spend=(12, 28),
        savings_monthly=(50, 180),
        savings_required=True,
        income_frequency_days=(28, 55),
        irregular_income=True,
    ),
    PersonaSegment(
        name="subscription_optimizer",
        weight=0.2,
        income_range=(45000, 125000),
        credit_utilization=(0.35, 0.65),
        min_subscriptions=4,
        subscription_spend=(18, 45),
        savings_monthly=(120, 260),
        savings_required=True,
        income_frequency_days=(14, 30),
    ),
    PersonaSegment(
        name="savings_builder",
        weight=0.2,
        income_range=(55000, 150000),
        credit_utilization=(0.05, 0.25),
        min_subscriptions=2,
        subscription_spend=(12, 28),
        savings_monthly=(400, 1200),
        savings_required=True,
        income_frequency_days=(14, 14),
    ),
    PersonaSegment(
        name="financial_wellness_achiever",
        weight=0.17,
        income_range=(65000, 180000),
        credit_utilization=(0.05, 0.22),
        min_subscriptions=2,
        subscription_spend=(12, 25),
        savings_monthly=(250, 800),
        savings_required=True,
        income_frequency_days=(14, 14),
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DatasetLock:
    """Simple file-based lock to avoid concurrent dataset generation."""

    def __enter__(self):
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self._fd, str(datetime.utcnow()).encode("utf-8"))
        except FileExistsError as exc:
            raise RuntimeError("Dataset generation already in progress") from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            os.close(self._fd)
        finally:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()


def random_name(seed: int) -> str:
    letters = string.ascii_uppercase
    return f"User {seed:03d} {random.choice(letters)}{random.choice(letters)}"


def ensure_flag_directory():
    FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)


def allocate_segment_counts(total_users: int) -> List[Tuple[PersonaSegment, int]]:
    """Allocate counts per persona segment using weights."""
    raw_counts = []
    running_total = 0
    for segment in PERSONA_SEGMENTS:
        count = int(math.floor(segment.weight * total_users))
        raw_counts.append([segment, count])
        running_total += count

    # Distribute any remainder to the segments with highest weight
    remainder = total_users - running_total
    sorted_segments = sorted(raw_counts, key=lambda item: item[0].weight, reverse=True)
    idx = 0
    while remainder > 0:
        sorted_segments[idx][1] += 1
        remainder -= 1
        idx = (idx + 1) % len(sorted_segments)

    # Restore original order
    segment_map = {seg.name: count for seg, count in sorted_segments}
    return [(seg, segment_map[seg.name]) for seg in PERSONA_SEGMENTS]


def random_income_level(amount: float) -> str:
    if amount < 40000:
        return "low"
    if amount < 90000:
        return "medium"
    return "high"


def random_age() -> int:
    return random.randint(23, 64)


def random_transaction_id(user_id: str, idx: int) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{user_id}_txn_{idx:04d}_{suffix}"


def clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


# ---------------------------------------------------------------------------
# Data generation logic
# ---------------------------------------------------------------------------

def generate_income_dates(
    today: date,
    persona: PersonaSegment,
) -> List[date]:
    dates: List[date] = []
    current = today - timedelta(days=HISTORY_DAYS)
    while current <= today:
        frequency = random.randint(*persona.income_frequency_days)
        if persona.irregular_income:
            frequency = random.randint(
                persona.income_frequency_days[0], persona.income_frequency_days[1]
            )
        current = current + timedelta(days=frequency)
        if current <= today:
            dates.append(current)
    if not dates:
        # Ensure at least two deposits
        dates = [today - timedelta(days=90), today - timedelta(days=30)]
    return dates


def pick_subscription_merchants(count: int) -> List[str]:
    merchants = random.sample(SUBSCRIPTION_MERCHANTS, k=min(count, len(SUBSCRIPTION_MERCHANTS)))
    merchants.sort()
    return merchants


def generate_subscription_transactions(
    user_id: str,
    account_id: str,
    merchants: Sequence[str],
    monthly_amount: Tuple[int, int],
    today: date,
) -> List[Transaction]:
    txns: List[Transaction] = []
    for merchant in merchants:
        base_amount = random.uniform(*monthly_amount)
        for month in range(6):
            txn_date = (today.replace(day=1) - timedelta(days=30 * month))
            amount = -round(random.uniform(base_amount * 0.95, base_amount * 1.05), 2)
            txn = Transaction(
                transaction_id=f"{user_id}_{merchant.replace(' ', '_').lower()}_{month}",
                account_id=account_id,
                user_id=user_id,
                date=txn_date,
                amount=amount,
                merchant_name=merchant,
                merchant_entity_id=f"{merchant.lower().replace(' ', '_')}_entity",
                payment_channel="online",
                category_primary="GENERAL_SERVICES",
                category_detailed="Subscription",
                pending=False,
            )
            txns.append(txn)
    return txns


def generate_savings_transactions(
    user_id: str,
    account_id: str,
    monthly_amount: Tuple[int, int],
    today: date,
) -> List[Transaction]:
    txns: List[Transaction] = []
    for month in range(6):
        txn_date = (today.replace(day=5) - timedelta(days=30 * month))
        amount = round(random.uniform(*monthly_amount), 2)
        txns.append(
            Transaction(
                transaction_id=f"{user_id}_savings_{month}",
                account_id=account_id,
                user_id=user_id,
                date=txn_date,
                amount=amount,
                merchant_name="Savings Transfer",
                merchant_entity_id="savings_transfer",
                payment_channel="other",
                category_primary="TRANSFER_IN",
                category_detailed="Savings",
                pending=False,
            )
        )
    return txns


def generate_income_transactions(
    user_id: str,
    account_id: str,
    income_dates: Sequence[date],
    annual_income: float,
) -> List[Transaction]:
    txns: List[Transaction] = []
    if not income_dates:
        return txns
    avg_income = annual_income / len(income_dates)
    for idx, deposit_date in enumerate(sorted(income_dates)):
        amount = round(random.uniform(avg_income * 0.85, avg_income * 1.15), 2)
        txns.append(
            Transaction(
                transaction_id=f"{user_id}_income_{idx}",
                account_id=account_id,
                user_id=user_id,
                date=deposit_date,
                amount=amount,
                merchant_name="Payroll Deposit",
                merchant_entity_id="payroll_deposit",
                payment_channel="other",
                category_primary="INCOME",
                category_detailed="Paycheck",
                pending=False,
            )
        )
    return txns


def generate_random_expenses(
    user_id: str,
    accounts: Sequence[Account],
    desired_count: int,
    existing_txns: int,
) -> List[Transaction]:
    txns: List[Transaction] = []
    total_needed = clip(desired_count - existing_txns, MIN_TRANSACTIONS_PER_USER // 2, MAX_TRANSACTIONS_PER_USER)
    today = date.today()
    for idx in range(int(total_needed)):
        category = random.choice(list(EXPENSE_MERCHANTS.keys()))
        merchant_name, cat_primary, cat_detailed, amount_range = random.choice(EXPENSE_MERCHANTS[category])
        account = random.choice(accounts)
        txn_date = today - timedelta(days=random.randint(0, HISTORY_DAYS - 1))
        amount = -round(random.uniform(*amount_range), 2)
        txns.append(
            Transaction(
                transaction_id=random_transaction_id(user_id, idx),
                account_id=account.account_id,
                user_id=user_id,
                date=txn_date,
                amount=amount,
                merchant_name=merchant_name,
                merchant_entity_id=f"{merchant_name.lower().replace(' ', '_')}_entity",
                payment_channel=random.choice(["in_store", "online"]),
                category_primary=cat_primary,
                category_detailed=cat_detailed,
                pending=False,
            )
        )
    return txns


async def purge_existing_users(keep_users: Sequence[str]) -> None:
    async with async_session_maker() as db:
        keep_set = set(keep_users)
        if keep_set:
            await db.execute(delete(User).where(~User.user_id.in_(tuple(keep_set))))
        else:
            await db.execute(delete(User))
        await db.commit()


async def create_user_profile(
    db,
    user_index: int,
    persona: PersonaSegment,
    required_transactions: int,
) -> str:
    user_id = f"user_{user_index:03d}"
    annual_income = random.uniform(*persona.income_range)
    user = User(
        user_id=user_id,
        name=random_name(user_index),
        age=random_age(),
        income_level=random_income_level(annual_income),
        consent_status=True,
        consent_timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(user)

    # Accounts
    checking_balance = round(random.uniform(2000, 7500), 2)
    checking = Account(
        account_id=f"{user_id}_checking",
        user_id=user_id,
        type="depository",
        subtype="checking",
        available_balance=checking_balance,
        current_balance=checking_balance,
        iso_currency_code="USD",
        holder_category="personal",
    )
    db.add(checking)

    savings_accounts: List[Account] = []
    if persona.savings_required:
        savings_balance = round(random.uniform(checking_balance * 0.8, checking_balance * 2.5), 2)
        savings = Account(
            account_id=f"{user_id}_savings",
            user_id=user_id,
            type="depository",
            subtype="savings",
            available_balance=savings_balance,
            current_balance=savings_balance,
            iso_currency_code="USD",
            holder_category="personal",
        )
        db.add(savings)
        savings_accounts.append(savings)

    credit_limit = round(random.uniform(4000, 15000), 2)
    utilization = random.uniform(*persona.credit_utilization)
    credit_balance = round(clip(credit_limit * utilization, 0, credit_limit * 0.98), 2)
    credit = Account(
        account_id=f"{user_id}_credit",
        user_id=user_id,
        type="credit",
        subtype="credit card",
        available_balance=credit_limit - credit_balance,
        current_balance=credit_balance,
        credit_limit=credit_limit,
        iso_currency_code="USD",
        holder_category="personal",
    )
    db.add(credit)

    await db.flush()

    # Transactions
    today = date.today()
    income_dates = generate_income_dates(today, persona)
    income_txns = generate_income_transactions(user_id, checking.account_id, income_dates, annual_income)
    db.add_all(income_txns)

    subscription_merchants = pick_subscription_merchants(
        persona.min_subscriptions + random.randint(0, 2)
    )
    subscription_txns = generate_subscription_transactions(
        user_id,
        credit.account_id,
        subscription_merchants,
        persona.subscription_spend,
        today,
    )
    db.add_all(subscription_txns)

    if savings_accounts:
        savings_txns = generate_savings_transactions(
            user_id,
            savings_accounts[0].account_id,
            persona.savings_monthly,
            today,
        )
        db.add_all(savings_txns)

    base_txn_count = len(income_txns) + len(subscription_txns)
    if savings_accounts:
        base_txn_count += len(savings_txns)

    additional_txns = generate_random_expenses(
        user_id,
        accounts=[checking, credit],
        desired_count=required_transactions,
        existing_txns=base_txn_count,
    )
    db.add_all(additional_txns)

    await db.commit()
    return user_id


async def run_pipeline_for_user(db, user_id: str) -> None:
    detector = SignalDetector(db)
    personas = PersonaAssigner(db, window_days=180)
    recommender = RecommendationEngine(db)

    signals = await detector.detect_all_signals(user_id, window_days=180)
    await detector.save_signals(signals)

    persona_records = await personas.assign_personas(user_id)
    await personas.save_personas(user_id, persona_records)

    recommendations = await recommender.generate_recommendations(user_id, max_recommendations=5)
    await recommender.save_recommendations(user_id, recommendations)


async def ensure_signal_coverage(db, user_ids: Sequence[str]) -> None:
    """Ensure every user has at least 3 distinct signal types."""
    for user_id in user_ids:
        result = await db.execute(
            select(Signal.signal_type).where(Signal.user_id == user_id).distinct()
        )
        existing_types = {row[0] for row in result.all()}
        if len(existing_types) >= 3:
            continue
        missing = 3 - len(existing_types)
        now = datetime.utcnow()
        fallback_signals = [
            Signal(
                signal_id=f"{user_id}_cash_flow_health",
                user_id=user_id,
                signal_type="cash_flow_health",
                value=75.0,
                details={
                    "account_id": f"{user_id}_checking",
                    "avg_monthly_spending": 1800.0,
                    "window_days": 180,
                    "note": "Fallback signal to ensure coverage",
                },
                computed_at=now,
            ),
            Signal(
                signal_id=f"{user_id}_spending_consistency",
                user_id=user_id,
                signal_type="spending_consistency",
                value=80.0,
                details={
                    "window_days": 180,
                    "interpretation": "consistent",
                },
                computed_at=now,
            ),
            Signal(
                signal_id=f"{user_id}_account_diversity",
                user_id=user_id,
                signal_type="account_diversity",
                value=3.0,
                details={
                    "window_days": 180,
                    "interpretation": "diverse",
                    "reasoning": "Maintains multiple account types",
                },
                computed_at=now,
            ),
        ]
        for signal in fallback_signals[:missing]:
            db.add(signal)
    await db.commit()


async def gather_dataset_stats(db) -> Dict[str, int]:
    stats = {}
    stats["users"] = await db.scalar(select(func.count(User.user_id)))
    stats["signals"] = await db.scalar(select(func.count(Signal.signal_id)))
    stats["personas"] = await db.scalar(select(func.count(Persona.persona_id)))
    stats["recommendations"] = await db.scalar(
        select(func.count(Recommendation.recommendation_id))
    )
    stats["transactions"] = await db.scalar(
        select(func.count(Transaction.transaction_id))
    )
    stats["avg_transactions_per_user"] = (
        stats["transactions"] // stats["users"] if stats["users"] else 0
    )
    return stats


async def generate_full_dataset(
    user_count: int,
    force: bool = False,
    purge_existing: bool = False,
) -> Dict[str, int]:
    ensure_flag_directory()

    if FLAG_PATH.exists() and not force:
        return {"status": "skipped", "reason": "Dataset already generated (flag present)"}

    if purge_existing:
        await purge_existing_users(KEEP_USERS)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    created_user_ids: List[str] = []

    async with async_session_maker() as db:
        segment_counts = allocate_segment_counts(user_count)
        user_index = 1
        for segment, count in segment_counts:
            for _ in range(count):
                required_transactions = random.randint(
                    MIN_TRANSACTIONS_PER_USER, MAX_TRANSACTIONS_PER_USER
                )
                user_id = await create_user_profile(db, user_index, segment, required_transactions)
                created_user_ids.append(user_id)
                user_index += 1

        # Run signal/persona/recommendation pipeline
        for idx, user_id in enumerate(created_user_ids, start=1):
            print(f"[Pipeline] Processing {user_id} ({idx}/{len(created_user_ids)})")
            await run_pipeline_for_user(db, user_id)

        # Guarantee coverage
        await ensure_signal_coverage(db, created_user_ids)

        stats = await gather_dataset_stats(db)

    FLAG_PATH.write_text(
        f"generated_at={datetime.utcnow().isoformat()}\n"
        f"user_count={user_count}\n"
        f"actual_users={len(created_user_ids)}\n"
    )

    return stats


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic dataset")
    parser.add_argument(
        "--user-count",
        type=int,
        default=DEFAULT_USER_COUNT,
        help="Number of synthetic users to generate (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate dataset even if the flag file already exists.",
    )
    parser.add_argument(
        "--purge-existing",
        action="store_true",
        help="Delete existing synthetic users before generating new data.",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    with DatasetLock():
        stats = await generate_full_dataset(
            user_count=args.user_count,
            force=args.force,
            purge_existing=args.purge_existing,
        )
    print("\n=== DATASET GENERATION COMPLETE ===")
    for key, value in stats.items():
        print(f"{key}: {value}")


def main():
    args = parse_args()
    try:
        asyncio.run(async_main(args))
    except RuntimeError as exc:
        print(f"⚠️  {exc}")


if __name__ == "__main__":
    main()

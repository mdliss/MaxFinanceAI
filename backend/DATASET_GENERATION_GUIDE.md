# Dataset Generation Guide

## Overview

This guide explains how to generate a complete, rubric-compliant dataset with 50-100 diverse users for the operator dashboard.

## Quick Start

```bash
cd backend

# Generate full dataset (85 users covering all 5 personas)
python3 populate_full_dataset.py

# Validate rubric compliance
python3 validate_rubric_compliance.py
```

## What Gets Generated

### User Distribution (85 total users)

| Persona Type | Count | Description |
|--------------|-------|-------------|
| **High Utilization** | 20 | High credit card debt, struggling with payments |
| **Variable Income** | 15 | Freelancers/gig workers with irregular income |
| **Subscription-Heavy** | 15 | Multiple subscriptions, streaming, SaaS |
| **Savings Builder** | 20 | Actively saving, low debt, building wealth |
| **Overspender** | 15 | Spending exceeds income, lifestyle inflation |
| **Balanced** | 10 | No extreme patterns, edge case |

### Data Per User

Each user receives:
- **1-4 accounts**: Checking, savings (optional), 1-3 credit cards
- **~400-700 transactions**: 180 days of realistic spending patterns
- **Credit liabilities**: APR, payment history, due dates
- **Behavioral signals**: Detected patterns based on persona
- **Persona assignment**: 1-3 personas with confidence scores
- **Recommendations**: 3-5 education items + 1-3 partner offers

### Total Dataset

- **85 users**
- **~50,000 transactions**
- **~200 accounts**
- **~500 behavioral signals**
- **~150 persona assignments**
- **~400 recommendations**

## Persona Profiles

### 1. High Utilization (20 users)

**Financial Profile:**
- Income: $30,000 - $80,000/year
- Credit card utilization: 50% - 95%
- 30% have overdue payments
- 50% only make minimum payments

**Transaction Patterns:**
- Regular income (bi-weekly or monthly)
- High credit card usage
- Minimum or small payments
- Some have interest charges

**Generated Signals:**
- `credit_utilization`: 50-95%
- `minimum_payment_only`: true/false
- `is_overdue`: true (30% of users)
- `interest_charges`: present

### 2. Variable Income Budgeter (15 users)

**Financial Profile:**
- Income: $25,000 - $70,000/year
- Irregular pay schedule (20-90 day gaps)
- Low cash buffer (0.2-0.8 months)
- Difficulty budgeting

**Transaction Patterns:**
- Irregular income deposits (variable amounts and timing)
- Erratic spending patterns
- Some months overspend, some underspend
- Thin cash cushion

**Generated Signals:**
- `median_pay_gap`: 45-90 days
- `cash_flow_buffer`: <1 month
- `income_variability`: high
- `irregular_patterns`: detected

### 3. Subscription-Heavy (15 users)

**Financial Profile:**
- Income: $40,000 - $100,000/year
- 4-12 active subscriptions
- $100-$400/month in recurring charges
- Many unused services

**Transaction Patterns:**
- Regular subscription charges (Netflix, Spotify, etc.)
- Multiple SaaS tools
- Some subscriptions unused for months
- Otherwise normal spending

**Generated Signals:**
- `recurring_merchants`: 4-12
- `monthly_recurring_spend`: $100-$400
- `subscription_spend_share`: 10-25%
- `unused_subscriptions`: detected

### 4. Savings Builder (20 users)

**Financial Profile:**
- Income: $50,000 - $150,000/year
- Strong savings habit (3-10% monthly growth)
- Low credit utilization (0-25%)
- Building emergency fund

**Transaction Patterns:**
- Regular savings transfers ($300-$1,500/month)
- Disciplined spending
- Low credit card usage
- Living below means

**Generated Signals:**
- `savings_growth_rate`: 3-10%/month
- `net_savings_inflow`: $300-$1,500
- `credit_utilization`: <30%
- `emergency_fund_coverage`: growing

### 5. Overspender (15 users - Custom Persona)

**Financial Profile:**
- Income: $40,000 - $90,000/year
- Spending 110-150% of income
- Declining savings
- Increasing credit debt
- Lifestyle inflation

**Transaction Patterns:**
- High frequency of transactions (4-10/day)
- Many discretionary purchases
- Impulse buying (large random purchases)
- Multiple subscriptions
- Spending trends upward

**Generated Signals:**
- `spending_to_income_ratio`: 1.1-1.5
- `savings_balance_change`: negative
- `credit_utilization_trend`: increasing
- `impulse_purchase_count`: high
- `discretionary_spending`: excessive

**See PERSONA_5_DOCUMENTATION.md for full details**

### 6. Balanced (10 users - Edge Case)

**Financial Profile:**
- Income: varied
- No extreme patterns
- Moderate saving, moderate spending
- Healthy credit usage

**Purpose:**
- Tests that system doesn't force-fit personas
- Validates that not everyone needs intervention
- Edge case for operator review

## Generated Transaction Types

### Income Transactions
- **Payroll deposits**: Bi-weekly or monthly
- **Variable income**: For freelancers (irregular timing and amounts)
- **Realistic amounts**: Based on user's annual income

### Expense Transactions

**Subscriptions (monthly on day 1):**
- Netflix ($15.99)
- Spotify ($10.99)
- Amazon Prime ($14.99)
- Adobe Creative Cloud ($52.99)
- And 8+ more options

**Daily Spending:**
- **Groceries**: $25-$150 (Whole Foods, Safeway, Trader Joe's)
- **Restaurants**: $12-$60 (Chipotle, Starbucks, local places)
- **Gas**: $30-$70 (Shell, Chevron, BP)
- **Shopping**: $20-$300 (Amazon, Target, Best Buy)

**Savings Transfers (day 5):**
- For savings builders: $300-$1,500/month
- Regular automatic transfers

**Impulse Purchases:**
- For overspenders: Random large amounts
- Non-essential categories
- 2-3x normal transaction size

## Rubric Compliance Checks

The validation script checks:

### ✅ Critical Requirements

1. **User Count**: 50-100 users
2. **Consent**: 100% of users have granted consent
3. **Coverage**: 100% of users have assigned persona + ≥3 detected behaviors
4. **Explainability**: 100% of recommendations have plain-language rationales

### ✅ Data Quality

5. **Persona Distribution**: All 5 personas represented
6. **Signal Types**: All required signal types detected
7. **Transaction Density**: >100 transactions per user
8. **Account Diversity**: Checking, savings, credit cards present
9. **Recommendation Diversity**: Multiple types generated
10. **Data Freshness**: Recent transactions (last 30 days)

## Customization

### Adjust User Counts

Edit `PERSONA_PROFILES` in `populate_full_dataset.py`:

```python
PERSONA_PROFILES = {
    "high_utilization": {
        "count": 25,  # Change from 20 to 25
        # ... rest of config
    },
    # ... other personas
}
```

### Modify Transaction Patterns

Adjust spending behavior in `create_transactions()`:

```python
# More transactions for overspenders
if profile_type == "overspender":
    daily_txn_count = random.randint(6, 12)  # Increase from (4, 10)
```

### Add More Merchants

Extend the `MERCHANTS` dictionary:

```python
MERCHANTS = {
    "groceries": ["Whole Foods", "Safeway", "Your New Store"],
    # ... add more
}
```

## Performance

- **Generation time**: ~5-10 minutes for 85 users
- **Database size**: ~50-100 MB
- **Pipeline processing**: ~30 seconds per user
- **Total time**: ~10-15 minutes

## Troubleshooting

### "FileNotFoundError: app/database.py"

Run from backend directory:
```bash
cd backend
python3 populate_full_dataset.py
```

### "Some users missing personas"

Check that persona assignment logic is working:
```bash
python3 -c "from app.services.persona_assigner import PersonaAssigner; print('OK')"
```

### "Recommendations missing rationales"

Verify recommendation engine has rationale templates:
```bash
grep -r "rationale" app/services/recommendation_engine.py
```

### "Transaction count too low"

Increase days or transaction frequency in `create_transactions()`:
```python
for days_ago in range(180):  # Increase to 365 for more data
```

## Deployment

### For Railway

The dataset is too large to generate on every deploy. Instead:

1. **Option A: Keep demo user only**
   - Use `initialize_all.py` (current approach)
   - Fast deployment, minimal data
   - Good for demos, not for operator dashboard

2. **Option B: Pre-populate database**
   - Generate full dataset locally
   - Upload database file to Railway volume
   - Slower but full featured

3. **Option C: Conditional initialization**
   - Check environment variable `FULL_DATASET=true`
   - Run `populate_full_dataset.py` instead of `initialize_all.py`
   - Only on first deploy

**Recommended approach for Railway:**

```bash
# start.sh
if [ "$FULL_DATASET" = "true" ] && [ ! -f /app/data/populated.flag ]; then
    echo "Generating full dataset..."
    python populate_full_dataset.py
    touch /app/data/populated.flag
else
    echo "Using quick initialization..."
    python initialize_all.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Set Railway environment variable: `FULL_DATASET=true`

## Verification

After generation, verify data quality:

```bash
# Run validation
python3 validate_rubric_compliance.py

# Check specific user
python3 -c "
from app.database import async_session_maker
from app.models import User
from sqlalchemy import select
import asyncio

async def check():
    async with async_session_maker() as db:
        result = await db.execute(select(User).limit(5))
        for user in result.scalars():
            print(f'{user.user_id}: {user.name}')

asyncio.run(check())
"

# Count records
sqlite3 data/spendsense.db "
SELECT 'Users:', COUNT(*) FROM users
UNION ALL
SELECT 'Transactions:', COUNT(*) FROM transactions
UNION ALL
SELECT 'Personas:', COUNT(*) FROM persona_assignments
UNION ALL
SELECT 'Recommendations:', COUNT(*) FROM recommendations;
"
```

## Next Steps

After generating the dataset:

1. **Start the server**: Already running at http://localhost:8000
2. **View operator dashboard**: http://localhost:3001/operator
3. **Review personas**: Check distribution and assignments
4. **Validate recommendations**: Ensure rationales are present
5. **Test filtering**: Filter by persona, status, etc.
6. **Run evaluation**: Check metrics meet rubric targets

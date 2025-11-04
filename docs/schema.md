# SpendSense: Database Schema Documentation

## Overview

SpendSense uses SQLite with SQLAlchemy ORM. The database models Plaid-style financial data with behavioral signals, persona assignments, and recommendations.

**Database File:** `./data/spendsense.db`
**ORM:** SQLAlchemy 2.0 (async)
**Total Tables:** 9

---

## Entity Relationship Diagram

```
users (1) ──< (M) accounts ──< (M) transactions
  │                  │
  │                  └──< (M) liabilities
  │
  ├──< (M) signals
  ├──< (M) personas
  ├──< (M) recommendations
  └──< (M) audit_logs
```

---

## Table Schemas

### 1. users

Stores user profiles and consent status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | String | PRIMARY KEY, INDEX | Unique user identifier |
| name | String | NOT NULL | User's full name (synthetic) |
| age | Integer | NULL | User's age (18-75) |
| income_level | String | NULL | Income bracket (low, medium, high) |
| consent_status | Boolean | DEFAULT FALSE | Whether user has consented to processing |
| consent_timestamp | DateTime | NULL | When consent was granted |
| created_at | DateTime | DEFAULT now() | Account creation timestamp |

**Relationships:**
- One-to-many: accounts, transactions, liabilities, signals, personas, recommendations

**Sample Data:**
```json
{
  "user_id": "user_001",
  "name": "Charlotte Jackson",
  "age": 34,
  "income_level": "medium",
  "consent_status": true,
  "consent_timestamp": "2025-11-03T10:30:00",
  "created_at": "2025-11-03T10:00:00"
}
```

---

### 2. accounts

Bank accounts (checking, savings, credit cards) following Plaid structure.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| account_id | String | PRIMARY KEY, INDEX | Unique account identifier |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | Owner user ID |
| type | String | NOT NULL | Account type (depository, credit) |
| subtype | String | NULL | Account subtype (checking, savings, credit_card, money_market, hsa) |
| available_balance | Float | NULL | Available balance |
| current_balance | Float | NULL | Current balance |
| credit_limit | Float | NULL | Credit limit (for credit cards) |
| iso_currency_code | String | DEFAULT "USD" | Currency code |
| holder_category | String | NULL | Account holder type (personal only) |

**Relationships:**
- Many-to-one: user
- One-to-many: transactions, liabilities

**Sample Data:**
```json
{
  "account_id": "acc_checking_001",
  "user_id": "user_001",
  "type": "depository",
  "subtype": "checking",
  "available_balance": 2450.00,
  "current_balance": 2450.00,
  "credit_limit": null,
  "iso_currency_code": "USD",
  "holder_category": "personal"
}
```

---

### 3. transactions

Transaction history following Plaid API structure.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| transaction_id | String | PRIMARY KEY, INDEX | Unique transaction identifier |
| account_id | String | FOREIGN KEY (accounts.account_id), INDEX | Account ID |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | User ID |
| date | Date | NOT NULL, INDEX | Transaction date |
| amount | Float | NOT NULL | Amount (negative = outflow, positive = inflow) |
| merchant_name | String | NULL | Merchant name |
| merchant_entity_id | String | NULL | Merchant entity ID |
| payment_channel | String | NULL | Payment channel (online, in_store, other) |
| category_primary | String | NULL | Primary category (Income, Food & Drink, Shopping, etc.) |
| category_detailed | String | NULL | Detailed category |
| pending | Boolean | DEFAULT FALSE | Whether transaction is pending |

**Relationships:**
- Many-to-one: account, user

**Sample Data:**
```json
{
  "transaction_id": "tx_001",
  "account_id": "acc_checking_001",
  "user_id": "user_001",
  "date": "2025-11-03",
  "amount": -45.67,
  "merchant_name": "Netflix",
  "payment_channel": "online",
  "category_primary": "Entertainment",
  "category_detailed": "Streaming Services",
  "pending": false
}
```

---

### 4. liabilities

Credit card and loan details following Plaid structure.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| liability_id | String | PRIMARY KEY, INDEX | Unique liability identifier |
| account_id | String | FOREIGN KEY (accounts.account_id) | Associated account |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | User ID |
| apr_percentage | Float | NULL | Annual percentage rate |
| apr_type | String | NULL | APR type (purchase_apr, cash_advance_apr) |
| minimum_payment_amount | Float | NULL | Minimum payment due |
| last_payment_amount | Float | NULL | Last payment amount |
| last_payment_date | Date | NULL | Last payment date |
| is_overdue | Boolean | DEFAULT FALSE | Overdue status |
| next_payment_due_date | Date | NULL | Next payment due date |
| last_statement_balance | Float | NULL | Last statement balance |

**Relationships:**
- Many-to-one: account, user

**Sample Data:**
```json
{
  "liability_id": "liab_001",
  "account_id": "acc_credit_001",
  "user_id": "user_001",
  "apr_percentage": 19.99,
  "apr_type": "purchase_apr",
  "minimum_payment_amount": 50.00,
  "last_payment_amount": 150.00,
  "last_payment_date": "2025-10-28",
  "is_overdue": false,
  "next_payment_due_date": "2025-11-28"
}
```

---

### 5. signals

Detected behavioral signals from transaction analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| signal_id | String | PRIMARY KEY, INDEX | Unique signal identifier |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | User ID |
| signal_type | String | NOT NULL, INDEX | Signal type (subscription_detected, credit_utilization, income_stability, savings_growth) |
| value | Float | NOT NULL | Numeric value of signal |
| details | JSON | NULL | Additional signal details |
| computed_at | DateTime | DEFAULT now() | When signal was computed |

**Relationships:**
- Many-to-one: user

**Signal Types:**
1. `subscription_detected`: Recurring payment patterns
2. `credit_utilization`: Credit card utilization percentage
3. `income_stability`: Income consistency score
4. `savings_growth`: Savings growth rate

**Sample Data:**
```json
{
  "signal_id": "sig_001",
  "user_id": "user_001",
  "signal_type": "credit_utilization",
  "value": 68.0,
  "details": {
    "card_type": "Visa",
    "last_4": "4523",
    "current_balance": 3400.00,
    "credit_limit": 5000.00
  },
  "computed_at": "2025-11-03T12:00:00"
}
```

---

### 6. personas

Assigned financial personas based on behavioral signals.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| persona_id | Integer | PRIMARY KEY, AUTOINCREMENT | Auto-generated ID |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | User ID |
| window_days | Integer | NOT NULL | Analysis window (30 or 180 days) |
| persona_type | String | NOT NULL, INDEX | Persona category |
| priority_rank | Integer | NULL | Priority ranking (lower = higher priority) |
| criteria_met | String | NULL | Human-readable criteria description |
| assigned_at | DateTime | DEFAULT now() | Assignment timestamp |

**Relationships:**
- Many-to-one: user

**Persona Types:**
1. `credit_optimizer`: High credit utilization (priority 1)
2. `variable_income_budgeter`: Irregular income (priority 2)
3. `subscription_optimizer`: High subscription spending (priority 3)
4. `savings_builder`: Growing savings (priority 4)
5. `financial_newcomer`: Stable income, low buffer (priority 5)

**Sample Data:**
```json
{
  "persona_id": 1,
  "user_id": "user_001",
  "window_days": 30,
  "persona_type": "credit_optimizer",
  "priority_rank": 1,
  "criteria_met": "Credit utilization 68% on Visa ending in 4523",
  "assigned_at": "2025-11-03T12:05:00"
}
```

---

### 7. recommendations

AI-generated financial education recommendations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| recommendation_id | Integer | PRIMARY KEY, AUTOINCREMENT | Auto-generated ID |
| user_id | String | FOREIGN KEY (users.user_id), INDEX | User ID |
| persona_type | String | NOT NULL | Associated persona |
| content_type | String | NOT NULL | Content type (article, guide, video, calculator, partner_offer) |
| title | String | NOT NULL | Recommendation title |
| description | Text | NULL | Detailed description |
| rationale | Text | NOT NULL | Plain-language explanation citing user data |
| disclaimer | Text | NULL | Required disclaimer text |
| eligibility_met | Boolean | DEFAULT TRUE | Whether user meets eligibility criteria |
| approval_status | String | DEFAULT "pending" | Approval status (pending, approved, rejected, flagged) |
| operator_notes | Text | NULL | Operator review notes |
| created_at | DateTime | DEFAULT now() | Creation timestamp |

**Relationships:**
- Many-to-one: user

**Content Types:**
- `article`: Educational article
- `guide`: Step-by-step guide
- `video`: Educational video
- `calculator`: Financial calculator tool
- `partner_offer`: Product/service offer

**Sample Data:**
```json
{
  "recommendation_id": 1,
  "user_id": "user_001",
  "persona_type": "credit_optimizer",
  "content_type": "guide",
  "title": "How to Reduce Credit Utilization in 3 Steps",
  "description": "A practical guide to lowering your credit card balances",
  "rationale": "Your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score and reduce interest charges of $87/month.",
  "disclaimer": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.",
  "eligibility_met": true,
  "approval_status": "approved",
  "created_at": "2025-11-03T12:10:00"
}
```

---

### 8. audit_log

Complete audit trail of all system actions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| log_id | Integer | PRIMARY KEY, AUTOINCREMENT | Auto-generated ID |
| timestamp | DateTime | DEFAULT now() | Action timestamp |
| user_id | String | NULL, INDEX | Associated user (if applicable) |
| action | String | NOT NULL | Action type |
| actor | String | NOT NULL | Who performed action (system/operator) |
| details | JSON | NULL | Action details |

**Action Types:**
- `consent_granted`
- `consent_revoked`
- `recommendation_approved`
- `recommendation_rejected`
- `recommendation_flagged`
- `signal_detected`
- `persona_assigned`

**Sample Data:**
```json
{
  "log_id": 1,
  "timestamp": "2025-11-03T12:10:15",
  "user_id": "user_001",
  "action": "recommendation_approved",
  "actor": "operator_jane",
  "details": {
    "recommendation_id": 1,
    "title": "How to Reduce Credit Utilization"
  }
}
```

---

### 9. feedback

User and operator feedback on recommendations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| feedback_id | Integer | PRIMARY KEY, AUTOINCREMENT | Auto-generated ID |
| recommendation_id | Integer | FOREIGN KEY (recommendations.recommendation_id) | Associated recommendation |
| user_id | String | FOREIGN KEY (users.user_id) | User who provided feedback |
| rating | Integer | NULL | Rating (1-5) |
| comment | Text | NULL | Feedback comment |
| helpful | Boolean | NULL | Whether recommendation was helpful |
| created_at | DateTime | DEFAULT now() | Feedback timestamp |

**Relationships:**
- Many-to-one: recommendation, user

**Sample Data:**
```json
{
  "feedback_id": 1,
  "recommendation_id": 1,
  "user_id": "user_001",
  "rating": 5,
  "comment": "This guide was really helpful!",
  "helpful": true,
  "created_at": "2025-11-04T09:00:00"
}
```

---

## Indexes

Performance-critical indexes:
- `users.user_id` (PRIMARY)
- `accounts.account_id` (PRIMARY)
- `accounts.user_id` (FOREIGN KEY)
- `transactions.transaction_id` (PRIMARY)
- `transactions.account_id` (FOREIGN KEY)
- `transactions.user_id` (FOREIGN KEY)
- `transactions.date` (for time-range queries)
- `signals.user_id` (FOREIGN KEY)
- `signals.signal_type` (for filtering)
- `personas.user_id` (FOREIGN KEY)
- `personas.persona_type` (for filtering)
- `recommendations.user_id` (FOREIGN KEY)
- `audit_log.user_id` (for user audit trails)

---

## Constraints & Validation

### Foreign Key Constraints
- All foreign keys enforce referential integrity
- CASCADE DELETE for dependent records (e.g., deleting user deletes their data)

### Data Validation
- Consent required before processing (enforced in application layer)
- Age ≥ 18 for eligibility
- Minimum 10 transactions for signal detection
- All recommendations require rationale (NOT NULL)
- All recommendations require disclaimer

### Enumerations

**Income Levels:**
- `low` (< $30k)
- `medium` ($30k - $75k)
- `high` (> $75k)

**Approval Status:**
- `pending`
- `approved`
- `rejected`
- `flagged`

**Payment Channels:**
- `online`
- `in_store`
- `other`

---

## Data Volume

Current production data (as of 2025-11-04):
- Users: 73
- Accounts: 200+
- Transactions: 2,500+
- Signals: 42
- Personas: 61
- Recommendations: 120
- Audit Logs: 200+

---

## Migration & Versioning

**Schema Version:** 1.0
**Last Updated:** 2025-11-04

No migration framework currently implemented. Schema is created via:
```python
Base.metadata.create_all(engine)
```

For production, consider:
- Alembic for schema migrations
- Version tracking in schema_migrations table
- Backup/restore procedures

---

## Data Retention

- Transactions: 180+ days required for signal detection
- Signals: Retained indefinitely for historical analysis
- Audit logs: Retained indefinitely for compliance
- Recommendations: Soft delete (mark as archived)

---

## Privacy & Security

- All user data is synthetic (no real PII)
- Consent status tracked per user
- Audit trail for all data access
- No plaintext passwords (no authentication in demo)
- Database file permissions restricted

---

## Performance Considerations

- SQLite performs well for <100 users
- Transaction queries use date index
- Signal detection optimized with user_id index
- Recommendation filtering uses persona_type index

**For scaling beyond demo:**
- Migrate to PostgreSQL
- Add read replicas
- Implement caching (Redis)
- Partition transactions by date

---

**Last Updated:** 2025-11-04
**Project:** SpendSense Financial Education Platform

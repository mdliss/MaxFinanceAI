# SpendSense - Product Requirements Document

**Project**: SpendSense - From Plaid to Personalized Learning
**Goal**: Build an explainable, consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education

---

## Project Overview

SpendSense transforms synthetic Plaid-style transaction data into personalized financial education through behavioral pattern detection, persona assignment, and educational content recommendations.

**Core Principle**: Transparency over sophistication. Every recommendation must be explainable and auditable.

---

## Success Criteria

| Category | Metric | Target |
|----------|--------|--------|
| Coverage | Users with assigned persona + ≥3 detected behaviors | 100% |
| Explainability | Recommendations with rationales | 100% |
| Latency | Processing time per user | <5 seconds |
| Auditability | Recommendations with decision traces | 100% |
| Code Quality | Passing unit/integration tests | ≥10 tests |
| Documentation | Schema and decision log | Complete |

---

## Core Requirements

### 1. Data Ingestion (Plaid-Style)

Generate synthetic data matching Plaid API structure:

**Accounts:**
- `account_id`, `type/subtype` (checking, savings, credit card, money market, HSA)
- `balances`: available, current, limit
- `iso_currency_code`, `holder_category` (exclude business accounts)

**Transactions:**
- `account_id`, `date`, `amount`
- `merchant_name` or `merchant_entity_id`
- `payment_channel`, `personal_finance_category` (primary/detailed)
- `pending` status

**Liabilities:**
- Credit cards: APRs, `minimum_payment_amount`, `last_payment_amount`, `is_overdue`, `next_payment_due_date`, `last_statement_balance`
- Mortgages/Student Loans: `interest_rate`, `next_payment_due_date`

**Requirements:**
- 50-100 synthetic users with diverse financial situations
- No real PII—use fake names, masked account numbers
- 180+ days of transaction history
- Deterministic generation using seed values
- Ingest from CSV/JSON (no live Plaid connection)

### 2. Behavioral Signal Detection

Compute signals per time window (30-day and 180-day):

**Subscriptions:**
- Recurring merchants (≥3 in 90 days with monthly/weekly cadence)
- Monthly recurring spend
- Subscription share of total spend

**Savings:**
- Net inflow to savings-like accounts
- Growth rate
- Emergency fund coverage = savings balance / average monthly expenses

**Credit:**
- Utilization = balance / limit
- Flags for ≥30%, ≥50%, ≥80% utilization
- Minimum-payment-only detection
- Interest charges present
- Overdue status

**Income Stability:**
- Payroll ACH detection
- Payment frequency and variability
- Cash-flow buffer in months

### 3. Persona Assignment (Maximum 5)

#### Persona 1: High Utilization
**Criteria:** Any card utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR `is_overdue = true`
**Focus:** Reduce utilization and interest; payment planning and autopay education

#### Persona 2: Variable Income Budgeter
**Criteria:** Median pay gap > 45 days AND cash-flow buffer < 1 month
**Focus:** Percent-based budgets, emergency fund basics, smoothing strategies

#### Persona 3: Subscription-Heavy
**Criteria:** Recurring merchants ≥3 AND (monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)
**Focus:** Subscription audit, cancellation/negotiation tips, bill alerts

#### Persona 4: Savings Builder
**Criteria:** Savings growth rate ≥2% over window OR net savings inflow ≥$200/month, AND all card utilizations < 30%
**Focus:** Goal setting, automation, APY optimization (HYSA/CD basics)

#### Persona 5: Paycheck-to-Paycheck Navigator (Custom)
**Criteria:** Regular income (stability score ≥70) AND low cash buffer (<2 weeks expenses) AND no savings growth
**Rationale:** Represents stable-income earners who need help stretching paychecks without complex budgeting
**Focus:** Micro-savings strategies, bill timing optimization, overdraft protection education
**Prioritization:** Applied after checking other personas; if multiple match, use priority ranking (High Utilization > Variable Income > Subscription-Heavy > Savings Builder > Paycheck-to-Paycheck)

### 4. Personalization & Recommendations

Output per user per window:
- 3-5 education items mapped to persona/signals
- 1-3 partner offers with eligibility checks
- Every item includes a "because" rationale citing concrete data
- Plain-language explanations (no jargon)

**Example Rationale Format:**
> "We noticed your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score and reduce interest charges of $87/month."

**Education Content Examples:**
- Articles on debt paydown strategies
- Budget templates for variable income
- Subscription audit checklists
- Emergency fund calculators
- Credit utilization explainers

**Partner Offer Examples:**
- Balance transfer credit cards (if credit utilization high)
- High-yield savings accounts (if building emergency fund)
- Budgeting apps (if variable income)
- Subscription management tools (if subscription-heavy)

### 5. Consent, Eligibility & Tone Guardrails

**Consent:**
- Require explicit opt-in before processing data
- Allow users to revoke consent at any time
- Track consent status per user
- No recommendations without consent

**Eligibility:**
- Don't recommend products user isn't eligible for
- Check minimum income/credit requirements
- Filter based on existing accounts
- Avoid harmful suggestions (no payday loans, predatory products)

**Tone:**
- No shaming language
- Empowering, educational tone
- Avoid judgmental phrases like "you're overspending"
- Use neutral, supportive language

**Disclosure:**
Every recommendation must include: *"This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."*

### 6. Operator View

Build interface for human oversight:
- View detected signals for any user
- See 30-day and 180-day persona assignments
- Review generated recommendations with rationales
- Approve or override recommendations
- Access decision trace (why this recommendation was made)
- Flag recommendations for review

### 7. Evaluation & Metrics

Measure:
- **Coverage:** % of users with assigned persona and ≥3 detected behaviors
- **Explainability:** % of recommendations with plain-language rationales
- **Relevance:** Simple scoring of education-persona fit
- **Latency:** Time to generate recommendations (fast on laptop)
- **Fairness:** Basic demographic parity check if synthetic data includes demographics

**Output:**
- JSON/CSV metrics file
- Brief summary report (1-2 pages)
- Per-user decision traces

---

## Technical Architecture

### Modular Structure
- `ingest/` - Data loading and validation
- `features/` - Signal detection and feature engineering
- `personas/` - Persona assignment logic
- `recommend/` - Recommendation engine
- `guardrails/` - Consent, eligibility, tone checks
- `ui/` - Operator view
- `eval/` - Evaluation harness
- `docs/` - Decision log and schema documentation

### Storage
- SQLite for relational data
- JSON for configs and logs

### API
- `POST /users` - Create user
- `POST /consent` - Record consent
- `GET /profile/{user_id}` - Get behavioral profile
- `GET /recommendations/{user_id}` - Get recommendations
- `POST /feedback` - Record user feedback
- `GET /operator/review` - Operator approval queue

### AI Integration
- OpenAI API for generating educational content text (optional)
- Rules-based baseline acceptable
- Focus on explainability over sophistication

---

## Code Quality Requirements

- Clear modular structure
- One-command setup (`docker-compose up` or similar)
- Concise README with setup and usage instructions
- ≥10 unit/integration tests
- Deterministic behavior (use seeds for randomness)
- Decision log in `/docs` explaining key choices
- Explicit limitations documented
- Standard "not financial advice" disclaimer

---

## Submission Requirements

### Deliverables
1. Code repository (GitHub preferred)
2. Brief technical writeup (1-2 pages)
3. Documentation of AI tools and prompts used
4. Demo video or live presentation
5. Performance metrics and benchmarks
6. Test cases and validation results
7. Data model/schema documentation
8. Evaluation report (JSON/CSV + summary)

### Documentation
- Decision log explaining technical choices
- Schema documentation with field descriptions
- AI integration points and prompt templates
- Performance benchmarks (processing time, API response time)
- Test results summary

---

## Implementation Phases

1. **Data Foundation:** Generate synthetic dataset, validate schema
2. **Feature Engineering:** Build signal detection for subscriptions, savings, credit, income
3. **Persona System:** Implement assignment logic and prioritization
4. **Recommendations:** Build engine with rationales and content catalog
5. **Guardrails & UX:** Add consent, eligibility, tone checks; build operator view
6. **Evaluation:** Run metrics harness, document results and limitations

---

## Core Principles

- Transparency over sophistication
- User control over automation
- Education over sales
- Fairness built in from day one

Build systems people can trust with their financial data.

---

**Document Version**: 3.0 (Aligned with Rubric)
**Last Updated**: 2025-11-04
**Status**: Requirements defined per rubric specifications

# SpendSense - Product Requirements Document

**Project**: SpendSense - Explainable Financial Education Platform  
**Goal**: Build a consent-aware system that transforms transaction data into personalized financial education

---

## Project Overview

SpendSense analyzes synthetic Plaid-style transaction data to detect behavioral patterns, assign financial personas, and deliver personalized educational content with strict guardrails around consent, eligibility, and tone.

**Core Principle**: Transparency over sophistication. Every recommendation must be explainable and auditable.

---

## User Stories

### Primary User: Bank Customer

- As a customer, I want to **opt-in to data analysis** so that I maintain control over my financial information
- As a customer, I want to **see my financial behavior patterns** explained in plain language so I understand my habits
- As a customer, I want to **receive personalized educational content** that matches my specific situation
- As a customer, I want to **understand why recommendations are made** so I can make informed decisions
- As a customer, I want to **revoke consent at any time** so I maintain privacy control
- As a customer, I want **empowering, non-judgmental guidance** so I feel supported, not shamed

### Secondary User: Bank Operator

- As an operator, I want to **review detected patterns** for any user to ensure quality
- As an operator, I want to **see persona assignments with justification** to validate the system
- As an operator, I want to **approve or override recommendations** before they reach customers
- As an operator, I want **decision traces** to understand system reasoning
- As an operator, I want to **flag problematic recommendations** for review

### Tertiary User: Compliance Officer

- As a compliance officer, I want **full audit trails** of all recommendations
- As a compliance officer, I want to **verify consent tracking** is working correctly
- As a compliance officer, I want to **ensure no regulated advice is provided**
- As a compliance officer, I want to **validate tone guardrails** prevent harmful messaging

---

## Key Features for MVP

### 1. Synthetic Data Generation

**Must Have:**
- Generate 50-100 synthetic users with diverse financial profiles
- Match Plaid API structure exactly (accounts, transactions, liabilities)
- No real PII - use fake names and masked account numbers
- Deterministic generation with seed values
- Export to CSV/JSON for ingestion

**Account Types:**
- Checking accounts
- Savings accounts
- Credit cards
- Money market accounts
- HSA accounts
- Exclude business accounts

**Transaction Attributes:**
- account_id linkage
- Date (180+ days of history)
- Amount (debits and credits)
- Merchant name or entity ID
- Payment channel
- Personal finance category (primary/detailed)
- Pending status flag

**Liability Details:**
- Credit card APRs and payment history
- Minimum payment amounts
- Overdue flags
- Next payment due dates
- Statement balances

**Diversity Requirements:**
- Income levels: $20k-$200k annual range
- Credit behaviors: pristine to problematic
- Saving patterns: none to aggressive
- Age demographics: 22-65 years
- Geographic distribution across US

**Success Criteria:**
- 100% of generated users have complete 180-day transaction history
- Data passes Plaid schema validation
- At least 3 distinct financial behavior archetypes represented
- Deterministic: same seed produces identical dataset

---

### 2. Behavioral Signal Detection

**Must Have:**
- Compute signals for both 30-day and 180-day windows
- All calculations deterministic and reproducible
- Handle missing data gracefully
- Performance: <1 second per user

**Subscription Signals:**
- Detect recurring merchants (≥3 occurrences in 90 days)
- Calculate monthly recurring spend
- Compute subscription share of total spend
- Identify subscription cadence (weekly/monthly/annual)

**Savings Signals:**
- Net inflow to savings-like accounts
- Savings growth rate (%)
- Emergency fund coverage (months)
- Savings velocity (rate of change)

**Credit Signals:**
- Utilization percentage per card
- Flag ≥30%, ≥50%, ≥80% thresholds
- Minimum-payment-only detection
- Interest charge presence
- Overdue status tracking
- Total credit available vs. used

**Income Stability Signals:**
- Payroll ACH detection
- Payment frequency identification
- Income variability coefficient
- Cash-flow buffer (months)
- Income source diversification

**Success Criteria:**
- 100% of users have ≥3 detectable behaviors
- Signal detection completes in <5 seconds for 100 users
- Results are deterministic (same input = same output)
- Edge cases handled (zero income, zero savings, etc.)

---

### 3. Persona Assignment System

**Must Have:**
- Maximum 5 personas total
- Clear, documented criteria for each
- Prioritization logic when multiple personas match
- Plain-language persona descriptions
- Support both 30-day and 180-day assignments

**Persona 1: High Utilization**

**Criteria:**
- Any card utilization ≥50% OR
- Interest charges > $0 OR
- Minimum-payment-only detected OR
- is_overdue = true

**Primary Focus:**
- Credit utilization reduction
- Interest minimization strategies
- Payment planning and autopay
- Debt paydown frameworks

**Education Topics:**
- Avalanche vs. snowball methods
- Balance transfer strategies
- Credit score impact education
- Payment automation setup

---

**Persona 2: Variable Income Budgeter**

**Criteria:**
- Median pay gap > 45 days AND
- Cash-flow buffer < 1 month

**Primary Focus:**
- Percent-based budgeting
- Emergency fund establishment
- Income smoothing strategies
- Irregular income management

**Education Topics:**
- Zero-based budgeting
- Buffer building techniques
- Quarterly tax planning
- Feast-famine cycle management

---

**Persona 3: Subscription-Heavy**

**Criteria:**
- Recurring merchants ≥3 AND
- (Monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)

**Primary Focus:**
- Subscription audit
- Cancellation tactics
- Negotiation strategies
- Bill alert setup

**Education Topics:**
- Subscription inventory checklists
- Cancellation timing optimization
- Service negotiation scripts
- Free alternative discovery

---

**Persona 4: Savings Builder**

**Criteria:**
- Savings growth rate ≥2% over window OR
- Net savings inflow ≥$200/month, AND
- All card utilizations < 30%

**Primary Focus:**
- Goal setting frameworks
- Savings automation
- APY optimization
- HYSA/CD education

**Education Topics:**
- SMART financial goals
- Automated savings plans
- High-yield account comparison
- CD laddering strategies

---

**Persona 5: Paycheck-to-Paycheck Navigator**

**Criteria:**
- Cash-flow buffer < 0.5 months AND
- Checking account balance < $500 average AND
- At least 2 overdraft/NSF fees in 180 days OR
- Income regularity (biweekly payroll) AND
- No net savings growth

**Rationale:**
- Addresses ~40% of Americans living paycheck-to-paycheck
- Distinct from Variable Income (regular paychecks vs. irregular)
- Requires different strategies than High Utilization (cash flow vs. credit)

**Primary Focus:**
- Expense timing optimization
- Micro-savings techniques
- Overdraft avoidance
- Emergency fund starter strategies

**Education Topics:**
- Bill timing alignment with payday
- Rounding-up savings apps
- No-fee banking options
- $500 starter emergency fund

**Prioritization Logic:**
1. High Utilization (immediate credit risk)
2. Paycheck-to-Paycheck Navigator (immediate cash flow risk)
3. Variable Income Budgeter (income stability risk)
4. Subscription-Heavy (spending optimization opportunity)
5. Savings Builder (positive reinforcement, lowest priority)

---

**Success Criteria:**
- 100% of users assigned to at least one persona
- Persona distribution is not uniform (reflects realistic patterns)
- Multi-persona cases resolved by priority logic
- Persona assignment deterministic and reproducible

---

### 4. Recommendation Engine

**Must Have:**
- 3-5 educational items per user per window
- 1-3 partner offers with eligibility checks
- Every recommendation has "because" rationale
- Plain-language explanations (8th grade reading level)
- Concrete data citations in rationales

**Rationale Format Template:**
```
"We noticed your [Account Type] ending in [Last4] is at [X]% utilization 
($[Current] of $[Limit] limit). [Impact Statement]. [Action Suggestion]."
```

**Example Rationale:**
```
"We noticed your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). 
Bringing this below 30% could improve your credit score and reduce interest charges 
of $87/month."
```

**Education Content Catalog:**

*High Utilization:*
- "Debt Avalanche vs. Snowball: Which is Right for You?"
- "Balance Transfer 101: Save on Interest"
- "Credit Utilization: The 30% Rule Explained"
- "Automate Your Debt Payments"

*Variable Income:*
- "Budgeting with Irregular Income"
- "Building Your First Emergency Fund"
- "Quarterly Tax Planning for Freelancers"
- "Smoothing Income Peaks and Valleys"

*Subscription-Heavy:*
- "The 30-Day Subscription Audit Checklist"
- "How to Negotiate Lower Bills"
- "Free Alternatives to Paid Services"
- "Setting Up Bill Alerts"

*Savings Builder:*
- "SMART Financial Goal Setting"
- "HYSA vs. CD: Which is Better?"
- "Automating Your Savings"
- "CD Laddering for Beginners"

*Paycheck-to-Paycheck:*
- "Aligning Bills with Payday"
- "The $500 Emergency Fund Challenge"
- "No-Fee Banking Options"
- "Rounding-Up Savings Apps"

**Partner Offer Examples:**

*High Utilization:*
- Balance transfer credit cards (0% APR for 15+ months)
- Eligibility: Credit score ≥650, no recent delinquencies
- Debt consolidation loans
- Eligibility: Debt-to-income <43%, income ≥$30k

*Variable Income:*
- Budgeting apps (YNAB, EveryDollar)
- Eligibility: All users
- Business checking accounts
- Eligibility: Self-employment income detected

*Subscription-Heavy:*
- Subscription management tools (Truebill, Trim)
- Eligibility: ≥3 subscriptions detected
- Bill negotiation services
- Eligibility: Monthly recurring spend ≥$100

*Savings Builder:*
- High-yield savings accounts (2.5%+ APY)
- Eligibility: No existing HYSA, savings balance <$10k
- Brokerage account promotions
- Eligibility: Savings balance >$5k, age <65

*Paycheck-to-Paycheck:*
- No-fee checking accounts
- Eligibility: Recent overdraft fees detected
- Micro-savings apps (Acorns, Digit)
- Eligibility: Checking account balance <$1000

**Success Criteria:**
- 100% of recommendations include plain-language rationale
- All rationales cite specific account numbers and amounts
- No jargon above 8th grade reading level
- Recommended offers match user eligibility
- Content maps to assigned persona

---

### 5. Consent & Guardrails System

**Consent Management:**

**Must Have:**
- Explicit opt-in required before any data processing
- Revoke consent feature accessible at any time
- Consent status tracked per user in database
- No recommendations generated without active consent
- Clear consent language (not buried in terms)

**Consent Flow:**
1. User presented with plain-language consent request
2. Explicit "I agree" button (not pre-checked)
3. Consent timestamp recorded
4. User can revoke via settings page
5. Revocation stops all processing immediately

**Eligibility Guardrails:**

**Must Prevent:**
- Recommending products user isn't eligible for
- Suggesting existing accounts (no duplicate savings accounts)
- Predatory products (payday loans, high-fee cards)
- Products requiring income above user's level
- Credit products requiring scores above user's estimated score

**Eligibility Checks:**
- Minimum income requirements
- Credit score proxies (utilization, payment history)
- Existing account deduplication
- Age requirements (retirement accounts)
- Account balance thresholds

**Tone Guardrails:**

**Must Avoid:**
- Shaming language ("you're overspending")
- Judgmental phrases ("bad financial habits")
- Panic-inducing warnings
- Condescending tone
- Absolute demands ("you must")

**Must Use:**
- Empowering language ("opportunity to improve")
- Neutral observations ("we noticed")
- Supportive framing ("here's a strategy")
- Optional suggestions ("consider trying")
- Educational tone (explain the why)

**Tone Check Examples:**

❌ Bad: "You're drowning in debt and making terrible choices."
✅ Good: "Your credit utilization is high. Here are strategies that could help reduce interest charges."

❌ Bad: "Stop wasting money on subscriptions!"
✅ Good: "We noticed $180/month in subscriptions. An audit could identify services you no longer use."

❌ Bad: "You have no savings. You need to fix this immediately."
✅ Good: "Building an emergency fund could provide peace of mind. Start with a goal of $500."

**Disclosure Requirements:**

Every recommendation must include:
```
"This is educational content, not financial advice. Consult a licensed advisor 
for personalized guidance."
```

**Success Criteria:**
- Zero recommendations sent without active consent
- Consent revocation stops processing within 1 second
- Zero ineligible offers shown to users
- Zero shaming language in any recommendation
- 100% of recommendations include disclaimer
- Tone check catches ≥95% of problematic phrases

---

### 6. Operator View

**Must Have:**
- View detected signals for any user
- See 30-day and 180-day persona assignments
- Review generated recommendations with rationales
- Approve or override recommendations
- Access complete decision trace
- Flag recommendations for manual review

**Operator Dashboard Features:**

*User Search & Selection:*
- Search by user ID or name
- Filter by persona
- Sort by risk level or recommendation count

*Signal Visualization:*
- Tabular view of all computed signals
- Highlight signals triggering persona assignment
- Show trend over time (30d vs. 180d)
- Flag outliers or edge cases

*Persona Review:*
- Display assigned persona with criteria met
- Show prioritization logic if multiple personas match
- Highlight confidence scores
- Allow manual persona override

*Recommendation Queue:*
- List all generated recommendations
- Show rationale and data citations
- Display eligibility check results
- Indicate approval status
- Allow bulk approve/reject

*Decision Trace:*
- Step-by-step logic explanation
- Show which signals triggered which rules
- Display calculation details
- Highlight any guardrail interventions
- Export trace as JSON

*Audit Log:*
- All operator actions timestamped
- User consent history
- Recommendation approval history
- Override justifications
- Flag resolution notes

**Success Criteria:**
- Can review any user's profile in <5 seconds
- Decision trace includes all computational steps
- Operator can override any recommendation
- All actions are logged with timestamps
- Interface is usable without training

---

### 7. Evaluation & Metrics Harness

**Must Have:**
- Automated evaluation pipeline
- JSON/CSV metrics output
- 1-2 page summary report
- Per-user decision traces
- Deterministic evaluation (seeded randomness)

**Metrics to Compute:**

**Coverage:**
- % of users with assigned persona
- % of users with ≥3 detected behaviors
- % of users with ≥3 recommendations
- Average behaviors detected per user
- Persona distribution

**Explainability:**
- % of recommendations with plain-language rationale
- % of rationales citing concrete data
- Average rationale word count
- Reading level score (Flesch-Kincaid)

**Relevance:**
- Persona-education content alignment score
- Offer-eligibility match rate
- Duplicate offer detection
- Inappropriate recommendation flagging

**Latency:**
- Time to generate recommendations per user
- Signal detection time per user
- Persona assignment time per user
- Total pipeline time for 100 users

**Fairness:**
- Persona distribution by demographic (if available)
- Recommendation distribution by income level
- Tone check failure rate by persona
- Eligibility rejection rate by criteria

**Auditability:**
- % of recommendations with complete decision trace
- Missing data handling rate
- Error handling robustness

**Target Metrics:**

| Category | Metric | Target |
|----------|--------|--------|
| Coverage | Users with persona + ≥3 behaviors | 100% |
| Explainability | Recommendations with rationales | 100% |
| Latency | Time per user | <5 seconds |
| Auditability | Recommendations with traces | 100% |
| Code Quality | Passing tests | ≥10 tests |
| Documentation | Schema and decision log | Complete |

**Success Criteria:**
- All target metrics met or exceeded
- Evaluation runs deterministically
- Summary report auto-generates
- Metrics exportable as JSON/CSV
- Fairness analysis identifies no systemic bias

---

## Data Models

### SQLite Schema

**users table:**
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    income_level TEXT,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**accounts table:**
```sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    subtype TEXT,
    available_balance REAL,
    current_balance REAL,
    credit_limit REAL,
    iso_currency_code TEXT DEFAULT 'USD',
    holder_category TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**transactions table:**
```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    merchant_name TEXT,
    merchant_entity_id TEXT,
    payment_channel TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    pending BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**liabilities table:**
```sql
CREATE TABLE liabilities (
    liability_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    apr_percentage REAL,
    apr_type TEXT,
    minimum_payment_amount REAL,
    last_payment_amount REAL,
    is_overdue BOOLEAN DEFAULT FALSE,
    next_payment_due_date DATE,
    last_statement_balance REAL,
    interest_rate REAL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**signals table:**
```sql
CREATE TABLE signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    signal_type TEXT NOT NULL,
    signal_name TEXT NOT NULL,
    signal_value REAL,
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**personas table:**
```sql
CREATE TABLE personas (
    persona_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    persona_type TEXT NOT NULL,
    priority_rank INTEGER,
    criteria_met TEXT,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**recommendations table:**
```sql
CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    persona_type TEXT NOT NULL,
    content_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    rationale TEXT NOT NULL,
    eligibility_met BOOLEAN DEFAULT TRUE,
    approval_status TEXT DEFAULT 'pending',
    operator_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**audit_log table:**
```sql
CREATE TABLE audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### Parquet Analytics Schema

**user_profiles.parquet:**
- user_id
- window_days (30 or 180)
- all computed signals (columns)
- assigned_persona
- persona_priority
- recommendation_count

**recommendations_feed.parquet:**
- user_id
- persona_type
- recommendation_id
- content_type
- rationale
- approval_status
- timestamp

---

## Technical Architecture

### Tech Stack

**Frontend:**
- React + Next.js (fast prototyping, SSR capability)
- Tailwind CSS (rapid UI development)

**Backend:**
- Python FastAPI (strong ML/data library support)
- SQLite (single-file, portable, no server needed)
- Parquet (efficient columnar analytics)

**Deployment:**
- Docker (one-command startup, repeatable environments)

**Testing:**
- pytest (Python unit/integration tests)
- Vitest (React component tests)

---

## API Endpoints

### User Management
```
POST /users
POST /consent
GET /users/{user_id}
```

### Data Processing
```
GET /profile/{user_id}
GET /signals/{user_id}?window_days=30
GET /persona/{user_id}?window_days=30
```

### Recommendations
```
GET /recommendations/{user_id}
POST /feedback
```

### Operator
```
GET /operator/review
POST /operator/approve/{recommendation_id}
POST /operator/override/{recommendation_id}
POST /operator/flag/{recommendation_id}
```

---

## Out of Scope for MVP

### Features NOT Included:
- Live Plaid API integration
- Real-time transaction streaming
- Mobile app (web only)
- Multi-language support
- User authentication beyond basic consent
- Payment processing
- Investment advice
- Tax filing guidance
- Loan origination
- Credit score tracking
- Complex visualizations/charts
- Email notifications
- SMS alerts
- Push notifications
- Social features

### Technical Items NOT Included:
- Advanced ML models (neural networks, deep learning)
- Real-time model training
- A/B testing framework
- Feature flags
- Rate limiting
- CDN integration
- Advanced caching
- Microservices architecture
- Event streaming (Kafka, etc.)
- Message queues

---

## Risk Mitigation

**Biggest Risk:** Generating inappropriate or harmful recommendations  
**Mitigation:** Multi-layer guardrails (eligibility, tone checks, operator approval); comprehensive testing with edge cases

**Second Risk:** Synthetic data not representative of real patterns  
**Mitigation:** Validate against published financial behavior statistics; diverse persona templates; operator review

**Third Risk:** Performance degradation with 100+ users  
**Mitigation:** Optimize signal computation with vectorization; cache expensive calculations; use Parquet for analytics

**Fourth Risk:** Consent tracking failure  
**Mitigation:** Consent checks at every data access point; audit logging; fail-closed (no consent = no processing)

**Fifth Risk:** Tone guardrails insufficient  
**Mitigation:** Extensive prohibited phrase list; human review; continuous improvement based on operator flags

---

## Success Metrics for MVP

### Core Functionality:
- [ ] Generate 100 synthetic users with 180 days of transactions
- [ ] Detect ≥3 behavioral signals for 100% of users
- [ ] Assign persona to 100% of users
- [ ] Generate 3-5 recommendations per user with rationales
- [ ] All recommendations pass eligibility checks
- [ ] All recommendations pass tone checks

### Explainability:
- [ ] 100% of recommendations cite concrete data
- [ ] All rationales are plain-language (≤8th grade reading level)
- [ ] Decision traces complete for all recommendations

### Performance:
- [ ] Generate recommendations for 100 users in <500 seconds total
- [ ] Individual user profile generation <5 seconds

### Auditability:
- [ ] Operator can review any user's profile
- [ ] Complete audit log of all actions
- [ ] Decision traces exportable as JSON

### Guardrails:
- [ ] Zero recommendations without active consent
- [ ] Zero ineligible offers shown
- [ ] Zero shaming language detected in approved content

---

## Testing Checklist

### Data Generation:
- [ ] 100 users generated deterministically
- [ ] All users have 180+ days of transactions
- [ ] Account types distributed realistically
- [ ] Income levels span $20k-$200k range
- [ ] Credit behaviors range from pristine to problematic

### Signal Detection:
- [ ] Subscription detection identifies recurring merchants
- [ ] Savings calculations handle zero balances
- [ ] Credit utilization computed correctly for multiple cards
- [ ] Income detection handles irregular payroll
- [ ] Edge cases handled gracefully (no crashes)

### Persona Assignment:
- [ ] High Utilization detects 50%+ utilization correctly
- [ ] Variable Income Budgeter catches irregular income + low buffer
- [ ] Subscription-Heavy identifies 3+ recurring merchants
- [ ] Savings Builder rewards positive behaviors
- [ ] Paycheck-to-Paycheck detects cash flow issues
- [ ] Priority logic resolves multi-persona cases correctly

### Recommendations:
- [ ] Content maps to assigned persona
- [ ] Rationales cite specific account numbers
- [ ] Eligibility checks prevent ineligible offers
- [ ] No duplicate recommendations
- [ ] Disclaimer present on all recommendations

### Guardrails:
- [ ] Consent check blocks data processing
- [ ] Revoke consent stops recommendations immediately
- [ ] Tone check catches shaming language
- [ ] Eligibility filters out predatory products
- [ ] Existing account deduplication works

### Operator View:
- [ ] Can search and select any user
- [ ] Signals displayed correctly
- [ ] Decision trace is complete
- [ ] Can approve/override/flag recommendations
- [ ] Audit log records all actions

### Evaluation:
- [ ] All metrics compute correctly
- [ ] Summary report generates automatically
- [ ] Fairness analysis runs without errors
- [ ] Latency targets met (<5s per user)

---

## Deployment Checklist

- [ ] Docker container builds successfully
- [ ] One-command startup works (`docker-compose up`)
- [ ] README has clear setup instructions
- [ ] All dependencies documented
- [ ] Environment variables documented
- [ ] Sample data included
- [ ] Tests pass (≥10 tests)
- [ ] API endpoints documented
- [ ] Decision log complete
- [ ] Limitations documented

---

## Known Limitations & Trade-offs

1. **Synthetic Data**: Not real user behavior, may miss edge cases
2. **Rules-Based Logic**: No ML sophistication, but fully explainable
3. **Single Timeframe**: 30d and 180d only (no weekly or annual views)
4. **No Optimization**: Recommendations not personalized beyond persona
5. **English Only**: No multi-language support
6. **Desktop Web**: Not optimized for mobile
7. **No Authentication**: Basic consent tracking only
8. **Local Only**: Designed for laptop, not production scale
9. **No Real-Time**: Batch processing, not streaming
10. **Manual Approval**: Operator-in-loop required for production use

---

## Future Enhancements (Post-MVP)

### Phase 2:
- Machine learning models for persona classification
- Reinforcement learning for offer optimization
- Real-time transaction streaming
- Mobile-responsive design
- Email/SMS notification system

### Phase 3:
- Live Plaid integration
- Advanced visualizations (spending trends, category breakdowns)
- Goal tracking and progress monitoring
- Social comparison (anonymized benchmarks)
- Gamification elements

### Phase 4:
- Multi-bank aggregation
- Investment account support
- Tax optimization suggestions
- Retirement planning tools
- Credit score monitoring

---

## Compliance & Legal

**Disclaimers Required:**
- "This is educational content, not financial advice."
- "Consult a licensed advisor for personalized guidance."
- "We do not provide investment, tax, or legal advice."

**Privacy:**
- All data is synthetic (no real PII)
- Consent required before processing
- User can revoke consent at any time
- No data sold or shared with third parties

**Regulatory:**
- System does NOT provide regulated financial advice
- All content is educational and informational
- Partner offers are referrals only (not endorsements)
- Operator approval required before delivery

---

## Glossary

**Persona**: Financial behavior archetype assigned based on detected patterns  
**Signal**: Computed metric from transaction data (e.g., credit utilization)  
**Rationale**: Plain-language explanation for why a recommendation was made  
**Guardrail**: Automated check preventing harmful or ineligible recommendations  
**Decision Trace**: Complete audit trail showing system reasoning  
**Operator**: Human reviewer with override authority  
**Consent**: User's explicit permission to process financial data  
**Eligibility**: User meets minimum requirements for a partner offer  
**Tone Check**: Validation that content is empowering, not shaming

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-03  
**Next Review**: After MVP completion
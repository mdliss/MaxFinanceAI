# FinanceMaxAI V2: Enhanced User Features PRD

## Executive Summary

Building on the successful v1 implementation of SpendSense/FinanceMaxAI, this PRD outlines five high-impact features that will significantly enhance user engagement, provide actionable insights, and drive measurable behavior change.

---

## Problem Statement

While v1 successfully provides personalized recommendations and financial insights, users need:
- **Actionable goals** - Passive insights don't drive behavior change
- **Proactive guidance** - Users shouldn't need to check the app daily
- **Budget management** - Understanding spending isn't enough; users need guardrails
- **Subscription visibility** - Hidden recurring costs drain budgets
- **Progress tracking** - Users need a simple metric to measure financial health

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Daily Active Users (DAU) | Baseline | +40% |
| User Retention (30-day) | Baseline | +50% |
| Avg. Session Duration | Baseline | +35% |
| Feature Adoption | 0% | 60% |
| User-Reported Savings | $0 | $150/month avg |

---

## Feature Specifications

### Feature 1: Goal Setting & Tracking

**Priority:** P0 (Critical)
**Impact:** High engagement driver, transforms passive insights into actions

#### User Stories
- As a user, I want to set a savings goal so I can track progress toward my emergency fund
- As a user, I want to see projected completion dates so I know if I'm on track
- As a user, I want the chatbot to reference my goals so I get contextual advice

#### Requirements

**Backend (Python/FastAPI)**
```python
# Models
class FinancialGoal:
    goal_id: int
    user_id: str
    goal_type: str  # "save", "pay_debt", "invest"
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[datetime]
    created_at: datetime
    status: str  # "active", "completed", "abandoned"

# Endpoints
POST   /api/v1/goals                    # Create goal
GET    /api/v1/goals/{user_id}          # List user goals
PUT    /api/v1/goals/{goal_id}          # Update goal
DELETE /api/v1/goals/{goal_id}          # Delete goal
GET    /api/v1/goals/{goal_id}/progress # Get progress + projections
```

**Frontend (React/TypeScript)**
- Goals dashboard page with CRUD operations
- Progress visualization (circular progress bars, trend charts)
- Projected completion date calculator
- Integration with chatbot context

**Business Logic**
- Auto-calculate progress based on account balances
- Project completion date using historical savings rate
- Suggest realistic goals based on income/expenses
- Alert when falling behind or accelerating

#### Acceptance Criteria
- ✅ User can create up to 5 active goals
- ✅ Progress updates automatically daily
- ✅ Chatbot references goals in responses
- ✅ Visual progress indicators show percentage complete
- ✅ Realistic projections based on 90-day average savings rate

---

### Feature 2: Smart Budget System

**Priority:** P0 (Critical)
**Impact:** Core financial management, addresses all personas

#### User Stories
- As a user, I want an auto-generated budget based on my spending history
- As a user, I want alerts when I approach spending limits
- As a user, I want to adjust budgets and see the impact

#### Requirements

**Backend**
```python
# Models
class Budget:
    budget_id: int
    user_id: str
    category: str
    monthly_limit: Decimal
    alert_threshold: float  # 0.8 = 80%
    auto_generated: bool

class BudgetAlert:
    alert_id: int
    budget_id: int
    user_id: str
    alert_type: str  # "warning", "exceeded", "reset"
    percentage_used: float
    sent_at: datetime

# Endpoints
POST   /api/v1/budgets                    # Create budget
GET    /api/v1/budgets/{user_id}          # Get all budgets
PUT    /api/v1/budgets/{budget_id}        # Update budget
GET    /api/v1/budgets/{user_id}/status   # Current month status
POST   /api/v1/budgets/auto-generate      # Auto-generate from history
```

**Frontend**
- Budget configuration page
- Category-wise spending vs budget charts
- Alert notification system
- Budget adjustment simulator ("What if I reduce dining by $100?")

**Business Logic**
- Auto-generate using 50/30/20 rule + 3-month spending average
- Send alerts at 80%, 100%, 110% thresholds
- Roll over unused amounts (optional user setting)
- Suggest budget adjustments based on overspending patterns

#### Acceptance Criteria
- ✅ Auto-generate budgets for all spending categories
- ✅ Real-time spending tracking with percentage indicators
- ✅ Alerts sent via UI notification + email
- ✅ Budget vs actual comparison charts
- ✅ Historical budget performance tracking

---

### Feature 3: Smart Alerts System

**Priority:** P1 (High)
**Impact:** Proactive engagement without user effort

#### User Stories
- As a user, I want to be notified of unusual spending so I can catch fraud
- As a user, I want reminders for upcoming bills so I avoid late fees
- As a user, I want low balance warnings so I don't overdraft

#### Requirements

**Backend**
```python
# Models
class Alert:
    alert_id: int
    user_id: str
    alert_type: str
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    data: dict  # Contextual data
    is_read: bool
    created_at: datetime

# Alert Types
- unusual_spending
- low_balance
- large_transaction
- subscription_increase
- bill_reminder
- goal_milestone
- budget_exceeded

# Endpoints
GET    /api/v1/alerts/{user_id}           # Get alerts
PUT    /api/v1/alerts/{alert_id}/read     # Mark as read
POST   /api/v1/alerts/preferences         # Configure alert prefs
```

**Alert Detection Logic**
```python
# Scheduled job (runs every 6 hours)
def detect_alerts(user_id):
    # Unusual spending: >2 std deviations from category avg
    # Low balance: checking < $500
    # Large transaction: >$200 (or >3x category avg)
    # Subscription increase: recurring amount +10%
    # Bill reminder: due date within 3 days
```

**Frontend**
- Notification bell with unread count
- Alerts dropdown panel
- Alert preferences page
- Email digest settings

#### Acceptance Criteria
- ✅ Alerts generated within 1 hour of trigger event
- ✅ No duplicate alerts for same event within 24h
- ✅ User can configure alert types and delivery methods
- ✅ Critical alerts shown prominently
- ✅ Weekly digest email option

---

### Feature 4: Subscription Management Dashboard

**Priority:** P1 (High)
**Impact:** Immediate savings opportunity, high user satisfaction

#### User Stories
- As a user, I want to see all my subscriptions in one place
- As a user, I want to know how much I spend annually on subscriptions
- As a user, I want suggestions for subscriptions to cancel

#### Requirements

**Backend**
```python
# Models
class Subscription:
    subscription_id: int
    user_id: str
    merchant_name: str
    amount: Decimal
    frequency: str  # "monthly", "annual", "weekly"
    first_detected: datetime
    last_charge: datetime
    next_charge: datetime  # Estimated
    status: str  # "active", "cancelled"
    annual_cost: Decimal  # Calculated

# Endpoints
GET    /api/v1/subscriptions/{user_id}        # List all
PUT    /api/v1/subscriptions/{sub_id}/status  # Mark cancelled
GET    /api/v1/subscriptions/{user_id}/summary # Total annual cost
POST   /api/v1/subscriptions/detect           # Re-run detection
```

**Enhanced Detection Algorithm**
- Identify recurring merchants with 90%+ charge consistency
- Detect frequency changes (monthly → annual)
- Flag price increases >5%
- Estimate next charge date

**Frontend**
- Subscription list with annual cost
- Calendar view of upcoming charges
- Cost breakdown pie chart
- Savings calculator (if cancelled)
- Quick links to cancellation pages

#### Acceptance Criteria
- ✅ Detect 95%+ of actual subscriptions
- ✅ Accurate next charge date predictions (±3 days)
- ✅ Show annual cost per subscription
- ✅ Total annual subscription spend prominently displayed
- ✅ Suggestions for potentially unused subscriptions

---

### Feature 5: Financial Health Score

**Priority:** P1 (High)
**Impact:** Gamification drives engagement, simple KPI for users

#### User Stories
- As a user, I want a single score that summarizes my financial health
- As a user, I want to track how my score changes over time
- As a user, I want to know what actions will improve my score

#### Requirements

**Score Calculation**
```python
class FinancialHealthScore:
    total_score: int  # 0-100

    components:
        credit_utilization: float  # 30% weight
        savings_rate: float        # 25% weight
        emergency_fund: float      # 20% weight
        debt_to_income: float      # 15% weight
        payment_history: float     # 10% weight

    grade: str  # "Excellent", "Good", "Fair", "Poor"

# Scoring Formula
def calculate_score(user_data):
    cu_score = (1 - (utilization / 100)) * 30
    sr_score = min(savings_rate / 20, 1) * 25
    ef_score = min(emergency_fund_months / 6, 1) * 20
    di_score = (1 - min(debt_ratio, 1)) * 15
    ph_score = (on_time_payments / total_payments) * 10

    return cu_score + sr_score + ef_score + di_score + ph_score
```

**Backend**
```python
# Models
class HealthScore:
    score_id: int
    user_id: str
    score: int
    grade: str
    components: dict
    computed_at: datetime

# Endpoints
GET    /api/v1/health-score/{user_id}         # Current score
GET    /api/v1/health-score/{user_id}/history # Historical scores
GET    /api/v1/health-score/{user_id}/improve # Improvement suggestions
```

**Frontend**
- Large score display (0-100 with color gradient)
- Component breakdown chart
- Historical score line chart
- "How to Improve" action items
- Score sharing (optional)

#### Acceptance Criteria
- ✅ Score calculated daily for all active users
- ✅ 30-day score history displayed
- ✅ Component breakdown shown
- ✅ Top 3 improvement actions suggested
- ✅ Celebrate score improvements with animations

---

## Technical Architecture

### Database Schema Additions

**Note:** All new tables will be added to your existing SQLite database (`spendsense.db`). No new database required - just schema migrations to add these tables alongside your existing users, transactions, recommendations, etc.

```sql
-- Goals
CREATE TABLE financial_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    goal_type TEXT NOT NULL,
    target_amount DECIMAL(12,2) NOT NULL,
    current_amount DECIMAL(12,2) DEFAULT 0,
    deadline TIMESTAMP,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Budgets
CREATE TABLE budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    monthly_limit DECIMAL(12,2) NOT NULL,
    alert_threshold DECIMAL(3,2) DEFAULT 0.8,
    auto_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Alerts
CREATE TABLE alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,  -- JSON
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Subscriptions
CREATE TABLE subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    frequency TEXT NOT NULL,
    first_detected TIMESTAMP NOT NULL,
    last_charge TIMESTAMP,
    next_charge TIMESTAMP,
    status TEXT DEFAULT 'active',
    annual_cost DECIMAL(12,2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Health Scores
CREATE TABLE health_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    grade TEXT NOT NULL,
    components TEXT,  -- JSON
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Background Jobs

```python
# New scheduled jobs
- compute_health_scores()      # Daily at 2 AM
- detect_alerts()              # Every 6 hours
- update_goal_progress()       # Daily at 3 AM
- check_budget_status()        # Every 12 hours
- detect_subscriptions()       # Weekly
```

---

## API Changes

All new endpoints will follow existing patterns:
- RESTful conventions
- Consistent error handling
- OpenAPI/Swagger documentation
- Same auth/consent requirements

---

## Testing Strategy

### Unit Tests (Target: 90%+ coverage)
- Goal CRUD operations
- Budget calculation logic
- Alert detection algorithms
- Score calculation accuracy
- Subscription detection

### Integration Tests
- End-to-end goal creation → progress tracking
- Budget exceeded → alert generated
- New transaction → budget/alert updates
- Score calculation with real data

### Performance Tests
- Alert detection: <2s for 100 users
- Score calculation: <1s per user
- Budget status check: <500ms per user

---

## User Experience Flow

### First-Time User Flow
1. Complete onboarding (existing)
2. View auto-generated budget suggestions
3. Prompted to set first financial goal
4. See initial health score with explanation
5. Review detected subscriptions

### Returning User Flow
1. Dashboard shows health score prominently
2. Alert badge if new notifications
3. Goal progress visible in summary cards
4. Budget status indicators by category

---

## Implementation Phases

### Phase 1 - Foundation
- Setup database schema (5 new tables)
- Background job scheduler
- Core infrastructure

### Phase 2 - Core Features
- Goals CRUD + UI
- Budget system + auto-generation
- Alert detection system
- Health score calculation

### Phase 3 - Enhanced Features
- Subscription dashboard
- Chatbot integration
- Dashboard integration

### Phase 4 - Polish & Launch
- Feature-specific pages
- Performance optimization
- Comprehensive testing
- Documentation
- Production deployment

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alert fatigue | High | Smart thresholds, user preferences |
| Budget inaccuracy | Medium | 3-month avg + manual override |
| Subscription false positives | Low | Confidence score, manual review |
| Performance degradation | Medium | Caching, background jobs |
| User confusion | Medium | Onboarding tour, tooltips |

---

## Success Criteria

**Launch Readiness:**
- ✅ All 5 features implemented and tested
- ✅ 90%+ test coverage
- ✅ <2s page load times
- ✅ Mobile responsive
- ✅ Accessibility compliant

**Post-Launch:**
- 60%+ feature adoption rate
- <5% error rate
- Average health score improvement of 5+ points
- User-reported savings of $100+/month
- 4+ star user satisfaction rating

---

## Future Enhancements (V3)

- Social features (compare with friends)
- Advanced budgeting (envelope method)
- Bill negotiation assistant
- Investment tracking
- Tax optimization suggestions

---

## Appendix

### Related Documents
- V1 Rubric: `/rubric.md`
- Existing API Docs: `/backend/README.md`
- Database Schema: `/backend/app/database.py`

### Stakeholders
- Product Owner: Max
- Developer: Max
- End Users: 50-100 synthetic + beta testers

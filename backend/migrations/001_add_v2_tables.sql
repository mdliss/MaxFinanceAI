-- Migration: Add V2 Enhancement Tables
-- Date: 2025-11-07
-- Description: Adds 5 new tables for V2 features: goals, budgets, alerts, subscriptions, and health scores

-- 1. Financial Goals Table
CREATE TABLE IF NOT EXISTS financial_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    goal_type TEXT NOT NULL,  -- emergency_fund, vacation, debt_payoff, major_purchase, retirement, custom
    title TEXT NOT NULL,
    description TEXT,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0.0,
    target_date TEXT,  -- ISO 8601 date
    status TEXT DEFAULT 'active',  -- active, completed, paused, cancelled
    progress_percent REAL DEFAULT 0.0,
    projected_completion_date TEXT,  -- ISO 8601 date, calculated
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goals_user_id ON financial_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON financial_goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_created_at ON financial_goals(created_at);

-- 2. Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,  -- dining, transportation, shopping, entertainment, etc.
    amount REAL NOT NULL,
    period TEXT DEFAULT 'monthly',  -- weekly, monthly, yearly
    spent_amount REAL DEFAULT 0.0,
    remaining_amount REAL,
    status TEXT DEFAULT 'active',  -- active, exceeded, warning, inactive
    is_auto_generated INTEGER DEFAULT 0,  -- 0 = manual, 1 = auto-generated
    rollover_enabled INTEGER DEFAULT 0,  -- 0 = no rollover, 1 = allow rollover
    alert_threshold REAL DEFAULT 80.0,  -- Alert when spent reaches this % of budget
    period_start_date TEXT,  -- ISO 8601 date
    period_end_date TEXT,  -- ISO 8601 date
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category);
CREATE INDEX IF NOT EXISTS idx_budgets_status ON budgets(status);
CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period_start_date, period_end_date);

-- 3. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- budget_exceeded, unusual_spending, goal_milestone, subscription_renewal, low_balance, etc.
    severity TEXT DEFAULT 'info',  -- info, warning, critical
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    related_entity_type TEXT,  -- budget, goal, transaction, subscription, account
    related_entity_id TEXT,
    is_read INTEGER DEFAULT 0,
    is_dismissed INTEGER DEFAULT 0,
    action_url TEXT,  -- Optional link to related entity
    meta_data TEXT,  -- JSON string for additional data
    created_at TEXT DEFAULT (datetime('now')),
    read_at TEXT,
    dismissed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts(is_read);

-- 4. Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    amount REAL NOT NULL,
    frequency TEXT DEFAULT 'monthly',  -- weekly, monthly, quarterly, yearly
    category TEXT,
    next_billing_date TEXT,  -- ISO 8601 date
    status TEXT DEFAULT 'active',  -- active, cancelled, paused
    auto_detected INTEGER DEFAULT 1,  -- 1 = auto-detected, 0 = manually added
    first_detected_date TEXT,
    last_transaction_date TEXT,
    transaction_count INTEGER DEFAULT 0,
    annual_cost REAL,  -- Calculated annual cost
    cancellation_difficulty TEXT,  -- easy, medium, hard
    cancellation_url TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date);
CREATE INDEX IF NOT EXISTS idx_subscriptions_merchant ON subscriptions(merchant_name);

-- 5. Health Scores Table
CREATE TABLE IF NOT EXISTS health_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    overall_score INTEGER NOT NULL,  -- 0-100
    savings_score INTEGER,  -- 0-100
    spending_score INTEGER,  -- 0-100
    debt_score INTEGER,  -- 0-100
    emergency_fund_score INTEGER,  -- 0-100
    budget_adherence_score INTEGER,  -- 0-100
    score_trend TEXT,  -- improving, declining, stable
    recommendations_applied_count INTEGER DEFAULT 0,
    days_since_last_calculation INTEGER DEFAULT 0,
    meta_data TEXT,  -- JSON string with detailed breakdown
    computed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_health_scores_user_id ON health_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_health_scores_computed_at ON health_scores(computed_at);
CREATE INDEX IF NOT EXISTS idx_health_scores_overall ON health_scores(overall_score);

-- Create triggers to update updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_goals_timestamp
AFTER UPDATE ON financial_goals
FOR EACH ROW
BEGIN
    UPDATE financial_goals SET updated_at = datetime('now') WHERE goal_id = NEW.goal_id;
END;

CREATE TRIGGER IF NOT EXISTS update_budgets_timestamp
AFTER UPDATE ON budgets
FOR EACH ROW
BEGIN
    UPDATE budgets SET updated_at = datetime('now') WHERE budget_id = NEW.budget_id;
END;

CREATE TRIGGER IF NOT EXISTS update_subscriptions_timestamp
AFTER UPDATE ON subscriptions
FOR EACH ROW
BEGIN
    UPDATE subscriptions SET updated_at = datetime('now') WHERE subscription_id = NEW.subscription_id;
END;

-- Verify tables were created
SELECT 'Migration completed successfully. Added tables:' as status;
SELECT name FROM sqlite_master WHERE type='table' AND name IN (
    'financial_goals', 'budgets', 'alerts', 'subscriptions', 'health_scores'
) ORDER BY name;

#!/bin/bash

# MaxFinanceAI V2 Feature Testing Script
# Tests Goals, Budgets, and Smart Alerts

set -e

BASE_URL="http://localhost:8000/api/v1"
USER_ID="test_user_$(date +%s)"

echo "=================================="
echo "MaxFinanceAI V2 Testing Suite"
echo "=================================="
echo ""
echo "Testing with user_id: $USER_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5

    echo -e "${BLUE}Testing: $name${NC}"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓ Passed${NC} (Status: $status_code)"
        echo "Response: $body" | jq -C '.' 2>/dev/null || echo "$body"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Failed${NC} (Expected: $expected_status, Got: $status_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo "=================================="
echo "PART 1: Financial Goals System"
echo "=================================="
echo ""

# First, create a user
echo -e "${YELLOW}1.0 Creating user...${NC}"
USER_DATA='{
    "user_id": "'$USER_ID'",
    "name": "Test User",
    "age": 30,
    "income_level": "middle"
}'
test_endpoint "Create User" "POST" "/users/" "$USER_DATA" "201"

# Grant consent
echo -e "${YELLOW}1.0b Granting consent...${NC}"
CONSENT_DATA='{
    "user_id": "'$USER_ID'",
    "consent_status": true
}'
test_endpoint "Grant Consent" "POST" "/consent/" "$CONSENT_DATA" "200"

# Create a savings goal
echo -e "${YELLOW}1.1 Creating a savings goal...${NC}"
GOAL_DATA='{
    "user_id": "'$USER_ID'",
    "goal_type": "emergency_fund",
    "title": "Emergency Fund",
    "description": "Build 3-month emergency fund",
    "target_amount": 5000.00,
    "target_date": "'$(date -v+90d +%Y-%m-%d)'"
}'
test_endpoint "Create Savings Goal" "POST" "/goals/" "$GOAL_DATA" "200"

# Get all goals
echo -e "${YELLOW}1.2 Fetching all goals...${NC}"
test_endpoint "Get All Goals" "GET" "/goals/$USER_ID" "" "200"

# Create another goal (debt payoff)
echo -e "${YELLOW}1.3 Creating a debt payoff goal...${NC}"
GOAL_DATA2='{
    "user_id": "'$USER_ID'",
    "goal_type": "debt_payoff",
    "title": "Credit Card Payoff",
    "description": "Pay off remaining credit card debt",
    "target_amount": 10000.00,
    "target_date": "'$(date -v+180d +%Y-%m-%d)'"
}'
test_endpoint "Create Debt Goal" "POST" "/goals/" "$GOAL_DATA2" "200"

# Get goal with projection (capture goal_id from previous response)
echo -e "${YELLOW}1.4 Getting goal with 90-day projection...${NC}"
# Note: You'll need to replace GOAL_ID with actual ID from response
echo "(To test projection, manually call: GET /goals/$USER_ID/GOAL_ID)"
echo ""

echo "=================================="
echo "PART 2: Budget System"
echo "=================================="
echo ""

# Create a budget category
echo -e "${YELLOW}2.1 Creating a budget category (Groceries)...${NC}"
BUDGET_DATA='{
    "user_id": "'$USER_ID'",
    "category": "groceries",
    "amount": 600.00,
    "period": "monthly",
    "rollover_enabled": false,
    "alert_threshold": 80.0
}'
test_endpoint "Create Budget" "POST" "/budgets/" "$BUDGET_DATA" "200"

# Create another budget (Entertainment)
echo -e "${YELLOW}2.2 Creating budget (Entertainment)...${NC}"
BUDGET_DATA2='{
    "user_id": "'$USER_ID'",
    "category": "entertainment",
    "amount": 200.00,
    "period": "monthly",
    "rollover_enabled": false,
    "alert_threshold": 80.0
}'
test_endpoint "Create Entertainment Budget" "POST" "/budgets/" "$BUDGET_DATA2" "200"

# Get all budgets
echo -e "${YELLOW}2.3 Fetching all budgets...${NC}"
test_endpoint "Get All Budgets" "GET" "/budgets/$USER_ID" "" "200"

# Get budget summary
echo -e "${YELLOW}2.4 Getting budget summary...${NC}"
test_endpoint "Get Budget Summary" "GET" "/budgets/$USER_ID/summary" "" "200"

# Auto-generate budgets (if user has transaction history)
echo -e "${YELLOW}2.5 Auto-generating budgets (90-day analysis)...${NC}"
test_endpoint "Auto-Generate Budgets" "POST" "/budgets/$USER_ID/auto-generate" "" "200"

echo "=================================="
echo "PART 3: Smart Alerts System"
echo "=================================="
echo ""

# Create a manual alert
echo -e "${YELLOW}3.1 Creating a manual alert...${NC}"
ALERT_DATA='{
    "user_id": "'$USER_ID'",
    "alert_type": "spending",
    "severity": "warning",
    "title": "High Spending Detected",
    "message": "Your spending today is higher than usual",
    "action_url": "/dashboard"
}'
test_endpoint "Create Alert" "POST" "/alerts/" "$ALERT_DATA" "200"

# Get all alerts
echo -e "${YELLOW}3.2 Fetching all alerts...${NC}"
test_endpoint "Get All Alerts" "GET" "/alerts/$USER_ID" "" "200"

# Get unread count
echo -e "${YELLOW}3.3 Getting unread alert count...${NC}"
test_endpoint "Get Unread Count" "GET" "/alerts/$USER_ID/unread-count" "" "200"

# Auto-generate alerts (this will detect budget/goal milestones, unusual spending, etc.)
echo -e "${YELLOW}3.4 Auto-generating smart alerts...${NC}"
test_endpoint "Auto-Generate Alerts" "POST" "/alerts/$USER_ID/generate" "" "200"

# Mark all as read
echo -e "${YELLOW}3.5 Marking all alerts as read...${NC}"
test_endpoint "Mark All Read" "POST" "/alerts/$USER_ID/mark-all-read" "" "200"

echo "=================================="
echo "PART 4: End-to-End Workflow Test"
echo "=================================="
echo ""

echo -e "${YELLOW}4.1 Creating a complete financial scenario...${NC}"
echo "Scenario: User sets a goal, creates budgets, and receives alerts"
echo ""

# Create investment goal
INVESTMENT_GOAL='{
    "user_id": "'$USER_ID'",
    "goal_type": "retirement",
    "title": "Investment Portfolio",
    "description": "Build diversified investment portfolio",
    "target_amount": 20000.00,
    "target_date": "'$(date -v+365d +%Y-%m-%d)'"
}'
test_endpoint "Create Investment Goal" "POST" "/goals/" "$INVESTMENT_GOAL" "200"

# Create dining budget
DINING_BUDGET='{
    "user_id": "'$USER_ID'",
    "category": "dining",
    "amount": 400.00,
    "period": "monthly",
    "rollover_enabled": false,
    "alert_threshold": 75.0
}'
test_endpoint "Create Dining Budget" "POST" "/budgets/" "$DINING_BUDGET" "200"

# Trigger alert generation to see if system detects anything
test_endpoint "Generate Smart Alerts" "POST" "/alerts/$USER_ID/generate" "" "200"

# Get final summary
echo -e "${YELLOW}4.2 Getting final summary...${NC}"
test_endpoint "Final Goals List" "GET" "/goals/$USER_ID" "" "200"
test_endpoint "Final Budget Summary" "GET" "/budgets/$USER_ID/summary" "" "200"
test_endpoint "Final Alerts List" "GET" "/alerts/$USER_ID?unread_only=true" "" "200"

echo "=================================="
echo "Test Results Summary"
echo "=================================="
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your V2 backend is working perfectly!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
fi

echo ""
echo "=================================="
echo "What You Can Do Next:"
echo "=================================="
echo ""
echo "1. View the data in your database:"
echo "   docker exec -it maxfinanceai-backend-1 sqlite3 /app/maxfinance.db"
echo "   sqlite> SELECT * FROM goals WHERE user_id='$USER_ID';"
echo "   sqlite> SELECT * FROM budgets WHERE user_id='$USER_ID';"
echo "   sqlite> SELECT * FROM alerts WHERE user_id='$USER_ID';"
echo ""
echo "2. Test individual endpoints with curl:"
echo "   curl http://localhost:8000/api/v1/goals/$USER_ID"
echo "   curl http://localhost:8000/api/v1/budgets/$USER_ID/summary"
echo "   curl http://localhost:8000/api/v1/alerts/$USER_ID/unread-count"
echo ""
echo "3. Build the frontend UI:"
echo "   - Goals Dashboard"
echo "   - Budget Tracker"
echo "   - Alerts Center"
echo ""
echo "4. Test the chatbot integration:"
echo "   - Ask about goals: 'What are my financial goals?'"
echo "   - Ask about budgets: 'How am I doing on my grocery budget?'"
echo "   - Ask for alerts: 'Do I have any alerts?'"
echo ""
echo "Your test user_id for this session: $USER_ID"
echo ""

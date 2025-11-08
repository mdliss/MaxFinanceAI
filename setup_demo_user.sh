#!/bin/bash

# Setup script for demo user

USER_ID="demo"
BASE_URL="http://localhost:8000/api/v1"

echo "🚀 Setting up demo user: $USER_ID"
echo ""

# Create user
echo "1. Creating user..."
curl -s -X POST $BASE_URL/users/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"name\": \"Demo User\",
    \"age\": 30,
    \"income_level\": \"medium\"
  }" | jq -r '.user_id // .detail'

# Grant consent
echo "2. Granting consent..."
curl -s -X POST $BASE_URL/consent/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"consent_status\": true
  }" | jq -r '.message // .detail'

# Create financial goals
echo "3. Creating financial goals..."
curl -s -X POST $BASE_URL/goals/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"goal_type\": \"emergency_fund\",
    \"title\": \"Emergency Fund\",
    \"description\": \"Build 6-month emergency fund\",
    \"target_amount\": 15000.00,
    \"target_date\": \"2026-06-01\"
  }" | jq -r '.title // .detail'

curl -s -X POST $BASE_URL/goals/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"goal_type\": \"vacation\",
    \"title\": \"Summer Vacation\",
    \"description\": \"Save for summer trip to Europe\",
    \"target_amount\": 5000.00,
    \"target_date\": \"2026-07-15\"
  }" | jq -r '.title // .detail'

# Create budgets
echo "4. Creating budgets..."
curl -s -X POST $BASE_URL/budgets/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"category\": \"groceries\",
    \"amount\": 600.00,
    \"period\": \"monthly\",
    \"alert_threshold\": 80.0
  }" | jq -r '.category // .detail'

curl -s -X POST $BASE_URL/budgets/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"category\": \"dining\",
    \"amount\": 400.00,
    \"period\": \"monthly\",
    \"alert_threshold\": 75.0
  }" | jq -r '.category // .detail'

curl -s -X POST $BASE_URL/budgets/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"category\": \"entertainment\",
    \"amount\": 200.00,
    \"period\": \"monthly\",
    \"alert_threshold\": 80.0
  }" | jq -r '.category // .detail'

# Create an alert
echo "5. Creating alerts..."
curl -s -X POST $BASE_URL/alerts/ \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"alert_type\": \"goal\",
    \"severity\": \"info\",
    \"title\": \"Welcome to MaxFinanceAI!\",
    \"message\": \"Start tracking your financial goals and budgets today\",
    \"action_url\": \"/dashboard\"
  }" | jq -r '.title // .detail'

echo ""
echo "✅ Demo user setup complete!"
echo ""
echo "You can now access the dashboard at http://localhost:3001/dashboard"
echo "User ID: $USER_ID"

#!/bin/bash

echo "🎲 Generating Test Data for SpendSense..."
echo ""

# Get a user with consent
USER_ID="test_user_2"

echo "1️⃣ Detecting signals for user: $USER_ID"
curl -X POST "http://localhost:8000/api/v1/signals/${USER_ID}/detect?window_days=30" \
  -H "Content-Type: application/json" 2>&1 | python3 -m json.tool

echo ""
echo "2️⃣ Assigning persona for user: $USER_ID"
curl -X POST "http://localhost:8000/api/v1/personas/${USER_ID}/assign?window_days=30" \
  -H "Content-Type: application/json" 2>&1 | python3 -m json.tool

echo ""
echo "3️⃣ Generating recommendations for user: $USER_ID"
curl -X POST "http://localhost:8000/api/v1/recommendations/${USER_ID}/generate?window_days=30&count=5" \
  -H "Content-Type: application/json" 2>&1 | python3 -m json.tool

echo ""
echo "✅ Test data generated! You should now see recommendations in the dashboard."
echo "🌐 Visit: http://localhost:3001/operator"

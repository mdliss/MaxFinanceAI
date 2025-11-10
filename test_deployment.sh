#!/bin/bash

# Quick deployment verification script
# Usage: ./test_deployment.sh <RAILWAY_URL>

RAILWAY_URL="${1:-https://your-app.railway.app}"
FRONTEND_URL="${2:-https://frontend-bky8pef7o-max-liss-projects.vercel.app}"

echo "============================================"
echo "  DEPLOYMENT VERIFICATION TEST"
echo "============================================"
echo ""
echo "Backend:  $RAILWAY_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Backend Health
echo -n "1. Backend Health Check... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health/")
if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $HEALTH)${NC}"
    exit 1
fi

# Test 2: Dataset Status
echo -n "2. Dataset Generation Status... "
DATASET=$(curl -s "$RAILWAY_URL/status/dataset")
USER_COUNT=$(echo "$DATASET" | grep -o '"user_count":[0-9]*' | cut -d':' -f2)
IS_COMPLETE=$(echo "$DATASET" | grep -o '"is_complete":[a-z]*' | cut -d':' -f2)

if [ "$IS_COMPLETE" = "true" ]; then
    echo -e "${GREEN}✅ COMPLETE ($USER_COUNT users)${NC}"
elif [ "$USER_COUNT" -gt "0" ]; then
    echo -e "${YELLOW}⏳ GENERATING ($USER_COUNT/100 users)${NC}"
else
    echo -e "${YELLOW}⏳ STARTING${NC}"
fi

# Test 3: Demo User
echo -n "3. Demo User Exists... "
DEMO_CHECK=$(curl -s "$RAILWAY_URL/api/v1/users/demo")
if echo "$DEMO_CHECK" | grep -q "demo"; then
    echo -e "${GREEN}✅ EXISTS${NC}"
else
    echo -e "${YELLOW}⚠️  NOT YET (will be created after dataset completes)${NC}"
fi

# Test 4: Operator Dashboard API
echo -n "4. Operator Dashboard API... "
STATS=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/v1/operator/dashboard/stats")
if [ "$STATS" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $STATS)${NC}"
fi

# Test 5: Evaluation Metrics
echo -n "5. Evaluation Metrics... "
METRICS=$(curl -s "$RAILWAY_URL/api/v1/operator/evaluation/metrics")
COVERAGE=$(echo "$METRICS" | grep -o '"coverage_percentage":[0-9.]*' | cut -d':' -f2)

if [ ! -z "$COVERAGE" ]; then
    if (( $(echo "$COVERAGE >= 100" | bc -l 2>/dev/null) )); then
        echo -e "${GREEN}✅ 100% COVERAGE${NC}"
    else
        echo -e "${YELLOW}⚠️  ${COVERAGE}% COVERAGE (expected 100%)${NC}"
    fi
else
    echo -e "${YELLOW}⏳ WAITING FOR DATA${NC}"
fi

# Test 6: Frontend Health
echo -n "6. Frontend Accessible... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $FRONTEND_STATUS)${NC}"
fi

echo ""
echo "============================================"
echo "  QUICK ACCESS LINKS"
echo "============================================"
echo ""
echo "🎯 OPERATOR DASHBOARD:"
echo "   $FRONTEND_URL/operator"
echo ""
echo "📊 USER DASHBOARD (demo user):"
echo "   $FRONTEND_URL/dashboard"
echo ""
echo "👤 LOGIN PAGE:"
echo "   $FRONTEND_URL/login"
echo ""
echo "📈 BACKEND METRICS:"
echo "   $RAILWAY_URL/api/v1/operator/evaluation/metrics"
echo ""
echo "🔍 DATASET STATUS:"
echo "   $RAILWAY_URL/status/dataset"
echo ""
echo "============================================"
echo "  TESTING INSTRUCTIONS"
echo "============================================"
echo ""
echo "1. Open Operator Dashboard:"
echo "   → $FRONTEND_URL/operator"
echo "   → Should show:"
echo "     • Quality Metrics"
echo "     • User statistics"
echo "     • Persona distribution"
echo "     • Recommendations flagged"
echo ""
echo "2. Check Coverage:"
echo "   → Should show 100% (users with persona + ≥3 behaviors)"
echo "   → If not 100%, wait for dataset generation to complete"
echo ""
echo "3. Test Demo User Login:"
echo "   → Go to: $FRONTEND_URL/login"
echo "   → Enter user_id: demo"
echo "   → Should redirect to dashboard with user data"
echo ""
echo "4. Verify Recommendations:"
echo "   → In operator dashboard, click on any user"
echo "   → Should see signals, personas, recommendations"
echo "   → All recommendations should have rationales"
echo ""
echo "============================================"
echo ""

if [ "$IS_COMPLETE" = "true" ] && [ ! -z "$COVERAGE" ] && (( $(echo "$COVERAGE >= 100" | bc -l 2>/dev/null) )); then
    echo -e "${GREEN}✅ ALL SYSTEMS OPERATIONAL - 100% COVERAGE ACHIEVED${NC}"
else
    echo -e "${YELLOW}⏳ SYSTEM INITIALIZING - CHECK AGAIN IN 10-15 MINUTES${NC}"
fi

echo ""

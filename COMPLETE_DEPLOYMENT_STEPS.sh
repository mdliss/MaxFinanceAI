#!/bin/bash

# Complete deployment automation script
# This will deploy everything and configure it correctly

set -e

echo "=========================================="
echo "  MAXFINANCEAI DEPLOYMENT AUTOMATION"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Commit the backend fix
echo -e "${BLUE}Step 1: Committing backend fixes...${NC}"
cd /Users/max/MaxFinanceAI
git add backend/app/api/admin.py
git add backend/populate_full_dataset.py
git add backend/start.sh
git add backend/app/main.py
git commit -m "Fix 100% coverage + auto demo user + FastAPI dependency injection" || echo "Already committed"
echo -e "${GREEN}✅ Code committed${NC}"
echo ""

# Step 2: Push to trigger Railway deployment
echo -e "${BLUE}Step 2: Pushing to GitHub (triggers Railway)...${NC}"
git push
echo -e "${GREEN}✅ Pushed to GitHub${NC}"
echo ""

# Step 3: Wait for Railway to start
echo -e "${YELLOW}⏳ Waiting 30 seconds for Railway to start building...${NC}"
sleep 30

echo ""
echo "=========================================="
echo "  MANUAL STEPS REQUIRED"
echo "=========================================="
echo ""
echo -e "${YELLOW}I need you to do these 3 things:${NC}"
echo ""

echo -e "${BLUE}1. GET YOUR RAILWAY BACKEND URL:${NC}"
echo "   → Go to: https://railway.app/dashboard"
echo "   → Click on your backend service"
echo "   → Go to 'Settings' tab"
echo "   → Copy the 'Public Domain' URL"
echo "   → It looks like: https://something-production-xxxx.up.railway.app"
echo ""

echo -e "${BLUE}2. SET VERCEL ENVIRONMENT VARIABLE:${NC}"
echo "   → Go to: https://vercel.com/max-liss-projects/frontend/settings/environment-variables"
echo "   → Click 'Add New'"
echo "   → Name: NEXT_PUBLIC_API_URL"
echo "   → Value: https://YOUR-RAILWAY-URL.railway.app/api/v1"
echo "   → Environment: Check 'Production'"
echo "   → Click 'Save'"
echo ""

echo -e "${BLUE}3. REDEPLOY FRONTEND:${NC}"
echo "   → Option A: In Vercel dashboard → Deployments → Click 'Redeploy'"
echo "   → Option B: Run in terminal:"
echo "      cd /Users/max/MaxFinanceAI/frontend"
echo "      vercel --prod"
echo ""

echo "=========================================="
echo "  VERIFICATION (after 10-15 minutes)"
echo "=========================================="
echo ""
echo "Check dataset generation:"
echo "  curl https://YOUR-RAILWAY-URL.railway.app/status/dataset"
echo ""
echo "Check operator metrics:"
echo "  curl https://YOUR-RAILWAY-URL.railway.app/api/v1/operator/evaluation/metrics"
echo ""
echo "Test frontend:"
echo "  https://frontend-bky8pef7o-max-liss-projects.vercel.app/operator"
echo ""
echo "Should see:"
echo "  ✅ 100% coverage"
echo "  ✅ Numbers on metric cards"
echo "  ✅ Green PASS badges"
echo ""

echo -e "${GREEN}Backend code is ready and pushed to Railway!${NC}"
echo -e "${YELLOW}Complete the 3 manual steps above to finish deployment.${NC}"

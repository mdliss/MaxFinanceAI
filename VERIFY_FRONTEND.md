# How to Tell if Frontend is Working

## Quick Test URLs

### 1. **Operator Dashboard** (Main Testing Page)
```
https://your-frontend.vercel.app/operator
```

**What You Should See:**
- ✅ Quality Metrics card showing:
  - AVG BEHAVIORS/USER
  - PERSONAS ASSIGNED
  - RECOMMENDATIONS FLAGGED
  - FLAG RATE %
- ✅ Rubric Compliance Summary showing:
  - Coverage (users with persona ≥3 behaviors)
  - Explainability (recommendations with rationales)
  - Latency (avg time to generate recommendations)
  - Auditability (recommendations with decision traces)
- ✅ All metrics showing **PASS** in green
- ✅ Coverage showing **100%** (may take 10-15 min after deployment)

**What FAIL Looks Like:**
- ❌ "Failed to fetch" error
- ❌ Blank page or loading spinner forever
- ❌ Coverage showing <100%
- ❌ "Cannot connect to backend" message

---

### 2. **User Dashboard** (Demo User Test)
```
https://your-frontend.vercel.app/dashboard
```

**What You Should See:**
- ✅ User greeting (e.g., "Welcome, Demo User")
- ✅ Account balances (Checking, Savings, Credit Card)
- ✅ Recent transactions list
- ✅ Financial goals with progress bars
- ✅ Budget tracking cards

**What FAIL Looks Like:**
- ❌ "Please log in" message
- ❌ Empty dashboard
- ❌ API connection errors

---

### 3. **Login Page** (Demo User Login)
```
https://your-frontend.vercel.app/login
```

**How to Test:**
1. Enter user_id: `demo`
2. Click "Log In"
3. Should redirect to `/dashboard`
4. Should show demo user's data

**What FAIL Looks Like:**
- ❌ "User not found" error
- ❌ Login button doesn't work
- ❌ Stuck on login page after clicking

---

## Automated Testing Script

Run this to check everything at once:

```bash
./test_deployment.sh https://your-railway-url.railway.app https://your-frontend.vercel.app
```

**Expected Output:**
```
1. Backend Health Check... ✅ PASS
2. Dataset Generation Status... ✅ COMPLETE (100 users)
3. Demo User Exists... ✅ EXISTS
4. Operator Dashboard API... ✅ PASS
5. Evaluation Metrics... ✅ 100% COVERAGE
6. Frontend Accessible... ✅ PASS
```

---

## Manual Verification Steps

### Step 1: Check Backend is Running
```bash
curl https://your-railway-url.railway.app/health/
```

**Expected:** `{"status":"healthy"}`

---

### Step 2: Check Dataset Status
```bash
curl https://your-railway-url.railway.app/status/dataset
```

**Expected (when complete):**
```json
{
  "status": "complete",
  "user_count": 100,
  "expected_users": 100,
  "is_complete": true
}
```

**Expected (while generating):**
```json
{
  "status": "generating",
  "user_count": 45,
  "expected_users": 100,
  "is_complete": false
}
```

---

### Step 3: Check Coverage Percentage
```bash
curl https://your-railway-url.railway.app/api/v1/operator/evaluation/metrics | jq '.coverage'
```

**Expected:**
```json
{
  "total_users": 100,
  "users_with_persona": 100,
  "users_with_3plus_behaviors": 100,
  "coverage_percentage": 100.0
}
```

---

### Step 4: Open Operator Dashboard in Browser

1. Go to: `https://your-frontend.vercel.app/operator`
2. **Look for these specific elements:**
   - Top left: "Quality Metrics" heading
   - 4 metric cards with numbers
   - "Rubric Compliance Summary" section
   - Green "PASS" badges (or yellow "FAIL" if still generating)
   - Coverage percentage (should be 100%)

3. **Scroll down to see:**
   - User list table
   - Persona distribution chart
   - Recommendation statistics

---

### Step 5: Test Demo User

1. Go to: `https://your-frontend.vercel.app/login`
2. Type: `demo`
3. Click "Log In"
4. Should see dashboard with:
   - Account balances
   - Transaction history
   - Goals and budgets

---

## Common Issues & Fixes

### Issue: Frontend shows "Cannot connect to backend"

**Cause:** Frontend doesn't have the correct API URL

**Fix:**
1. Go to Vercel dashboard: https://vercel.com/max-liss-projects/frontend/settings/environment-variables
2. Set: `NEXT_PUBLIC_API_URL = https://your-railway-url.railway.app/api/v1`
3. Redeploy frontend

---

### Issue: Operator dashboard is blank

**Cause:** Dataset generation not complete yet

**Fix:**
- Wait 10-15 minutes after Railway deployment
- Check status: `curl .../status/dataset`
- Once `is_complete: true`, refresh operator page

---

### Issue: Coverage shows 99% instead of 100%

**Cause:** One user has < 3 signal types

**Fix:**
```bash
curl -X POST https://your-railway-url.railway.app/api/v1/admin/fix-coverage
```

Then refresh operator dashboard. Should show 100%.

---

### Issue: Demo user not found

**Cause:** Demo user creation script hasn't run yet

**Fix:**
```bash
curl -X POST https://your-railway-url.railway.app/api/v1/admin/setup-demo-user
```

Then try logging in again with `demo`.

---

## Quick Visual Checklist

**Frontend is Working if:**
- [ ] Operator dashboard loads (not blank)
- [ ] Shows 4 metric cards with numbers
- [ ] Shows "Rubric Compliance Summary"
- [ ] Coverage is 100% (or close if still generating)
- [ ] Can log in with user_id `demo`
- [ ] Dashboard shows account balances
- [ ] Can see user list in operator dashboard

**Frontend is NOT Working if:**
- [ ] Page is completely blank
- [ ] Shows "Failed to fetch" or network errors
- [ ] Login doesn't redirect to dashboard
- [ ] Operator dashboard shows no data
- [ ] Browser console shows CORS errors

---

## Expected Final State

**After 15 minutes of deployment:**

1. **Backend:**
   - ✅ 100 users generated
   - ✅ 1 demo user created
   - ✅ 100% coverage achieved
   - ✅ All endpoints responding

2. **Frontend:**
   - ✅ Operator dashboard fully populated
   - ✅ All metrics showing PASS
   - ✅ Demo user can log in
   - ✅ Dashboard shows complete data

3. **Rubric Compliance:**
   - ✅ Coverage: 100%
   - ✅ Explainability: 100%
   - ✅ Auditability: 100%
   - ✅ Latency: <5s
   - ✅ Users: 100 (within 50-100 range)

---

## Still Not Sure?

**Just open this URL in your browser:**
```
https://your-frontend.vercel.app/operator
```

**If you see this, it's working:**
- Numbers on metric cards
- Green "PASS" badges
- "100%" coverage percentage
- User table with data

**If you see this, it's NOT working:**
- Blank white page
- Error messages
- Loading spinner that never stops
- "0" on all metrics

---

**TL;DR:**
1. Go to: `https://your-frontend.vercel.app/operator`
2. Look for numbers and green "PASS" badges
3. If you see them, it's working!
4. If not, run: `./test_deployment.sh <railway-url> <vercel-url>`

# Reset Railway Database - Get 100 Users + 100% Coverage

## Current State:
- ✅ Backend deployed and healthy
- ✅ Frontend connected to Railway
- ❌ Database only has 1 old user (needs 100 users)

## Quick Fix (2 minutes):

### Option 1: Delete Volume and Redeploy (Recommended)

1. **Go to Railway Dashboard:**
   - https://railway.app/dashboard
   - Click on your **MaxFinanceAI** service

2. **Delete the Database Volume:**
   - Click **"Settings"** tab
   - Scroll to **"Volumes"** section
   - Click **"Remove"** or **"Delete"** on the volume
   - Confirm deletion

3. **Redeploy:**
   - Go to **"Deployments"** tab
   - Click **"Redeploy"** on the latest deployment

4. **Wait 10-15 minutes:**
   - Railway will create fresh volume
   - start.sh will generate 100 users
   - Demo user will be created
   - Coverage will be fixed to 100%

---

### Option 2: Run Command via Railway Shell

1. **Open Railway Shell:**
   - Go to your service
   - Click the **"..."** menu (top right)
   - Click **"Shell"** or **"Terminal"**

2. **Run these commands:**
   ```bash
   rm /app/data/spendsense.db
   rm /app/data/full_dataset.flag
   exit
   ```

3. **Redeploy the service:**
   - Go to "Deployments" tab
   - Click "Redeploy"

---

## After Redeployment:

**Wait 10-15 minutes** for data generation, then check:

### Check Dataset Status:
```bash
curl https://maxfinanceai-production.up.railway.app/status/dataset
```

Expected:
```json
{
  "status": "complete",
  "user_count": 100,
  "expected_users": 100,
  "is_complete": true
}
```

### Check Coverage:
```bash
curl https://maxfinanceai-production.up.railway.app/api/v1/operator/evaluation/metrics
```

Expected:
```json
{
  "coverage": {
    "coverage_percentage": 100.0
  }
}
```

### Test Frontend:
Open: **https://frontend-7w28jda22-max-liss-projects.vercel.app/operator**

Should see:
- ✅ Numbers on metric cards
- ✅ Green "PASS" badges
- ✅ 100% coverage
- ✅ User list populated

---

## Current Status:

✅ Backend: https://maxfinanceai-production.up.railway.app
✅ Frontend: https://frontend-7w28jda22-max-liss-projects.vercel.app
✅ Demo User: Created and working
❌ Full Dataset: Needs regeneration (only 1 user currently)

**Just delete the volume and redeploy. Everything else is ready!**

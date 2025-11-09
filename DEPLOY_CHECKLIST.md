# 🚀 Deployment Checklist for MaxFinanceAI

Use this checklist to deploy MaxFinanceAI to production.

## ✅ Pre-Deployment Checklist

- [ ] All features tested locally
- [ ] Demo user has data (goals, budgets, transactions, alerts)
- [ ] Environment variables documented
- [ ] Database backup created (if applicable)
- [ ] Remove any sensitive data from code
- [ ] Update CORS settings for production domain

## 🎯 Quick Deploy (Recommended)

### Option A: Vercel Frontend Only (for demo/testing)

```bash
cd frontend
vercel --prod
```

**After deployment:**
1. Set `NEXT_PUBLIC_API_URL` in Vercel dashboard
2. Point it to your backend URL or keep as `http://localhost:8000/api/v1` for local testing

### Option B: Full Stack Deploy (Production Ready)

#### Step 1: Deploy Backend (Railway)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select MaxFinanceAI repository
4. Configure:
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add PostgreSQL database (optional) or use SQLite
6. Copy the backend URL (e.g., `https://maxfinanceai-backend.up.railway.app`)

#### Step 2: Deploy Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

**In Vercel Dashboard:**
1. Go to Settings → Environment Variables
2. Add: `NEXT_PUBLIC_API_URL` = `https://your-backend-url.railway.app/api/v1`
3. Redeploy

#### Step 3: Populate Demo Data

SSH into backend or use Railway CLI:
```bash
railway run python create_demo_user.py
railway run python add_demo_goals_budgets.py
railway run python populate_budget_spending.py
railway run python populate_goal_progress.py
```

## 🔧 Post-Deployment

- [ ] Test frontend URL
- [ ] Test backend health endpoint: `https://backend-url/health/`
- [ ] Login with demo user
- [ ] Verify all features:
  - [ ] Dashboard loads
  - [ ] Financial goals show progress
  - [ ] Budgets show spending
  - [ ] Notifications/alerts work
  - [ ] Chat/chatbot works
  - [ ] All pages accessible

## 🌐 URLs

After deployment, you'll have:

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-app.railway.app`
- **Health Check**: `https://your-app.railway.app/health/`
- **API Docs**: `https://your-app.railway.app/docs`

## 🐛 Troubleshooting

### CORS Errors
Update `backend/app/main.py` line 36:
```python
allow_origins=["https://your-app.vercel.app"],
```

### API Connection Failed
- Check `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Ensure backend is running: visit `https://backend-url/health/`
- Check browser console for errors

### Database Issues
- For production, use PostgreSQL instead of SQLite
- Update `DATABASE_URL` environment variable
- Run migrations if needed

## 📊 Demo User Credentials

**User ID**: `demo`

The demo user includes:
- 3 financial goals with progress
- 5 budget categories with spending data
- 675 transactions (6 months of history)
- 6 behavioral signals
- 2 personas assigned
- 4 recommendations
- 3 active notifications

## 💰 Costs

- **Vercel**: Free (Hobby tier)
- **Railway**: ~$5/month (includes 500 hours + PostgreSQL)
- **Alternative**: Render.com has a free tier

## 🎉 You're Done!

Share your deployed app:
- Frontend: `https://your-app.vercel.app`
- Login: Use "demo" as user ID

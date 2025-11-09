# MaxFinanceAI Deployment Guide

This guide covers deploying MaxFinanceAI to production using Vercel (frontend) and Railway/Render (backend).

## Architecture

- **Frontend**: Next.js app deployed to Vercel
- **Backend**: FastAPI app deployed to Railway or Render
- **Database**: PostgreSQL (recommended for production) or SQLite

---

## Option 1: Deploy to Vercel (Frontend) + Railway (Backend)

### Step 1: Deploy Backend to Railway

1. **Install Railway CLI** (optional):
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Create a new Railway project**:
   ```bash
   railway init
   ```

4. **Add PostgreSQL database**:
   - Go to Railway dashboard
   - Click "New" → "Database" → "PostgreSQL"
   - Copy the database URL

5. **Set environment variables in Railway**:
   ```
   DATABASE_URL=<your-postgresql-url>
   ```

6. **Deploy backend**:
   ```bash
   cd backend
   railway up
   ```

7. **Note the backend URL** (e.g., `https://your-app.railway.app`)

### Step 2: Deploy Frontend to Vercel

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy frontend**:
   ```bash
   cd frontend
   vercel
   ```

3. **Set environment variable**:
   - Go to Vercel dashboard → Your Project → Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app/api/v1`

4. **Redeploy**:
   ```bash
   vercel --prod
   ```

---

## Option 2: Deploy to Render

### Backend on Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: maxfinanceai-backend
   - **Environment**: Python 3
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Add PostgreSQL database** (optional)

5. Set environment variables:
   ```
   DATABASE_URL=<postgresql-url>
   ```

### Frontend on Vercel

Same as Option 1, Step 2 above.

---

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app/api/v1
```

### Backend (.env)
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
# For SQLite (development only)
# DATABASE_URL=sqlite:///./maxfinance.db
```

---

## Database Migration (SQLite → PostgreSQL)

If you want to use PostgreSQL in production:

1. Update `backend/app/database.py` to support PostgreSQL
2. Install `psycopg2-binary`:
   ```bash
   pip install psycopg2-binary
   ```
3. Update requirements.txt

---

## Populate Demo Data in Production

After deployment, populate demo data:

```bash
# SSH into your backend server or use Railway/Render CLI
python /app/create_demo_user.py
python /app/add_demo_goals_budgets.py
python /app/populate_budget_spending.py
python /app/populate_goal_progress.py
```

---

## Quick Deploy (Vercel Only - Frontend)

If you only want to deploy the frontend for demo purposes:

```bash
cd frontend
vercel --prod
```

Set environment variable:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Note**: Backend will need to be running locally or on a separate server.

---

## Verification

After deployment:

1. Visit your frontend URL
2. Login with user ID: `demo`
3. Verify all features work:
   - Dashboard loads
   - Goals show progress
   - Budgets show spending
   - Notifications work
   - Chat works

---

## Troubleshooting

### CORS Issues
If you get CORS errors, update `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],  # Add your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Connection Issues
- Check DATABASE_URL is set correctly
- Ensure database is accessible from your backend host
- Check firewall rules

### Build Failures
- Check Node.js version (should be 18.x or higher)
- Clear cache: `rm -rf .next node_modules && npm install`

---

## Cost Estimates

- **Vercel**: Free tier for personal projects
- **Railway**: $5/month (includes PostgreSQL)
- **Render**: Free tier available (with limitations)

---

## Next Steps

1. Set up custom domain
2. Configure SSL/TLS (automatic on Vercel/Railway)
3. Set up monitoring (Sentry, LogRocket)
4. Configure CI/CD pipeline
5. Set up staging environment

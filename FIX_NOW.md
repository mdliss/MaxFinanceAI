# FIX FRONTEND - IMMEDIATE STEPS

## THE PROBLEM:

Your frontend is trying to connect to `http://localhost:8000/api/v1` which doesn't work in production.

You need to tell Vercel where your Railway backend is.

---

## STEP 1: Get Your Railway Backend URL

Go to Railway dashboard and copy your backend URL.

It should look like: `https://something-production-xxxx.railway.app`

---

## STEP 2: Set Environment Variable in Vercel

1. Go to: https://vercel.com/max-liss-projects/frontend/settings/environment-variables

2. Click "Add New"

3. Enter:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://YOUR-RAILWAY-URL.railway.app/api/v1`
   - **Environment:** Production (check the box)

4. Click "Save"

---

## STEP 3: Redeploy Frontend

In your terminal:
```bash
cd /Users/max/MaxFinanceAI/frontend
vercel --prod
```

Or just go to Vercel dashboard → Deployments → Click "Redeploy"

---

## STEP 4: Check if It Works

After redeployment (~2 minutes):

1. Open: https://frontend-bky8pef7o-max-liss-projects.vercel.app/operator
2. Open browser console (F12)
3. Should see API calls going to Railway (not localhost)
4. Dashboard should populate with data

---

## IF YOU DON'T KNOW YOUR RAILWAY URL:

Run this in terminal:
```bash
railway login
railway status
railway domain
```

Or check your Railway dashboard: https://railway.app/dashboard

Look for your "backend" service and copy the public URL.

---

## STILL NOT WORKING?

The backend might not be deployed yet. Check Railway logs:
```bash
railway logs
```

Or go to Railway dashboard → Your service → Deployments tab

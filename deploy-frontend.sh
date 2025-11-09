#!/bin/bash

# MaxFinanceAI - Frontend Deployment Script
# This script deploys the frontend to Vercel

set -e

echo "🚀 Deploying MaxFinanceAI Frontend to Vercel"
echo "=============================================="

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Navigate to frontend directory
cd frontend

# Build the frontend
echo "📦 Building frontend..."
npm run build

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
if [ "$1" == "prod" ]; then
    echo "Deploying to PRODUCTION..."
    vercel --prod
else
    echo "Deploying to PREVIEW..."
    vercel
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Go to Vercel dashboard"
echo "  2. Set environment variable: NEXT_PUBLIC_API_URL"
echo "  3. Redeploy if needed"

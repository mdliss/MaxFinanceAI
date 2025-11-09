#!/bin/bash
set -e

# Ensure data directory exists
mkdir -p /app/data

echo "🚀 Initializing database..."
python init_db.py

# Wait a moment for database file to be fully written
sleep 1

echo "👤 Creating demo user..."
python create_demo_user.py || true

echo "📊 Adding demo data..."
python add_demo_goals_budgets.py || true

echo "✅ Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

#!/bin/bash
set -e

echo "🚀 Initializing database and demo user..."
python initialize_all.py || true

echo "📊 Adding demo goals and budgets..."
python add_demo_goals_budgets.py || true

echo "✅ Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

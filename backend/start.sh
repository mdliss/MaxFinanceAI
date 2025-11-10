#!/bin/bash
set -e

echo "🚀 Initializing database, demo user, goals, and budgets..."
python initialize_all.py || true

echo "✅ Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

#!/bin/bash

# Railway initialization script
# Run this on Railway to populate the full dataset

echo "🚀 Initializing Railway production database..."

# Delete old database and flag
rm -f /app/data/spendsense.db
rm -f /app/data/full_dataset.flag

echo "✅ Old database deleted"

# Run dataset generation
echo "📊 Generating 100 users..."
python /app/populate_full_dataset.py

echo "👤 Creating demo user..."
curl -s -X POST http://localhost:8000/api/v1/admin/setup-demo-user

echo "📈 Fixing coverage to 100%..."
curl -s -X POST http://localhost:8000/api/v1/admin/fix-coverage

echo "✅ Railway initialization complete!"

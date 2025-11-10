#!/bin/bash
# Simple script to populate 100 users locally then upload database to Railway

cd /Users/max/MaxFinanceAI/backend

# Run populate script locally
python3 populate_full_dataset.py

echo "✅ Done! 100 users created in local database."
echo ""
echo "Now you need to upload this database to Railway:"
echo "1. Find your local database at: /Users/max/MaxFinanceAI/data/spendsense.db"
echo "2. Use Railway CLI to upload it, or"
echo "3. Delete Railway's volume and redeploy to regenerate"

#!/bin/bash
set -e

# Function to generate dataset in background
generate_dataset() {
    echo "🚀 Starting full dataset generation (85 users)..."
    echo "⏱️  This will take ~10-15 minutes in the background"

    if python populate_full_dataset.py; then
        touch /app/data/full_dataset.flag
        echo "✅ Full dataset generation completed successfully!"
        echo "📊 85 users with ~50,000 transactions now available"
    else
        echo "❌ Dataset generation failed, but server continues running"
    fi
}

# Check if we need to generate data
if [ ! -f /app/data/full_dataset.flag ]; then
    echo "🔍 No existing dataset found, will generate in background..."

    # Start dataset generation in background
    generate_dataset > /tmp/dataset_generation.log 2>&1 &

    echo "📝 Dataset generation logs: /tmp/dataset_generation.log"
    echo "✅ Server starting immediately (healthcheck will pass)..."
else
    echo "ℹ️  Full dataset already exists (found flag file)"
    echo "✅ Using existing data, starting server..."
fi

# Start the server (this happens immediately, healthcheck passes)
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

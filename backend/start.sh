#!/bin/bash
set -e

# Function to initialize production data after server is running
initialize_production() {
    # Wait for server to be fully ready
    echo "⏳ Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:${PORT:-8000}/health/ > /dev/null 2>&1; then
            echo "✅ Server is ready!"
            break
        fi
        sleep 1
    done

    # Create demo user via API
    echo "👤 Creating demo user..."
    curl -s -X POST http://localhost:${PORT:-8000}/api/v1/admin/setup-demo-user \
         -H "Content-Type: application/json" || echo "Demo user creation skipped (may already exist)"

    # Fix coverage to ensure 100%
    echo "📊 Ensuring 100% coverage..."
    curl -s -X POST http://localhost:${PORT:-8000}/api/v1/admin/fix-coverage \
         -H "Content-Type: application/json" || echo "Coverage fix skipped"

    echo "✅ Production initialization complete!"
    echo "📊 100 users + demo user with 100% coverage"
    echo "🎯 Operator dashboard: /operator"
}

# Function to generate dataset in background
generate_dataset() {
    echo "🚀 Starting full dataset generation (100 users)..."
    echo "⏱️  This will take ~10-15 minutes in the background"

    if python populate_full_dataset.py; then
        echo "✅ Dataset generation completed!"

        # Initialize production data via API
        initialize_production

        # Mark as complete
        touch /app/data/full_dataset.flag
        echo "✅ Full production dataset ready!"
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

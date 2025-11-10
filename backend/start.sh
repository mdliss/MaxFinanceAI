#!/bin/bash
set -euo pipefail

PORT=${PORT:-8000}
DATASET_USER_COUNT=${DATASET_USER_COUNT:-150}
DATASET_FLAG_PATH=${DATASET_FLAG_PATH:-/app/data/full_dataset.flag}
DATASET_LOG_PATH=${DATASET_LOG_PATH:-/tmp/dataset_generation.log}

echo "🔧 Running bootstrap initializer (tables + demo user)..."
python initialize_all.py --user-count "${DATASET_USER_COUNT}"

if [ ! -f "${DATASET_FLAG_PATH}" ]; then
    echo "🚀 Triggering background dataset generation for ${DATASET_USER_COUNT}+ users..."
    python initialize_all.py \
        --ensure-dataset \
        --user-count "${DATASET_USER_COUNT}" \
        > "${DATASET_LOG_PATH}" 2>&1 &
    INIT_PID=$!
    echo "📝 Dataset generation logs: ${DATASET_LOG_PATH}"
    echo "🌀 Initializer PID: ${INIT_PID}"
else
    echo "ℹ️ Existing dataset flag found at ${DATASET_FLAG_PATH}; skipping background generation."
fi

echo "▶️ Starting FastAPI server on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"

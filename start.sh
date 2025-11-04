#!/bin/bash

echo "🚀 Starting SpendSense Application..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backend API:  http://localhost:8000"
echo "  Frontend UI:  http://localhost:3001"
echo "  Operator Dashboard: http://localhost:3001/operator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start services
docker-compose up

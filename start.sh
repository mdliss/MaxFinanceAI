#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting FinanceMaxAI Application...${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Parse command line arguments
BUILD_FLAG=""
DETACHED_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        -d|--detach)
            DETACHED_FLAG="-d"
            shift
            ;;
        --clean)
            echo -e "${YELLOW}🧹 Cleaning up old containers and volumes...${NC}"
            docker-compose down -v
            shift
            ;;
        -h|--help)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build    Rebuild containers before starting"
            echo "  -d, --detach    Run in detached mode (background)"
            echo "  --clean    Remove old containers and volumes before starting"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Backend API:${NC}          http://localhost:8000"
echo -e "${GREEN}  Frontend UI:${NC}          http://localhost:3001"
echo -e "${GREEN}  Operator Dashboard:${NC}   http://localhost:3001/operator"
echo -e "${GREEN}  API Documentation:${NC}    http://localhost:8000/docs"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create data directory if it doesn't exist
mkdir -p data

# Start services
if [ -n "$BUILD_FLAG" ]; then
    echo -e "${YELLOW}🔨 Building containers...${NC}"
fi

if [ -n "$DETACHED_FLAG" ]; then
    docker-compose up $BUILD_FLAG $DETACHED_FLAG
    echo ""
    echo -e "${GREEN}✅ Services started in background${NC}"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f backend"
    echo "  docker-compose logs -f frontend"
    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
else
    docker-compose up $BUILD_FLAG
fi

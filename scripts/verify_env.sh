#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}BenBot Environment Verification${NC}"
echo "=================================="

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Python virtual environment not found${NC}"
    echo "   Run ./scripts/setup_env.sh first to set up the environment"
    exit 1
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source venv/bin/activate

# Check Python dependencies
echo "Checking Python dependencies..."
MISSING_DEPS=0

check_python_dependency() {
    python -c "import $1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $1"
    else
        echo -e "  ${RED}✗${NC} $1 (missing)"
        MISSING_DEPS=$((MISSING_DEPS+1))
    fi
}

check_python_dependency flask
check_python_dependency fastapi
check_python_dependency uvicorn
check_python_dependency dotenv
check_python_dependency requests

if [ $MISSING_DEPS -gt 0 ]; then
    echo -e "${RED}❌ Missing Python dependencies${NC}"
    echo "   Run 'pip install -r requirements.txt' to install them"
else
    echo -e "${GREEN}✓ All core Python dependencies are installed${NC}"
fi

# Check if frontend directory exists
if [ ! -d "new-trading-dashboard" ]; then
    echo -e "${RED}❌ Frontend directory not found${NC}"
    exit 1
fi

# Check frontend dependencies
echo "Checking frontend dependencies..."
cd new-trading-dashboard

if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in frontend directory${NC}"
    cd ..
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo -e "${RED}❌ Node modules not installed${NC}"
    echo "   Run 'cd new-trading-dashboard && npm install' to install dependencies"
    cd ..
    exit 1
fi

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..

# Check for required environment files
echo "Checking environment files..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Create a .env file based on .env.example"
    exit 1
fi

if [ ! -f "new-trading-dashboard/.env.local" ]; then
    echo -e "${RED}❌ Frontend .env.local file not found${NC}"
    echo "   Create a new-trading-dashboard/.env.local file"
    exit 1
fi

echo -e "${GREEN}✓ Environment files exist${NC}"

# Attempt to start backend in background
echo "Starting backend server for health check..."
python demo_backend.py > backend_test.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start (max 10 seconds)..."
for i in {1..10}; do
    sleep 1
    curl -s http://localhost:8000/health > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backend started successfully${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Backend failed to start within 10 seconds${NC}"
        echo "   Check backend_test.log for details"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done

# Check backend health endpoint
echo "Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [[ $HEALTH_RESPONSE == *"status"* ]]; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "   Response: $HEALTH_RESPONSE"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Stop backend
echo "Stopping backend server..."
kill $BACKEND_PID

# Final status
echo "=================================="
echo -e "${GREEN}✓ Environment verification complete${NC}"
echo "You can now start the backend with: python demo_backend.py"
echo "You can start the frontend with: cd new-trading-dashboard && npm run dev" 
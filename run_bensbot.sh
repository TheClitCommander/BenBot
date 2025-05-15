#!/bin/bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ASCII art banner
echo -e "${BLUE}"
echo "======================================="
echo "       BensBot Trading System          "
echo "=======================================${NC}"

# Set up environment variables
WORKSPACE_DIR="$(pwd)"

# Check if virtual environment exists
if [ -d "trading_venv" ]; then
    echo -e "${GREEN}Found trading virtual environment.${NC}"
    source trading_venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Creating one...${NC}"
    python3 -m venv trading_venv
    source trading_venv/bin/activate
    pip install -r requirements.txt
fi

# Set PYTHONPATH for module imports
export PYTHONPATH=$WORKSPACE_DIR
echo -e "${GREEN}Set PYTHONPATH to: $PYTHONPATH${NC}"

# Check if ports are already in use
BACKEND_PORT=8000
FRONTEND_PORT=5173

check_port() {
    if lsof -i:$1 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port $1 is already in use. Trying to kill the process...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

check_port $BACKEND_PORT
check_port $FRONTEND_PORT

# Start Backend API
echo -e "${BLUE}Starting FastAPI backend...${NC}"
cd $WORKSPACE_DIR
python -m uvicorn trading_bot.api.app:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo -e "${GREEN}FastAPI backend started on http://localhost:$BACKEND_PORT${NC}"

# Sleep to give backend time to start
sleep 2

# Check if backend started successfully
if ! curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
    echo -e "${RED}Backend failed to start properly. Falling back to mock API...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    
    # Start mock API instead
    python dev_tools/mock_api.py &
    BACKEND_PID=$!
    BACKEND_PORT=8001
    echo -e "${YELLOW}Mock API started on http://localhost:$BACKEND_PORT${NC}"
fi

# Start Frontend
echo -e "${BLUE}Starting React frontend...${NC}"
cd $WORKSPACE_DIR/trading-dashboard

# Update .env.local with correct backend URL
echo "VITE_API_BASE_URL=http://localhost:$BACKEND_PORT" > .env.local

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}React frontend started - check console for URL${NC}"

# Display status
echo -e "${BLUE}==========================="
echo "BensBot is running!"
echo -e "Backend API: ${GREEN}http://localhost:$BACKEND_PORT${BLUE}"
echo -e "Frontend UI: ${GREEN}http://localhost:$FRONTEND_PORT${BLUE} (or check terminal output)"
echo -e "Press Ctrl+C to stop all components"
echo -e "===========================${NC}"

# Function to clean up on exit
cleanup() {
    echo -e "${YELLOW}Shutting down components...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Register cleanup function
trap cleanup INT TERM

# Wait for processes to finish
wait 
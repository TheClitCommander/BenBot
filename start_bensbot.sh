#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting BensBot Trading System...${NC}"

# Check if trading_venv exists
if [ ! -d "/Users/bendickinson/Desktop/trading_venv" ]; then
    echo -e "${YELLOW}Trading virtual environment not found. Creating it...${NC}"
    cd /Users/bendickinson/Desktop
    python3 -m venv trading_venv
    source trading_venv/bin/activate
    pip install fastapi uvicorn pandas numpy plotly websockets
else
    echo -e "${GREEN}Found trading virtual environment.${NC}"
fi

# Set up environment
export PYTHONPATH="/Users/bendickinson/Desktop/Trading:BenBot"
echo -e "${BLUE}Set PYTHONPATH to: $PYTHONPATH${NC}"

# Start backend in background
echo -e "${GREEN}Starting FastAPI backend...${NC}"
cd /Users/bendickinson/Desktop/Trading:BenBot/trading_bot/api
source /Users/bendickinson/Desktop/trading_venv/bin/activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}FastAPI backend started on http://localhost:8000${NC}"

# Sleep to ensure backend is up before frontend connects
sleep 3

# Start React frontend
echo -e "${GREEN}Starting React frontend...${NC}"
cd /Users/bendickinson/Desktop/Trading:BenBot/trading-dashboard
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}React frontend started${NC}"

# Function to kill processes on exit
cleanup() {
    echo -e "${YELLOW}Shutting down BensBot...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    echo -e "${GREEN}BensBot stopped successfully.${NC}"
    exit 0
}

# Register the cleanup function for when script exits
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}===========================${NC}"
echo -e "${GREEN}BensBot is running!${NC}"
echo -e "${GREEN}Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}Frontend UI: Check terminal output for URL (likely http://localhost:5173)${NC}"
echo -e "${GREEN}Press Ctrl+C to stop all components${NC}"
echo -e "${GREEN}===========================${NC}"

# Keep script running
wait

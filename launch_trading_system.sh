#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}      BensBot Trading System Launcher        ${NC}"
echo -e "${BLUE}==============================================${NC}"

# Setup the Python virtual environment
if [ -d "/Users/bendickinson/Desktop/trading_venv" ]; then
    echo -e "${GREEN}Using existing virtual environment...${NC}"
    source /Users/bendickinson/Desktop/trading_venv/bin/activate
else
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    cd /Users/bendickinson/Desktop
    python3 -m venv trading_venv
    source trading_venv/bin/activate
    
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install fastapi uvicorn pandas numpy matplotlib websockets alpaca-trade-api
fi

# Set PYTHONPATH to include the project root
export PYTHONPATH="/Users/bendickinson/Desktop/Trading:BenBot"
echo -e "${GREEN}Set PYTHONPATH to: $PYTHONPATH${NC}"

# Find the FastAPI entry point
echo -e "${YELLOW}Searching for FastAPI backend entry point...${NC}"
MAIN_API_FILE=""

# Try to find the main FastAPI file in common locations
for api_file in $(find /Users/bendickinson/Desktop/Trading:BenBot -name "*.py" -type f -exec grep -l "FastAPI" {} \; 2>/dev/null); do
    if grep -q "app = FastAPI" "$api_file"; then
        MAIN_API_FILE="$api_file"
        break
    fi
done

if [ -z "$MAIN_API_FILE" ]; then
    # If we can't find it, look for any app.py file that might be our backend
    MAIN_API_FILE=$(find /Users/bendickinson/Desktop/Trading:BenBot -name "app.py" -type f | head -1)
fi

if [ -z "$MAIN_API_FILE" ]; then
    echo -e "${RED}Could not find the FastAPI backend entry point!${NC}"
    echo -e "${YELLOW}Using /Users/bendickinson/Desktop/backtester_api.py as fallback...${NC}"
    MAIN_API_FILE="/Users/bendickinson/Desktop/backtester_api.py"
fi

# Find the React frontend
echo -e "${YELLOW}Searching for React frontend...${NC}"
FRONTEND_DIR=""

# First check if the backtester is in the expected location from memories
if [ -f "/Users/bendickinson/Desktop/backtester_api.py" ]; then
    echo -e "${GREEN}Found backtester API at /Users/bendickinson/Desktop/backtester_api.py${NC}"
    BACKTESTER_API="/Users/bendickinson/Desktop/backtester_api.py"
fi

# Try to find the React frontend directory
for pkg_json in $(find /Users/bendickinson/Desktop/Trading:BenBot -name "package.json" -type f 2>/dev/null); do
    pkg_dir=$(dirname "$pkg_json")
    if grep -q "react" "$pkg_json"; then
        FRONTEND_DIR="$pkg_dir"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo -e "${RED}Could not find React frontend directory with package.json!${NC}"
    echo -e "${YELLOW}Looking for any React-related directories...${NC}"
    
    # Try looking for node_modules or src directories that might contain React
    for dir in $(find /Users/bendickinson/Desktop/Trading:BenBot -type d -name "node_modules" 2>/dev/null); do
        FRONTEND_DIR=$(dirname "$dir")
        echo -e "${YELLOW}Found potential frontend at $FRONTEND_DIR (has node_modules)${NC}"
        break
    done
    
    # If we still don't have it, use the trading-dashboard directory as fallback
    if [ -z "$FRONTEND_DIR" ] && [ -d "/Users/bendickinson/Desktop/Trading:BenBot/trading-dashboard" ]; then
        FRONTEND_DIR="/Users/bendickinson/Desktop/Trading:BenBot/trading-dashboard"
        echo -e "${YELLOW}Using trading-dashboard directory as fallback${NC}"
    fi
fi

# Print found components
echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}Components found:${NC}"
echo -e "  Backend: ${MAIN_API_FILE:-Not found}"
if [ ! -z "$BACKTESTER_API" ]; then
    echo -e "  Backtester API: ${BACKTESTER_API}"
fi
echo -e "  Frontend: ${FRONTEND_DIR:-Not found}"
echo -e "${BLUE}==============================================${NC}"

# Start the backend if found
if [ ! -z "$MAIN_API_FILE" ]; then
    echo -e "${GREEN}Starting FastAPI backend...${NC}"
    API_DIR=$(dirname "$MAIN_API_FILE")
    API_FILENAME=$(basename "$MAIN_API_FILE")
    API_MODULE="${API_FILENAME%.*}"
    
    cd "$API_DIR"
    python3 -m uvicorn "$API_MODULE":app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}FastAPI backend started on http://localhost:8000 (PID: $BACKEND_PID)${NC}"
    sleep 2
else
    echo -e "${RED}Cannot start backend - entry point not found!${NC}"
fi

# Start the backtester API if found
if [ ! -z "$BACKTESTER_API" ]; then
    echo -e "${GREEN}Starting Backtester API...${NC}"
    cd $(dirname "$BACKTESTER_API")
    python3 "$BACKTESTER_API" &
    BACKTESTER_PID=$!
    echo -e "${GREEN}Backtester API started on http://localhost:5002 (PID: $BACKTESTER_PID)${NC}"
    sleep 2
else
    echo -e "${YELLOW}Backtester API not found - some functionality will be limited${NC}"
fi

# Start the frontend if found
if [ ! -z "$FRONTEND_DIR" ]; then
    echo -e "${GREEN}Starting React frontend...${NC}"
    cd "$FRONTEND_DIR"
    
    # Check if the package.json file exists
    if [ -f "package.json" ]; then
        # Try to determine the correct npm start command
        if grep -q "\"dev\"" package.json; then
            echo -e "${GREEN}Using 'npm run dev' command...${NC}"
            npm run dev &
        elif grep -q "\"start\"" package.json; then
            echo -e "${GREEN}Using 'npm start' command...${NC}"
            npm start &
        else
            echo -e "${RED}Couldn't determine the right npm command - trying 'npm start'...${NC}"
            npm start &
        fi
        FRONTEND_PID=$!
        echo -e "${GREEN}React frontend started (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}No package.json found in frontend directory!${NC}"
        echo -e "${YELLOW}Cannot start React frontend${NC}"
    fi
else
    echo -e "${RED}Cannot start frontend - directory not found!${NC}"
fi

# Function to kill processes on exit
cleanup() {
    echo -e "${YELLOW}Shutting down BensBot...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$BACKTESTER_PID" ]; then
        kill $BACKTESTER_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}BensBot stopped successfully.${NC}"
    exit 0
}

# Register the cleanup function for when script exits
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}BensBot System is running!${NC}"
echo -e "${GREEN}Access your trading dashboard in your browser${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all components${NC}"

# Keep script running
wait

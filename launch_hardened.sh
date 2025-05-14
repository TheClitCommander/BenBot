#!/bin/bash

# ==================================================================
# HARDENED TRADING SYSTEM LAUNCHER
# Features:
# - Process conflict detection and resolution
# - Robust virtual environment handling
# - Graceful signal trapping
# - Comprehensive logging
# - Port availability checking
# - System state verification
# ==================================================================

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
BACKTESTER_PORT=5002
FRONTEND_PORT=5173  # Default Vite port
LOG_DIR="/Users/bendickinson/Desktop/Trading:BenBot/logs"
VENV_PATH="/Users/bendickinson/Desktop/trading_venv"
PROJECT_ROOT="/Users/bendickinson/Desktop/Trading:BenBot"

# Process tracking
BACKEND_PID=""
BACKTESTER_PID=""
FRONTEND_PID=""
PIDS_TO_KILL=()

# ==================================================================
# HELPER FUNCTIONS
# ==================================================================

log() {
    local level=$1
    local message=$2
    local color=$GREEN
    
    case $level in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "HIGHLIGHT") color=$BLUE ;;
    esac
    
    # Print to console
    echo -e "${color}[$level] $message${NC}"
    
    # Log to file if log directory exists
    if [ -d "$LOG_DIR" ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$LOG_DIR/launcher_$(date +'%Y%m%d').log"
    fi
}

check_port() {
    local port=$1
    local process_name=$2
    
    if command -v lsof &> /dev/null; then
        # Use lsof if available (common on macOS)
        local pid=$(lsof -i :$port -t 2>/dev/null)
        if [ ! -z "$pid" ]; then
            local process_info=$(ps -p $pid -o comm= 2>/dev/null)
            log "WARN" "Port $port is already in use by process $pid ($process_info)"
            PIDS_TO_KILL+=($pid)
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        # Fallback to netstat
        if netstat -an | grep -q "LISTEN.*:$port "; then
            log "WARN" "Port $port is already in use, but cannot determine PID"
            return 1
        fi
    else
        log "WARN" "Cannot check if port $port is in use (neither lsof nor netstat available)"
    fi
    
    return 0
}

kill_existing_processes() {
    if [ ${#PIDS_TO_KILL[@]} -eq 0 ]; then
        return 0
    fi
    
    log "WARN" "The following processes need to be terminated to free required ports:"
    for pid in "${PIDS_TO_KILL[@]}"; do
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "Unknown")
        log "WARN" "  PID $pid ($process_info)"
    done
    
    log "INFO" "Killing conflicting processes..."
    for pid in "${PIDS_TO_KILL[@]}"; do
        kill -15 $pid 2>/dev/null
        sleep 1
        if ps -p $pid > /dev/null 2>&1; then
            log "WARN" "Process $pid did not terminate gracefully, using force kill"
            kill -9 $pid 2>/dev/null
        else
            log "INFO" "Process $pid terminated successfully"
        fi
    done
    
    # Verify ports are now free
    sleep 2
    local all_clear=true
    if ! check_port $BACKEND_PORT "Backend"; then all_clear=false; fi
    if ! check_port $BACKTESTER_PORT "Backtester"; then all_clear=false; fi
    if ! check_port $FRONTEND_PORT "Frontend"; then all_clear=false; fi
    
    if [ "$all_clear" = false ]; then
        log "ERROR" "Could not free all required ports. Please manually check processes."
        return 1
    fi
    
    return 0
}

setup_virtual_environment() {
    if [ -d "$VENV_PATH" ]; then
        log "INFO" "Using existing virtual environment at $VENV_PATH"
        
        # Check if it's a valid venv
        if [ ! -f "$VENV_PATH/bin/activate" ]; then
            log "ERROR" "Invalid virtual environment (missing activate script). Recreating..."
            rm -rf "$VENV_PATH"
            create_virtual_environment
            return $?
        fi
        
        source "$VENV_PATH/bin/activate"
        
        # Verify key packages
        local missing_packages=false
        for pkg in fastapi uvicorn websockets pydantic pandas numpy matplotlib; do
            if ! python3 -c "import $pkg" &>/dev/null; then
                log "WARN" "Package $pkg is missing from virtual environment"
                missing_packages=true
            fi
        done
        
        if [ "$missing_packages" = true ]; then
            log "INFO" "Installing missing packages..."
            pip install fastapi uvicorn websockets pydantic pandas numpy matplotlib alpaca-trade-api yfinance
        fi
    else
        create_virtual_environment
        return $?
    fi
    
    return 0
}

create_virtual_environment() {
    log "INFO" "Creating new virtual environment at $VENV_PATH"
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to create virtual environment"
        return 1
    fi
    
    source "$VENV_PATH/bin/activate"
    
    log "INFO" "Installing required packages..."
    pip install --upgrade pip
    pip install fastapi uvicorn websockets pydantic pandas numpy matplotlib alpaca-trade-api yfinance
    
    return $?
}

setup_logs_directory() {
    if [ ! -d "$LOG_DIR" ]; then
        log "INFO" "Creating logs directory at $LOG_DIR"
        mkdir -p "$LOG_DIR"
    fi
    
    # Create subdirectories for component-specific logs
    mkdir -p "$LOG_DIR/backend"
    mkdir -p "$LOG_DIR/backtester"
    mkdir -p "$LOG_DIR/frontend"
}

find_backend() {
    log "INFO" "Searching for FastAPI backend entry point..."
    
    # Try to find the main FastAPI file in common locations
    for api_file in $(find "$PROJECT_ROOT" -name "*.py" -type f -exec grep -l "FastAPI\|fastapi" {} \; 2>/dev/null | sort); do
        if grep -q "app = FastAPI\|app=FastAPI" "$api_file"; then
            BACKEND_FILE="$api_file"
            log "INFO" "Found FastAPI backend at: $BACKEND_FILE"
            return 0
        fi
    done
    
    # If we can't find it, look for app.py in api directories
    for api_dir in $(find "$PROJECT_ROOT" -path "*/api" -type d 2>/dev/null); do
        if [ -f "$api_dir/app.py" ]; then
            BACKEND_FILE="$api_dir/app.py"
            log "INFO" "Found FastAPI backend at: $BACKEND_FILE"
            return 0
        fi
    done
    
    # Fallback to any app.py
    BACKEND_FILE=$(find "$PROJECT_ROOT" -name "app.py" -type f | head -1)
    if [ ! -z "$BACKEND_FILE" ]; then
        log "INFO" "Found potential backend at: $BACKEND_FILE"
        return 0
    fi
    
    # Ultimate fallback
    if [ -f "/Users/bendickinson/Desktop/backtester_api.py" ]; then
        log "WARN" "Using fallback backend: /Users/bendickinson/Desktop/backtester_api.py"
        BACKEND_FILE="/Users/bendickinson/Desktop/backtester_api.py"
        return 0
    fi
    
    log "ERROR" "Could not find FastAPI backend entry point"
    return 1
}

find_backtester() {
    log "INFO" "Searching for Backtester API..."
    
    # First check if the backtester is in the expected location from memories
    if [ -f "/Users/bendickinson/Desktop/backtester_api.py" ]; then
        BACKTESTER_FILE="/Users/bendickinson/Desktop/backtester_api.py"
        log "INFO" "Found Backtester API at: $BACKTESTER_FILE"
        return 0
    fi
    
    # Look for backtester in common locations
    for file in $(find "$PROJECT_ROOT" -name "*backtester*.py" -type f 2>/dev/null); do
        if grep -q "app\|API\|Flask\|fastapi" "$file"; then
            BACKTESTER_FILE="$file"
            log "INFO" "Found Backtester API at: $BACKTESTER_FILE"
            return 0
        fi
    done
    
    log "WARN" "Could not find Backtester API"
    return 1
}

find_frontend() {
    log "INFO" "Searching for React frontend..."
    
    # Try to find package.json with React dependency
    for pkg_json in $(find "$PROJECT_ROOT" -name "package.json" -type f 2>/dev/null); do
        if grep -q '"react"' "$pkg_json"; then
            FRONTEND_DIR=$(dirname "$pkg_json")
            log "INFO" "Found React frontend at: $FRONTEND_DIR"
            return 0
        fi
    done
    
    # Check if there's a trading-dashboard directory
    if [ -d "$PROJECT_ROOT/trading-dashboard" ]; then
        # Check if it has node_modules, indicating it's a JS project
        if [ -d "$PROJECT_ROOT/trading-dashboard/node_modules" ]; then
            FRONTEND_DIR="$PROJECT_ROOT/trading-dashboard"
            log "INFO" "Found potential frontend at: $FRONTEND_DIR"
            return 0
        fi
    fi
    
    # Look for other common frontend directories
    for dir in "frontend" "ui" "client" "web" "app"; do
        if [ -d "$PROJECT_ROOT/$dir" ] && [ -f "$PROJECT_ROOT/$dir/package.json" ]; then
            FRONTEND_DIR="$PROJECT_ROOT/$dir"
            log "INFO" "Found potential frontend at: $FRONTEND_DIR"
            return 0
        fi
    done
    
    log "WARN" "Could not find React frontend"
    return 1
}

cleanup() {
    log "HIGHLIGHT" "Shutting down BensBot Trading System..."
    
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null; then
        log "INFO" "Stopping backend (PID: $BACKEND_PID)"
        kill -15 $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$BACKTESTER_PID" ] && ps -p $BACKTESTER_PID > /dev/null; then
        log "INFO" "Stopping backtester (PID: $BACKTESTER_PID)"
        kill -15 $BACKTESTER_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
        log "INFO" "Stopping frontend (PID: $FRONTEND_PID)"
        kill -15 $FRONTEND_PID 2>/dev/null
    fi
    
    # Give processes a moment to shut down gracefully
    sleep 2
    
    # Force kill any remaining processes
    for pid in $BACKEND_PID $BACKTESTER_PID $FRONTEND_PID; do
        if [ ! -z "$pid" ] && ps -p $pid > /dev/null; then
            log "WARN" "Process $pid did not terminate gracefully, using force kill"
            kill -9 $pid 2>/dev/null
        fi
    done
    
    log "HIGHLIGHT" "BensBot Trading System shut down successfully"
    exit 0
}

# ==================================================================
# MAIN SCRIPT
# ==================================================================

# Set up signal trapping for graceful shutdown
trap cleanup SIGINT SIGTERM

# Print header
echo -e "${BLUE}${BOLD}==============================================${NC}"
echo -e "${BLUE}${BOLD}        BensBot Trading System Launcher       ${NC}"
echo -e "${BLUE}${BOLD}==============================================${NC}"

# Create logs directory
setup_logs_directory

# Check if required ports are free
log "INFO" "Checking port availability..."
PORTS_AVAILABLE=true
if ! check_port $BACKEND_PORT "Backend"; then PORTS_AVAILABLE=false; fi
if ! check_port $BACKTESTER_PORT "Backtester"; then PORTS_AVAILABLE=false; fi
if ! check_port $FRONTEND_PORT "Frontend"; then PORTS_AVAILABLE=false; fi

if [ "$PORTS_AVAILABLE" = false ]; then
    log "WARN" "Some required ports are in use by other processes"
    kill_existing_processes
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to free required ports. Please close the conflicting applications manually."
        exit 1
    fi
fi

# Set up Python virtual environment
log "INFO" "Setting up Python environment..."
setup_virtual_environment
if [ $? -ne 0 ]; then
    log "ERROR" "Failed to set up Python virtual environment"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"
log "INFO" "Set PYTHONPATH to: $PYTHONPATH"

# Find all components
find_backend
BACKEND_FOUND=$?

find_backtester
BACKTESTER_FOUND=$?

find_frontend
FRONTEND_FOUND=$?

# Print component status
log "HIGHLIGHT" "Component detection complete:"
if [ $BACKEND_FOUND -eq 0 ]; then
    log "INFO" "✓ Backend: $BACKEND_FILE"
else
    log "ERROR" "✗ Backend: Not found"
fi

if [ $BACKTESTER_FOUND -eq 0 ]; then
    log "INFO" "✓ Backtester: $BACKTESTER_FILE"
else
    log "WARN" "✗ Backtester: Not found (non-critical)"
fi

if [ $FRONTEND_FOUND -eq 0 ]; then
    log "INFO" "✓ Frontend: $FRONTEND_DIR"
else
    log "ERROR" "✗ Frontend: Not found"
fi

# Verify minimum viable components
if [ $BACKEND_FOUND -ne 0 ] && [ $FRONTEND_FOUND -ne 0 ]; then
    log "ERROR" "Critical components missing. Cannot start system."
    exit 1
fi

# Start backend
if [ $BACKEND_FOUND -eq 0 ]; then
    log "INFO" "Starting FastAPI backend..."
    API_DIR=$(dirname "$BACKEND_FILE")
    API_FILENAME=$(basename "$BACKEND_FILE")
    API_MODULE="${API_FILENAME%.*}"
    
    cd "$API_DIR"
    python3 -m uvicorn "$API_MODULE":app --reload --host 0.0.0.0 --port $BACKEND_PORT > "$LOG_DIR/backend/backend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
    BACKEND_PID=$!
    
    if ps -p $BACKEND_PID > /dev/null; then
        log "INFO" "FastAPI backend started on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
    else
        log "ERROR" "Failed to start FastAPI backend"
    fi
    
    # Give the backend a moment to start
    sleep 3
fi

# Start backtester if found
if [ $BACKTESTER_FOUND -eq 0 ]; then
    log "INFO" "Starting Backtester API..."
    cd $(dirname "$BACKTESTER_FILE")
    python3 "$BACKTESTER_FILE" > "$LOG_DIR/backtester/backtester_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
    BACKTESTER_PID=$!
    
    if ps -p $BACKTESTER_PID > /dev/null; then
        log "INFO" "Backtester API started on http://localhost:$BACKTESTER_PORT (PID: $BACKTESTER_PID)"
    else
        log "ERROR" "Failed to start Backtester API"
    fi
    
    # Give the backtester a moment to start
    sleep 2
fi

# Start frontend if found
if [ $FRONTEND_FOUND -eq 0 ]; then
    log "INFO" "Starting React frontend..."
    cd "$FRONTEND_DIR"
    
    # Check if the package.json file exists
    if [ -f "package.json" ]; then
        # Check npm packages installed
        if [ ! -d "node_modules" ]; then
            log "INFO" "Installing npm packages (this may take a while)..."
            npm install > "$LOG_DIR/frontend/npm_install_$(date +'%Y%m%d_%H%M%S').log" 2>&1
        fi
        
        # Try to determine the correct npm start command
        if grep -q '"dev"' package.json; then
            log "INFO" "Using 'npm run dev' command..."
            npm run dev > "$LOG_DIR/frontend/frontend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
        elif grep -q '"start"' package.json; then
            log "INFO" "Using 'npm start' command..."
            npm start > "$LOG_DIR/frontend/frontend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
        else
            log "WARN" "Couldn't determine the right npm command - trying 'npm start'..."
            npm start > "$LOG_DIR/frontend/frontend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
        fi
        
        FRONTEND_PID=$!
        
        if ps -p $FRONTEND_PID > /dev/null; then
            log "INFO" "React frontend started (PID: $FRONTEND_PID)"
        else
            log "ERROR" "Failed to start React frontend"
        fi
    else
        log "ERROR" "No package.json found in frontend directory!"
    fi
fi

# Verify API connectivity with a simple curl check
log "INFO" "Verifying backend API connectivity..."
sleep 5
if curl -s http://localhost:$BACKEND_PORT > /dev/null; then
    log "INFO" "✓ Backend API is responding"
else
    log "WARN" "✗ Backend API is not responding. The system may not function correctly."
fi

# System is running
log "HIGHLIGHT" "==============================================" 
log "HIGHLIGHT" "BensBot Trading System is running!"
log "HIGHLIGHT" "==============================================" 
log "INFO" "Backend API: http://localhost:$BACKEND_PORT"
if [ $BACKTESTER_FOUND -eq 0 ]; then
    log "INFO" "Backtester API: http://localhost:$BACKTESTER_PORT"
fi
log "INFO" "Frontend: Check browser (typically http://localhost:$FRONTEND_PORT)"
log "INFO" "Logs directory: $LOG_DIR"
log "INFO" "Press Ctrl+C to stop all components"
log "HIGHLIGHT" "==============================================" 

# Keep script running until user presses Ctrl+C
wait

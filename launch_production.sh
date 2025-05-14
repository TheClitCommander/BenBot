#!/bin/bash

# ===================================================
# PRODUCTION LAUNCH SCRIPT FOR BENSBOT TRADING SYSTEM
# Features:
# - Comprehensive environment validation
# - Production-ready configuration
# - Enhanced logging and monitoring
# - Auto-recovery capabilities
# ===================================================

# Terminal Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/bendickinson/Desktop/Trading:BenBot"
LOG_DIR="$PROJECT_ROOT/logs"
ENV_FILE="$PROJECT_ROOT/.env.production"
FRONTEND_DIR="/Users/bendickinson/Desktop/TradingBenBot/new-trading-dashboard"
MONITOR_LOG="$LOG_DIR/system_monitor.log"
RESTART_COUNT=0
MAX_RESTARTS=5
DOWNTIME_ALERT_THRESHOLD=300 # 5 minutes in seconds

# Process tracking
BACKEND_PID=""
BACKTESTER_PID=""
FRONTEND_PID=""
MONITOR_PID=""

# ===================================================
# HELPER FUNCTIONS
# ===================================================

log() {
    local level=$1
    local message=$2
    local color=$GREEN
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "SYSTEM") color=$BLUE ;;
    esac
    
    # Print to console with timestamp
    echo -e "${color}[$timestamp] [$level] $message${NC}"
    
    # Log to file
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
    fi
    
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/production_$(date '+%Y%m%d').log"
}

setup_environment() {
    log "INFO" "Setting up production environment..."
    
    # Create log directories
    log "INFO" "Creating log directories..."
    mkdir -p "$LOG_DIR/api"
    mkdir -p "$LOG_DIR/backtester"
    mkdir -p "$LOG_DIR/frontend"
    mkdir -p "$LOG_DIR/monitor"
    
    # Check if production env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log "WARN" "Production environment file not found, creating from example..."
        
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            log "INFO" "Created $ENV_FILE from example"
        else
            log "INFO" "Creating basic $ENV_FILE..."
            cat > "$ENV_FILE" << EOL
# Production Environment Configuration
LOG_LEVEL=INFO
ENABLE_DEBUG=false
TRADING_MODE=PAPER
API_PORT=8000
BACKTESTER_PORT=5002
FRONTEND_PORT=3003
EOL
        fi
    fi
    
    # Load environment variables
    log "INFO" "Loading environment variables from $ENV_FILE..."
    set -a
    source "$ENV_FILE"
    set +a
    
    # Set Python path
    export PYTHONPATH="$PROJECT_ROOT"
    log "INFO" "Set PYTHONPATH to: $PYTHONPATH"
    
    # Verify Python environment
    if [ ! -d "/Users/bendickinson/Desktop/trading_venv" ]; then
        log "ERROR" "Trading virtual environment not found at expected location!"
        return 1
    fi
    
    # Activate virtual environment
    source /Users/bendickinson/Desktop/trading_venv/bin/activate
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to activate virtual environment!"
        return 1
    fi
    
    # Verify required packages
    log "INFO" "Verifying required packages..."
    if ! pip list | grep -q "fastapi"; then
        log "ERROR" "FastAPI not installed. Please run setup script first."
        return 1
    fi
    
    if ! pip list | grep -q "uvicorn"; then
        log "ERROR" "Uvicorn not installed. Please run setup script first."
        return 1
    fi
    
    # Add version info to logs
    python_version=$(python --version 2>&1)
    log "INFO" "Using Python: $python_version"
    node_version=$(node --version 2>&1)
    log "INFO" "Using Node: $node_version"
    
    return 0
}

# System monitoring
start_monitoring() {
    log "INFO" "Starting system monitoring..."
    
    # Start monitoring in background
    (
    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Check CPU usage
        cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | tr -d '%')
        
        # Check memory usage
        mem_usage=$(top -l 1 | grep "PhysMem" | awk '{print $2}' | tr -d 'M')
        
        # Check process health
        backend_health="DOWN"
        backtester_health="DOWN"
        frontend_health="DOWN"
        
        if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null; then
            backend_health="UP"
        fi
        
        if [ ! -z "$BACKTESTER_PID" ] && ps -p $BACKTESTER_PID > /dev/null; then
            backtester_health="UP"
        fi
        
        if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
            frontend_health="UP"
        fi
        
        # Check API health
        api_health="UNKNOWN"
        api_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null)
        if [ "$api_response" = "200" ]; then
            api_health="HEALTHY"
        else
            api_health="UNHEALTHY"
        fi
        
        # Log system status
        echo "[$timestamp] CPU: ${cpu_usage}%, Memory: ${mem_usage}M, Backend: $backend_health, Backtester: $backtester_health, Frontend: $frontend_health, API: $api_health" >> "$MONITOR_LOG"
        
        # Auto-recovery for backend
        if [ "$backend_health" = "DOWN" ] && [ "$RESTART_COUNT" -lt "$MAX_RESTARTS" ]; then
            log "WARN" "Backend down, attempting restart..."
            start_backend
            RESTART_COUNT=$((RESTART_COUNT+1))
            log "WARN" "Restart attempt $RESTART_COUNT of $MAX_RESTARTS"
        fi
        
        # Sleep for 30 seconds before next check
        sleep 30
    done
    ) &
    
    MONITOR_PID=$!
    log "INFO" "System monitoring started (PID: $MONITOR_PID)"
}

start_backend() {
    log "INFO" "Starting FastAPI backend..."
    cd "$PROJECT_ROOT/trading_bot/api"
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/api/api_$(date '+%Y%m%d_%H%M%S').log" 2>&1 &
    BACKEND_PID=$!
    
    if ps -p $BACKEND_PID > /dev/null; then
        log "INFO" "FastAPI backend started on http://localhost:8000 (PID: $BACKEND_PID)"
        
        # Verify backend is accepting connections
        sleep 5
        if curl -s http://localhost:8000/api/health > /dev/null; then
            log "INFO" "Backend API is responding correctly"
        else
            log "WARN" "Backend API is not responding properly"
        fi
    else
        log "ERROR" "Failed to start FastAPI backend"
        return 1
    fi
    
    return 0
}

start_backtester() {
    log "INFO" "Starting Backtester API..."
    cd /Users/bendickinson/Desktop
    python backtester_api.py > "$LOG_DIR/backtester/backtester_$(date '+%Y%m%d_%H%M%S').log" 2>&1 &
    BACKTESTER_PID=$!
    
    if ps -p $BACKTESTER_PID > /dev/null; then
        log "INFO" "Backtester API started on http://localhost:5002 (PID: $BACKTESTER_PID)"
    else
        log "ERROR" "Failed to start Backtester API"
        return 1
    fi
    
    return 0
}

start_frontend() {
    log "INFO" "Starting React frontend in production mode..."
    cd "$FRONTEND_DIR"
    
    # First check if the build exists, if not, build it
    if [ ! -d "$FRONTEND_DIR/dist" ]; then
        log "INFO" "Building production frontend..."
        npm run build > "$LOG_DIR/frontend/build_$(date '+%Y%m%d_%H%M%S').log" 2>&1
        
        if [ $? -ne 0 ]; then
            log "ERROR" "Failed to build frontend"
            return 1
        fi
    fi
    
    # Serve the built files
    log "INFO" "Serving frontend from dist directory..."
    cd "$FRONTEND_DIR"
    npm run preview -- --port 3003 --host > "$LOG_DIR/frontend/frontend_$(date '+%Y%m%d_%H%M%S').log" 2>&1 &
    FRONTEND_PID=$!
    
    if ps -p $FRONTEND_PID > /dev/null; then
        log "INFO" "React frontend started at http://localhost:3003 (PID: $FRONTEND_PID)"
    else
        log "ERROR" "Failed to start React frontend"
        return 1
    fi
    
    return 0
}

cleanup() {
    log "SYSTEM" "Shutting down BensBot Trading System..."
    
    # Stop monitoring
    if [ ! -z "$MONITOR_PID" ] && ps -p $MONITOR_PID > /dev/null; then
        log "INFO" "Stopping monitoring process..."
        kill -15 $MONITOR_PID 2>/dev/null
    fi
    
    # Stop backend
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null; then
        log "INFO" "Stopping backend process..."
        kill -15 $BACKEND_PID 2>/dev/null
    fi
    
    # Stop backtester
    if [ ! -z "$BACKTESTER_PID" ] && ps -p $BACKTESTER_PID > /dev/null; then
        log "INFO" "Stopping backtester process..."
        kill -15 $BACKTESTER_PID 2>/dev/null
    fi
    
    # Stop frontend
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
        log "INFO" "Stopping frontend process..."
        kill -15 $FRONTEND_PID 2>/dev/null
    fi
    
    # Give processes a moment to shut down gracefully
    sleep 3
    
    # Force kill any remaining processes
    for pid in $BACKEND_PID $BACKTESTER_PID $FRONTEND_PID $MONITOR_PID; do
        if [ ! -z "$pid" ] && ps -p $pid > /dev/null; then
            log "WARN" "Process $pid did not terminate gracefully, using force kill"
            kill -9 $pid 2>/dev/null
        fi
    done
    
    log "SYSTEM" "BensBot Trading System shut down complete"
    exit 0
}

# ===================================================
# MAIN SCRIPT
# ===================================================

# Set up signal handler for graceful shutdown
trap cleanup SIGINT SIGTERM

# Print header
log "SYSTEM" "===== BensBot Trading System - Production Launcher ====="
log "SYSTEM" "Starting at $(date '+%Y-%m-%d %H:%M:%S')"

# Set up environment
setup_environment
if [ $? -ne 0 ]; then
    log "ERROR" "Environment setup failed, aborting startup"
    exit 1
fi

# Start monitoring
start_monitoring

# Start backend
start_backend
if [ $? -ne 0 ]; then
    log "ERROR" "Backend startup failed, aborting"
    cleanup
    exit 1
fi

# Start backtester
start_backtester
if [ $? -ne 0 ]; then
    log "WARN" "Backtester startup failed, continuing without backtester"
fi

# Start frontend
start_frontend
if [ $? -ne 0 ]; then
    log "ERROR" "Frontend startup failed, aborting"
    cleanup
    exit 1
fi

# System is running
log "SYSTEM" "===== BensBot Trading System is running ====="
log "INFO" "API: http://localhost:8000"
log "INFO" "Backtester: http://localhost:5002"
log "INFO" "Frontend: http://localhost:3003"
log "INFO" "Logs: $LOG_DIR"
log "INFO" "Monitor Log: $MONITOR_LOG"
log "INFO" "Press Ctrl+C to stop all components"

# Keep script running until user presses Ctrl+C
while true; do
    sleep 60
    
    # Verify critical processes are still running
    backend_running=false
    frontend_running=false
    
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null; then
        backend_running=true
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
        frontend_running=true
    fi
    
    # If critical processes died, try to restart them (limited attempts)
    if [ "$backend_running" = false ] && [ "$RESTART_COUNT" -lt "$MAX_RESTARTS" ]; then
        log "WARN" "Backend process died, attempting restart..."
        start_backend
        RESTART_COUNT=$((RESTART_COUNT+1))
    fi
    
    if [ "$frontend_running" = false ] && [ "$RESTART_COUNT" -lt "$MAX_RESTARTS" ]; then
        log "WARN" "Frontend process died, attempting restart..."
        start_frontend
        RESTART_COUNT=$((RESTART_COUNT+1))
    fi
    
    # If both critical processes are down and we've exceeded restart limit, exit
    if [ "$backend_running" = false ] && [ "$frontend_running" = false ] && [ "$RESTART_COUNT" -ge "$MAX_RESTARTS" ]; then
        log "ERROR" "Critical components failed repeatedly, shutting down system"
        cleanup
        exit 1
    fi
done

#!/bin/bash
#
# BensBot Trading System - Production Deployment Script
# This script handles the deployment of the trading system to a production environment.
#

# Exit on any error
set -e

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOY_DIR="deployment"
BACKUP_DIR="backups"
CONFIG_DIR="config"
ENV_FILE="$CONFIG_DIR/.env.production"
VERSION_TAG="v1.0-autonomous"
LOG_FILE="deploy_${TIMESTAMP}.log"

# Required tools
REQUIRED_TOOLS=("git" "python3" "pip3")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

log_success() {
    log "${GREEN}SUCCESS:${NC} $1"
}

log_warning() {
    log "${YELLOW}WARNING:${NC} $1"
}

log_error() {
    log "${RED}ERROR:${NC} $1"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check for required tools
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' is not installed. Please install it and try again."
            exit 1
        fi
    done
    
    # Check for environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Production environment file '$ENV_FILE' not found."
        log "Please create it from the template and fill in your API keys before deploying."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    if [[ ! "$PYTHON_VERSION" =~ ^3\.[789] ]]; then
        log_warning "Recommended Python version is 3.7 or higher. You have $PYTHON_VERSION."
    else
        log_success "Python version $PYTHON_VERSION is compatible."
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    log "Available disk space: $AVAILABLE_SPACE"
    
    log_success "All system requirements met."
}

create_backup() {
    log "Creating backup of current state..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup data directory
    if [ -d "data" ]; then
        log "Backing up data directory..."
        tar -czf "$BACKUP_DIR/data_backup_${TIMESTAMP}.tar.gz" data
    fi
    
    # Backup configuration
    if [ -d "$CONFIG_DIR" ]; then
        log "Backing up configuration..."
        tar -czf "$BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz" "$CONFIG_DIR"
    fi
    
    # Backup logs
    if [ -d "logs" ]; then
        log "Backing up logs..."
        tar -czf "$BACKUP_DIR/logs_backup_${TIMESTAMP}.tar.gz" logs
    fi
    
    log_success "Backup created in $BACKUP_DIR directory."
}

prepare_deployment() {
    log "Preparing deployment..."
    
    # Create deployment directory
    mkdir -p "$DEPLOY_DIR"
    
    # Clean previous deployment files
    if [ -d "$DEPLOY_DIR" ]; then
        rm -rf "$DEPLOY_DIR"/*
    fi
    
    # Copy essential files
    log "Copying trading system files to deployment directory..."
    
    # Copy trading bot code
    cp -r trading_bot "$DEPLOY_DIR/"
    
    # Copy scripts and exclude development tools
    mkdir -p "$DEPLOY_DIR/scripts"
    cp scripts/*.py "$DEPLOY_DIR/scripts/"
    cp scripts/deploy_live.sh "$DEPLOY_DIR/scripts/"
    
    # Copy configuration (but not sensitive files)
    mkdir -p "$DEPLOY_DIR/$CONFIG_DIR"
    cp "$CONFIG_DIR"/*.json "$DEPLOY_DIR/$CONFIG_DIR/" 2>/dev/null || true
    
    # Create directories
    mkdir -p "$DEPLOY_DIR/logs"
    mkdir -p "$DEPLOY_DIR/data"
    
    # Copy production environment file
    cp "$ENV_FILE" "$DEPLOY_DIR/$ENV_FILE"
    
    # Create version file
    echo "$VERSION_TAG" > "$DEPLOY_DIR/VERSION"
    
    log_success "Deployment prepared."
}

install_dependencies() {
    log "Installing Python dependencies..."
    
    # Create and activate virtual environment
    cd "$DEPLOY_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install requirements
    pip install --upgrade pip
    pip install numpy pandas scikit-learn matplotlib seaborn plotly
    pip install requests websocket-client python-dotenv 
    pip install alpaca-trade-api python-binance oandapyV20
    pip install prometheus-client psutil
    pip install python-telegram-bot slackclient
    pip install openai
    
    # Deactivate virtual environment
    deactivate
    cd ..
    
    log_success "Dependencies installed."
}

configure_system() {
    log "Configuring system..."
    
    # Create data and log directories
    mkdir -p "$DEPLOY_DIR/data/history"
    mkdir -p "$DEPLOY_DIR/data/strategies"
    mkdir -p "$DEPLOY_DIR/data/performance"
    mkdir -p "$DEPLOY_DIR/logs/alerts"
    mkdir -p "$DEPLOY_DIR/logs/trades"
    mkdir -p "$DEPLOY_DIR/logs/system"
    
    # Create deployment configuration
    cat > "$DEPLOY_DIR/config/deployment.json" << EOF
{
    "deployment": {
        "version": "$VERSION_TAG",
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "environment": "production"
    },
    "paths": {
        "data": "data",
        "logs": "logs",
        "config": "config"
    },
    "startup": {
        "health_check_required": true,
        "start_monitoring": true,
        "start_with_allocation": false,
        "enable_strategy_guardian": true
    }
}
EOF
    
    log_success "System configured."
}

create_startup_script() {
    log "Creating startup script..."
    
    # Create startup script
    cat > "$DEPLOY_DIR/start_trading.sh" << 'EOF'
#!/bin/bash
#
# BensBot Trading System - Production Startup Script
#

# Exit on any error
set -e

# Activate virtual environment
source venv/bin/activate

# Load environment variables
set -a
source config/.env.production
set +a

# Create log directory for today
LOG_DATE=$(date +"%Y-%m-%d")
mkdir -p "logs/$LOG_DATE"

# Start monitoring system
echo "Starting health monitoring system..."
python -m trading_bot.utils.system_health_monitor &
MONITOR_PID=$!
echo "Health monitor started (PID: $MONITOR_PID)"

# Allow system to initialize
sleep 5

# Start main trading system
echo "Starting BensBot trading system..."
python -m trading_bot.main --production --config=config/deployment.json 2>&1 | tee "logs/$LOG_DATE/trading.log"

# Cleanup
kill $MONITOR_PID
deactivate

echo "Trading system shutdown."
EOF
    
    # Make startup script executable
    chmod +x "$DEPLOY_DIR/start_trading.sh"
    
    log_success "Startup script created."
}

finalize_deployment() {
    log "Finalizing deployment..."
    
    # Create deployment tag
    cd "$DEPLOY_DIR"
    
    # Create deployment summary
    cat > "DEPLOYMENT.md" << EOF
# BensBot Trading System Deployment

**Version:** $VERSION_TAG
**Deployed:** $(date)

## Deployment Information

This is a production deployment of the BensBot trading system.

## Starting the System

To start the trading system:

1. Navigate to the deployment directory
2. Run \`./start_trading.sh\`

## Monitoring

The system health monitor runs on port 9090 (configurable in .env.production).

## Logs

Logs are stored in the \`logs\` directory, organized by date.

## Backup

Regular backups are essential. Use \`scripts/backup.sh\` to create a backup.
EOF
    
    cd ..
    
    log_success "Deployment finalized."
    log "Deployment is ready in the '$DEPLOY_DIR' directory."
    log "To start the trading system, cd into '$DEPLOY_DIR' and run './start_trading.sh'"
}

# Main deployment flow
log "Starting BensBot deployment process..."
log "Deployment timestamp: $TIMESTAMP"
log "Version tag: $VERSION_TAG"

check_requirements
create_backup
prepare_deployment
install_dependencies
configure_system
create_startup_script
finalize_deployment

log_success "Deployment completed successfully!" 
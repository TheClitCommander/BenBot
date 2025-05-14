#!/bin/bash
#
# BensBot Trading System - Master Setup Script
# This script runs all the setup steps in sequence for a complete deployment.
#

# Exit on any error
set -e

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="setup_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
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

log_step() {
    echo
    echo -e "${BLUE}=========================================================${NC}"
    echo -e "${BLUE}= STEP $1: $2${NC}"
    echo -e "${BLUE}=========================================================${NC}"
    echo
    log "Starting step $1: $2"
}

run_step() {
    command=$1
    if [ -f "$command" ] && [ -x "$command" ]; then
        $command
        if [ $? -eq 0 ]; then
            log_success "Step completed successfully: $command"
            return 0
        else
            log_error "Step failed: $command"
            return 1
        fi
    else
        log_error "Script not found or not executable: $command"
        return 1
    fi
}

check_requirements() {
    log_step "1" "Checking system requirements"
    
    # Check for required tools
    REQUIRED_TOOLS=("git" "python3" "pip3")
    
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' is not installed. Please install it and try again."
            exit 1
        fi
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

make_scripts_executable() {
    log_step "2" "Making scripts executable"
    
    chmod +x scripts/*.sh
    log_success "Made all scripts executable"
}

setup_local_environment() {
    log_step "3" "Setting up local environment"
    
    if run_step "./scripts/setup_local_env.sh"; then
        log_success "Local environment setup completed"
    else
        log_error "Local environment setup failed"
        exit 1
    fi
}

setup_local_backup() {
    log_step "4" "Setting up local backup system"
    
    if run_step "./scripts/setup_local_backup.sh"; then
        log_success "Local backup setup completed"
    else
        log_error "Local backup setup failed"
        exit 1
    fi
}

deploy_system() {
    log_step "5" "Deploying the system"
    
    if run_step "./scripts/deploy_live.sh"; then
        log_success "System deployment completed"
    else
        log_error "System deployment failed"
        exit 1
    fi
}

setup_complete() {
    log_step "6" "Setup complete"
    
    echo
    echo -e "${GREEN}=========================================================${NC}"
    echo -e "${GREEN}= BensBot Trading System Setup Completed Successfully =${NC}"
    echo -e "${GREEN}=========================================================${NC}"
    echo
    
    echo "Next steps:"
    echo "1. Check your configuration in config/.env.production"
    echo "2. Start the system by running: cd deployment && ./start_trading.sh"
    echo "3. Monitor the system using the dashboard and health reports"
    echo
    echo "For more information, refer to README-PRODUCTION.md"
    echo
}

# Main execution
echo
echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}= BensBot Trading System Setup${NC}"
echo -e "${BLUE}= $(date)${NC}"
echo -e "${BLUE}=========================================================${NC}"
echo

log "Starting BensBot setup process..."

# Run all steps in sequence
check_requirements
make_scripts_executable
setup_local_environment
setup_local_backup
deploy_system
setup_complete

log_success "Setup process completed successfully!" 
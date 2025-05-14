#!/bin/bash
#
# BensBot Trading System - Local Environment Setup Script
# This script sets up the local environment with necessary configuration files.
#

# Exit on any error
set -e

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONFIG_DIR="config"
LOG_FILE="setup_env_${TIMESTAMP}.log"

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

create_config_directory() {
    log "Setting up configuration directory..."
    
    # Create config directory if it doesn't exist
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        log "Created configuration directory: $CONFIG_DIR"
    else
        log "Configuration directory already exists: $CONFIG_DIR"
    fi
}

setup_environment_file() {
    log "Setting up environment file..."
    
    # Check if template exists
    TEMPLATE_FILE="$CONFIG_DIR/env.production.template"
    TARGET_FILE="$CONFIG_DIR/.env.production"
    
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "Environment template file not found: $TEMPLATE_FILE"
        log "Please make sure the template file exists before running this script."
        exit 1
    fi
    
    # Check if production env file already exists
    if [ -f "$TARGET_FILE" ]; then
        log_warning "Production environment file already exists: $TARGET_FILE"
        read -p "Do you want to overwrite it? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing environment file."
            return
        fi
        # Backup existing file
        cp "$TARGET_FILE" "${TARGET_FILE}.backup-${TIMESTAMP}"
        log "Backed up existing environment file to ${TARGET_FILE}.backup-${TIMESTAMP}"
    fi
    
    # Copy template to target
    cp "$TEMPLATE_FILE" "$TARGET_FILE"
    log_success "Created production environment file: $TARGET_FILE"
    log "Please edit this file to configure your API keys and other settings."
    
    # Make the file readable only by the owner for security
    chmod 600 "$TARGET_FILE"
    log "Set secure permissions on environment file"
}

configure_local_paths() {
    log "Configuring local paths in environment file..."
    
    TARGET_FILE="$CONFIG_DIR/.env.production"
    if [ ! -f "$TARGET_FILE" ]; then
        log_error "Environment file not found: $TARGET_FILE"
        return
    }
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    
    # Update paths in the environment file
    sed -i.bak "s|DATA_DIR=.*|DATA_DIR=$CURRENT_DIR/data|g" "$TARGET_FILE"
    sed -i.bak "s|CONFIG_DIR=.*|CONFIG_DIR=$CURRENT_DIR/config|g" "$TARGET_FILE"
    sed -i.bak "s|LOG_DIR=.*|LOG_DIR=$CURRENT_DIR/logs|g" "$TARGET_FILE"
    
    # Clean up backup file
    rm -f "${TARGET_FILE}.bak"
    
    log_success "Updated environment paths for local development"
}

disable_cloud_sync() {
    log "Disabling cloud sync in environment file..."
    
    TARGET_FILE="$CONFIG_DIR/.env.production"
    if [ ! -f "$TARGET_FILE" ]; then
        log_error "Environment file not found: $TARGET_FILE"
        return
    }
    
    # Disable cloud sync in the environment file
    sed -i.bak "s|ENABLE_CLOUD_SYNC=.*|ENABLE_CLOUD_SYNC=false|g" "$TARGET_FILE"
    sed -i.bak "s|CLOUD_SYNC_PROVIDER=.*|CLOUD_SYNC_PROVIDER=none|g" "$TARGET_FILE"
    
    # Clean up backup file
    rm -f "${TARGET_FILE}.bak"
    
    log_success "Disabled cloud sync in environment file"
}

create_directories() {
    log "Creating necessary directories..."
    
    # Create data directory and subdirectories
    mkdir -p data/strategies
    mkdir -p data/performance
    mkdir -p data/history
    mkdir -p data/portfolio
    
    # Create logs directory and subdirectories
    mkdir -p logs/alerts
    mkdir -p logs/trades
    mkdir -p logs/system
    
    log_success "Created data and log directories"
}

setup_monitoring_config() {
    log "Setting up monitoring configuration..."
    
    # Create health monitor config
    HEALTH_CONFIG_FILE="$CONFIG_DIR/health_monitor.json"
    
    if [ ! -f "$HEALTH_CONFIG_FILE" ]; then
        cat > "$HEALTH_CONFIG_FILE" << EOF
{
    "components": {
        "data_feed": {
            "enabled": true,
            "max_latency_ms": 5000,
            "check_interval_sec": 120,
            "data_sources": ["alpaca", "yahoo", "binance"]
        },
        "strategy_execution": {
            "enabled": true,
            "max_cycle_time_ms": 2000,
            "min_cycles_per_minute": 1
        },
        "portfolio_allocation": {
            "enabled": true,
            "max_cycle_time_ms": 5000,
            "check_interval_sec": 300
        },
        "disk_space": {
            "enabled": true,
            "min_free_space_mb": 1000,
            "check_interval_sec": 3600
        },
        "memory_usage": {
            "enabled": true,
            "max_usage_percent": 85,
            "check_interval_sec": 300
        }
    },
    "actions": {
        "auto_restart_on_failure": false,
        "max_restart_attempts": 3,
        "cool_down_period_sec": 300
    },
    "reporting": {
        "log_to_file": true,
        "report_interval_sec": 3600,
        "keep_history_days": 7
    },
    "alerts": {
        "levels": {
            "data_feed_latency": "WARNING",
            "strategy_execution_delay": "WARNING",
            "disk_space_low": "WARNING",
            "memory_usage_high": "WARNING",
            "component_failure": "CRITICAL"
        }
    }
}
EOF
        log_success "Created health monitor configuration: $HEALTH_CONFIG_FILE"
    else
        log "Health monitor configuration already exists: $HEALTH_CONFIG_FILE"
    fi
}

# Main execution
log "Starting BensBot local environment setup..."

create_config_directory
setup_environment_file
configure_local_paths
disable_cloud_sync
create_directories
setup_monitoring_config

log_success "Local environment setup completed successfully!"
log "Next steps:"
log "1. Edit $CONFIG_DIR/.env.production to set your API keys"
log "2. Run ./scripts/setup_local_backup.sh to configure local backups"
log "3. Run ./scripts/deploy_live.sh to deploy the system" 
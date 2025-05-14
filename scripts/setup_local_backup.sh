#!/bin/bash
#
# BensBot Trading System - Local Backup Setup Script
# This script sets up local backup directories and configurations.
#

# Exit on any error
set -e

# Configuration
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/trading_backups}"
BACKUP_SUBDIRS=("daily" "weekly" "monthly" "system_state" "strategies")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="setup_backup_${TIMESTAMP}.log"

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

# Main setup function
setup_backup_directories() {
    log "Setting up local backup directories..."
    
    # Create main backup directory
    if [ ! -d "$BACKUP_ROOT" ]; then
        mkdir -p "$BACKUP_ROOT"
        log "Created main backup directory: $BACKUP_ROOT"
    else
        log "Main backup directory already exists: $BACKUP_ROOT"
    fi
    
    # Create backup subdirectories
    for subdir in "${BACKUP_SUBDIRS[@]}"; do
        if [ ! -d "$BACKUP_ROOT/$subdir" ]; then
            mkdir -p "$BACKUP_ROOT/$subdir"
            log "Created backup subdirectory: $BACKUP_ROOT/$subdir"
        else
            log "Backup subdirectory already exists: $BACKUP_ROOT/$subdir"
        fi
    done
    
    # Set permissions to restrict access
    chmod -R 750 "$BACKUP_ROOT"
    log "Set secure permissions on backup directories"
    
    # Create a test file to verify write access
    TEST_FILE="$BACKUP_ROOT/backup_test_${TIMESTAMP}.txt"
    echo "Backup directory test file - $(date)" > "$TEST_FILE"
    
    if [ -f "$TEST_FILE" ]; then
        log_success "Successfully verified write access to backup directory"
        rm "$TEST_FILE"
    else
        log_error "Failed to write test file to backup directory. Check permissions."
        exit 1
    fi
}

setup_crontab_entries() {
    log "Setting up crontab entries for regular backups..."
    
    # Path to the backup script - use absolute path for crontab
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
    
    if [ ! -f "$BACKUP_SCRIPT" ]; then
        log_error "Backup script not found at: $BACKUP_SCRIPT"
        exit 1
    fi
    
    # Make backup script executable
    chmod +x "$BACKUP_SCRIPT"
    log "Made backup script executable"
    
    # Create temporary crontab file
    TEMP_CRONTAB=$(mktemp)
    
    # Export current crontab
    crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# BensBot Trading System Backups" > "$TEMP_CRONTAB"
    
    # Check if backup entries already exist
    if grep -q "backup.sh" "$TEMP_CRONTAB"; then
        log_warning "Backup entries already exist in crontab. Skipping crontab setup."
        rm "$TEMP_CRONTAB"
        return
    fi
    
    # Add backup crontab entries
    cat >> "$TEMP_CRONTAB" << EOF

# BensBot Trading System - Automated Backups
# Added on $(date)
# Daily backup at 1:00 AM
0 1 * * * $BACKUP_SCRIPT --backup-dir=$BACKUP_ROOT/daily

# Weekly full backup on Sundays at 2:00 AM
0 2 * * 0 $BACKUP_SCRIPT --full --backup-dir=$BACKUP_ROOT/weekly

# Monthly backup on 1st of month at 3:00 AM
0 3 1 * * $BACKUP_SCRIPT --full --backup-dir=$BACKUP_ROOT/monthly

# Strategy backup every 6 hours
0 */6 * * * $BACKUP_SCRIPT --backup-dir=$BACKUP_ROOT/strategies --strategy-only
EOF
    
    # Install new crontab
    crontab "$TEMP_CRONTAB"
    rm "$TEMP_CRONTAB"
    
    log_success "Crontab entries for backups have been set up"
    log "Backup schedule:"
    log "  - Daily backups at 1:00 AM"
    log "  - Weekly full backups on Sundays at 2:00 AM"
    log "  - Monthly full backups on 1st of month at 3:00 AM"
    log "  - Strategy backups every 6 hours"
}

create_backup_config() {
    log "Creating backup configuration file..."
    
    CONFIG_DIR="config"
    mkdir -p "$CONFIG_DIR"
    
    CONFIG_FILE="$CONFIG_DIR/backup_config.json"
    
    # Create backup configuration
    cat > "$CONFIG_FILE" << EOF
{
    "backup": {
        "directories": {
            "root": "$BACKUP_ROOT",
            "daily": "$BACKUP_ROOT/daily",
            "weekly": "$BACKUP_ROOT/weekly",
            "monthly": "$BACKUP_ROOT/monthly",
            "strategies": "$BACKUP_ROOT/strategies",
            "system_state": "$BACKUP_ROOT/system_state"
        },
        "retention": {
            "daily": 7,
            "weekly": 4,
            "monthly": 12,
            "strategies": 30
        },
        "cloud_sync": {
            "enabled": false,
            "provider": "none",
            "aws_bucket": "",
            "aws_region": "us-east-1",
            "sync_schedule": "daily"
        }
    }
}
EOF
    
    log_success "Created backup configuration file: $CONFIG_FILE"
}

# Main execution
log "Starting BensBot local backup setup..."

setup_backup_directories
create_backup_config
setup_crontab_entries

log_success "Local backup setup completed successfully!"
log "Backup root directory: $BACKUP_ROOT"
log "You can modify backup settings in config/backup_config.json"

# Optional: copy backup config to deployment directory
if [ -d "deployment/config" ]; then
    cp "config/backup_config.json" "deployment/config/"
    log "Copied backup configuration to deployment directory"
fi 
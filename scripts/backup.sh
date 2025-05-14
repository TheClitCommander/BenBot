#!/bin/bash
#
# BensBot Trading System - Backup Script
# This script creates comprehensive backups of system data and configuration.
#

# Exit on any error
set -e

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"
DATA_DIR="data"
CONFIG_DIR="config"
LOGS_DIR="logs"
CLOUD_SYNC=${CLOUD_SYNC:-false}  # Set to true via env var or argument to upload to cloud
STRATEGY_ONLY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --cloud-sync)
            CLOUD_SYNC=true
            shift
            ;;
        --aws-profile)
            AWS_PROFILE="$2"
            shift
            shift
            ;;
        --aws-bucket)
            AWS_BUCKET="$2"
            shift
            shift
            ;;
        --full)
            FULL_BACKUP=true
            shift
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift
            shift
            ;;
        --strategy-only)
            STRATEGY_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log() {
    echo -e "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
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

# Load config file if it exists
load_config() {
    CONFIG_FILE="config/backup_config.json"
    if [ -f "$CONFIG_FILE" ]; then
        log "Loading backup configuration from $CONFIG_FILE"
        
        # Try to use jq if available
        if command -v jq &> /dev/null; then
            if [ -z "$BACKUP_DIR_OVERRIDE" ]; then
                BACKUP_ROOT=$(jq -r '.backup.directories.root' "$CONFIG_FILE")
                if [ "$BACKUP_ROOT" != "null" ] && [ ! -z "$BACKUP_ROOT" ]; then
                    BACKUP_DIR="$BACKUP_ROOT"
                    log "Using backup directory from config: $BACKUP_DIR"
                fi
            fi
            
            # Load cloud sync settings if not overridden by command line
            if [ "$CLOUD_SYNC" = false ]; then
                CLOUD_SYNC_ENABLED=$(jq -r '.backup.cloud_sync.enabled' "$CONFIG_FILE")
                if [ "$CLOUD_SYNC_ENABLED" = "true" ]; then
                    CLOUD_SYNC=true
                    log "Cloud sync enabled from config"
                    
                    # Get AWS settings
                    AWS_BUCKET_FROM_CONFIG=$(jq -r '.backup.cloud_sync.aws_bucket' "$CONFIG_FILE")
                    if [ "$AWS_BUCKET_FROM_CONFIG" != "null" ] && [ ! -z "$AWS_BUCKET_FROM_CONFIG" ]; then
                        AWS_BUCKET="$AWS_BUCKET_FROM_CONFIG"
                        log "Using AWS bucket from config: $AWS_BUCKET"
                    fi
                    
                    AWS_REGION_FROM_CONFIG=$(jq -r '.backup.cloud_sync.aws_region' "$CONFIG_FILE")
                    if [ "$AWS_REGION_FROM_CONFIG" != "null" ] && [ ! -z "$AWS_REGION_FROM_CONFIG" ]; then
                        export AWS_REGION="$AWS_REGION_FROM_CONFIG"
                    fi
                fi
            fi
        else
            log_warning "jq not found. Install jq for better config parsing."
        fi
    fi
}

create_backup_dir() {
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/$TIMESTAMP"
    log "Created backup directory: $BACKUP_DIR/$TIMESTAMP"
}

backup_data() {
    log "Backing up trading data..."
    
    if [ -d "$DATA_DIR" ]; then
        if [ "$FULL_BACKUP" = true ]; then
            # Full backup
            tar -czf "$BACKUP_DIR/$TIMESTAMP/data_full.tar.gz" "$DATA_DIR"
        else
            # Selective backup - only essential data
            
            # Backup strategies
            if [ -d "$DATA_DIR/strategies" ]; then
                tar -czf "$BACKUP_DIR/$TIMESTAMP/strategies.tar.gz" "$DATA_DIR/strategies"
            fi
            
            # Skip other data if strategy-only mode
            if [ "$STRATEGY_ONLY" = false ]; then
                # Backup performance data
                if [ -d "$DATA_DIR/performance" ]; then
                    tar -czf "$BACKUP_DIR/$TIMESTAMP/performance.tar.gz" "$DATA_DIR/performance"
                fi
                
                # Backup portfolio data
                if [ -d "$DATA_DIR/portfolio" ]; then
                    tar -czf "$BACKUP_DIR/$TIMESTAMP/portfolio.tar.gz" "$DATA_DIR/portfolio"
                fi
                
                # Backup recent history only (last 30 days)
                if [ -d "$DATA_DIR/history" ]; then
                    find "$DATA_DIR/history" -type f -mtime -30 -print0 | tar -czf "$BACKUP_DIR/$TIMESTAMP/recent_history.tar.gz" --null -T -
                fi
            fi
        fi
        
        log_success "Data backup completed."
    else
        log_warning "Data directory not found. Skipping data backup."
    fi
}

backup_config() {
    # Skip if strategy-only mode
    if [ "$STRATEGY_ONLY" = true ]; then
        log "Skipping config backup in strategy-only mode"
        return
    fi
    
    log "Backing up configuration..."
    
    if [ -d "$CONFIG_DIR" ]; then
        # Exclude sensitive files like .env with API keys
        tar --exclude="$CONFIG_DIR/.env*" -czf "$BACKUP_DIR/$TIMESTAMP/config.tar.gz" "$CONFIG_DIR"
        log_success "Configuration backup completed."
    else
        log_warning "Configuration directory not found. Skipping config backup."
    fi
}

backup_logs() {
    # Skip if strategy-only mode
    if [ "$STRATEGY_ONLY" = true ]; then
        log "Skipping logs backup in strategy-only mode"
        return
    fi
    
    log "Backing up logs..."
    
    if [ -d "$LOGS_DIR" ]; then
        if [ "$FULL_BACKUP" = true ]; then
            # Full log backup
            tar -czf "$BACKUP_DIR/$TIMESTAMP/logs_full.tar.gz" "$LOGS_DIR"
        else
            # Only recent logs (last 7 days)
            find "$LOGS_DIR" -type f -mtime -7 -print0 | tar -czf "$BACKUP_DIR/$TIMESTAMP/recent_logs.tar.gz" --null -T -
        fi
        
        log_success "Logs backup completed."
    else
        log_warning "Logs directory not found. Skipping logs backup."
    fi
}

create_backup_manifest() {
    log "Creating backup manifest..."
    
    # Create manifest file with details about backup
    MANIFEST_FILE="$BACKUP_DIR/$TIMESTAMP/manifest.json"
    
    cat > "$MANIFEST_FILE" << EOF
{
    "backup_id": "$TIMESTAMP",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "system": "$(uname -a)",
    "hostname": "$(hostname)",
    "backup_type": "$([ "$FULL_BACKUP" = true ] && echo "full" || ([ "$STRATEGY_ONLY" = true ] && echo "strategy_only" || echo "selective"))",
    "contents": {
        "data": $([ -f "$BACKUP_DIR/$TIMESTAMP/data_full.tar.gz" ] && echo "true" || echo "false"),
        "strategies": $([ -f "$BACKUP_DIR/$TIMESTAMP/strategies.tar.gz" ] && echo "true" || echo "false"),
        "performance": $([ -f "$BACKUP_DIR/$TIMESTAMP/performance.tar.gz" ] && echo "true" || echo "false"),
        "portfolio": $([ -f "$BACKUP_DIR/$TIMESTAMP/portfolio.tar.gz" ] && echo "true" || echo "false"),
        "history": $([ -f "$BACKUP_DIR/$TIMESTAMP/recent_history.tar.gz" ] && echo "true" || echo "false"),
        "config": $([ -f "$BACKUP_DIR/$TIMESTAMP/config.tar.gz" ] && echo "true" || echo "false"),
        "logs": $([ -f "$BACKUP_DIR/$TIMESTAMP/logs_full.tar.gz" ] && echo "true" || ([ -f "$BACKUP_DIR/$TIMESTAMP/recent_logs.tar.gz" ] && echo "true" || echo "false"))
    },
    "files": [
        $(find "$BACKUP_DIR/$TIMESTAMP" -type f -name "*.tar.gz" | sort | sed 's/.*\///' | sed 's/^\(.*\)$/"\1"/' | paste -sd "," -)
    ],
    "backup_dir": "$BACKUP_DIR"
}
EOF
    
    log_success "Backup manifest created."
}

compress_backup() {
    log "Compressing backup..."
    
    # Create a single archive of the backup directory
    cd "$BACKUP_DIR"
    
    if [ "$STRATEGY_ONLY" = true ]; then
        ARCHIVE_NAME="bensbot_strategies_$TIMESTAMP.tar.gz"
    else
        ARCHIVE_NAME="bensbot_backup_$TIMESTAMP.tar.gz"
    fi
    
    tar -czf "$ARCHIVE_NAME" "$TIMESTAMP"
    cd - > /dev/null
    
    log_success "Backup compressed to $BACKUP_DIR/$ARCHIVE_NAME"
    return "$BACKUP_DIR/$ARCHIVE_NAME"
}

cloud_sync_backup() {
    if [ "$CLOUD_SYNC" = true ]; then
        log "Syncing backup to cloud storage..."
        
        if [ "$STRATEGY_ONLY" = true ]; then
            BACKUP_FILE="$BACKUP_DIR/bensbot_strategies_$TIMESTAMP.tar.gz"
            CLOUD_PREFIX="strategies"
        else
            BACKUP_FILE="$BACKUP_DIR/bensbot_backup_$TIMESTAMP.tar.gz"
            CLOUD_PREFIX="backups"
        fi
        
        if [ -f "$BACKUP_FILE" ]; then
            if command -v aws &> /dev/null; then
                if [ -n "$AWS_BUCKET" ]; then
                    # Set AWS profile if provided
                    if [ -n "$AWS_PROFILE" ]; then
                        AWS_PROFILE_ARG="--profile $AWS_PROFILE"
                    else
                        AWS_PROFILE_ARG=""
                    fi
                    
                    # Upload to S3
                    aws $AWS_PROFILE_ARG s3 cp "$BACKUP_FILE" "s3://$AWS_BUCKET/$CLOUD_PREFIX/$(basename "$BACKUP_FILE")"
                    log_success "Backup uploaded to S3 bucket: $AWS_BUCKET/$CLOUD_PREFIX"
                else
                    log_error "AWS bucket not specified. Use --aws-bucket to specify."
                fi
            else
                log_warning "AWS CLI not found. Falling back to local backup only."
            fi
        else
            log_error "Backup file not found: $BACKUP_FILE"
        fi
    else
        log "Cloud sync not enabled. Keeping backup local only."
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Load retention settings
    RETENTION_DAYS=10  # Default
    if [ -f "config/backup_config.json" ] && command -v jq &> /dev/null; then
        if [ "$STRATEGY_ONLY" = true ]; then
            RETENTION_DAYS=$(jq -r '.backup.retention.strategies // 30' "config/backup_config.json")
        elif [[ "$BACKUP_DIR" == *"/daily"* ]]; then
            RETENTION_DAYS=$(jq -r '.backup.retention.daily // 7' "config/backup_config.json")
        elif [[ "$BACKUP_DIR" == *"/weekly"* ]]; then
            RETENTION_DAYS=$(jq -r '.backup.retention.weekly // 4' "config/backup_config.json")
        elif [[ "$BACKUP_DIR" == *"/monthly"* ]]; then
            RETENTION_DAYS=$(jq -r '.backup.retention.monthly // 12' "config/backup_config.json")
        fi
    fi
    
    # Keep only the last N backups based on backup type
    cd "$BACKUP_DIR"
    
    if [ "$STRATEGY_ONLY" = true ]; then
        ls -t bensbot_strategies_*.tar.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
    else
        ls -t bensbot_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    fi
    
    # Remove extracted backup directories older than retention period
    find . -type d -name "20*" -mtime +$RETENTION_DAYS | xargs rm -rf 2>/dev/null || true
    
    cd - > /dev/null
    
    log_success "Cleanup completed. Keeping backups for $RETENTION_DAYS days."
}

# Main backup flow
log "Starting BensBot backup process..."
log "Backup type: $([ "$FULL_BACKUP" = true ] && echo "Full" || ([ "$STRATEGY_ONLY" = true ] && echo "Strategy Only" || echo "Selective"))"
log "Backup destination: $BACKUP_DIR"

# Load configuration
load_config

create_backup_dir
backup_data
backup_config
backup_logs
create_backup_manifest
compress_backup
cloud_sync_backup
cleanup_old_backups

log_success "Backup process completed successfully!"
if [ "$STRATEGY_ONLY" = true ]; then
    log "Backup location: $BACKUP_DIR/bensbot_strategies_$TIMESTAMP.tar.gz"
else
    log "Backup location: $BACKUP_DIR/bensbot_backup_$TIMESTAMP.tar.gz"
fi 
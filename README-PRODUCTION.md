# BensBot Trading System - Production Guide

This guide provides instructions for deploying and managing the BensBot trading system in a production environment.

## System Overview

BensBot is a sophisticated multi-asset trading system with:

- AI-driven trading strategies (via GPT and evolutionary algorithms)
- Dynamic capital allocation
- Comprehensive risk management
- Live system monitoring
- Multiple data sources and execution adapters
- Cloud backup and recovery

## Quick Start

For a quick deployment without AWS:

```bash
# Set up local environment
./scripts/setup_local_env.sh

# Set up local backup
./scripts/setup_local_backup.sh

# Deploy the system
./scripts/deploy_live.sh
```

## Detailed Setup Process

### 1. Configure Environment

First, create and configure your production environment file:

```bash
# Set up the environment with local paths
./scripts/setup_local_env.sh
```

This script will:
- Create a `.env.production` file from the template
- Configure paths for local development
- Disable cloud sync (until AWS credentials are available)
- Create necessary directories
- Set up monitoring configuration

Edit the `.env.production` file to add your API credentials:
```bash
nano config/.env.production
```

### 2. Configure Backup System

Set up the backup system for regular data and strategy backups:

```bash
# Set up local backup directories and schedule
./scripts/setup_local_backup.sh
```

This will:
- Create local backup directories
- Configure backup retention policies
- Set up crontab entries for scheduled backups

### 3. Deploy the System

Deploy the system to a clean production environment:

```bash
# Deploy the system
./scripts/deploy_live.sh
```

The deployment script will:
- Check system requirements
- Create a backup of the current state
- Create a clean deployment directory
- Install dependencies
- Configure the system
- Create startup scripts

### 4. Start the System

After deployment, you can start the system:

```bash
cd deployment
./start_trading.sh
```

## Directory Structure

```
deployment/               # Production deployment directory
├── config/               # Configuration files
│   ├── .env.production   # Production environment variables
│   ├── deployment.json   # Deployment configuration
│   └── health_monitor.json # Health monitoring configuration
├── data/                 # Trading data
│   ├── strategies/       # Trading strategies
│   ├── performance/      # Performance records
│   └── history/          # Historical data
├── logs/                 # Log files
├── scripts/              # Utility scripts
├── trading_bot/          # Trading system code
├── venv/                 # Python virtual environment
└── start_trading.sh      # Startup script
```

## Cloud Backup Integration

When your AWS account is verified, update your `.env.production` file:

```
ENABLE_CLOUD_SYNC=true
CLOUD_SYNC_PROVIDER=s3
AWS_ACCESS_KEY_ID=your_verified_key
AWS_SECRET_ACCESS_KEY=your_verified_secret
AWS_S3_BUCKET=your-bensbot-bucket
AWS_REGION=us-east-1
```

Then run a manual backup to test cloud integration:

```bash
./scripts/backup.sh --cloud-sync --aws-bucket your-bensbot-bucket
```

## Monitoring and Maintenance

### Health Monitoring

The system health monitor runs automatically and provides:
- Data feed latency monitoring
- Strategy execution performance
- System resource usage
- Alert generation

Health reports are stored in:
```
data/health_monitor/reports/
```

### Regular Maintenance

1. **Daily**: Review health reports and alerts
2. **Weekly**: Perform full backups and strategy performance reviews
3. **Monthly**: Optimize system parameters and risk settings

### Going Live

Before switching from paper to live trading:

1. Run at least 1 week in paper mode to validate performance
2. Review all strategies and allocation decisions
3. Check guard rails and safety mechanisms
4. Update environment to enable live trading:
   ```
   TRADE_MODE=live
   ```
5. Restart the system with live trading enabled

## Troubleshooting

### Common Issues

1. **Data feed connectivity issues**:
   - Check API credentials in .env.production
   - Verify network connectivity
   - Check data feed latency in health reports

2. **Strategy performance issues**:
   - Review strategy logs in logs/strategies/
   - Check allocator decisions in logs/system/
   - Review Monte Carlo simulation results

3. **System resource limitations**:
   - Check system health reports for memory/CPU usage
   - Consider upgrading hardware if consistently at limits

### Support

For additional support or questions about the system, refer to the internal documentation or contact the development team. 
# BensBot Production Launch Checklist

This checklist guides you through deploying BensBot trading system to production with or without AWS integration.

## Pre-Launch Preparation

- [ ] Review all strategies and allocation settings
- [ ] Verify broker API connectivity (Alpaca, Binance, etc.)
- [ ] Set risk parameters (max drawdown, per-strategy allocation, etc.)
- [ ] Create backup directories and verify permissions
- [ ] Ensure monitoring channels are configured (Telegram, Slack, etc.)

## Configuration Setup

- [ ] Copy environment template:
  ```bash
  cp config/env.production.template .env.production
  ```

- [ ] Edit production environment file:
  ```bash
  nano .env.production
  ```

- [ ] Configure critical settings:
  - [ ] API credentials for all brokers
  - [ ] Set `TRADE_MODE=paper` for initial testing (change to `live` after validation)
  - [ ] Set `ENABLE_STRATEGY_GUARDIAN=true` for safety
  - [ ] Configure alert channels (Telegram/Slack)
  - [ ] Set backup preferences

## Launch Without AWS (Temporary)

- [ ] Create local backup directory:
  ```bash
  mkdir -p ~/trading_backups
  ```

- [ ] Configure local backup in .env.production:
  ```
  ENABLE_CLOUD_SYNC=false
  CLOUD_SYNC_PROVIDER=none
  ```

- [ ] Deploy the system:
  ```bash
  chmod +x ./scripts/deploy_live.sh
  ./scripts/deploy_live.sh
  ```

- [ ] Set up local backup schedule:
  ```bash
  crontab -e
  
  # Add these lines
  0 */6 * * * /full/path/to/deployment/scripts/backup.sh
  0 0 * * 0 /full/path/to/deployment/scripts/backup.sh --full
  ```

## Post-Launch Verification

- [ ] Verify system health monitor is running:
  ```bash
  cd deployment
  tail -f logs/$(date +"%Y-%m-%d")/system_health.log
  ```

- [ ] Check trading system status via dashboard
- [ ] Verify strategy guardian is active
- [ ] Confirm allocation engine is running
- [ ] Test alert system by generating a test alert
- [ ] Run a manual backup and verify contents:
  ```bash
  cd deployment
  ./scripts/backup.sh
  ls -la backups/
  ```

## When AWS Verification Completes

- [ ] Update .env.production with AWS credentials:
  ```
  ENABLE_CLOUD_SYNC=true
  CLOUD_SYNC_PROVIDER=s3
  AWS_ACCESS_KEY_ID=your_verified_key
  AWS_SECRET_ACCESS_KEY=your_verified_secret
  AWS_S3_BUCKET=your-bensbot-bucket
  AWS_REGION=us-east-1
  ```

- [ ] Run initial cloud backup:
  ```bash
  ./scripts/backup.sh --cloud-sync --aws-bucket your-bensbot-bucket
  ```

- [ ] Verify file transfer to S3:
  ```bash
  aws s3 ls s3://your-bensbot-bucket/backups/
  ```

## Going Live Checklist

Before switching from paper to live trading:

- [ ] Run for at least 1 week in paper mode
- [ ] Verify no critical health monitor alerts
- [ ] Confirm strategy performance matches expectations
- [ ] Check all guard rails are functioning
- [ ] Review allocation decisions
- [ ] Update .env.production:
  ```
  TRADE_MODE=live
  ```

- [ ] Restart the system:
  ```bash
  cd deployment
  ./start_trading.sh
  ```

## Maintenance Schedule

- [ ] Daily: Review health monitor reports
- [ ] Weekly: Full backup and strategy performance review
- [ ] Monthly: System optimization and risk parameter review 
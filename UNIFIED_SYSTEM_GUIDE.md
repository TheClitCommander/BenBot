# BensBot Trading System: Unified Setup Guide

This guide consolidates all methods for running your trading system, from simple scripts to containerized deployment.

## Quick Start Options

Choose your preferred method to start the system:

### 1. One-Click Script (Recommended for Development)

```bash
./launch_hardened.sh
```

This script automatically:
- Detects and kills conflicting processes
- Sets up your Python virtual environment
- Starts the FastAPI backend (port 8000)
- Starts the backtester API (port 5002) 
- Launches the React frontend (port 3003)
- Provides comprehensive logging in the `logs` directory

### 2. Docker Deployment (Recommended for Production)

```bash
docker-compose up -d
```

This launches the containerized stack with:
- API backend container
- Backtester API container
- React frontend container (with NGINX)
- NGINX gateway for production deployments

## System Architecture

```
┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │
│  React Frontend │◄────►│  FastAPI Backend│
│   (Port 3003)   │      │   (Port 8000)   │
│                 │      │                 │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │                        │
         │                        │
         │                ┌───────┴────────┐
         │                │                │
         └───────────────►│Backtester API  │
                          │  (Port 5002)   │
                          │                │
                          └────────────────┘
```

## Components

### Backend API (Port 8000)

The core trading engine with endpoints for:
- Portfolio management
- Strategy execution
- Market data
- Alerts and notifications
- Authentication

### Backtester API (Port 5002)

Specialized backtesting service for:
- Strategy testing
- Performance simulation
- Parameter optimization
- Evolution testing

### React Dashboard (Port 3003)

Modern UI dashboard with:
- Portfolio overview
- Strategy management
- Backtesting controls
- Real-time charts and performance metrics

## Configuration

### API Configuration

Backend API settings can be adjusted in:
- `.env` file for environment variables
- `trading_bot/config.py` for application settings

### Frontend Configuration 

React settings are managed in:
- `.env` file in the React project root
- `vite.config.ts` for server and proxy settings

## Troubleshooting

### API Connection Issues
- Verify ports 8000 and 5002 are available
- Check Python environment has all dependencies
- Ensure PYTHONPATH includes project root

### Frontend Issues
- Verify Node.js and NPM are installed
- Check for correct proxy settings in vite.config.ts
- Clear browser cache if displaying old data

### Docker Issues
- Ensure Docker and Docker Compose are installed
- Check disk space for container storage
- Verify all ports are available

## Cloud Deployment (Optional)

For 24/7 uptime, deploy to a cloud provider:

1. Push your code to GitHub
2. Set up a VPS (DigitalOcean, Linode, AWS)
3. Use the Docker Compose setup for deployment
4. Configure GitHub actions for CI/CD

## Next Steps

Consider implementing:
1. Automated backups for trading data
2. HTTPS for secure API connections
3. User authentication for dashboard access
4. Performance monitoring with Prometheus/Grafana

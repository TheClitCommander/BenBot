# BensBot Trading System - Quick Start Guide

## One-Click Launch
1. Double-click `BensBot.command` on your desktop to start the entire system
2. The terminal will show you the URL (usually http://localhost:5173)
3. Open that URL in your browser to access the dashboard

## What's Included
- Trading bot backend running with real exchange data
- Professional trading dashboard with real-time monitoring
- Strategy management and performance tracking

## Requirements
- Python 3.11+ (automatically configured)
- Node.js 18+ (for the dashboard)
- No Docker required - everything runs directly on your machine

## Troubleshooting
If you encounter issues:
1. Check the terminal window for any error messages
2. Make sure port 5173 and 8000 aren't already in use
3. If dashboard won't connect to backend, check that API is running at http://localhost:8000

## Stopping the System
- Simply press Ctrl+C in the terminal window where you launched the system
- The script will cleanly shut down all components 
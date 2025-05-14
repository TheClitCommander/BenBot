# Trading Dashboard

A modern frontend dashboard for monitoring and controlling automated trading activities.

## Overview

This dashboard provides a complete interface for:

1. **Safety Controls**: Monitor and control trading guardrails like emergency stops, circuit breakers, and cooldown periods
2. **Performance Tracking**: Visualize trading performance with equity curves, position tables, and signal logs
3. **Strategy Management**: View strategy evolution and performance metrics (coming soon)

## Features

### Safety Controls

- Emergency Stop switch for immediate trading halt
- Trading Mode toggle (Live/Paper)
- Circuit Breaker status and management
- Cooldown Timer display
- Safety Event History log

### Performance Dashboard

- Equity Curve visualization
- Current Positions table with real-time data
- Signal Log for tracking recent trading signals
- Performance metrics and statistics

### Coming Soon

- Strategy Evolution tracking
- Custom Alert creation
- Backtesting and optimization interface
- User Account management

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Configuration

Configure the API endpoints in:
- `src/services/safetyApi.ts`
- `src/services/websocket.ts`

## Connecting to Backend

This dashboard connects to the trading bot API via:

1. REST API for configuration and commands
2. WebSockets for real-time updates

## Development

The dashboard is built with:

- React
- TypeScript
- Tailwind CSS
- Recharts
- React Query 
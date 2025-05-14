# BensBot Trading Dashboard

A modern React dashboard for monitoring and controlling the BensBot multi-asset trading system.

## Features

- **System Health Monitoring**: Real-time monitoring of system components, data feeds, and resource usage
- **Trading Performance Visualization**: Charts and metrics for trading performance analysis
- **Strategy Management**: View, edit, and activate trading strategies
- **Safety Controls**: Emergency stop features and circuit breakers
- **Portfolio Management**: Asset allocation visualization and management

## System Architecture

The dashboard connects to the BensBot backend API to retrieve data and control the trading system. The UI is built with:

- React for the component structure
- TypeScript for type safety
- TailwindCSS for styling
- React Query for data fetching and caching
- Lucide for icons and visual elements

## Screenshots

![System Health Panel](./public/screenshots/system-health.png)
![Strategy Dashboard](./public/screenshots/strategy-dashboard.png)

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```
3. Start the development server:
   ```
   npm run dev
   ```

## Environment Configuration

Create a `.env` file with the following variables:

```
REACT_APP_API_URL=http://localhost:8000  # Replace with your backend API URL
```

## Main Components

- **Dashboard**: Main container component that manages the application state
- **SystemHealthPanel**: Monitoring component for system health
- **PerformanceChart**: Trading performance visualization
- **SafetyControls**: Trading safety controls and circuit breakers
- **StrategyTrainer**: Strategy creation and optimization interface

## API Services

- **orchestrationApi**: Core trading functionality API
- **healthMonitorApi**: System health monitoring API
- **safetyApi**: Trading safety controls API
- **evolutionApi**: Strategy evolution API

## License

Copyright (c) 2023 Ben Dickinson. All rights reserved. 
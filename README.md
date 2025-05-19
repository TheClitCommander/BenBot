# BenBot Trading System

A modular trading system with a FastAPI backend and React dashboard frontend, focused on evolutionary trading strategies.

## Getting Started

### Prerequisites

- Python 3.9+ 
- Node.js 16+
- Docker and Docker Compose (optional, for containerized setup)
- Git

### Installation - Local Development

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/benbot.git
cd benbot
```

2. **Setup the environment**

```bash
# Make the setup script executable
chmod +x scripts/setup_env.sh

# Run the setup script
./scripts/setup_env.sh
```

This script will:
- Create a Python virtual environment
- Install Python dependencies
- Install Node.js dependencies for the frontend
- Create template environment files

3. **Configure environment variables**

Edit the `.env` file in the root directory with your API keys and other configurations.
Edit the `new-trading-dashboard/.env.local` file with frontend configurations.

4. **Verify the environment**

```bash
# Make the verify script executable
chmod +x scripts/verify_env.sh

# Run the verification
./scripts/verify_env.sh
```

### Installation - Docker Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/benbot.git
cd benbot
```

2. **Configure environment variables**

Copy the example environment file and edit it with your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

3. **Start the containers**

```bash
docker-compose up -d
```

## Running the Application

### Local Development

1. **Start the backend server**

```bash
# Activate the virtual environment
source venv/bin/activate

# Start the backend server
python demo_backend.py
```

2. **Start the frontend development server**

```bash
cd new-trading-dashboard
npm run dev
```

The frontend will be available at http://localhost:5173 (or another port if 5173 is in use).
The API will be available at http://localhost:8000.

### Docker Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

The frontend will be available at http://localhost:80.
The API will be available at http://localhost:8000.

## Architecture

- **Backend**: FastAPI application with endpoints for trading operations, strategy management, and market data
- **Frontend**: React application with TypeScript, Vite, and modern UI libraries
- **Brokers**: Supports Alpaca and Tradier integration

## Available Scripts

- `scripts/setup_env.sh` - Set up the development environment
- `scripts/verify_env.sh` - Verify that the environment is properly configured

## Troubleshooting

### Common Issues

1. **Missing dependencies**

If you encounter missing Python dependencies, run:
```bash
pip install -r requirements.txt
```

If you encounter missing Node.js dependencies, run:
```bash
cd new-trading-dashboard
npm install
npm install @tanstack/react-query-devtools @mui/icons-material
```

2. **Port conflicts**

If you see "address already in use" errors, check for existing processes using the required ports:
```bash
# Check what's using port 8000 (backend)
lsof -i :8000

# Check what's using port 5173 (frontend)
lsof -i :5173
```

3. **WebSocket connection issues**

If the WebSocket connection fails with 400 errors, verify:
- The WebSocket URL is correct in the frontend .env.local file
- The backend server is properly configured for WebSocket connections

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Structure

```
.
├── trading-dashboard/        # React frontend
├── trading_bot/              # Python trading system backend
│   └── api/                  # FastAPI backend application
├── dev_tools/                # Development utilities
├── docker/                   # Docker configuration
├── docs/                     # Documentation
└── data/                     # Trading data and logs
```

## Quick Start

### Development Environment

1. Run the consolidated startup script:

```bash
./run_bensbot.sh
```

This will:
- Start the FastAPI backend (port 8000)
- Start the React dev server (port 5173)
- Configure proper environment variables

2. Visit the frontend at: http://localhost:5173
3. API endpoints are available at: http://localhost:8000

### Using Docker

```bash
docker-compose up -d
```

Access the frontend at: http://localhost:5173
API endpoints are available at: http://localhost:8000

## Integration Points

The frontend connects to the backend via:

- REST API at `/api/*` endpoints
- WebSocket connections at `/ws`

For detailed API documentation, visit http://localhost:8000/docs when the backend is running.

## Configuration

Environment variables can be set in:

- `trading-dashboard/.env.local` for frontend
- `.env` for backend

## Development Notes

- A clean codebase can be achieved with: `./cleanup.sh`
- The API backend uses FastAPI and requires Python 3.10+
- The frontend uses React, Vite, and TypeScript
- WebSocket connections provide real-time updates

## Documentation

For more detailed information, see the following guides:
- [Production Guide](docs/production-guide.md)
- [System Guide](docs/system-guide.md)
- [Launch Checklist](docs/launch-checklist.md)

## Key Components

### Execution Adapter

The `EvoToExecAdapter` in `trading_bot/core/execution/evo_adapter.py` is the bridge between evolved strategies and trading execution:

- Converts evolved strategy genomes to executable trading instructions
- Handles strategy activation/deactivation with risk management checks
- Includes strategy-specific parameter mapping
- Integrates with alerts for strategy activation notifications

### Scheduler Service

The `EvolutionScheduler` in `trading_bot/core/execution/scheduler.py` handles automated strategy evolution:

- Schedules strategy evolution runs during off-peak hours
- Manages recurring and one-time evolution tasks
- Tracks evolution progress and results
- Auto-promotes successful strategies based on performance criteria

### Risk Management Integration

The system integrates with the `SafetyManager` to provide comprehensive risk controls:

- Performs pre-activation checks for risk metrics (drawdown, Sharpe ratio, etc.)
- Respects global trading restrictions (emergency stop, circuit breakers)
- Enforces per-strategy risk limits during execution

### LLM-Guided Fitness Evaluation

The `LLMEvaluator` in `trading_bot/core/evolution/llm_evaluator.py` enhances strategy evaluation:

- Uses language models to evaluate strategy fitness beyond simple metrics
- Provides insights and feedback for improving strategies
- Suggests parameter adjustments based on performance patterns

## API Endpoints

### Execution Endpoints

- `POST /execution/strategies/{strategy_id}/activate` - Activate a specific strategy
- `POST /execution/strategies/auto-promote` - Auto-promote strategies meeting criteria
- `POST /execution/strategies/{strategy_id}/deactivate` - Deactivate a strategy
- `GET /execution/strategies/active` - Get all active strategies
- `POST /execution/evolution/schedule` - Schedule a strategy evolution run
- `GET /execution/evolution/schedules` - Get all scheduled evolution runs
- `DELETE /execution/evolution/schedules/{schedule_id}` - Delete a scheduled run
- `POST /execution/risk-checks` - Update risk check configuration

### Evolution Endpoints

- `GET /evolution/status` - Get evolution status and summary
- `POST /evolution/start` - Start a new evolution run
- `POST /evolution/backtest` - Run backtests for current generation
- `POST /evolution/evolve` - Evolve current generation
- `GET /evolution/strategies` - Get strategies from population
- `GET /evolution/best` - Get best strategies
- `GET /evolution/strategy/{strategy_id}` - Get specific strategy details
- `POST /evolution/promote` - Auto-promote strategies
- `POST /evolution/grid` - Create and run a backtest parameter grid
- `GET /evolution/grid/{grid_id}` - Get grid results
- `GET /evolution/grids` - List all available grids
- `POST /evolution/evaluate/llm` - Evaluate strategy with LLM guidance
- `POST /evolution/evaluate/llm/batch` - Batch evaluate strategies
- `POST /evolution/improve/llm` - Get improvement recommendations

## Usage Examples

### Schedule a Strategy Evolution Run

```python
import requests
import json
from datetime import time

url = "http://localhost:8000/execution/evolution/schedule"
payload = {
    "strategy_type": "mean_reversion",
    "parameter_space": {
        "lookback_period": [10, 50],
        "entry_threshold": [1.5, 3.0],
        "exit_threshold": [0.5, 1.5]
    },
    "market_data_id": "btc_hourly_2023",
    "schedule_time": time(22, 0).isoformat(),  # 10:00 PM
    "run_daily": True,
    "auto_promote": True,
    "generations": 20,
    "population_size": 50
}

response = requests.post(url, json=payload)
print(response.json())
```

### Activate a Specific Strategy

```python
import requests

strategy_id = "mean_reversion_gen10_elite0"
url = f"http://localhost:8000/execution/strategies/{strategy_id}/activate"

response = requests.post(url)
print(response.json())
```

# BenBot Trading Dashboard

A real-time trading dashboard that connects to Alpaca for live portfolio data.

## Quick Start

1. Get Alpaca API credentials:
   - Sign up at [Alpaca](https://alpaca.markets/)
   - Create a new API key in your Alpaca dashboard
   - Copy your API key and secret

2. Edit the `.env` file with your Alpaca credentials:
   ```
   ALPACA_API_KEY=your_api_key_here
   ALPACA_API_SECRET=your_api_secret_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

3. Run the dashboard:
   ```
   chmod +x start_alpaca.sh
   ./start_alpaca.sh
   ```

4. Access the dashboard in your browser:
   - Frontend: http://localhost:5173 (or port shown in terminal)
   - API: http://localhost:5001
   - API Health Check: http://localhost:5001/health

## Features

- Real-time connection to Alpaca API
- Live portfolio value and performance metrics
- Position tracking with P&L calculations
- Trade history
- Strategy management

## Paper Trading vs. Live Trading

By default, the dashboard connects to Alpaca's paper trading API. To switch to live trading:

1. Edit the `.env` file:
   ```
   ALPACA_BASE_URL=https://api.alpaca.markets
   ```

WARNING: Live trading involves real money. Use at your own risk.

## Troubleshooting

If you experience connection issues:

1. Check that your Alpaca API credentials are correct
2. Verify your internet connection
3. Check that port 5001 is not being used by another application
4. Look at the API server logs for error messages

For debugging mode:
```
./launch_debug.sh
```
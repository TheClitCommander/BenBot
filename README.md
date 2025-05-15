# BensBot Trading System

A reactive trading system with FastAPI backend and React dashboard frontend.

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
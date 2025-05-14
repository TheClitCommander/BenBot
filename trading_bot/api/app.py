"""
FastAPI application for BensBot trading system.

This module provides the main FastAPI application that serves as the backend
for the trading dashboard and exposes REST API endpoints for various trading
system functionality.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from trading_bot.api.routers.safety import router as safety_router
from trading_bot.api.routers.metrics import router as metrics_router
from trading_bot.api.routers.evolution import router as evolution_router, init_evolution_services
from trading_bot.api.routers.execution import router as execution_router, init_execution_adapter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Event bus for system-wide events
from trading_bot.core.event_bus import EventBus
event_bus = EventBus()

# Initialize safety manager
from trading_bot.core.safety import SafetyManager
safety_manager = SafetyManager(
    event_bus=event_bus,
    config_dir="./config/safety",
    safety_db_path="./data/safety_events.json"
)

# Mock backtester for development - replace with real implementation later
class MockBacktester:
    def run_backtest(self, strategy_type, parameters, market_data):
        """Simple mock for the backtester."""
        import random
        import time
        
        # Simulate processing time
        time.sleep(1)
        
        # Generate mock performance data
        return {
            "status": "success",
            "strategy_type": strategy_type,
            "parameters": parameters,
            "performance": {
                "total_return": random.uniform(-10, 25),
                "sharpe_ratio": random.uniform(0.1, 2.5),
                "max_drawdown": random.uniform(-30, -5),
                "win_rate": random.uniform(40, 70),
                "trades": random.randint(50, 200)
            }
        }

# Initialize backtester - replace with real backtester when available
backtester = MockBacktester()

# Initialize evolution services
evo_trader = init_evolution_services(backtester=backtester)

# Initialize trade executor
from trading_bot.core.execution.evo_adapter import TradeExecutor
trade_executor = TradeExecutor()

# Initialize scheduler
from trading_bot.core.execution.scheduler import EvolutionScheduler
scheduler = EvolutionScheduler(
    evo_trader=evo_trader,
    data_dir="./data/scheduler",
    config_path="./config/scheduler.json"
)

# Initialize execution adapter
init_execution_adapter(
    trade_executor=trade_executor,
    evo_trader=evo_trader,
    safety_mgr=safety_manager,
    scheduler_service=scheduler
)

# Start the scheduler
scheduler.start()

# Create FastAPI app
app = FastAPI(
    title="BensBot Trading API",
    description="Trading system API with comprehensive safety guardrails",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(safety_router)
app.include_router(metrics_router)
app.include_router(evolution_router)
app.include_router(execution_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to confirm API is running."""
    return {"status": "healthy", "version": "1.0.0"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with a structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with a structured response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

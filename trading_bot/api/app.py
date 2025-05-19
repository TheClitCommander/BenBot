"""
FastAPI application for BensBot trading system.

This module provides the main FastAPI application that serves as the backend
for the trading dashboard and exposes REST API endpoints for various trading
system functionality.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
from datetime import datetime
import os

# Import routers
from trading_bot.api.routers.safety import router as safety_router
from trading_bot.api.routers.health import router as health_router
from trading_bot.api.routers.evolution import router as evolution_router, init_evolution_services, evo_trader as evo_trader_service_from_router
from trading_bot.api.routers.execution import router as execution_router, init_execution_adapter, evo_adapter as evo_adapter_service_from_router
from trading_bot.api.routers.orchestration import router as orchestration_router
from trading_bot.api.routers.live_data import router as live_data_router
from trading_bot.api.routers.metrics import router as metrics_router
from trading_bot.api.routers.tradier import router as tradier_router

# Import monitoring middleware
from trading_bot.api.middleware.monitoring import MonitoringMiddleware
from trading_bot.api.middleware.performance import PerformanceMiddleware

# Setup logging
logging_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/api.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Check if in production mode
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
logger.info(f"Starting application in {os.getenv('ENVIRONMENT', 'development')} mode")

# Event bus for system-wide events
from trading_bot.core.event_bus import EventBus
event_bus = EventBus()

# Initialize safety manager
from trading_bot.core.safety import SafetyManager
safety_manager_instance = SafetyManager(
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
        time.sleep(0.1)
        
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
backtester_instance = MockBacktester()

# Initialize evolution services
_ = init_evolution_services(backtester=backtester_instance)

# Initialize trade executor
from trading_bot.core.execution.evo_adapter import TradeExecutor
trade_executor_instance = TradeExecutor()

# Initialize scheduler
from trading_bot.core.execution.scheduler import EvolutionScheduler
scheduler_instance = EvolutionScheduler(
    evo_trader=evo_trader_service_from_router,
    data_dir="./data/scheduler",
    config_path="./config/scheduler.json"
)

# Initialize execution adapter
_ = init_execution_adapter(
    trade_executor=trade_executor_instance,
    evo_trader=evo_trader_service_from_router,
    safety_mgr=safety_manager_instance,
    scheduler_service=scheduler_instance
)

# Initialize Orchestrator Service
from trading_bot.core.orchestration.orchestrator import Orchestrator
orchestrator_service = Orchestrator(
    evo_trader=evo_trader_service_from_router,
    scheduler=scheduler_instance,
    adapter=evo_adapter_service_from_router,
    safety=safety_manager_instance
)

# Dependency getter for Orchestrator
async def get_orchestrator() -> Orchestrator:
    return orchestrator_service

# Start the scheduler
scheduler_instance.start()

# Create FastAPI app
app = FastAPI(
    title="BensBot Trading API",
    description="Trading system API with comprehensive safety guardrails and orchestration",
    version="1.0.1",
    docs_url=None if IS_PRODUCTION else "/docs",  # Disable Swagger UI in production
    redoc_url=None if IS_PRODUCTION else "/redoc"  # Disable ReDoc in production
)

# Try to import our AI routes
try:
    from trading_bot.api.ai_routes import router as ai_router
    HAS_AI = True
    logger.info("AI modules loaded successfully")
except ImportError:
    logger.warning("AI modules not available - AI features will be disabled")
    HAS_AI = False

# Configure CORS
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:5177",
    "http://127.0.0.1:5178",
    "http://127.0.0.1:5179",
    "http://127.0.0.1:5180",
]

# In production, restrict origins to specific domains
if IS_PRODUCTION:
    production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if production_origins and production_origins[0]:
        allowed_origins = production_origins
    logger.info(f"CORS configured with origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware - should be added before other middleware
app.add_middleware(MonitoringMiddleware)

# Add performance middleware for tracking slow requests
app.add_middleware(PerformanceMiddleware)

# Include routers
app.include_router(safety_router)
app.include_router(health_router)
app.include_router(evolution_router)
app.include_router(execution_router)
app.include_router(orchestration_router)
app.include_router(live_data_router)
app.include_router(metrics_router)  # Add metrics router
app.include_router(tradier_router)  # Add tradier router

# Include AI routes if available
if HAS_AI:
    app.include_router(ai_router)
    logger.info("AI trading routes registered successfully")

# Health check endpoint
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": app.version,
        "ai_modules_available": HAS_AI,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint for real-time trading data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading events."""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        # Mock data for demonstration
        while True:
            # Send a ping every 5 seconds with some mock data
            mock_data = {
                "type": "trade_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": "BTC/USD",
                    "price": 28500 + (hash(datetime.now().isoformat()) % 1000),
                    "volume": 0.05,
                    "side": "buy"
                }
            }
            await websocket.send_text(json.dumps(mock_data))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

# Enhanced exception handling for production
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions with detailed logging."""
    error_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    logger.error(f"Unhandled exception {error_id}: {str(exc)}", exc_info=True)
    
    # In development, return the full error details
    if not IS_PRODUCTION:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal server error: {str(exc)}",
                "error_id": error_id
            }
        )
    # In production, hide implementation details
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please contact support.",
                "error_id": error_id
            }
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BensBot Trading API",
        "version": app.version,
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs" if not IS_PRODUCTION else None
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Runs when the API server starts up."""
    logger.info(f"BensBot Trading API v{app.version} starting up")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Make sure we have required directories
    for dir_path in ["./data", "./config", "./logs"]:
        os.makedirs(dir_path, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Runs when the API server is shutting down."""
    logger.info("BensBot Trading API shutting down")
    # Stop the scheduler
    scheduler_instance.stop()
    logger.info("Trading scheduler stopped")

if __name__ == "__main__":
    import uvicorn
    from trading_bot.api.routers import orchestration
    orchestration.get_orchestrator = get_orchestrator
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

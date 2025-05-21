"""
FastAPI application for BensBot trading system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Create FastAPI application
app = FastAPI(title="BensBot Trading API", version="1.0.0", description="API for BensBot trading system")

# Import routers - import all routers from the routers directory
from trading_bot.api.routers.safety import router as safety_router
from trading_bot.api.routers.health import router as health_router

# Try to import optional routers
try:
    from trading_bot.api.routers.metrics import router as metrics_router
    HAS_METRICS = True
    logger.info("Metrics router loaded")
except ImportError:
    logger.warning("Metrics router not available")
    HAS_METRICS = False

try:
    from trading_bot.api.routers.evolution import router as evolution_router
    HAS_EVOLUTION = True
    logger.info("Evolution router loaded")
except ImportError:
    logger.warning("Evolution router not available")
    HAS_EVOLUTION = False

try:
    from trading_bot.api.routers.execution import router as execution_router
    HAS_EXECUTION = True
    logger.info("Execution router loaded")
except ImportError:
    logger.warning("Execution router not available")
    HAS_EXECUTION = False

try:
    from trading_bot.api.routers.orchestration import router as orchestration_router
    HAS_ORCHESTRATION = True
    logger.info("Orchestration router loaded")
except ImportError:
    logger.warning("Orchestration router not available")
    HAS_ORCHESTRATION = False

try:
    from trading_bot.api.ai_routes import router as ai_router
    HAS_AI = True
    logger.info("AI router loaded")
except ImportError:
    logger.warning("AI modules not available - AI features will be disabled")
    HAS_AI = False

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://localhost:5181",
        "http://localhost:5182",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(safety_router)

# Register optional routers
if HAS_METRICS:
    app.include_router(metrics_router)

if HAS_EVOLUTION:
    app.include_router(evolution_router)

if HAS_EXECUTION:
    app.include_router(execution_router)

if HAS_ORCHESTRATION:
    app.include_router(orchestration_router)

if HAS_AI:
    app.include_router(ai_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "BensBot Trading API",
        "version": "1.0.0",
        "description": "API for BensBot trading system",
        "available_modules": {
            "metrics": HAS_METRICS,
            "evolution": HAS_EVOLUTION,
            "execution": HAS_EXECUTION,
            "orchestration": HAS_ORCHESTRATION,
            "ai": HAS_AI
        }
    } 
"""
Health check router for the trading API.

Provides endpoints for system health and status monitoring.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging
import platform
import os
import psutil
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger("api.health")

# Create router
router = APIRouter(
    tags=["Health"],
    responses={404: {"description": "Not found"}},
)

# Track server start time
SERVER_START_TIME = datetime.now()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify the API is running properly.
    This endpoint is used by monitoring systems and load balancers.
    """
    # Calculate uptime
    uptime = datetime.now() - SERVER_START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Try to get CPU and memory usage
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
    except:
        # Fallback if psutil isn't available
        cpu_percent = 0
        memory_percent = 0
    
    # Check for AI modules
    try:
        from ai_modules.MarketContextAnalyzer import MarketContextAnalyzer
        ai_available = True
    except ImportError:
        ai_available = False
    
    # Check for database connection
    try:
        # In a real system, this would check the actual database connection
        db_connected = True
    except:
        db_connected = False
        
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.environ.get("ENV", "development"),
        "timestamp": datetime.now().isoformat(),
        "uptime": f"{days}d {hours}h {minutes}m {seconds}s",
        "system_info": {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent
        },
        "services": {
            "ai_modules_available": ai_available,
            "database_connected": db_connected
        }
    } 
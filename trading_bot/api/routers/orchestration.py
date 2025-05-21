"""
Orchestration router for trading API.

Provides endpoints for orchestrating the trading system components and workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging
import random
from datetime import datetime, timedelta
from pydantic import BaseModel

# Setup logging
logger = logging.getLogger("api.orchestration")

# Create router
router = APIRouter(
    prefix="/orchestration",
    tags=["Orchestration"],
    responses={404: {"description": "Not found"}},
)

# Global system status
system_status = {
    "trading_mode": "paper",  # "paper" or "live"
    "auto_trading": False,
    "scheduled_jobs": {
        "daily_optimization": {
            "enabled": True,
            "time": "01:00:00",
            "status": "idle",
            "last_run": None,
            "next_run": (datetime.now() + timedelta(days=1)).replace(hour=1, minute=0, second=0).isoformat()
        },
        "market_analysis": {
            "enabled": True,
            "time": "08:00:00",
            "status": "idle",
            "last_run": None,
            "next_run": (datetime.now() + timedelta(days=1)).replace(hour=8, minute=0, second=0).isoformat()
        }
    },
    "active_strategies": [],
    "system_started_at": datetime.now().isoformat()
}

class TradingModeRequest(BaseModel):
    """Request model for changing trading mode."""
    mode: str  # 'paper' or 'live'

class ScheduleJobRequest(BaseModel):
    """Request model for scheduling a job."""
    job_id: str
    enabled: bool
    time: Optional[str] = None

class StrategyActivationRequest(BaseModel):
    """Request model for activating/deactivating a strategy."""
    strategy_id: str
    active: bool
    allocation: Optional[float] = None  # Percentage of capital to allocate

@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get the current status of the trading system."""
    # Update "current time" fields
    current_time = datetime.now().isoformat()
    uptime_seconds = (datetime.now() - datetime.fromisoformat(system_status["system_started_at"])).total_seconds()
    
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    return {
        **system_status,
        "current_time": current_time,
        "uptime": f"{days}d {hours}h {minutes}m",
        "system_health": {
            "cpu_usage": random.randint(10, 50),
            "memory_usage": random.randint(20, 70),
            "db_connection": "healthy",
            "api_status": "operational"
        }
    }

@router.put("/trading-mode")
async def set_trading_mode(request: TradingModeRequest) -> Dict[str, Any]:
    """Set the trading mode (paper or live)."""
    if request.mode not in ["paper", "live"]:
        raise HTTPException(status_code=400, detail=f"Invalid trading mode: {request.mode}. Must be 'paper' or 'live'.")
    
    # In a real implementation, this would trigger safety checks and confirmation flows
    # before allowing transition to live trading
    
    system_status["trading_mode"] = request.mode
    logger.info(f"Trading mode changed to {request.mode}")
    
    return {
        "success": True,
        "trading_mode": request.mode,
        "message": f"Trading mode set to {request.mode}"
    }

@router.put("/auto-trading")
async def set_auto_trading(enabled: bool) -> Dict[str, Any]:
    """Enable or disable automatic trading."""
    system_status["auto_trading"] = enabled
    status_str = "enabled" if enabled else "disabled"
    logger.info(f"Auto-trading {status_str}")
    
    return {
        "success": True,
        "auto_trading": enabled,
        "message": f"Auto-trading {status_str}"
    }

@router.post("/schedule-job")
async def schedule_job(request: ScheduleJobRequest) -> Dict[str, Any]:
    """Schedule a job in the trading system."""
    if request.job_id not in system_status["scheduled_jobs"]:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")
    
    job = system_status["scheduled_jobs"][request.job_id]
    job["enabled"] = request.enabled
    
    if request.time:
        try:
            # Parse time string (HH:MM:SS)
            hours, minutes, seconds = map(int, request.time.split(':'))
            
            # Validate time
            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59:
                raise ValueError("Invalid time")
                
            job["time"] = request.time
            
            # Calculate next run time
            now = datetime.now()
            target_time = now.replace(hour=hours, minute=minutes, second=seconds)
            
            # If target time is in the past, schedule for tomorrow
            if target_time < now:
                target_time += timedelta(days=1)
                
            job["next_run"] = target_time.isoformat()
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM:SS")
    
    return {
        "success": True,
        "job": {
            "id": request.job_id,
            **job
        }
    }

@router.post("/trigger-job/{job_id}")
async def trigger_job(job_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Manually trigger a scheduled job."""
    if job_id not in system_status["scheduled_jobs"]:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = system_status["scheduled_jobs"][job_id]
    
    # Update job status
    job["status"] = "running"
    job["last_run"] = datetime.now().isoformat()
    
    # Run job in background
    background_tasks.add_task(simulate_job_execution, job_id)
    
    return {
        "success": True,
        "message": f"Job {job_id} triggered",
        "job": {
            "id": job_id,
            **job
        }
    }

@router.post("/strategies/activate")
async def activate_strategy(request: StrategyActivationRequest) -> Dict[str, Any]:
    """Activate or deactivate a trading strategy."""
    # In a real implementation, this would check if the strategy exists in the system
    # For demo, we'll just assume it does
    
    # Check if strategy already in active strategies list
    strategy_exists = False
    for i, strategy in enumerate(system_status["active_strategies"]):
        if strategy["id"] == request.strategy_id:
            if request.active:
                # Update existing strategy
                system_status["active_strategies"][i] = {
                    "id": request.strategy_id,
                    "active": True,
                    "allocation": request.allocation or strategy["allocation"],
                    "activated_at": strategy["activated_at"]
                }
            else:
                # Remove from active strategies
                system_status["active_strategies"].pop(i)
            strategy_exists = True
            break
    
    if not strategy_exists and request.active:
        # Add new active strategy
        system_status["active_strategies"].append({
            "id": request.strategy_id,
            "active": True,
            "allocation": request.allocation or 10.0,  # Default 10% allocation
            "activated_at": datetime.now().isoformat()
        })
    
    return {
        "success": True,
        "active_strategies": system_status["active_strategies"]
    }

@router.get("/strategies/active")
async def get_active_strategies() -> Dict[str, Any]:
    """Get the list of currently active strategies."""
    return {
        "active_strategies": system_status["active_strategies"]
    }

# Helper function to simulate job execution
async def simulate_job_execution(job_id: str):
    """Simulate the execution of a scheduled job."""
    import asyncio
    
    # Simulate job running
    await asyncio.sleep(2)
    
    # Update job status
    system_status["scheduled_jobs"][job_id]["status"] = "idle"
    
    # Calculate next run
    hours, minutes, seconds = map(int, system_status["scheduled_jobs"][job_id]["time"].split(':'))
    now = datetime.now()
    target_time = now.replace(hour=hours, minute=minutes, second=seconds)
    
    # If target time is in the past, schedule for tomorrow
    if target_time < now:
        target_time += timedelta(days=1)
        
    system_status["scheduled_jobs"][job_id]["next_run"] = target_time.isoformat()
    
    logger.info(f"Job {job_id} completed, next run at {target_time.isoformat()}") 
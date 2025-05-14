"""
API routes for strategy execution and management.

This module provides endpoints for:
- Activating evolved strategies
- Managing active trading strategies
- Monitoring strategy execution
- Scheduling strategy evolution runs
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, time

# Router setup
router = APIRouter(
    prefix="/execution",
    tags=["execution"],
    responses={404: {"description": "Not found"}},
)

# Singleton instances, will be initialized by the app
evo_adapter = None
scheduler = None
safety_manager = None

class ActivationConfig(BaseModel):
    min_performance: Optional[float] = 5.0

class RiskCheckConfig(BaseModel):
    min_return: float = Field(5.0, description="Minimum total return percentage")
    max_drawdown: float = Field(-25.0, description="Maximum allowed drawdown percentage")
    min_sharpe: float = Field(0.5, description="Minimum Sharpe ratio")
    min_win_rate: float = Field(0.4, description="Minimum win rate (0-1)")

class ScheduleConfig(BaseModel):
    strategy_type: str = Field(..., description="Type of strategy to evolve")
    parameter_space: Dict[str, Any] = Field(..., description="Parameter ranges for evolution")
    market_data_id: Optional[str] = Field(None, description="Market data ID for backtesting")
    schedule_time: time = Field(..., description="Time to run (24h format)")
    run_daily: bool = Field(True, description="Whether to run daily")
    auto_promote: bool = Field(False, description="Auto-promote successful strategies")
    generations: int = Field(20, description="Number of generations to run")
    population_size: int = Field(50, description="Population size")

@router.post("/strategies/{strategy_id}/activate")
async def activate_strategy(strategy_id: str):
    """Activate a specific strategy for live trading."""
    if not evo_adapter:
        return {"success": False, "error": "Execution adapter not initialized"}
    
    success = evo_adapter.activate_strategy(strategy_id)
    if not success:
        return {"success": False, "error": f"Failed to activate strategy {strategy_id}"}
    
    return {"success": True, "message": f"Strategy {strategy_id} activated for live trading"}

@router.post("/strategies/auto-promote")
async def activate_auto_promoted(config: ActivationConfig = ActivationConfig()):
    """Activate all auto-promoted strategies meeting criteria."""
    if not evo_adapter:
        return {"success": False, "error": "Execution adapter not initialized"}
    
    activated_ids = evo_adapter.activate_auto_promoted(config.min_performance)
    
    return {
        "success": True, 
        "data": {
            "activated_strategies": activated_ids,
            "count": len(activated_ids)
        }
    }

@router.post("/strategies/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: str):
    """Deactivate a strategy from live trading."""
    if not evo_adapter:
        return {"success": False, "error": "Execution adapter not initialized"}
    
    success = evo_adapter.deactivate_strategy(strategy_id)
    if not success:
        return {"success": False, "error": f"Failed to deactivate strategy {strategy_id}"}
    
    return {"success": True, "message": f"Strategy {strategy_id} deactivated from trading"}

@router.get("/strategies/active")
async def get_active_strategies():
    """Get all active trading strategies."""
    if not evo_adapter:
        return {"success": False, "error": "Execution adapter not initialized"}
    
    active_strategies = evo_adapter.get_active_strategies()
    
    return {"success": True, "data": active_strategies}

@router.post("/evolution/schedule")
async def schedule_evolution(config: ScheduleConfig, background_tasks: BackgroundTasks):
    """Schedule strategy evolution runs."""
    if not scheduler:
        return {"success": False, "error": "Scheduler not initialized"}
    
    if not config.market_data_id:
        return {"success": False, "error": "Market data ID is required"}
    
    # Create a schedule entry
    schedule_id = f"evo_schedule_{int(datetime.now().timestamp())}"
    
    # Schedule the evolution job
    success = scheduler.schedule_evolution(
        schedule_id=schedule_id,
        strategy_type=config.strategy_type,
        parameter_space=config.parameter_space,
        market_data_id=config.market_data_id,
        schedule_time=config.schedule_time,
        run_daily=config.run_daily,
        auto_promote=config.auto_promote,
        generations=config.generations,
        population_size=config.population_size,
        background_tasks=background_tasks
    )
    
    if not success:
        return {"success": False, "error": "Failed to schedule evolution run"}
    
    return {
        "success": True,
        "data": {
            "schedule_id": schedule_id,
            "strategy_type": config.strategy_type,
            "schedule_time": config.schedule_time.isoformat(),
            "run_daily": config.run_daily
        }
    }

@router.get("/evolution/schedules")
async def get_evolution_schedules():
    """Get all scheduled evolution runs."""
    if not scheduler:
        return {"success": False, "error": "Scheduler not initialized"}
    
    schedules = scheduler.get_schedules()
    
    return {"success": True, "data": schedules}

@router.delete("/evolution/schedules/{schedule_id}")
async def delete_evolution_schedule(schedule_id: str):
    """Delete a scheduled evolution run."""
    if not scheduler:
        return {"success": False, "error": "Scheduler not initialized"}
    
    success = scheduler.delete_schedule(schedule_id)
    
    if not success:
        return {"success": False, "error": f"Failed to delete schedule {schedule_id}"}
    
    return {"success": True, "message": f"Schedule {schedule_id} deleted"}

@router.post("/risk-checks")
async def update_risk_check_config(config: RiskCheckConfig):
    """Update risk management check configuration."""
    if not evo_adapter:
        return {"success": False, "error": "Execution adapter not initialized"}
    
    # Store the new configuration
    global risk_check_config
    risk_check_config = {
        "min_return": config.min_return,
        "max_drawdown": config.max_drawdown,
        "min_sharpe": config.min_sharpe,
        "min_win_rate": config.min_win_rate
    }
    
    return {"success": True, "data": risk_check_config}

# Initialize the adapter
def init_execution_adapter(trade_executor, evo_trader, safety_mgr=None, scheduler_service=None):
    """Initialize the execution adapter with dependencies."""
    global evo_adapter, safety_manager, scheduler
    from trading_bot.core.execution.evo_adapter import EvoToExecAdapter
    
    safety_manager = safety_mgr
    scheduler = scheduler_service
    
    evo_adapter = EvoToExecAdapter(
        trade_executor=trade_executor,
        evo_trader=evo_trader,
        safety_manager=safety_manager
    )
    return evo_adapter 
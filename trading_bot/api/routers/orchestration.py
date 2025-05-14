"""
API routes for the Orchestrator service.

Provides endpoints to manage and monitor the autonomous trading pipeline,
including scheduling evolution, viewing status, activating strategies,
and checking safety measures.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import time # For schedule_time

# Assuming Orchestrator and other services will be injected or globally available
# This is a common pattern in FastAPI app setup
from trading_bot.core.orchestration.orchestrator import Orchestrator
from trading_bot.api.app import get_orchestrator # We'll define this dependency getter in app.py

logger = __import__("logging").getLogger(__name__)

router = APIRouter(
    prefix="/orchestration",
    tags=["Orchestration"],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models for API Requests and Responses ---

class ScheduleEvolutionPayload(BaseModel):
    strategy_type: str = Field(..., example="mean_reversion")
    parameter_space: Dict[str, Any] = Field(..., example={"lookback_period": [10, 50]})
    market_data_id: str = Field(..., example="btc_hourly_2023")
    schedule_time: time = Field(..., example="22:00:00")
    run_daily: bool = Field(True, example=True)
    auto_promote: bool = Field(False, example=True)
    # Optional EvoTrader config overrides
    population_size: Optional[int] = Field(None, example=50)
    generations: Optional[int] = Field(None, example=20)
    mutation_rate: Optional[float] = Field(None, example=0.2)
    crossover_rate: Optional[float] = Field(None, example=0.7)
    elite_size: Optional[int] = Field(None, example=5)

class OrchestrationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StrategiesListResponse(BaseModel):
    success: bool
    strategies: List[Dict[str, Any]]
    error: Optional[str] = None

class SafetyStatusResponse(BaseModel):
    success: bool
    status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
class SystemOverviewResponse(BaseModel):
    evolution_overview: Dict[str, Any]
    scheduled_runs_summary: Dict[str, Any]
    active_strategies_count: int
    safety_status: Dict[str, Any]
    timestamp: str

# --- API Endpoints ---

@router.post("/schedule/evolution", response_model=OrchestrationResponse)
async def schedule_evolution_run_endpoint(
    payload: ScheduleEvolutionPayload,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Schedule a new strategy evolution run via the Orchestrator."""
    logger.info(f"Received request to schedule evolution: {payload.dict()}")
    # The payload needs to be converted to the format expected by EvolutionScheduler.add_schedule
    # which is used by Orchestrator.schedule_evolution_run
    schedule_config = payload.dict()
    # EvolutionScheduler.add_schedule might expect schedule_time as string
    schedule_config['schedule_time'] = payload.schedule_time.isoformat()
    
    result = await orchestrator.schedule_evolution_run(schedule_config)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to schedule evolution"))
    return result

@router.get("/evolution/status", response_model=OrchestrationResponse)
async def get_evolution_status_endpoint(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get the current status of strategy evolution from the Orchestrator."""
    result = await orchestrator.get_evolution_status()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get evolution status"))
    # Re-wrap data for consistent OrchestrationResponse structure if needed
    return {"success": True, "data": result}

@router.get("/strategies/best", response_model=StrategiesListResponse)
async def get_best_strategies_endpoint(
    limit: int = 10,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get the best performing strategies from the Orchestrator."""
    result = await orchestrator.get_best_strategies(limit=limit)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get best strategies"))
    return result

@router.post("/strategies/{strategy_id}/activate", response_model=OrchestrationResponse)
async def activate_strategy_endpoint(
    strategy_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Activate a specific strategy for (mock) trading via the Orchestrator."""
    logger.info(f"Received request to activate strategy: {strategy_id}")
    result = await orchestrator.activate_strategy(strategy_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", f"Failed to activate strategy {strategy_id}"))
    return result

@router.get("/strategies/active", response_model=StrategiesListResponse)
async def get_active_strategies_endpoint(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get the list of currently active (mock) strategies from the Orchestrator."""
    result = await orchestrator.get_active_strategies()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get active strategies"))
    return result

@router.get("/safety/status", response_model=SafetyStatusResponse)
async def get_safety_status_endpoint(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get the current safety status from the Orchestrator."""
    result = await orchestrator.get_safety_status()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get safety status"))
    return result
    
@router.get("/system/overview", response_model=SystemOverviewResponse)
async def get_system_overview_endpoint(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get a combined overview of the system status from the Orchestrator."""
    try:
        overview = await orchestrator.get_system_overview()
        return overview
    except Exception as e:
        logger.error(f"Error fetching system overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system overview: {str(e)}")

# Example of how to provide the orchestrator instance (to be defined in app.py)
# def get_orchestrator_dependency():
#     if not hasattr(router, '_orchestrator_instance'):
#         # This should be initialized in app.py startup
#         raise RuntimeError("Orchestrator not initialized")
#     return router._orchestrator_instance 
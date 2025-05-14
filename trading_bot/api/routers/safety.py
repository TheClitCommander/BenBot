"""
FastAPI router for safety guardrails endpoints.

This module provides API endpoints for managing the trading safety guardrails:
- Circuit breakers
- Cooldown periods
- Emergency stop functionality
- Trading mode control
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from trading_bot.core.safety import (
    SafetyManager, 
    CircuitBreakerManager, 
    CooldownManager, 
    EmergencyStopManager, 
    TradingModeManager
)

# Dependency that provides access to the safety manager
async def get_safety_manager():
    """Dependency that provides the safety manager."""
    # In a real implementation, this would be initialized once and shared
    # For now, we'll create a new instance each time as a placeholder
    # This should be replaced with a proper dependency injection mechanism
    safety_manager = SafetyManager(
        config_dir="./config/safety",
        safety_db_path="./data/safety_events.json"
    )
    return safety_manager

# Pydantic models for requests and responses
class SafetyStatusResponse(BaseModel):
    tradingMode: str
    emergencyStopActive: bool
    circuitBreakers: Dict[str, Any]
    cooldowns: Dict[str, Any]
    tradingAllowed: bool
    tradingBlockedReason: Optional[str] = None

class EmergencyStopRequest(BaseModel):
    active: bool
    reason: Optional[str] = None

class TradingModeRequest(BaseModel):
    mode: str

class CircuitBreakerConfigRequest(BaseModel):
    enabled: bool
    maxDailyLoss: float
    maxDrawdownPercent: float
    maxTradesPerDay: int
    maxConsecutiveLosses: int

class CooldownConfigRequest(BaseModel):
    enabled: bool
    durationSeconds: int
    afterConsecutiveLosses: int
    afterMaxDrawdown: bool

class SimpleResponse(BaseModel):
    success: bool
    message: str

class SafetyEventResponse(BaseModel):
    id: str
    type: str
    action: str
    timestamp: str
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    actor: Optional[str] = None

# Create router
router = APIRouter(
    prefix="/safety",
    tags=["safety"],
    responses={404: {"description": "Not found"}}
)

@router.get("/status", response_model=SafetyStatusResponse)
async def get_safety_status(
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Get the current status of all safety systems."""
    return safety_manager.get_safety_status()

@router.post("/emergency-stop", response_model=SimpleResponse)
async def set_emergency_stop(
    request: EmergencyStopRequest,
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Activate or deactivate the emergency stop."""
    success = safety_manager.set_emergency_stop(
        active=request.active,
        actor="api_user",
        reason=request.reason
    )
    
    action = "activated" if request.active else "deactivated"
    return {
        "success": success,
        "message": f"Emergency stop {action} successfully" if success 
                  else f"Emergency stop already {action}"
    }

@router.post("/trading-mode", response_model=SimpleResponse)
async def set_trading_mode(
    request: TradingModeRequest,
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Set the trading mode (live or paper)."""
    if request.mode not in ["live", "paper"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trading mode: {request.mode}. Must be 'live' or 'paper'."
        )
        
    success = safety_manager.set_trading_mode(
        mode=request.mode,
        actor="api_user"
    )
    
    return {
        "success": success,
        "message": f"Trading mode set to {request.mode} successfully" if success 
                  else f"Trading mode already set to {request.mode}"
    }

@router.get("/circuit-breakers/config", response_model=CircuitBreakerConfigRequest)
async def get_circuit_breaker_config(
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Get the current circuit breaker configuration."""
    return safety_manager.circuit_breaker.config

@router.put("/circuit-breakers/config", response_model=SimpleResponse)
async def update_circuit_breaker_config(
    config: CircuitBreakerConfigRequest,
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Update the circuit breaker configuration."""
    safety_manager.update_circuit_breaker_config(config.dict())
    return {
        "success": True,
        "message": "Circuit breaker configuration updated successfully"
    }

@router.post("/circuit-breakers/reset", response_model=SimpleResponse)
async def reset_circuit_breaker(
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Reset the circuit breaker (manual override)."""
    safety_manager.reset_circuit_breaker(actor="api_user")
    return {
        "success": True,
        "message": "Circuit breaker reset successfully"
    }

@router.get("/cooldowns/config", response_model=CooldownConfigRequest)
async def get_cooldown_config(
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Get the current cooldown configuration."""
    return safety_manager.cooldown.config

@router.put("/cooldowns/config", response_model=SimpleResponse)
async def update_cooldown_config(
    config: CooldownConfigRequest,
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Update the cooldown configuration."""
    safety_manager.update_cooldown_config(config.dict())
    return {
        "success": True,
        "message": "Cooldown configuration updated successfully"
    }

@router.post("/cooldowns/reset", response_model=SimpleResponse)
async def reset_cooldown(
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Reset the cooldown (manual override)."""
    safety_manager.reset_cooldown(actor="api_user")
    return {
        "success": True,
        "message": "Cooldown reset successfully"
    }

@router.get("/events", response_model=List[SafetyEventResponse])
async def get_safety_events(
    limit: int = Query(50, description="Maximum number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    safety_manager: SafetyManager = Depends(get_safety_manager)
):
    """Get safety event history."""
    return safety_manager.get_events(limit=limit, event_type=event_type)

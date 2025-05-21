"""
Safety router for trading API.

Provides endpoints for trading system safety controls and circuit breakers.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

router = APIRouter(
    prefix="/safety",
    tags=["Safety Controls"],
    responses={404: {"description": "Not found"}},
)

# Global safety settings
safety_settings = {
    "circuit_breaker_enabled": True,
    "max_drawdown_percent": 5.0,
    "max_daily_trades": 20,
    "max_position_size_percent": 10.0,
    "emergency_stop_enabled": False
}

@router.get("/status")
async def get_safety_status() -> Dict[str, Any]:
    """Get current safety settings and status."""
    return {
        "settings": safety_settings,
        "status": "active" if safety_settings["circuit_breaker_enabled"] else "disabled"
    }

@router.post("/emergency-stop")
async def trigger_emergency_stop() -> Dict[str, Any]:
    """Trigger emergency stop - halt all trading."""
    safety_settings["emergency_stop_enabled"] = True
    # In a real implementation, this would signal to all components to stop trading
    return {"status": "emergency_stop_activated", "message": "All trading halted"}

@router.post("/resume-trading")
async def resume_trading() -> Dict[str, Any]:
    """Resume trading after emergency stop."""
    if safety_settings["emergency_stop_enabled"]:
        safety_settings["emergency_stop_enabled"] = False
        return {"status": "trading_resumed", "message": "Trading resumed"}
    else:
        return {"status": "already_active", "message": "Trading already active"}

@router.put("/settings")
async def update_safety_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Update safety settings."""
    for key, value in settings.items():
        if key in safety_settings:
            safety_settings[key] = value
    
    return {"status": "settings_updated", "settings": safety_settings}

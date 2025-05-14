"""
FastAPI router for trading metrics endpoints.

This module provides API endpoints for retrieving trading performance metrics:
- Equity curve data
- Current positions
- Trading signals
- Performance summary
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from trading_bot.core.metrics import MetricsService

# Dependency that provides access to the metrics service
async def get_metrics_service():
    """Dependency that provides the metrics service."""
    # In a real implementation, this would be initialized once and shared
    # For now, we'll create a new instance each time as a placeholder
    metrics_service = MetricsService(
        data_dir="./data/metrics"
    )
    
    # Generate mock data if no data exists yet
    if not metrics_service._equity_history:
        metrics_service.generate_mock_data(days=30)
        
    return metrics_service

# Pydantic models for responses
class EquityPoint(BaseModel):
    timestamp: str
    equity: float
    daily_pnl: float
    total_pnl: float

class Position(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: int
    entryPrice: float
    currentPrice: float
    pnl: float
    pnlPercent: float
    openTime: str
    strategy: str

class Signal(BaseModel):
    id: str
    symbol: str
    type: str
    source: str
    confidence: float
    price: float
    timestamp: str
    executed: bool
    reason: Optional[str] = None
    
class PerformanceSummary(BaseModel):
    starting_equity: float
    current_equity: float
    total_pnl: float
    total_pnl_percent: float
    open_positions_count: int
    total_trade_count: int
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate: Optional[float] = None
    avg_daily_change_percent: Optional[float] = None
    max_daily_gain_percent: Optional[float] = None
    max_daily_loss_percent: Optional[float] = None

class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None

# Create router
router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    responses={404: {"description": "Not found"}}
)

@router.get("/equity-curve", response_model=ApiResponse)
async def get_equity_curve(
    timeframe: str = Query("1m", description="Time period (1d, 1w, 1m, 3m, 6m, 1y, all)"),
    start_time: Optional[str] = Query(None, description="Start timestamp (ISO format)"),
    end_time: Optional[str] = Query(None, description="End timestamp (ISO format)"),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get equity curve data for the specified timeframe."""
    try:
        data = metrics_service.get_equity_curve(
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time
        )
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/positions", response_model=ApiResponse)
async def get_positions(
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get all current open positions."""
    try:
        positions = metrics_service.get_positions()
        return {"success": True, "data": positions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/position/{position_id}", response_model=ApiResponse)
async def get_position(
    position_id: str,
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get details of a specific position."""
    try:
        position = metrics_service.get_position(position_id)
        if position is None:
            return {"success": False, "error": f"Position {position_id} not found"}
        return {"success": True, "data": position}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/signals", response_model=ApiResponse)
async def get_signals(
    limit: int = Query(50, description="Maximum number of signals to return"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type (buy, sell)"),
    executed: Optional[bool] = Query(None, description="Filter by execution status"),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get recent trading signals."""
    try:
        signals = metrics_service.get_signals(
            limit=limit,
            signal_type=signal_type,
            executed=executed
        )
        return {"success": True, "data": signals}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/summary", response_model=ApiResponse)
async def get_performance_summary(
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get trading performance summary metrics."""
    try:
        summary = metrics_service.get_performance_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/generate-mock-data", response_model=ApiResponse)
async def generate_mock_data(
    days: int = Query(30, description="Number of days of mock data to generate"),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Generate mock trading data for testing (development only)."""
    try:
        metrics_service.generate_mock_data(days=days)
        return {"success": True, "data": {"message": f"Generated mock data for {days} days"}}
    except Exception as e:
        return {"success": False, "error": str(e)} 
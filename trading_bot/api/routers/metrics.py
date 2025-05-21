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
import logging
import random
from datetime import datetime, timedelta
import sys
import os

from trading_bot.core.metrics import MetricsService
from trading_bot.api.middleware.monitoring import get_metrics, reset_metrics

# Setup logging
logger = logging.getLogger("api.metrics")

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

@router.get("/overview")
async def get_metrics_overview() -> Dict[str, Any]:
    """Get overview metrics for the dashboard."""
    try:
        # In a real implementation, this would fetch actual metrics
        # from a database or trading service
        return {
            "portfolio_value": round(10000 + random.uniform(-500, 500), 2),
            "portfolio_change_percent": round(random.uniform(-3, 5), 2),
            "portfolio_change_value": round(random.uniform(-300, 500), 2),
            "position_count": random.randint(1, 5),
            "position_summary": ["BTC (long)", "ETH (short)"],
            "strategy_count": random.randint(2, 5),
            "strategy_status": "All strategies running normally",
            "todays_pnl": round(random.uniform(-200, 300), 2),
            "pnl_percent": round(random.uniform(-2, 3), 2)
        }
    except Exception as e:
        logger.error(f"Error retrieving metrics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/risk")
async def get_risk_metrics() -> Dict[str, Any]:
    """Get risk metrics for the trading system."""
    try:
        # In a real implementation, this would calculate actual risk metrics
        # based on trading history and positions
        return {
            "sharpe_ratio": round(random.uniform(1.5, 3.0), 2),
            "max_drawdown": round(random.uniform(-15, -5), 2),
            "win_rate": round(random.uniform(55, 75), 2),
            "profit_loss_ratio": round(random.uniform(1.5, 2.5), 2),
            "equity_data": [10000 + i * random.uniform(-50, 100) for i in range(30)],
            "returns_data": [round(random.uniform(-1.5, 2.0), 2) for _ in range(14)]
        }
    except Exception as e:
        logger.error(f"Error retrieving risk metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving risk metrics: {str(e)}")

@router.get("/equity")
async def get_equity_curve(days: int = 30) -> Dict[str, Any]:
    """Get equity curve for a given number of days."""
    try:
        # Generate sample equity curve data
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        dates.reverse()  # Chronological order
        
        base_equity = 10000
        daily_change = []
        equity_values = []
        
        for i in range(days):
            if i == 0:
                change = 0
            else:
                change = random.uniform(-2, 2)
            daily_change.append(round(change, 2))
            
            if i == 0:
                equity = base_equity
            else:
                equity = equity_values[-1] * (1 + daily_change[-1]/100)
            equity_values.append(round(equity, 2))
        
        return {
            "dates": dates,
            "equity": equity_values,
            "daily_change": daily_change
        }
    except Exception as e:
        logger.error(f"Error generating equity curve: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating equity curve: {str(e)}")

@router.get("/performance")
async def get_system_performance() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        return {
            "cpu_usage": random.randint(10, 40),
            "memory_usage": random.randint(20, 60),
            "uptime": f"{random.randint(1, 10)}d {random.randint(1, 23)}h",
            "last_trade_time": f"{random.randint(1, 59)}m ago"
        }
    except Exception as e:
        logger.error(f"Error retrieving system performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving system performance: {str(e)}")

@router.get("/equity-curve", response_model=ApiResponse)
async def get_equity_curve_api(
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

@router.get("/markets")
async def get_market_data() -> Dict[str, Any]:
    """Get current market data for key cryptocurrencies."""
    try:
        markets = [
            {
                "symbol": "BTC",
                "price": round(45000 + random.uniform(-2000, 2000), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": round(random.uniform(20, 40), 1)
            },
            {
                "symbol": "ETH",
                "price": round(2500 + random.uniform(-100, 100), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": round(random.uniform(10, 20), 1)
            },
            {
                "symbol": "SOL",
                "price": round(120 + random.uniform(-10, 10), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": round(random.uniform(5, 10), 1)
            },
            {
                "symbol": "BNB",
                "price": round(600 + random.uniform(-30, 30), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": round(random.uniform(2, 5), 1)
            }
        ]
        
        return {
            "markets": markets,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving market data: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving market data: {str(e)}")

@router.get("/")
async def get_api_metrics():
    """Get API request metrics for monitoring"""
    try:
        current_metrics = get_metrics()
        return current_metrics
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.get("/live-data")
async def get_live_data_metrics():
    """Get metrics focused on the live data endpoints"""
    try:
        all_metrics = get_metrics()
        
        # Extract metrics specific to live data endpoints
        live_endpoints = {}
        for path, metrics in all_metrics.get("endpoint_latency", {}).items():
            if path.startswith("/live"):
                live_endpoints[path] = metrics
        
        # Count errors for live endpoints
        live_errors = [e for e in all_metrics.get("recent_errors", []) 
                       if e.get("path", "").startswith("/live")]
        
        return {
            "live_endpoints": live_endpoints,
            "error_count": len(live_errors),
            "recent_errors": live_errors[:10]  # Only return the 10 most recent errors
        }
    except Exception as e:
        logger.error(f"Error retrieving live data metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve live data metrics")

@router.post("/reset", status_code=204)
async def reset_api_metrics():
    """Reset all API metrics (for testing/debugging)"""
    try:
        reset_metrics()
        logger.info("API metrics have been reset")
        return {"status": "success", "message": "Metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset metrics")

@router.get("/alpaca")
async def get_alpaca_metrics():
    """Get metrics specific to Alpaca API usage"""
    try:
        all_metrics = get_metrics()
        
        # Extract metrics for Alpaca endpoints
        alpaca_endpoints = {}
        for path, metrics in all_metrics.get("endpoint_latency", {}).items():
            if path.startswith("/live/price") or path.startswith("/live/account") or \
               path.startswith("/live/positions") or path.startswith("/live/orders"):
                alpaca_endpoints[path] = metrics
        
        # Count errors for Alpaca endpoints
        alpaca_errors = [e for e in all_metrics.get("recent_errors", []) 
                         if any(e.get("path", "").startswith(p) for p in 
                                ["/live/price", "/live/account", "/live/positions", "/live/orders"])]
        
        # Compute success rate
        total_alpaca_requests = sum(m.get("count", 0) for m in alpaca_endpoints.values())
        success_rate = 0
        if total_alpaca_requests > 0:
            success_rate = (total_alpaca_requests - len(alpaca_errors)) / total_alpaca_requests * 100
            
        return {
            "endpoints": alpaca_endpoints,
            "total_requests": total_alpaca_requests,
            "error_count": len(alpaca_errors),
            "success_rate_pct": round(success_rate, 2),
            "recent_errors": alpaca_errors[:5]  # Only return the 5 most recent errors
        }
    except Exception as e:
        logger.error(f"Error retrieving Alpaca metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Alpaca metrics") 
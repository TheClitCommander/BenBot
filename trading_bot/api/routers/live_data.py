from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel
import sys
import os
import logging
import time
from typing import Optional, Dict, List, Any

# Add project root to Python path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from alpaca_service import get_live_price, get_account, submit_order, get_positions, get_orders, get_order, get_market_status, get_service_health, reset_circuit_breaker

logger = logging.getLogger(__name__)

# Load configuration settings
ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
MAX_ORDER_VALUE_USD = float(os.getenv("MAX_ORDER_VALUE_USD", "1000"))
IS_PAPER_TRADING = "paper" in os.getenv("ALPACA_BASE_URL", "paper").lower()

# Rate limiting tracking
request_timestamps = {}
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_MINUTE = {
    "price": 120,  # Higher limit for price API
    "account": 60,
    "positions": 60,
    "orders": 60,
    "order": 30   # Lower limit for order submission
}

def check_rate_limit(endpoint_type: str, client_ip: str) -> None:
    """Simple rate limiter implementation"""
    now = time.time()
    key = f"{endpoint_type}:{client_ip}"
    
    if key not in request_timestamps:
        request_timestamps[key] = []
    
    # Remove timestamps older than window
    request_timestamps[key] = [ts for ts in request_timestamps[key] if now - ts < RATE_LIMIT_WINDOW]
    
    # Check if limit exceeded
    if len(request_timestamps[key]) >= MAX_REQUESTS_PER_MINUTE.get(endpoint_type, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {endpoint_type}. Please try again later."
        )
    
    # Add current timestamp
    request_timestamps[key].append(now)

router = APIRouter(prefix="/live", tags=["live"])

@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint that verifies Alpaca API connectivity"""
    client_ip = request.client.host
    check_rate_limit("health", client_ip)
    
    try:
        market_status = get_market_status()
        if "error" in market_status:
            return {
                "status": "degraded",
                "message": f"Connected but market status check failed: {market_status['error']}"
            }
            
        return {
            "status": "ok", 
            "message": "Alpaca API connection successful",
            "market_status": market_status
        }
    except Exception as e:
        logger.error(f"Alpaca API health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alpaca API connection failed"
        )

@router.get("/service-health")
async def service_health(request: Request):
    """Get detailed health metrics for the Alpaca service integration"""
    client_ip = request.client.host
    check_rate_limit("health", client_ip)
    
    try:
        health_info = get_service_health()
        return health_info
    except Exception as e:
        logger.error(f"Error retrieving Alpaca service health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service health information"
        )

@router.post("/reset-circuit-breaker")
async def reset_circuit(request: Request):
    """Reset the circuit breaker if it's in OPEN state due to API issues"""
    # Only allow admins in production
    if not IS_PAPER_TRADING and os.getenv("ENVIRONMENT", "").lower() == "production":
        # Simplified auth check - in real production, use proper authentication
        admin_token = request.headers.get("X-Admin-Token")
        if not admin_token or admin_token != os.getenv("ADMIN_API_TOKEN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access required"
            )
    
    try:
        # Get current health before reset
        pre_health = get_service_health()
        
        # Reset the circuit breaker
        reset_circuit_breaker()
        
        # Log for audit trail
        logger.warning(f"Circuit breaker manually reset by request from {request.client.host}")
        
        return {
            "success": True,
            "message": "Circuit breaker reset successful",
            "previous_state": pre_health["circuit_state"],
            "current_state": "CLOSED"
        }
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )

@router.get("/environment")
async def environment():
    """Returns information about the trading environment (paper/live)"""
    return {
        "mode": "paper" if IS_PAPER_TRADING else "live",
        "live_trading_enabled": ENABLE_LIVE_TRADING,
        "max_order_value": MAX_ORDER_VALUE_USD
    }

@router.get("/price/{symbol}")
async def live_price(symbol: str, request: Request):
    """Get the latest price for a symbol with caching and rate limiting"""
    client_ip = request.client.host
    check_rate_limit("price", client_ip)
    
    try:
        symbol = symbol.upper()
        price = get_live_price(symbol)
        return {"symbol": symbol, "price": price}
    except ValueError as e:
        logger.warning(f"No data found for symbol {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Market data service unavailable: {str(e)}"
        )

@router.get("/account")
async def account_info(request: Request):
    """Get account details from Alpaca"""
    client_ip = request.client.host
    check_rate_limit("account", client_ip)
    
    try:
        account = get_account()
        # Log for monitoring/debugging
        logger.info(f"Account equity: ${account.get('equity', 'N/A')}, Cash: ${account.get('cash', 'N/A')}")
        return account
    except Exception as e:
        logger.error(f"Error fetching account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Account service unavailable"
        )

@router.get("/positions")
async def positions(request: Request):
    """Get current positions from Alpaca"""
    client_ip = request.client.host
    check_rate_limit("positions", client_ip)
    
    try:
        positions_data = get_positions()
        # Log position count for monitoring
        logger.info(f"Retrieved {len(positions_data)} positions")
        return positions_data
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Position service unavailable"
        )

@router.get("/orders")
async def orders(request: Request):
    """Get open orders from Alpaca"""
    client_ip = request.client.host
    check_rate_limit("orders", client_ip)
    
    try:
        orders_data = get_orders()
        return orders_data
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order service unavailable"
        )

@router.get("/orders/{order_id}")
async def get_order_by_id(order_id: str, request: Request):
    """Get a specific order by ID"""
    client_ip = request.client.host
    check_rate_limit("orders", client_ip)
    
    try:
        return get_order(order_id)
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order service unavailable"
        )

class OrderRequest(BaseModel):
    symbol: str
    side: str  # buy or sell
    qty: float
    type: str = "market"  # market, limit, stop, stop_limit
    limit_price: Optional[float] = None

@router.post("/order")
async def order(req: OrderRequest, request: Request):
    """Submit a new order with safety checks"""
    client_ip = request.client.host
    check_rate_limit("order", client_ip)
    
    # Safety check for live trading
    is_live_mode = not IS_PAPER_TRADING
    if is_live_mode and not ENABLE_LIVE_TRADING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live trading is disabled for safety. Set ENABLE_LIVE_TRADING=true to enable."
        )
    
    try:
        # Get current price to estimate order value
        symbol = req.symbol.upper()
        price = get_live_price(symbol)
        estimated_value = price * req.qty
        
        # Check against maximum order value
        if estimated_value > MAX_ORDER_VALUE_USD:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Order value (${estimated_value:.2f}) exceeds maximum allowed (${MAX_ORDER_VALUE_USD:.2f})"
            )
        
        # Log the order for audit/monitoring
        logger.info(f"ORDER: {req.side} {req.qty} {symbol} at {price:.2f} (est. value: ${estimated_value:.2f})")
        
        # Submit the order
        order_result = submit_order(
            symbol, 
            req.side, 
            req.qty, 
            req.type, 
            req.limit_price
        )
        
        # Log successful submission
        logger.info(f"Order {order_result.get('id', 'UNKNOWN')} submitted successfully")
        
        return order_result
    
    except HTTPException:
        raise
    except ValueError as e:
        # For market data errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Order execution failed: {str(e)}"
        ) 
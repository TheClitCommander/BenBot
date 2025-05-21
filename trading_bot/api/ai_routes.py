"""
AI Analysis API routes for the trading bot system.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import logging

from trading_bot.strategy.strategy_rotator import StrategyRotator
from ai_modules.MarketContextAnalyzer import MarketContextAnalyzer

# Setup logging
logger = logging.getLogger("api.ai_routes")

# Create FastAPI router
router = APIRouter(prefix="/ai", tags=["AI Analysis"])

# Dependency for StrategyRotator
def get_strategy_rotator() -> StrategyRotator:
    """Dependency to get strategy rotator instance."""
    # In a real implementation, this would be retrieved from a
    # global application state or DB
    from trading_bot import initialize_system
    system = initialize_system()
    return system["strategy_rotator"]

# Dependency for MarketContextAnalyzer
def get_market_analyzer() -> MarketContextAnalyzer:
    """Dependency to get MarketContextAnalyzer instance."""
    return MarketContextAnalyzer()

@router.get("/market-analysis", summary="Get AI market analysis")
async def get_market_analysis(
    symbols: Optional[str] = "SPY,QQQ,AAPL,MSFT,NVDA", 
    analyzer: MarketContextAnalyzer = Depends(get_market_analyzer)
) -> Dict[str, Any]:
    """
    Get AI-generated market analysis for the specified symbols.
    
    Args:
        symbols: Comma-separated list of symbols to analyze
        
    Returns:
        Market context analysis from AI
    """
    try:
        symbol_list = symbols.split(',')
        analysis = analyzer.generate_market_context(symbol_list)
        return analysis
    except Exception as e:
        logger.error(f"Error generating market analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating market analysis: {str(e)}")

@router.get("/sentiment", summary="Get market sentiment score")
async def get_sentiment(
    symbols: Optional[str] = "SPY,QQQ,AAPL,MSFT,NVDA", 
    analyzer: MarketContextAnalyzer = Depends(get_market_analyzer)
) -> Dict[str, Any]:
    """
    Get simplified market sentiment score for the specified symbols.
    
    Args:
        symbols: Comma-separated list of symbols to analyze
        
    Returns:
        Sentiment score between -1.0 (bearish) and 1.0 (bullish)
    """
    try:
        symbol_list = symbols.split(',')
        sentiment = analyzer.get_sentiment_score(symbol_list)
        return {
            "sentiment_score": sentiment,
            "symbols": symbol_list,
            "normalized": True  # Score is between -1.0 and 1.0
        }
    except Exception as e:
        logger.error(f"Error getting sentiment score: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sentiment score: {str(e)}")

@router.get("/strategies", summary="Get all AI-driven strategies")
async def get_strategies(
    rotator: StrategyRotator = Depends(get_strategy_rotator)
) -> Dict[str, Any]:
    """
    Get all available strategies in the rotator with their status.
    
    Returns:
        Dictionary of strategies with status information
    """
    strategies = {}
    for strategy_id, strategy in rotator.strategies.items():
        strategies[strategy_id] = strategy.get_status()
    
    return {
        "strategies": strategies,
        "active_strategy": rotator.active_strategy_id,
        "count": len(strategies)
    }

@router.get("/active-strategy", summary="Get the currently active AI strategy")
async def get_active_strategy(
    rotator: StrategyRotator = Depends(get_strategy_rotator)
) -> Dict[str, Any]:
    """
    Get information about the currently active AI strategy.
    
    Returns:
        Active strategy information or error if no active strategy
    """
    active = rotator.get_active_strategy()
    if not active:
        raise HTTPException(status_code=404, detail="No active strategy found")
    
    return active.get_status()

@router.post("/set-active/{strategy_id}", summary="Set the active AI strategy")
async def set_active_strategy(
    strategy_id: str,
    rotator: StrategyRotator = Depends(get_strategy_rotator)
) -> Dict[str, Any]:
    """
    Set the active AI strategy by ID.
    
    Args:
        strategy_id: ID of the strategy to activate
        
    Returns:
        Result of the operation
    """
    success = rotator.set_active_strategy(strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    return {"status": "success", "active_strategy": strategy_id}

@router.get("/rotation-history", summary="Get strategy rotation history")
async def get_rotation_history(
    limit: int = 10,
    rotator: StrategyRotator = Depends(get_strategy_rotator)
) -> Dict[str, Any]:
    """
    Get recent strategy rotation history.
    
    Args:
        limit: Maximum number of history items to return
        
    Returns:
        Recent rotation history
    """
    history = rotator.get_rotation_history(limit)
    return {
        "history": history,
        "count": len(history)
    }

@router.post("/auto-rotate", summary="Trigger automatic strategy rotation")
async def trigger_auto_rotation(
    rotator: StrategyRotator = Depends(get_strategy_rotator),
    analyzer: MarketContextAnalyzer = Depends(get_market_analyzer)
) -> Dict[str, Any]:
    """
    Trigger automatic strategy rotation based on current market data.
    
    Returns:
        Result of the rotation operation
    """
    try:
        # Get market data for common symbols
        symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
        market_data = analyzer.fetch_market_data(symbols)
        
        # Attempt rotation
        rotation_occurred = rotator.auto_rotate(market_data)
        
        return {
            "rotation_occurred": rotation_occurred,
            "active_strategy": rotator.active_strategy_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error during auto-rotation: {e}")
        raise HTTPException(status_code=500, detail=f"Error during auto-rotation: {str(e)}")

@router.get("/signals", summary="Get trading signals from active AI strategy")
async def get_signals(
    rotator: StrategyRotator = Depends(get_strategy_rotator),
    analyzer: MarketContextAnalyzer = Depends(get_market_analyzer)
) -> Dict[str, Any]:
    """
    Get trading signals from the currently active AI strategy.
    
    Returns:
        Trading signals from active strategy
    """
    try:
        # Get market data for common symbols
        symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
        market_data = analyzer.fetch_market_data(symbols)
        
        # Get signals from active strategy
        signals = rotator.get_active_signals(market_data)
        
        return signals
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting signals: {str(e)}") 
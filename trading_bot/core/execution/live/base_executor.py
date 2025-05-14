"""
Base Executor for Live Trading.

This module defines the abstract base class that all live execution
adapters must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseExecutor(ABC):
    """
    Abstract base class for all live execution adapters.
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        paper_trading: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the executor.
        
        Args:
            api_key: API key for the broker
            api_secret: API secret for the broker
            paper_trading: Whether to use paper trading
            config: Additional configuration parameters
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_trading = paper_trading
        self.config = config or {}
        self.connected = False
        self.last_error = None
        
        # Order tracking
        self.open_orders: Dict[str, Dict[str, Any]] = {}
        self.filled_orders: Dict[str, Dict[str, Any]] = {}
        
        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker API.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def place_market_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        strategy_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Symbol to trade
            quantity: Quantity to trade
            side: 'buy' or 'sell'
            strategy_id: ID of the strategy placing the order
            metadata: Additional order metadata
            
        Returns:
            Dictionary with order information
        """
        pass
    
    @abstractmethod
    def place_limit_order(
        self,
        symbol: str,
        quantity: float,
        price: float,
        side: str,
        strategy_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Symbol to trade
            quantity: Quantity to trade
            price: Limit price
            side: 'buy' or 'sell'
            strategy_id: ID of the strategy placing the order
            metadata: Additional order metadata
            
        Returns:
            Dictionary with order information
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Dictionary with order status information
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            Dictionary mapping symbols to position information
        """
        pass
    
    @abstractmethod
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary information.
        
        Returns:
            Dictionary with account information
        """
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> Dict[str, Any]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            timeframe: Timeframe for the data
            limit: Number of data points to fetch
            
        Returns:
            Dictionary with market data
        """
        pass
    
    def deploy_strategy(self, strategy_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a strategy to live trading.
        
        Args:
            strategy_dict: Dictionary with strategy information
            
        Returns:
            Dictionary with deployment status
        """
        strategy_id = strategy_dict.get("strategy_id", "unknown")
        logger.info(f"Deploying strategy {strategy_id} to live trading")
        
        # Ensure connection
        if not self.connected:
            success = self.connect()
            if not success:
                return {
                    "status": "error",
                    "message": f"Failed to connect to broker: {self.last_error}",
                    "strategy_id": strategy_id
                }
        
        # Default implementation - should be overridden by specific brokers
        # if they need special handling
        return {
            "status": "success",
            "message": "Strategy deployed successfully",
            "strategy_id": strategy_id,
            "deployment_time": datetime.now().isoformat(),
            "broker": self.__class__.__name__,
            "paper_trading": self.paper_trading
        }
    
    def handle_signal(
        self,
        strategy_id: str,
        symbol: str,
        signal: int,
        quantity: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a trading signal from a strategy.
        
        Args:
            strategy_id: ID of the strategy generating the signal
            symbol: Symbol to trade
            signal: Signal value (1 for buy, -1 for sell, 0 for no action)
            quantity: Quantity to trade
            metadata: Additional signal metadata
            
        Returns:
            Dictionary with execution result
        """
        if signal == 0:
            logger.info(f"No action signal received for {symbol} from strategy {strategy_id}")
            return {"status": "skipped", "message": "No action signal"}
        
        side = "buy" if signal > 0 else "sell"
        
        logger.info(f"Executing {side} signal for {symbol} from strategy {strategy_id}")
        
        # Execute the signal
        try:
            order_result = self.place_market_order(
                symbol=symbol,
                quantity=quantity,
                side=side,
                strategy_id=strategy_id,
                metadata=metadata
            )
            
            return {
                "status": "success",
                "message": f"{side.title()} order placed successfully",
                "order": order_result,
                "signal": signal,
                "strategy_id": strategy_id,
                "symbol": symbol,
                "quantity": quantity,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing {side} signal for {symbol}: {e}")
            self.last_error = str(e)
            return {
                "status": "error",
                "message": f"Failed to execute {side} signal: {e}",
                "signal": signal,
                "strategy_id": strategy_id,
                "symbol": symbol,
                "quantity": quantity,
                "timestamp": datetime.now().isoformat()
            } 
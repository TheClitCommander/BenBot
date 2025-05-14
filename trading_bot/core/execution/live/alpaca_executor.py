"""
Alpaca Executor for Live Equity Trading.

This module implements the Alpaca API for live equity trading.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from trading_bot.core.execution.live.base_executor import BaseExecutor

logger = logging.getLogger(__name__)

class AlpacaExecutor(BaseExecutor):
    """
    Executor for trading equities via Alpaca.
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        paper_trading: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Alpaca executor.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper_trading: Whether to use paper trading
            config: Additional configuration parameters
        """
        super().__init__(api_key, api_secret, paper_trading, config)
        self.api = None
        self.alpaca_base_url = "https://paper-api.alpaca.markets" if paper_trading else "https://api.alpaca.markets"
    
    def connect(self) -> bool:
        """
        Connect to the Alpaca API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Import Alpaca SDK here to avoid dependency issues
            from alpaca_trade_api import REST, TimeFrame
            
            # Store for later use
            self.TimeFrame = TimeFrame
            
            # Check if api_key and api_secret are provided
            if not self.api_key or not self.api_secret:
                logger.error("API key and secret must be provided for Alpaca")
                self.last_error = "API key and secret must be provided"
                return False
            
            # Initialize the API
            self.api = REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=self.alpaca_base_url
            )
            
            # Test connection by getting account
            account = self.api.get_account()
            logger.info(f"Connected to Alpaca for account {account.id}")
            
            # Update positions
            self._update_positions()
            
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to Alpaca: {e}")
            self.last_error = str(e)
            self.connected = False
            return False
    
    def place_market_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        strategy_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Place a market order via Alpaca.
        
        Args:
            symbol: Symbol to trade
            quantity: Quantity to trade
            side: 'buy' or 'sell'
            strategy_id: ID of the strategy placing the order
            metadata: Additional order metadata
            
        Returns:
            Dictionary with order information
        """
        if not self.connected:
            success = self.connect()
            if not success:
                raise ConnectionError(f"Failed to connect to Alpaca: {self.last_error}")
        
        try:
            # Create order
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day',
                client_order_id=f"{strategy_id}_{int(time.time())}"
            )
            
            # Convert order to dict
            order_dict = {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "filled_quantity": float(order.filled_qty) if hasattr(order, "filled_qty") else 0.0,
                "type": order.type,
                "status": order.status,
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else datetime.now().isoformat(),
                "strategy_id": strategy_id
            }
            
            # Store in open orders
            self.open_orders[order.id] = order_dict
            
            return order_dict
        except Exception as e:
            logger.error(f"Error placing market order on Alpaca: {e}")
            raise
    
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
        Place a limit order via Alpaca.
        
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
        if not self.connected:
            success = self.connect()
            if not success:
                raise ConnectionError(f"Failed to connect to Alpaca: {self.last_error}")
        
        try:
            # Create order
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type='limit',
                time_in_force='day',
                limit_price=price,
                client_order_id=f"{strategy_id}_{int(time.time())}"
            )
            
            # Convert order to dict
            order_dict = {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "price": float(order.limit_price) if hasattr(order, "limit_price") else price,
                "filled_quantity": float(order.filled_qty) if hasattr(order, "filled_qty") else 0.0,
                "type": order.type,
                "status": order.status,
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else datetime.now().isoformat(),
                "strategy_id": strategy_id
            }
            
            # Store in open orders
            self.open_orders[order.id] = order_dict
            
            return order_dict
        except Exception as e:
            logger.error(f"Error placing limit order on Alpaca: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return False
        
        try:
            self.api.cancel_order(order_id)
            
            # Remove from open orders if present
            if order_id in self.open_orders:
                del self.open_orders[order_id]
            
            return True
        except Exception as e:
            logger.error(f"Error cancelling order on Alpaca: {e}")
            self.last_error = str(e)
            return False
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Dictionary with order status information
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return {"status": "error", "message": f"Failed to connect to Alpaca: {self.last_error}"}
        
        try:
            # Get order from Alpaca
            order = self.api.get_order(order_id)
            
            # Convert to dict
            order_dict = {
                "id": order.id,
                "client_order_id": order.client_order_id if hasattr(order, "client_order_id") else "",
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "filled_quantity": float(order.filled_qty) if hasattr(order, "filled_qty") else 0.0,
                "type": order.type,
                "status": order.status,
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else "",
                "filled_at": order.filled_at.isoformat() if hasattr(order, "filled_at") and order.filled_at else None,
                "filled_avg_price": float(order.filled_avg_price) if hasattr(order, "filled_avg_price") and order.filled_avg_price else None
            }
            
            # Update order in our tracking
            if order.status == 'filled':
                if order.id in self.open_orders:
                    self.filled_orders[order.id] = self.open_orders[order.id]
                    self.filled_orders[order.id].update(order_dict)
                    del self.open_orders[order.id]
                else:
                    self.filled_orders[order.id] = order_dict
            else:
                self.open_orders[order.id] = order_dict
            
            return order_dict
        except Exception as e:
            logger.error(f"Error getting order status from Alpaca: {e}")
            self.last_error = str(e)
            return {"status": "error", "message": str(e)}
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            Dictionary mapping symbols to position information
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return {}
        
        # Update positions
        self._update_positions()
        
        return self.positions
    
    def _update_positions(self) -> None:
        """Update the positions dictionary with current positions."""
        try:
            positions = self.api.list_positions()
            
            # Clear current positions
            self.positions = {}
            
            # Update with new positions
            for position in positions:
                self.positions[position.symbol] = {
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "current_price": float(position.current_price),
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error updating positions from Alpaca: {e}")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary information.
        
        Returns:
            Dictionary with account information
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return {"status": "error", "message": f"Failed to connect to Alpaca: {self.last_error}"}
        
        try:
            account = self.api.get_account()
            
            return {
                "status": "success",
                "account_id": account.id,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "initial_margin": float(account.initial_margin) if hasattr(account, "initial_margin") else 0.0,
                "maintenance_margin": float(account.maintenance_margin) if hasattr(account, "maintenance_margin") else 0.0,
                "day_trade_count": int(account.daytrade_count) if hasattr(account, "daytrade_count") else 0,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting account summary from Alpaca: {e}")
            self.last_error = str(e)
            return {"status": "error", "message": str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str = "1D", limit: int = 100) -> Dict[str, Any]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            timeframe: Timeframe for the data (e.g., '1D', '1H', '15Min')
            limit: Number of data points to fetch
            
        Returns:
            Dictionary with market data
        """
        if not self.connected:
            success = self.connect()
            if not success:
                return {"status": "error", "message": f"Failed to connect to Alpaca: {self.last_error}"}
        
        try:
            # Map timeframe string to Alpaca TimeFrame enum
            tf_map = {
                "1m": self.TimeFrame.Minute,
                "1min": self.TimeFrame.Minute,
                "5m": self.TimeFrame.Minute(5),
                "5min": self.TimeFrame.Minute(5),
                "15m": self.TimeFrame.Minute(15),
                "15min": self.TimeFrame.Minute(15),
                "1h": self.TimeFrame.Hour,
                "1hour": self.TimeFrame.Hour,
                "1d": self.TimeFrame.Day,
                "1day": self.TimeFrame.Day,
                "1D": self.TimeFrame.Day
            }
            
            tf = tf_map.get(timeframe, self.TimeFrame.Day)
            
            # Calculate start time based on limit and timeframe
            end = datetime.now()
            
            # Get bars
            bars = self.api.get_bars(
                symbol,
                tf,
                limit=limit,
                end=end.isoformat()
            ).df
            
            # Convert to dict
            if not bars.empty:
                data = {
                    "status": "success",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": {
                        "timestamp": bars.index.tolist(),
                        "open": bars['open'].tolist(),
                        "high": bars['high'].tolist(),
                        "low": bars['low'].tolist(),
                        "close": bars['close'].tolist(),
                        "volume": bars['volume'].tolist()
                    }
                }
                return data
            else:
                return {"status": "error", "message": f"No data found for {symbol}"}
        except Exception as e:
            logger.error(f"Error getting market data from Alpaca: {e}")
            self.last_error = str(e)
            return {"status": "error", "message": str(e)} 
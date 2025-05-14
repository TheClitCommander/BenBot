"""
Metrics service for tracking and retrieving trading performance data.

This service provides methods for:
- Tracking equity and PnL
- Managing position data
- Recording trading signals
- Retrieving historical performance data
"""

import time
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

class MetricsService:
    """
    Service for tracking and retrieving trading metrics.
    
    This service manages:
    - Equity curve data
    - Current positions
    - Trading signals
    - Performance statistics
    """
    
    def __init__(
        self,
        data_dir: str = "./data/metrics",
        backup_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize the metrics service.
        
        Args:
            data_dir: Directory where metrics data files will be stored
            backup_interval: How often to save data to disk (in seconds)
        """
        self.data_dir = data_dir
        self.backup_interval = backup_interval
        self.last_backup_time = time.time()
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize data structures
        self._equity_history: List[Dict[str, Any]] = []
        self._positions: List[Dict[str, Any]] = []
        self._signals: List[Dict[str, Any]] = []
        self._trades: List[Dict[str, Any]] = []
        
        # Starting equity (default to 10000 if not set)
        self._starting_equity = 10000.0
        self._current_equity = self._starting_equity
        
        # Load data from disk if available
        self._load_data()
    
    def _load_data(self) -> None:
        """Load metrics data from disk."""
        try:
            # Load equity curve
            equity_file = os.path.join(self.data_dir, "equity_history.json")
            if os.path.exists(equity_file):
                with open(equity_file, "r") as f:
                    self._equity_history = json.load(f)
                if self._equity_history:
                    # Set starting equity from the first point
                    self._starting_equity = self._equity_history[0].get("equity", 10000.0)
                    # Set current equity from the latest point
                    self._current_equity = self._equity_history[-1].get("equity", self._starting_equity)
            
            # Load positions
            positions_file = os.path.join(self.data_dir, "positions.json")
            if os.path.exists(positions_file):
                with open(positions_file, "r") as f:
                    self._positions = json.load(f)
            
            # Load signals
            signals_file = os.path.join(self.data_dir, "signals.json")
            if os.path.exists(signals_file):
                with open(signals_file, "r") as f:
                    self._signals = json.load(f)
            
            # Load trades
            trades_file = os.path.join(self.data_dir, "trades.json")
            if os.path.exists(trades_file):
                with open(trades_file, "r") as f:
                    self._trades = json.load(f)
                    
            logger.info(f"Loaded metrics data: {len(self._equity_history)} equity points, "
                      f"{len(self._positions)} positions, {len(self._signals)} signals, "
                      f"{len(self._trades)} trades")
        except Exception as e:
            logger.error(f"Error loading metrics data: {e}")
    
    def _backup_data(self) -> None:
        """Save metrics data to disk."""
        try:
            # Save equity curve
            with open(os.path.join(self.data_dir, "equity_history.json"), "w") as f:
                json.dump(self._equity_history, f)
            
            # Save positions
            with open(os.path.join(self.data_dir, "positions.json"), "w") as f:
                json.dump(self._positions, f)
            
            # Save signals
            with open(os.path.join(self.data_dir, "signals.json"), "w") as f:
                json.dump(self._signals, f)
            
            # Save trades
            with open(os.path.join(self.data_dir, "trades.json"), "w") as f:
                json.dump(self._trades, f)
            
            self.last_backup_time = time.time()
            logger.debug("Backed up metrics data to disk")
        except Exception as e:
            logger.error(f"Error backing up metrics data: {e}")
    
    def _check_backup(self) -> None:
        """Check if it's time to backup data to disk."""
        if time.time() - self.last_backup_time > self.backup_interval:
            self._backup_data()
    
    def update_equity(self, equity: float, timestamp: Optional[str] = None) -> None:
        """
        Update the current equity value and add a point to the equity curve.
        
        Args:
            equity: Current portfolio equity value
            timestamp: ISO format timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        # Calculate daily PnL if we have previous points
        daily_pnl = 0.0
        if self._equity_history:
            # Find the latest point from the previous day
            today = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
            for point in reversed(self._equity_history):
                point_date = datetime.fromisoformat(
                    point['timestamp'].replace('Z', '+00:00')).date()
                if point_date < today:
                    daily_pnl = equity - point['equity']
                    break
        
        # Calculate total PnL from starting equity
        total_pnl = equity - self._starting_equity
        
        # Add new equity point
        self._equity_history.append({
            "timestamp": timestamp,
            "equity": equity,
            "daily_pnl": daily_pnl,
            "total_pnl": total_pnl
        })
        
        # Update current equity
        self._current_equity = equity
        
        # Check if we need to backup
        self._check_backup()
    
    def add_position(self, position: Dict[str, Any]) -> None:
        """
        Add or update a position.
        
        Args:
            position: Position data dict with at least id, symbol, side, quantity,
                     entryPrice, currentPrice, and pnl fields
        """
        # Check if position already exists (by ID)
        for i, existing in enumerate(self._positions):
            if existing.get("id") == position.get("id"):
                # Update existing position
                self._positions[i] = position
                logger.debug(f"Updated position {position.get('id')}")
                self._check_backup()
                return
        
        # Add timestamp if not provided
        if "timestamp" not in position:
            position["timestamp"] = datetime.utcnow().isoformat()
        
        # Add new position
        self._positions.append(position)
        logger.debug(f"Added position {position.get('id')}")
        
        # Check if we need to backup
        self._check_backup()
    
    def remove_position(self, position_id: str) -> bool:
        """
        Remove a position by ID.
        
        Args:
            position_id: Unique position identifier
            
        Returns:
            bool: True if position was found and removed, False otherwise
        """
        for i, position in enumerate(self._positions):
            if position.get("id") == position_id:
                del self._positions[i]
                logger.debug(f"Removed position {position_id}")
                self._check_backup()
                return True
        
        return False
    
    def add_signal(self, signal: Dict[str, Any]) -> None:
        """
        Add a new trading signal.
        
        Args:
            signal: Signal data dict with at least type, symbol, and confidence fields
        """
        # Add timestamp if not provided
        if "timestamp" not in signal:
            signal["timestamp"] = datetime.utcnow().isoformat()
        
        # Add unique ID if not provided
        if "id" not in signal:
            signal["id"] = f"sig_{int(time.time())}_{len(self._signals)}"
        
        # Add new signal at the beginning of the list
        self._signals.insert(0, signal)
        
        # Trim signals list if it's getting too long
        if len(self._signals) > 1000:  # Keep last 1000 signals
            self._signals = self._signals[:1000]
        
        logger.debug(f"Added signal {signal.get('id')}")
        
        # Check if we need to backup
        self._check_backup()
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """
        Record a completed trade.
        
        Args:
            trade: Trade data dict with details of the executed trade
        """
        # Add timestamp if not provided
        if "timestamp" not in trade:
            trade["timestamp"] = datetime.utcnow().isoformat()
        
        # Add unique ID if not provided
        if "id" not in trade:
            trade["id"] = f"trade_{int(time.time())}_{len(self._trades)}"
        
        # Add new trade
        self._trades.append(trade)
        logger.debug(f"Added trade {trade.get('id')}")
        
        # Check if we need to backup
        self._check_backup()
    
    def get_equity_curve(
        self, 
        timeframe: str = "1m",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get equity curve data.
        
        Args:
            timeframe: Time period ('1d', '1w', '1m', '3m', '6m', '1y', 'all')
            start_time: Optional ISO format start timestamp
            end_time: Optional ISO format end timestamp
            
        Returns:
            List of equity data points
        """
        # If specific time range is provided, use that
        if start_time and end_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            # Calculate time range based on timeframe
            end_dt = datetime.utcnow()
            if timeframe == "1d":
                start_dt = end_dt - timedelta(days=1)
            elif timeframe == "1w":
                start_dt = end_dt - timedelta(weeks=1)
            elif timeframe == "1m":
                start_dt = end_dt - timedelta(days=30)
            elif timeframe == "3m":
                start_dt = end_dt - timedelta(days=90)
            elif timeframe == "6m":
                start_dt = end_dt - timedelta(days=180)
            elif timeframe == "1y":
                start_dt = end_dt - timedelta(days=365)
            else:  # "all" or any other value
                return self._equity_history
        
        # Filter points in the selected time range
        filtered_points = []
        for point in self._equity_history:
            point_dt = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
            if start_dt <= point_dt <= end_dt:
                filtered_points.append(point)
        
        return filtered_points
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all current positions.
        
        Returns:
            List of position objects
        """
        return self._positions
    
    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific position by ID.
        
        Args:
            position_id: Unique position identifier
            
        Returns:
            Position object or None if not found
        """
        for position in self._positions:
            if position.get("id") == position_id:
                return position
        return None
    
    def get_signals(
        self, 
        limit: int = 50, 
        signal_type: Optional[str] = None,
        executed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent trading signals.
        
        Args:
            limit: Maximum number of signals to return
            signal_type: Optional filter by signal type (e.g., 'buy', 'sell')
            executed: Optional filter by execution status
            
        Returns:
            List of signal objects
        """
        # Start with all signals
        filtered_signals = self._signals
        
        # Apply type filter if specified
        if signal_type:
            filtered_signals = [s for s in filtered_signals if s.get("type") == signal_type]
        
        # Apply execution status filter if specified
        if executed is not None:
            filtered_signals = [s for s in filtered_signals if s.get("executed") == executed]
        
        # Return limited results
        return filtered_signals[:limit]
    
    def get_trades(
        self, 
        limit: int = 50,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Args:
            limit: Maximum number of trades to return
            symbol: Optional filter by symbol
            
        Returns:
            List of trade objects
        """
        # Start with all trades
        filtered_trades = self._trades
        
        # Apply symbol filter if specified
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get("symbol") == symbol]
        
        # Return most recent trades
        return list(reversed(filtered_trades))[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary metrics.
        
        Returns:
            Dict with performance metrics
        """
        # Initialize metrics
        metrics = {
            "starting_equity": self._starting_equity,
            "current_equity": self._current_equity,
            "total_pnl": self._current_equity - self._starting_equity,
            "total_pnl_percent": ((self._current_equity / self._starting_equity) - 1) * 100,
            "open_positions_count": len(self._positions),
            "total_trade_count": len(self._trades),
        }
        
        # Calculate win rate if we have trades
        if self._trades:
            winning_trades = [t for t in self._trades if t.get("pnl", 0) > 0]
            metrics["winning_trades"] = len(winning_trades)
            metrics["losing_trades"] = len(self._trades) - len(winning_trades)
            metrics["win_rate"] = (len(winning_trades) / len(self._trades)) * 100
        
        # Calculate daily metrics if we have equity history
        if len(self._equity_history) > 1:
            # Get daily changes
            daily_changes = []
            
            # Organize points by date
            points_by_date = {}
            for point in self._equity_history:
                date_str = datetime.fromisoformat(
                    point['timestamp'].replace('Z', '+00:00')).date().isoformat()
                points_by_date[date_str] = point
            
            # Sort dates and calculate daily changes
            dates = sorted(points_by_date.keys())
            prev_equity = None
            for date in dates:
                equity = points_by_date[date]['equity']
                if prev_equity is not None:
                    daily_change = (equity / prev_equity - 1) * 100
                    daily_changes.append(daily_change)
                prev_equity = equity
            
            if daily_changes:
                metrics["avg_daily_change_percent"] = sum(daily_changes) / len(daily_changes)
                metrics["max_daily_gain_percent"] = max(daily_changes)
                metrics["max_daily_loss_percent"] = min(daily_changes)
        
        return metrics
    
    def generate_mock_data(self, days: int = 30) -> None:
        """
        Generate mock trading data for testing.
        
        Args:
            days: Number of days of data to generate
        """
        import random
        
        # Clear existing data
        self._equity_history = []
        self._positions = []
        self._signals = []
        self._trades = []
        
        # Set starting equity
        starting_equity = 10000.0
        self._starting_equity = starting_equity
        equity = starting_equity
        
        # Generate daily equity points
        for i in range(days):
            # Generate timestamp for each day
            timestamp = (datetime.utcnow() - timedelta(days=days-i)).isoformat()
            
            # Create random daily change (-2.5% to +3.5%)
            daily_change = (random.random() * 6) - 2.5  # -2.5% to +3.5%
            daily_pnl = equity * (daily_change / 100)
            equity += daily_pnl
            
            # Add equity point
            self._equity_history.append({
                "timestamp": timestamp,
                "equity": equity,
                "daily_pnl": daily_pnl,
                "total_pnl": equity - starting_equity
            })
        
        # Current equity is last value
        self._current_equity = equity
        
        # Generate mock positions
        symbols = ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "META"]
        strategies = ["Mean Reversion", "Trend Following", "Breakout", "AI Predictor"]
        
        for i in range(min(5, days)):
            symbol = random.choice(symbols)
            side = random.choice(["long", "short"])
            quantity = random.randint(5, 50)
            entry_price = round(random.uniform(100, 500), 2)
            
            # Current price within ±10% of entry
            current_price = round(entry_price * (1 + (random.random() * 0.2 - 0.1)), 2)
            
            # Calculate PnL
            pnl = (current_price - entry_price) * quantity if side == "long" else (entry_price - current_price) * quantity
            pnl_percent = (current_price / entry_price - 1) * 100 if side == "long" else (entry_price / current_price - 1) * 100
            
            # Mock position
            self._positions.append({
                "id": f"pos_{i+1}",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entryPrice": entry_price,
                "currentPrice": current_price,
                "pnl": round(pnl, 2),
                "pnlPercent": round(pnl_percent, 2),
                "openTime": (datetime.utcnow() - timedelta(days=random.randint(1, days))).isoformat(),
                "strategy": random.choice(strategies)
            })
        
        # Generate mock signals (most recent first)
        for i in range(min(20, days * 3)):
            signal_time = (datetime.utcnow() - timedelta(
                days=random.randint(0, days-1),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )).isoformat()
            
            symbol = random.choice(symbols)
            signal_type = random.choice(["buy", "sell"])
            confidence = round(random.random() * 0.5 + 0.5, 2)  # 0.5 to 1.0
            executed = random.random() > 0.3  # 70% executed
            
            # Mock signal
            self._signals.append({
                "id": f"sig_{i+1}",
                "symbol": symbol,
                "type": signal_type,
                "source": random.choice(strategies),
                "confidence": confidence,
                "price": round(random.uniform(100, 500), 2),
                "timestamp": signal_time,
                "executed": executed,
                "reason": f"{'Strong' if confidence > 0.8 else 'Moderate'} "
                          f"{signal_type} signal detected"
            })
        
        # Sort signals by timestamp (newest first)
        self._signals.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Save mock data
        self._backup_data()
        logger.info(f"Generated mock data: {len(self._equity_history)} equity points, "
                  f"{len(self._positions)} positions, {len(self._signals)} signals") 
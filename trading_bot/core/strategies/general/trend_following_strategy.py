"""
Trend Following Strategy for Multiple Asset Classes.

This implements a flexible trend following strategy that can adapt to
different asset classes with appropriate parameter adjustments.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from trading_bot.core.strategies.multi_asset_strategy import MultiAssetStrategy

logger = logging.getLogger(__name__)

class TrendFollowingStrategy(MultiAssetStrategy):
    """
    A trend following strategy that works across equity, crypto, and forex markets.
    
    The strategy uses moving average crossovers and volume confirmation,
    with different default parameters for each asset class.
    """
    
    @staticmethod
    def get_parameter_schema() -> Dict[str, Any]:
        """
        Returns parameters schema for the trend following strategy.
        """
        return {
            # Moving average periods
            "fast_ma_period": {
                "type": "int", 
                "min": 3, 
                "max": 50, 
                "default": 10,
                "description": "Period for fast moving average"
            },
            "slow_ma_period": {
                "type": "int", 
                "min": 10, 
                "max": 200, 
                "default": 50,
                "description": "Period for slow moving average"
            },
            # Signal confirmation
            "use_volume_filter": {
                "type": "bool",
                "default": True,
                "description": "Whether to use volume as a confirmation filter"
            },
            "volume_ma_period": {
                "type": "int",
                "min": 5,
                "max": 50,
                "default": 20,
                "description": "Period for volume moving average"
            },
            # Risk management
            "stop_loss_pct": {
                "type": "float",
                "min": 0.5,
                "max": 10.0,
                "default": 2.0,
                "description": "Stop loss percentage"
            },
            "take_profit_pct": {
                "type": "float",
                "min": 1.0,
                "max": 20.0,
                "default": 4.0,
                "description": "Take profit percentage"
            },
            # Asset class specifics (specialized for each market)
            "trend_smoothing": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.3,
                "description": "Smoothing factor for trend detection, higher values are less sensitive"
            }
        }
    
    def _validate_parameters_crypto(self):
        """
        Crypto-specific parameter validation.
        """
        # Crypto needs a minimum stop loss percentage due to higher volatility
        if self.parameters.get("stop_loss_pct", 0) < 1.5:
            logger.warning(f"Crypto trading needs higher stop loss. Adjusting to 3%")
            self.parameters["stop_loss_pct"] = 3.0
    
    def _validate_parameters_forex(self):
        """
        Forex-specific parameter validation.
        """
        # For forex, the take profit should be smaller due to tighter ranges
        if self.parameters.get("take_profit_pct", 0) > 2.0:
            logger.warning(f"Forex profits are typically smaller. Adjusting to 1.5%")
            self.parameters["take_profit_pct"] = 1.5
    
    def _adapt_to_crypto(self) -> Dict[str, Any]:
        """
        Adapt the strategy for crypto markets.
        """
        changes = {}
        
        # Crypto markets require faster-moving averages due to 24/7 trading
        old_fast = self.parameters.get("fast_ma_period")
        old_slow = self.parameters.get("slow_ma_period")
        
        # Adjust moving averages to be more responsive
        self.parameters["fast_ma_period"] = max(3, int(old_fast * 0.7)) if old_fast else 7
        self.parameters["slow_ma_period"] = max(10, int(old_slow * 0.7)) if old_slow else 21
        
        # Increase stop loss for crypto volatility
        old_stop = self.parameters.get("stop_loss_pct")
        self.parameters["stop_loss_pct"] = max(3.0, old_stop * 1.5) if old_stop else 3.0
        
        changes = {
            "fast_ma_period": {"old": old_fast, "new": self.parameters["fast_ma_period"]},
            "slow_ma_period": {"old": old_slow, "new": self.parameters["slow_ma_period"]},
            "stop_loss_pct": {"old": old_stop, "new": self.parameters["stop_loss_pct"]}
        }
        
        return changes
    
    def _adapt_to_forex(self) -> Dict[str, Any]:
        """
        Adapt the strategy for forex markets.
        """
        changes = {}
        
        # Forex often requires larger moving average periods due to noise
        old_fast = self.parameters.get("fast_ma_period")
        old_slow = self.parameters.get("slow_ma_period")
        
        # Adjust moving averages to filter out more noise
        self.parameters["fast_ma_period"] = min(50, int(old_fast * 1.2)) if old_fast else 12
        self.parameters["slow_ma_period"] = min(150, int(old_slow * 1.2)) if old_slow else 50
        
        # Lower take profit in forex - smaller but more frequent gains
        old_tp = self.parameters.get("take_profit_pct")
        self.parameters["take_profit_pct"] = min(2.0, old_tp * 0.6) if old_tp else 1.5
        
        changes = {
            "fast_ma_period": {"old": old_fast, "new": self.parameters["fast_ma_period"]},
            "slow_ma_period": {"old": old_slow, "new": self.parameters["slow_ma_period"]},
            "take_profit_pct": {"old": old_tp, "new": self.parameters["take_profit_pct"]}
        }
        
        return changes
    
    def _generate_signals_generic(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals using a trend following approach adaptable to any asset class.
        """
        if historical_data.empty:
            logger.warning("Empty historical data provided")
            return pd.DataFrame(index=[], columns=['signal'])
        
        # Apply the correct MA type based on asset class 
        # (SMA for equity, EMA for crypto, WMA for forex)
        ma_type = {
            "equity": "sma",
            "crypto": "ema",
            "forex": "wma"
        }.get(self.asset_class, "sma")
        
        # Copy data to avoid modifying original
        df = historical_data.copy()
        
        # Get parameters
        fast_period = self.parameters.get("fast_ma_period", 10)
        slow_period = self.parameters.get("slow_ma_period", 50)
        use_volume = self.parameters.get("use_volume_filter", True)
        volume_period = self.parameters.get("volume_ma_period", 20)
        smoothing = self.parameters.get("trend_smoothing", 0.3)
        
        # Calculate moving averages based on the asset class
        if ma_type == "sma":
            # Simple Moving Average
            df['fast_ma'] = df['Close'].rolling(window=fast_period).mean()
            df['slow_ma'] = df['Close'].rolling(window=slow_period).mean()
        elif ma_type == "ema":
            # Exponential Moving Average
            df['fast_ma'] = df['Close'].ewm(span=fast_period, adjust=False).mean()
            df['slow_ma'] = df['Close'].ewm(span=slow_period, adjust=False).mean()
        elif ma_type == "wma":
            # Weighted Moving Average (linear weights)
            weights_fast = np.arange(1, fast_period + 1)
            weights_slow = np.arange(1, slow_period + 1)
            df['fast_ma'] = df['Close'].rolling(window=fast_period).apply(
                lambda x: np.sum(weights_fast * x) / weights_fast.sum(), raw=True)
            df['slow_ma'] = df['Close'].rolling(window=slow_period).apply(
                lambda x: np.sum(weights_slow * x) / weights_slow.sum(), raw=True)
        
        # Calculate trend/strength indicators
        df['ma_diff'] = df['fast_ma'] - df['slow_ma']
        df['ma_diff_pct'] = df['ma_diff'] / df['slow_ma'] * 100
        
        # Smooth the trend signal to reduce noise
        if smoothing > 0:
            df['ma_diff_smooth'] = df['ma_diff'].ewm(alpha=1-smoothing).mean()
        else:
            df['ma_diff_smooth'] = df['ma_diff']
        
        # Volume filter
        if use_volume and 'Volume' in df.columns:
            df['volume_ma'] = df['Volume'].rolling(window=volume_period).mean()
            volume_filter = df['Volume'] > df['volume_ma']
        else:
            volume_filter = pd.Series(True, index=df.index)
        
        # Generate signals
        # Buy when fast MA crosses above slow MA with volume confirmation
        # Sell when fast MA crosses below slow MA
        df['signal'] = 0  # Initialize signals
        
        # Crossover logic
        df['cross_above'] = (df['ma_diff_smooth'] > 0) & (df['ma_diff_smooth'].shift(1) <= 0)
        df['cross_below'] = (df['ma_diff_smooth'] < 0) & (df['ma_diff_smooth'].shift(1) >= 0)
        
        # Apply signals
        df.loc[df['cross_above'] & volume_filter, 'signal'] = 1  # Buy
        df.loc[df['cross_below'], 'signal'] = -1  # Sell
        
        # Calculate stop-loss and take-profit levels
        if 'signal' in df.columns:
            # Find all buy signals
            buy_signals = df[df['signal'] == 1].index
            buy_prices = df.loc[buy_signals, 'Close']
            
            # Calculate stop-loss and take-profit prices
            stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
            take_profit_pct = self.parameters.get("take_profit_pct", 4.0) / 100
            
            df['stop_loss'] = None
            df['take_profit'] = None
            
            for i, idx in enumerate(buy_signals):
                price = buy_prices.iloc[i]
                df.loc[idx, 'stop_loss'] = price * (1 - stop_loss_pct)
                df.loc[idx, 'take_profit'] = price * (1 + take_profit_pct)
        
        # Drop intermediate columns to keep the result clean
        result_columns = ['signal', 'stop_loss', 'take_profit']
        return df[result_columns]
    
    def _generate_signals_crypto(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crypto-specific signal generation with volatility adaptation.
        """
        df = historical_data.copy()
        
        # Add volatility detection for crypto
        if len(df) > 20:
            # Calculate historical volatility (20-day standard deviation of returns)
            df['returns'] = df['Close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(365)
            
            # If volatility is high, be more conservative with entry signals
            high_volatility = df['volatility'] > df['volatility'].rolling(window=50).mean()
            
            # Generate base signals
            signals_df = self._generate_signals_generic(historical_data)
            
            # Adjust signals based on volatility
            signals_df.loc[high_volatility, 'signal'] = signals_df.loc[high_volatility, 'signal'] * 0.5
            signals_df['signal'] = signals_df['signal'].round().astype(int)
            
            return signals_df
        
        # Not enough data for volatility calculation, use generic approach
        return self._generate_signals_generic(historical_data)
    
    def _generate_signals_forex(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Forex-specific signal generation with session awareness.
        """
        # For forex, we might want to be aware of trading sessions
        # This is a simplified approach - in practice you'd use precise session times
        if historical_data.index.name == 'datetime' or isinstance(historical_data.index, pd.DatetimeIndex):
            df = historical_data.copy()
            
            # Extract hour information from the index
            hours = df.index.hour
            
            # Define trading sessions (simplified)
            # Asian session: 0-8 UTC 
            # European session: 8-16 UTC
            # American session: 13-21 UTC
            df['asian_session'] = (hours >= 0) & (hours < 8)
            df['european_session'] = (hours >= 8) & (hours < 16)
            df['american_session'] = (hours >= 13) & (hours < 21)
            
            # Calculate session overlap periods (higher activity)
            df['session_overlap'] = df['european_session'] & df['american_session']
            
            # Generate base signals
            signals_df = self._generate_signals_generic(historical_data)
            
            # Boost signal strength during session overlaps (more liquid)
            if 'session_overlap' in df.columns:
                # During overlap, we trust the signals more
                overlap_mask = df['session_overlap']
                # Strengthen buy/sell signals in overlap periods (if they exist)
                signals_df.loc[overlap_mask & (signals_df['signal'] != 0), 'signal'] = \
                    signals_df.loc[overlap_mask & (signals_df['signal'] != 0), 'signal'] * 1.2
                
                # Round back to standard signal values
                signals_df['signal'] = signals_df['signal'].round().astype(int).clip(-1, 1)
            
            return signals_df
        
        # No datetime index, use generic approach
        return self._generate_signals_generic(historical_data) 
"""
Mean Reversion Strategy for Multiple Asset Classes.

This implements a flexible mean reversion strategy that can adapt to
different asset classes with appropriate parameter adjustments.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from trading_bot.core.strategies.multi_asset_strategy import MultiAssetStrategy

logger = logging.getLogger(__name__)

class MeanReversionStrategy(MultiAssetStrategy):
    """
    A mean reversion strategy that works across equity, crypto, and forex markets.
    
    The strategy uses relative strength index (RSI), Bollinger Bands, and z-score metrics
    to identify overbought/oversold conditions in different markets.
    """
    
    @staticmethod
    def get_parameter_schema() -> Dict[str, Any]:
        """
        Returns parameters schema for the mean reversion strategy.
        """
        return {
            # RSI parameters
            "rsi_period": {
                "type": "int", 
                "min": 2, 
                "max": 30, 
                "default": 14,
                "description": "Period for RSI calculation"
            },
            "rsi_overbought": {
                "type": "float", 
                "min": 60, 
                "max": 90, 
                "default": 70,
                "description": "RSI level considered overbought"
            },
            "rsi_oversold": {
                "type": "float", 
                "min": 10, 
                "max": 40, 
                "default": 30,
                "description": "RSI level considered oversold"
            },
            # Bollinger Bands parameters
            "bb_period": {
                "type": "int",
                "min": 5,
                "max": 50,
                "default": 20,
                "description": "Period for Bollinger Bands"
            },
            "bb_std_dev": {
                "type": "float",
                "min": 1.0,
                "max": 4.0,
                "default": 2.0,
                "description": "Standard deviation multiplier for Bollinger Bands"
            },
            # Mean reversion parameters
            "lookback_period": {
                "type": "int",
                "min": 5,
                "max": 100,
                "default": 20,
                "description": "Lookback period for mean calculation"
            },
            "z_score_threshold": {
                "type": "float",
                "min": 1.0,
                "max": 3.0,
                "default": 2.0,
                "description": "Z-score threshold for mean reversion signal"
            },
            # Exit parameters
            "mean_reversion_exit": {
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.5,
                "description": "Exit when price reverts this fraction back to the mean"
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
                "min": 0.5,
                "max": 10.0,
                "default": 3.0,
                "description": "Take profit percentage"
            },
            # Asset-specific parameters
            "use_volume_filter": {
                "type": "bool",
                "default": True,
                "description": "Whether to use volume as a confirmation filter"
            },
            "volume_filter_period": {
                "type": "int",
                "min": 5,
                "max": 30,
                "default": 10,
                "description": "Period for volume moving average"
            }
        }
    
    def _validate_parameters_crypto(self):
        """
        Crypto-specific parameter validation.
        """
        # Cryptocurrencies are more volatile, so we need wider bands
        if self.parameters.get("bb_std_dev", 0) < 2.5:
            logger.warning(f"Crypto needs wider Bollinger Bands. Adjusting to 2.5 STD")
            self.parameters["bb_std_dev"] = 2.5
            
        # Also need higher stop loss for crypto
        if self.parameters.get("stop_loss_pct", 0) < 3.0:
            logger.warning(f"Crypto trading needs higher stop loss. Adjusting to 3.5%")
            self.parameters["stop_loss_pct"] = 3.5
    
    def _validate_parameters_forex(self):
        """
        Forex-specific parameter validation.
        """
        # Forex markets are less volatile, so we can use tighter bands
        if self.parameters.get("bb_std_dev", 0) > 2.0:
            logger.warning(f"Forex works better with tighter Bollinger Bands. Adjusting to 1.8 STD")
            self.parameters["bb_std_dev"] = 1.8
            
        # Forex typically needs smaller take profit
        if self.parameters.get("take_profit_pct", 0) > 2.0:
            logger.warning(f"Forex profits are typically smaller. Adjusting to 1.5%")
            self.parameters["take_profit_pct"] = 1.5
    
    def _adapt_to_crypto(self) -> Dict[str, Any]:
        """
        Adapt the strategy for crypto markets.
        """
        changes = {}
        
        # Crypto markets need shorter RSI periods due to 24/7 trading
        old_rsi = self.parameters.get("rsi_period")
        old_bb = self.parameters.get("bb_period")
        
        # Adjust RSI and lookback periods to be more responsive
        self.parameters["rsi_period"] = max(4, int(old_rsi * 0.7)) if old_rsi else 10
        self.parameters["bb_period"] = max(10, int(old_bb * 0.7)) if old_bb else 14
        
        # Increase stop loss for crypto volatility
        old_stop = self.parameters.get("stop_loss_pct")
        self.parameters["stop_loss_pct"] = max(3.5, old_stop * 1.5) if old_stop else 3.5
        
        # Increase take profit for crypto opportunity
        old_tp = self.parameters.get("take_profit_pct")
        self.parameters["take_profit_pct"] = max(3.0, old_tp * 1.2) if old_tp else 3.0
        
        # Widen Z-score for crypto volatility
        old_z = self.parameters.get("z_score_threshold")
        self.parameters["z_score_threshold"] = min(2.5, old_z * 1.2) if old_z else 2.5
        
        changes = {
            "rsi_period": {"old": old_rsi, "new": self.parameters["rsi_period"]},
            "bb_period": {"old": old_bb, "new": self.parameters["bb_period"]},
            "stop_loss_pct": {"old": old_stop, "new": self.parameters["stop_loss_pct"]},
            "take_profit_pct": {"old": old_tp, "new": self.parameters["take_profit_pct"]},
            "z_score_threshold": {"old": old_z, "new": self.parameters["z_score_threshold"]}
        }
        
        return changes
    
    def _adapt_to_forex(self) -> Dict[str, Any]:
        """
        Adapt the strategy for forex markets.
        """
        changes = {}
        
        # Forex often requires longer lookback periods due to regular patterns
        old_lookback = self.parameters.get("lookback_period")
        old_rsi = self.parameters.get("rsi_period")
        
        # Adjust parameters for forex
        self.parameters["lookback_period"] = min(50, int(old_lookback * 1.3)) if old_lookback else 26
        self.parameters["rsi_period"] = min(21, int(old_rsi * 1.2)) if old_rsi else 16
        
        # Tighter bands for forex
        old_bb_std = self.parameters.get("bb_std_dev")
        self.parameters["bb_std_dev"] = max(1.5, min(2.0, old_bb_std * 0.9)) if old_bb_std else 1.8
        
        # Lower take profit in forex - smaller but more frequent gains
        old_tp = self.parameters.get("take_profit_pct")
        self.parameters["take_profit_pct"] = min(2.0, old_tp * 0.6) if old_tp else 1.5
        
        # Lower mean reversion exit for faster trades
        old_exit = self.parameters.get("mean_reversion_exit")
        self.parameters["mean_reversion_exit"] = min(0.4, old_exit * 0.8) if old_exit else 0.4
        
        changes = {
            "lookback_period": {"old": old_lookback, "new": self.parameters["lookback_period"]},
            "rsi_period": {"old": old_rsi, "new": self.parameters["rsi_period"]},
            "bb_std_dev": {"old": old_bb_std, "new": self.parameters["bb_std_dev"]},
            "take_profit_pct": {"old": old_tp, "new": self.parameters["take_profit_pct"]},
            "mean_reversion_exit": {"old": old_exit, "new": self.parameters["mean_reversion_exit"]}
        }
        
        return changes
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate common technical indicators for mean reversion.
        """
        # Get parameters
        rsi_period = self.parameters.get("rsi_period", 14)
        bb_period = self.parameters.get("bb_period", 20)
        bb_std_dev = self.parameters.get("bb_std_dev", 2.0)
        lookback_period = self.parameters.get("lookback_period", 20)
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, 0.00001)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_MA'] = df['Close'].rolling(window=bb_period).mean()
        df['BB_STD'] = df['Close'].rolling(window=bb_period).std()
        df['BB_Upper'] = df['BB_MA'] + (df['BB_STD'] * bb_std_dev)
        df['BB_Lower'] = df['BB_MA'] - (df['BB_STD'] * bb_std_dev)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_MA']
        
        # Z-Score (how many std devs price is from its mean)
        df['Mean'] = df['Close'].rolling(window=lookback_period).mean()
        df['STD'] = df['Close'].rolling(window=lookback_period).std()
        df['Z_Score'] = (df['Close'] - df['Mean']) / df['STD'].replace(0, 0.00001)
        
        # Distance from mean as percentage
        df['Pct_From_Mean'] = (df['Close'] - df['Mean']) / df['Mean'] * 100
        
        return df
    
    def _generate_signals_generic(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals using a mean reversion approach adaptable to any asset class.
        """
        if historical_data.empty:
            logger.warning("Empty historical data provided")
            return pd.DataFrame(index=[], columns=['signal'])
        
        # Copy data to avoid modifying original
        df = historical_data.copy()
        
        # Calculate indicators
        df = self._calculate_indicators(df)
        
        # Get signal parameters
        rsi_overbought = self.parameters.get("rsi_overbought", 70)
        rsi_oversold = self.parameters.get("rsi_oversold", 30)
        z_score_threshold = self.parameters.get("z_score_threshold", 2.0)
        use_volume_filter = self.parameters.get("use_volume_filter", True)
        volume_period = self.parameters.get("volume_filter_period", 10)
        
        # Volume filter
        if use_volume_filter and 'Volume' in df.columns:
            df['Volume_MA'] = df['Volume'].rolling(window=volume_period).mean()
            volume_filter = df['Volume'] > df['Volume_MA']
        else:
            volume_filter = pd.Series(True, index=df.index)
        
        # Initialize signals
        df['signal'] = 0
        
        # Generate mean reversion signals
        
        # Long signal: price below lower BB + oversold RSI + negative z-score beyond threshold
        long_condition = (
            (df['Close'] < df['BB_Lower']) &
            (df['RSI'] < rsi_oversold) &
            (df['Z_Score'] < -z_score_threshold) &
            volume_filter
        )
        
        # Short signal: price above upper BB + overbought RSI + positive z-score beyond threshold
        short_condition = (
            (df['Close'] > df['BB_Upper']) &
            (df['RSI'] > rsi_overbought) &
            (df['Z_Score'] > z_score_threshold) &
            volume_filter
        )
        
        # Apply signals
        df.loc[long_condition, 'signal'] = 1  # Buy when oversold
        df.loc[short_condition, 'signal'] = -1  # Sell when overbought
        
        # Calculate exit conditions (price returning to mean)
        mean_reversion_exit = self.parameters.get("mean_reversion_exit", 0.5)
        
        # When in a long position, exit when price reverts partway back to mean
        df['exit_long'] = (df['Pct_From_Mean'] >= -df['Pct_From_Mean'].shift(1) * (1 - mean_reversion_exit))
        
        # When in a short position, exit when price reverts partway back to mean
        df['exit_short'] = (df['Pct_From_Mean'] <= -df['Pct_From_Mean'].shift(1) * (1 - mean_reversion_exit))
        
        # Apply stop-loss and take-profit levels
        stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
        take_profit_pct = self.parameters.get("take_profit_pct", 3.0) / 100
        
        df['stop_loss'] = None
        df['take_profit'] = None
        
        # For each buy signal, set stop-loss and take-profit
        buy_signals = df[df['signal'] == 1].index
        buy_prices = df.loc[buy_signals, 'Close']
        
        for i, idx in enumerate(buy_signals):
            price = buy_prices.iloc[i]
            df.loc[idx, 'stop_loss'] = price * (1 - stop_loss_pct)
            df.loc[idx, 'take_profit'] = price * (1 + take_profit_pct)
        
        # For each sell signal, set stop-loss and take-profit (reversed for shorts)
        sell_signals = df[df['signal'] == -1].index
        sell_prices = df.loc[sell_signals, 'Close']
        
        for i, idx in enumerate(sell_signals):
            price = sell_prices.iloc[i]
            df.loc[idx, 'stop_loss'] = price * (1 + stop_loss_pct)
            df.loc[idx, 'take_profit'] = price * (1 - take_profit_pct)
        
        # Return only necessary columns
        result_columns = ['signal', 'stop_loss', 'take_profit']
        return df[result_columns]
    
    def _generate_signals_equity(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Equity-specific mean reversion signal generation.
        
        For equities, also checks for gap fills as a mean reversion opportunity.
        """
        # Copy data to avoid modifying original
        df = historical_data.copy()
        
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For equities, add gap fill signals
        if len(df) > 1:
            # Calculate overnight gaps
            df['prev_close'] = df['Close'].shift(1)
            df['gap_pct'] = (df['Open'] - df['prev_close']) / df['prev_close'] * 100
            
            # Large gaps often fill during the day
            large_gap_up = df['gap_pct'] > 2.0
            large_gap_down = df['gap_pct'] < -2.0
            
            # Fade large gap ups (go short)
            gap_up_signals = large_gap_up
            signals_df.loc[gap_up_signals, 'signal'] = -1
            
            # Buy large gap downs (go long)
            gap_down_signals = large_gap_down
            signals_df.loc[gap_down_signals, 'signal'] = 1
            
            # Calculate stop-loss and take-profit levels for gap trades
            stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
            take_profit_pct = self.parameters.get("take_profit_pct", 3.0) / 100
            
            # Update stop-loss and take-profit for gap trades
            gap_up_indices = signals_df[gap_up_signals].index
            for idx in gap_up_indices:
                price = df.loc[idx, 'Open']
                signals_df.loc[idx, 'stop_loss'] = price * (1 + stop_loss_pct)
                signals_df.loc[idx, 'take_profit'] = df.loc[idx, 'prev_close']  # Target the previous close
            
            gap_down_indices = signals_df[gap_down_signals].index
            for idx in gap_down_indices:
                price = df.loc[idx, 'Open']
                signals_df.loc[idx, 'stop_loss'] = price * (1 - stop_loss_pct)
                signals_df.loc[idx, 'take_profit'] = df.loc[idx, 'prev_close']  # Target the previous close
        
        return signals_df
    
    def _generate_signals_crypto(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crypto-specific mean reversion signal generation.
        
        For crypto, adds volatility-based filters to avoid false signals.
        """
        df = historical_data.copy()
        
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For crypto, add volatility-based filters
        if len(df) > 20:
            # Calculate historical volatility (20-day standard deviation of returns)
            df['returns'] = df['Close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(365)
            df['volatility_ma'] = df['volatility'].rolling(window=10).mean()
            
            # Volatility regime identification
            df['volatility_regime'] = np.where(
                df['volatility'] > df['volatility_ma'] * 1.2, 
                'high', 
                np.where(
                    df['volatility'] < df['volatility_ma'] * 0.8, 
                    'low', 
                    'normal'
                )
            )
            
            # Adjust signals based on volatility regime
            
            # High volatility: be more selective with signals
            high_volatility = df['volatility_regime'] == 'high'
            
            # Only allow stronger signals in high volatility regimes
            z_score_threshold = self.parameters.get("z_score_threshold", 2.0)
            high_vol_filter = abs(df['Z_Score']) > (z_score_threshold * 1.3)
            
            # Filter out weaker signals during high volatility
            signals_df.loc[high_volatility & ~high_vol_filter, 'signal'] = 0
            
            # Adjust stop-loss distances based on volatility
            stop_loss_pct = self.parameters.get("stop_loss_pct", 3.5) / 100
            for i, idx in enumerate(signals_df.index):
                if pd.notnull(signals_df.loc[idx, 'stop_loss']):
                    vol_mult = 1.0
                    if idx in df.index:
                        if df.loc[idx, 'volatility_regime'] == 'high':
                            vol_mult = 1.3  # Wider stops in high vol
                        elif df.loc[idx, 'volatility_regime'] == 'low':
                            vol_mult = 0.8  # Tighter stops in low vol
                    
                    # Adjust the stop loss
                    if signals_df.loc[idx, 'signal'] == 1:  # Long position
                        price = historical_data.loc[idx, 'Close']
                        signals_df.loc[idx, 'stop_loss'] = price * (1 - stop_loss_pct * vol_mult)
                    elif signals_df.loc[idx, 'signal'] == -1:  # Short position
                        price = historical_data.loc[idx, 'Close']
                        signals_df.loc[idx, 'stop_loss'] = price * (1 + stop_loss_pct * vol_mult)
        
        return signals_df
    
    def _generate_signals_forex(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Forex-specific mean reversion signal generation.
        
        For forex, considers session overlaps and range-bound behavior.
        """
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For forex, consider session overlaps
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
            
            # Forex mean reversion works best during range-bound sessions (Asian) 
            # and less well during volatile overlap periods
            
            # Strengthen signals during Asian session (typically more range-bound)
            asian_mask = df['asian_session'] & ~df['european_session'] & ~df['american_session']
            signals_df.loc[asian_mask & (signals_df['signal'] != 0), 'signal'] = \
                signals_df.loc[asian_mask & (signals_df['signal'] != 0), 'signal'] * 1.2
            
            # Weaken signals during session overlaps (more trending)
            overlap_mask = df['session_overlap']
            signals_df.loc[overlap_mask & (signals_df['signal'] != 0), 'signal'] = \
                signals_df.loc[overlap_mask & (signals_df['signal'] != 0), 'signal'] * 0.7
            
            # Round signals back to standard values
            signals_df['signal'] = signals_df['signal'].round().astype(int).clip(-1, 1)
            
            # Also check if today's range is small compared to recent days
            if len(df) > 10:
                df['daily_range'] = df['High'] - df['Low']
                df['avg_range_10d'] = df['daily_range'].rolling(window=10).mean()
                df['range_ratio'] = df['daily_range'] / df['avg_range_10d']
                
                # If today's range is small, we're more likely in a range-bound environment
                # which is favorable for mean reversion
                small_range = df['range_ratio'] < 0.8
                signals_df.loc[small_range & (signals_df['signal'] != 0), 'signal'] = \
                    signals_df.loc[small_range & (signals_df['signal'] != 0), 'signal'] * 1.2
                
                # Round signals back to standard values
                signals_df['signal'] = signals_df['signal'].round().astype(int).clip(-1, 1)
        
        return signals_df 
"""
Volatility Strategy for Multiple Asset Classes.

This implements a strategy that adapts to volatile market conditions
and aims to thrive in periods of high uncertainty across asset classes.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from trading_bot.core.strategies.multi_asset_strategy import MultiAssetStrategy

logger = logging.getLogger(__name__)

class VolatilityStrategy(MultiAssetStrategy):
    """
    A volatility-based strategy that works across equity, crypto, and forex markets.
    
    This strategy identifies volatility regimes and adjusts trading approaches accordingly.
    In high volatility, it looks for breakout opportunities and momentum.
    In low volatility, it can shift to mean reversion tactics or stay in cash.
    """
    
    @staticmethod
    def get_parameter_schema() -> Dict[str, Any]:
        """
        Returns parameters schema for the volatility strategy.
        """
        return {
            # Volatility measurement
            "volatility_lookback": {
                "type": "int", 
                "min": 5, 
                "max": 60, 
                "default": 21,
                "description": "Period for volatility calculation"
            },
            "volatility_ma_period": {
                "type": "int", 
                "min": 10, 
                "max": 100, 
                "default": 63,
                "description": "Lookback for volatility moving average"
            },
            "volatility_high_threshold": {
                "type": "float", 
                "min": 1.1, 
                "max": 2.0, 
                "default": 1.5,
                "description": "Threshold multiplier for high volatility"
            },
            "volatility_low_threshold": {
                "type": "float", 
                "min": 0.5, 
                "max": 0.9, 
                "default": 0.7,
                "description": "Threshold multiplier for low volatility"
            },
            # Breakout parameters
            "breakout_period": {
                "type": "int", 
                "min": 5, 
                "max": 50, 
                "default": 20,
                "description": "Period for breakout detection"
            },
            "breakout_multiplier": {
                "type": "float", 
                "min": 1.0, 
                "max": 3.0, 
                "default": 1.5,
                "description": "Multiplier for breakout threshold"
            },
            # Momentum parameters
            "momentum_period": {
                "type": "int", 
                "min": 2, 
                "max": 20, 
                "default": 10,
                "description": "Period for momentum calculation"
            },
            "momentum_threshold": {
                "type": "float", 
                "min": 0.5, 
                "max": 3.0, 
                "default": 1.0,
                "description": "Threshold for momentum strength"
            },
            # ATR for position sizing and stop loss
            "atr_period": {
                "type": "int", 
                "min": 5, 
                "max": 30, 
                "default": 14,
                "description": "Period for ATR calculation"
            },
            "atr_stop_multiplier": {
                "type": "float", 
                "min": 1.0, 
                "max": 5.0, 
                "default": 2.0,
                "description": "Multiplier for ATR-based stop loss"
            },
            # Risk management
            "stop_loss_pct": {
                "type": "float", 
                "min": 0.5, 
                "max": 10.0, 
                "default": 2.0,
                "description": "Fixed stop loss percentage (if not using ATR)"
            },
            "take_profit_pct": {
                "type": "float", 
                "min": 0.5, 
                "max": 10.0, 
                "default": 3.0,
                "description": "Take profit percentage"
            },
            "use_atr_stops": {
                "type": "bool", 
                "default": True,
                "description": "Whether to use ATR-based stop loss"
            },
            # Strategy behavior
            "use_regime_filter": {
                "type": "bool", 
                "default": True,
                "description": "Whether to filter trades based on volatility regime"
            },
            "trade_only_high_vol": {
                "type": "bool", 
                "default": False,
                "description": "Whether to only trade in high volatility regimes"
            }
        }
    
    def _validate_parameters_crypto(self):
        """
        Crypto-specific parameter validation.
        """
        # Cryptocurrencies are inherently volatile, so we need wider ATR multipliers
        if self.parameters.get("atr_stop_multiplier", 0) < 3.0:
            logger.warning("Crypto typically needs wider ATR stops. Adjusting to 3.0")
            self.parameters["atr_stop_multiplier"] = 3.0
        
        # Higher breakout threshold for crypto
        if self.parameters.get("breakout_multiplier", 0) < 1.8:
            logger.warning("Crypto typically needs higher breakout thresholds. Adjusting to 1.8")
            self.parameters["breakout_multiplier"] = 1.8
    
    def _validate_parameters_forex(self):
        """
        Forex-specific parameter validation.
        """
        # Forex has lower volatility, so we need tighter thresholds
        if self.parameters.get("volatility_high_threshold", 0) > 1.3:
            logger.warning("Forex typically has lower volatility thresholds. Adjusting to 1.3")
            self.parameters["volatility_high_threshold"] = 1.3
            
        # Lower take profit in forex
        if self.parameters.get("take_profit_pct", 0) > 2.0:
            logger.warning("Forex typically needs smaller take profit. Adjusting to 1.5%")
            self.parameters["take_profit_pct"] = 1.5
    
    def _adapt_to_crypto(self) -> Dict[str, Any]:
        """
        Adapt the strategy for crypto markets.
        """
        changes = {}
        
        # For crypto, shorter lookback periods and higher thresholds
        old_vol_lookback = self.parameters.get("volatility_lookback")
        old_breakout_period = self.parameters.get("breakout_period")
        old_atr_stop = self.parameters.get("atr_stop_multiplier")
        old_breakout_mult = self.parameters.get("breakout_multiplier")
        
        # Adjust parameters
        self.parameters["volatility_lookback"] = max(10, int(old_vol_lookback * 0.8)) if old_vol_lookback else 14
        self.parameters["breakout_period"] = max(10, int(old_breakout_period * 0.7)) if old_breakout_period else 14
        self.parameters["atr_stop_multiplier"] = max(3.0, old_atr_stop * 1.2) if old_atr_stop else 3.0
        self.parameters["breakout_multiplier"] = max(1.8, old_breakout_mult * 1.1) if old_breakout_mult else 1.8
        
        # In crypto, volatility transitions can be extreme and fast
        self.parameters["volatility_high_threshold"] = 1.8
        self.parameters["volatility_low_threshold"] = 0.6
        
        changes = {
            "volatility_lookback": {"old": old_vol_lookback, "new": self.parameters["volatility_lookback"]},
            "breakout_period": {"old": old_breakout_period, "new": self.parameters["breakout_period"]},
            "atr_stop_multiplier": {"old": old_atr_stop, "new": self.parameters["atr_stop_multiplier"]},
            "breakout_multiplier": {"old": old_breakout_mult, "new": self.parameters["breakout_multiplier"]},
            "volatility_high_threshold": {"old": self.parameters.get("volatility_high_threshold", "unknown"), "new": 1.8},
            "volatility_low_threshold": {"old": self.parameters.get("volatility_low_threshold", "unknown"), "new": 0.6}
        }
        
        return changes
    
    def _adapt_to_forex(self) -> Dict[str, Any]:
        """
        Adapt the strategy for forex markets.
        """
        changes = {}
        
        # For forex, we need longer lookbacks and tighter thresholds
        old_vol_lookback = self.parameters.get("volatility_lookback")
        old_momentum_period = self.parameters.get("momentum_period")
        old_take_profit = self.parameters.get("take_profit_pct")
        
        # Adjust parameters
        self.parameters["volatility_lookback"] = min(30, int(old_vol_lookback * 1.2)) if old_vol_lookback else 28
        self.parameters["momentum_period"] = min(15, int(old_momentum_period * 1.3)) if old_momentum_period else 13
        self.parameters["take_profit_pct"] = min(1.5, old_take_profit * 0.8) if old_take_profit else 1.5
        
        # Forex volatility thresholds
        self.parameters["volatility_high_threshold"] = 1.3
        self.parameters["volatility_low_threshold"] = 0.8
        
        # In forex, session awareness is important
        self.parameters["use_regime_filter"] = True
        
        changes = {
            "volatility_lookback": {"old": old_vol_lookback, "new": self.parameters["volatility_lookback"]},
            "momentum_period": {"old": old_momentum_period, "new": self.parameters["momentum_period"]},
            "take_profit_pct": {"old": old_take_profit, "new": self.parameters["take_profit_pct"]},
            "volatility_high_threshold": {"old": self.parameters.get("volatility_high_threshold", "unknown"), "new": 1.3},
            "volatility_low_threshold": {"old": self.parameters.get("volatility_low_threshold", "unknown"), "new": 0.8}
        }
        
        return changes
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate volatility and related indicators.
        """
        # Get parameters
        vol_lookback = self.parameters.get("volatility_lookback", 21)
        vol_ma_period = self.parameters.get("volatility_ma_period", 63)
        atr_period = self.parameters.get("atr_period", 14)
        breakout_period = self.parameters.get("breakout_period", 20)
        momentum_period = self.parameters.get("momentum_period", 10)
        
        # Calculate historical and realized volatility
        # Daily returns
        df['returns'] = df['Close'].pct_change()
        
        # Realized volatility (standard deviation of returns)
        df['realized_vol'] = df['returns'].rolling(window=vol_lookback).std() * np.sqrt(252)  # Annualized
        
        # Volatility moving average
        df['volatility_ma'] = df['realized_vol'].rolling(window=vol_ma_period).mean()
        
        # Volatility ratio (current vol / average vol)
        # This identifies regime changes
        df['volatility_ratio'] = df['realized_vol'] / df['volatility_ma']
        
        # ATR calculation for stop loss positioning
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df['Close'].shift())
        df['low_close'] = abs(df['Low'] - df['Close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=atr_period).mean()
        
        # Breakout detection
        df['upper_channel'] = df['High'].rolling(window=breakout_period).max()
        df['lower_channel'] = df['Low'].rolling(window=breakout_period).min()
        
        # Channel width as percentage of price
        df['channel_width'] = (df['upper_channel'] - df['lower_channel']) / df['Close']
        
        # Momentum indicators
        df['momentum'] = df['Close'] / df['Close'].shift(momentum_period) - 1
        
        # Identify volatility regimes
        vol_high_threshold = self.parameters.get("volatility_high_threshold", 1.5)
        vol_low_threshold = self.parameters.get("volatility_low_threshold", 0.7)
        
        df['volatility_regime'] = np.where(
            df['volatility_ratio'] > vol_high_threshold, 
            'high', 
            np.where(
                df['volatility_ratio'] < vol_low_threshold, 
                'low', 
                'normal'
            )
        )
        
        return df
    
    def _generate_signals_generic(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on volatility regime and breakout/momentum detection.
        """
        if historical_data.empty:
            logger.warning("Empty historical data provided")
            return pd.DataFrame(index=[], columns=['signal'])
        
        # Copy data to avoid modifying original
        df = historical_data.copy()
        
        # Calculate indicators
        df = self._calculate_indicators(df)
        
        # Get parameters
        breakout_multiplier = self.parameters.get("breakout_multiplier", 1.5)
        momentum_threshold = self.parameters.get("momentum_threshold", 1.0)
        use_regime_filter = self.parameters.get("use_regime_filter", True)
        trade_only_high_vol = self.parameters.get("trade_only_high_vol", False)
        
        # Initialize signals
        df['signal'] = 0
        
        # Generate signals based on volatility regime
        
        # High volatility regime
        high_vol_mask = df['volatility_regime'] == 'high'
        
        # In high volatility:
        # 1. Look for breakouts
        # 2. Favor momentum in the direction of breakout
        
        # Upside breakout: price breaks above upper channel with strong momentum
        upside_breakout = (
            (df['Close'] > df['upper_channel'].shift(1) * (1 + 0.01)) &  # 1% above previous upper channel
            (df['momentum'] > momentum_threshold / 100) &                # Positive momentum
            (df['Close'] > df['Close'].shift(1))                         # Still moving up
        )
        
        # Downside breakout: price breaks below lower channel with strong momentum
        downside_breakout = (
            (df['Close'] < df['lower_channel'].shift(1) * (1 - 0.01)) &  # 1% below previous lower channel
            (df['momentum'] < -momentum_threshold / 100) &               # Negative momentum
            (df['Close'] < df['Close'].shift(1))                         # Still moving down
        )
        
        # Low volatility regime
        low_vol_mask = df['volatility_regime'] == 'low'
        
        # Normal volatility regime
        normal_vol_mask = df['volatility_regime'] == 'normal'
        
        # Apply signals based on regime
        if trade_only_high_vol:
            # Only trade in high volatility
            df.loc[high_vol_mask & upside_breakout, 'signal'] = 1      # Buy on upside breakout in high vol
            df.loc[high_vol_mask & downside_breakout, 'signal'] = -1   # Sell on downside breakout in high vol
        else:
            # Trade in all regimes but with different tactics
            
            # High volatility: breakout trading
            df.loc[high_vol_mask & upside_breakout, 'signal'] = 1      # Buy on upside breakout in high vol
            df.loc[high_vol_mask & downside_breakout, 'signal'] = -1   # Sell on downside breakout in high vol
            
            # Normal volatility: momentum following
            momentum_up = df['momentum'] > momentum_threshold / 100
            momentum_down = df['momentum'] < -momentum_threshold / 100
            
            if not use_regime_filter or (use_regime_filter and any(normal_vol_mask)):
                df.loc[normal_vol_mask & momentum_up, 'signal'] = 1       # Buy on strong momentum in normal vol
                df.loc[normal_vol_mask & momentum_down, 'signal'] = -1    # Sell on negative momentum in normal vol
        
        # Apply stop loss - can be fixed or ATR-based
        use_atr_stops = self.parameters.get("use_atr_stops", True)
        atr_stop_multiplier = self.parameters.get("atr_stop_multiplier", 2.0)
        stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
        take_profit_pct = self.parameters.get("take_profit_pct", 3.0) / 100
        
        df['stop_loss'] = None
        df['take_profit'] = None
        
        # For each buy signal, set stop loss and take profit
        buy_signals = df[df['signal'] == 1].index
        for idx in buy_signals:
            price = df.loc[idx, 'Close']
            
            if use_atr_stops and 'atr' in df.columns and not pd.isna(df.loc[idx, 'atr']):
                stop_distance = df.loc[idx, 'atr'] * atr_stop_multiplier
                stop_loss = price - stop_distance
                
                # If ATR is very large, cap stop loss at fixed percentage
                if (price - stop_loss) / price > stop_loss_pct * 2:
                    stop_loss = price * (1 - stop_loss_pct)
            else:
                stop_loss = price * (1 - stop_loss_pct)
            
            take_profit = price * (1 + take_profit_pct)
            
            df.loc[idx, 'stop_loss'] = stop_loss
            df.loc[idx, 'take_profit'] = take_profit
        
        # For each sell signal, set stop loss and take profit (reversed for shorts)
        sell_signals = df[df['signal'] == -1].index
        for idx in sell_signals:
            price = df.loc[idx, 'Close']
            
            if use_atr_stops and 'atr' in df.columns and not pd.isna(df.loc[idx, 'atr']):
                stop_distance = df.loc[idx, 'atr'] * atr_stop_multiplier
                stop_loss = price + stop_distance
                
                # If ATR is very large, cap stop loss at fixed percentage
                if (stop_loss - price) / price > stop_loss_pct * 2:
                    stop_loss = price * (1 + stop_loss_pct)
            else:
                stop_loss = price * (1 + stop_loss_pct)
            
            take_profit = price * (1 - take_profit_pct)
            
            df.loc[idx, 'stop_loss'] = stop_loss
            df.loc[idx, 'take_profit'] = take_profit
        
        # Return only necessary columns
        result_columns = ['signal', 'stop_loss', 'take_profit']
        return df[result_columns]
    
    def _generate_signals_equity(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Equity-specific volatility signal generation.
        
        For equities, adds VIX-like indicators and gap analysis.
        """
        # Copy data to avoid modifying original
        df = historical_data.copy()
        
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For equities, add gap analysis (significant overnight gaps can signal volatility)
        if len(df) > 1:
            # Calculate overnight gaps
            df['prev_close'] = df['Close'].shift(1)
            df['gap_pct'] = (df['Open'] - df['prev_close']) / df['prev_close'] * 100
            
            # Calculate average gap size over lookback
            gap_lookback = 20
            df['avg_gap_size'] = df['gap_pct'].abs().rolling(window=gap_lookback).mean()
            
            # Calculate gap volatility (stddev of gap size)
            df['gap_vol'] = df['gap_pct'].rolling(window=gap_lookback).std()
            
            # Relative gap size (today's gap vs average)
            df['relative_gap'] = df['gap_pct'].abs() / df['avg_gap_size']
            
            # Large gaps signal high volatility and potential continuation
            large_gap_up = (df['gap_pct'] > 1.0) & (df['relative_gap'] > 1.5)
            large_gap_down = (df['gap_pct'] < -1.0) & (df['relative_gap'] > 1.5)
            
            # In high gap volatility, strengthen existing signals
            high_gap_vol = df['gap_vol'] > df['gap_vol'].rolling(window=63).mean() * 1.5
            
            # For signals on gap days, increase signal if gap is in direction of signal
            for idx in df[high_gap_vol].index:
                if idx in signals_df.index:
                    # For bullish signals with gap up, strengthen signal
                    if signals_df.loc[idx, 'signal'] == 1 and large_gap_up.loc[idx]:
                        # Keep the signal at 1 (maximum), but consider adjusting take profit
                        if pd.notnull(signals_df.loc[idx, 'take_profit']):
                            # Widen take profit by 25% on strong gap in signal direction
                            current_tp = signals_df.loc[idx, 'take_profit']
                            current_price = df.loc[idx, 'Close']
                            tp_pct = (current_tp / current_price) - 1
                            new_tp = current_price * (1 + tp_pct * 1.25)
                            signals_df.loc[idx, 'take_profit'] = new_tp
                    
                    # For bearish signals with gap down, strengthen signal
                    elif signals_df.loc[idx, 'signal'] == -1 and large_gap_down.loc[idx]:
                        # Keep the signal at -1 (maximum), but consider adjusting take profit
                        if pd.notnull(signals_df.loc[idx, 'take_profit']):
                            # Widen take profit by 25% on strong gap in signal direction
                            current_tp = signals_df.loc[idx, 'take_profit']
                            current_price = df.loc[idx, 'Close']
                            tp_pct = 1 - (current_tp / current_price)
                            new_tp = current_price * (1 - tp_pct * 1.25)
                            signals_df.loc[idx, 'take_profit'] = new_tp
                    
                    # For signals against gap direction, weaken or filter out
                    elif signals_df.loc[idx, 'signal'] == 1 and large_gap_down.loc[idx]:
                        # Filter out bullish signals on big gap down days
                        signals_df.loc[idx, 'signal'] = 0
                        signals_df.loc[idx, 'stop_loss'] = None
                        signals_df.loc[idx, 'take_profit'] = None
                    
                    elif signals_df.loc[idx, 'signal'] == -1 and large_gap_up.loc[idx]:
                        # Filter out bearish signals on big gap up days
                        signals_df.loc[idx, 'signal'] = 0
                        signals_df.loc[idx, 'stop_loss'] = None
                        signals_df.loc[idx, 'take_profit'] = None
            
            # Additionally, consider gaps as independent signals
            # A persistent gap in one direction could be a breakaway gap indicating trend continuation
            
            # If a large gap is followed by strong price action in same direction,
            # and we don't already have a signal, generate one
            for i, idx in enumerate(df.index):
                if i > 0 and idx in signals_df.index and signals_df.loc[idx, 'signal'] == 0:
                    # Large gap up followed by strong close (potential breakaway gap up)
                    if large_gap_up.loc[idx] and df.loc[idx, 'Close'] > df.loc[idx, 'Open'] * 1.005:
                        signals_df.loc[idx, 'signal'] = 1
                        # Set stop and take profit
                        price = df.loc[idx, 'Close']
                        stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
                        take_profit_pct = self.parameters.get("take_profit_pct", 3.0) / 100
                        signals_df.loc[idx, 'stop_loss'] = price * (1 - stop_loss_pct)
                        signals_df.loc[idx, 'take_profit'] = price * (1 + take_profit_pct)
                    
                    # Large gap down followed by weak close (potential breakaway gap down)
                    elif large_gap_down.loc[idx] and df.loc[idx, 'Close'] < df.loc[idx, 'Open'] * 0.995:
                        signals_df.loc[idx, 'signal'] = -1
                        # Set stop and take profit
                        price = df.loc[idx, 'Close']
                        stop_loss_pct = self.parameters.get("stop_loss_pct", 2.0) / 100
                        take_profit_pct = self.parameters.get("take_profit_pct", 3.0) / 100
                        signals_df.loc[idx, 'stop_loss'] = price * (1 + stop_loss_pct)
                        signals_df.loc[idx, 'take_profit'] = price * (1 - take_profit_pct)
        
        return signals_df
    
    def _generate_signals_crypto(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crypto-specific volatility signal generation.
        
        For crypto, adds liquidation cascades, funding rate extremes,
        and more aggressive signals during extreme volatility.
        """
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For crypto, volatility can be extremely high during liquidation cascades
        # We'll simulate this with price impact analysis
        df = historical_data.copy()
        
        if len(df) > 20:
            # Calculate extreme price movements
            df['pct_change'] = df['Close'].pct_change() * 100
            df['abs_pct_change'] = df['pct_change'].abs()
            
            # Rolling volatility
            df['rolling_vol_20d'] = df['pct_change'].rolling(window=20).std()
            
            # Identify extreme volatility events (> 3 sigma moves)
            df['extreme_vol'] = df['abs_pct_change'] > (df['rolling_vol_20d'] * 3)
            
            # Identify potential liquidation cascades
            # These are characterized by extreme moves followed by mean reversion
            # For now we'll use a simple approach - extreme down move followed by recovery
            df['big_down_day'] = (df['pct_change'] < -5.0) & (df['abs_pct_change'] > df['abs_pct_change'].rolling(window=60).quantile(0.9))
            
            # Check for recovery days after big down days
            df['recovery_day'] = False
            
            for i in range(1, min(3, len(df))):
                # Look up to 3 days after big down days for recovery
                df.loc[df.index[i:], 'recovery_day'] = df.loc[df.index[i:], 'recovery_day'] | df['big_down_day'].shift(i)
            
            # Look for strong recovery days - potential to enter long positions
            # Strong recovery = up day after big down day
            recovery_signal = (df['recovery_day']) & (df['pct_change'] > 2.0)
            
            # Apply to our signals
            for idx in df[recovery_signal].index:
                if idx in signals_df.index:
                    # Strong post-crash recoveries are good buying opportunities
                    signals_df.loc[idx, 'signal'] = 1
                    
                    # Set ambitious stops and targets for these recovery trades
                    price = df.loc[idx, 'Close']
                    # Wider stop to allow for volatility
                    stop_loss = price * 0.92  # 8% stop for recovery trades
                    # Ambitious target
                    take_profit = price * 1.15  # 15% target for recovery trades
                    
                    signals_df.loc[idx, 'stop_loss'] = stop_loss
                    signals_df.loc[idx, 'take_profit'] = take_profit
            
            # Also look for volatility compression before explosive moves
            # Calculate Bollinger Band Width Ratio
            df['bb_width'] = df['rolling_vol_20d'] / df['rolling_vol_20d'].rolling(window=60).mean()
            
            # Identify periods of compressed volatility (below 60-day average)
            df['vol_compressed'] = df['bb_width'] < 0.7
            
            # Volatility explosion (rapid increase from compressed state)
            df['vol_explosion'] = (df['vol_compressed'].shift(1)) & (df['rolling_vol_20d'] > df['rolling_vol_20d'].shift(1) * 1.5)
            
            # Generate signals for volatility breakouts
            for i, idx in enumerate(df.index[1:], 1):
                if df.loc[idx, 'vol_explosion'] and idx in signals_df.index:
                    # If we have a volatility explosion and price is moving up
                    if df.loc[idx, 'pct_change'] > 0:
                        # Volatility explosion to the upside
                        signals_df.loc[idx, 'signal'] = 1
                        
                        # Set adaptive stops and targets
                        price = df.loc[idx, 'Close']
                        stop_loss = price * (1 - df.loc[idx, 'rolling_vol_20d'] / 100 * 2)  # 2x daily vol as stop
                        take_profit = price * (1 + df.loc[idx, 'rolling_vol_20d'] / 100 * 4)  # 4x daily vol as target
                        
                        signals_df.loc[idx, 'stop_loss'] = stop_loss
                        signals_df.loc[idx, 'take_profit'] = take_profit
                    
                    # If we have a volatility explosion and price is moving down
                    elif df.loc[idx, 'pct_change'] < 0:
                        # Volatility explosion to the downside
                        signals_df.loc[idx, 'signal'] = -1
                        
                        # Set adaptive stops and targets
                        price = df.loc[idx, 'Close']
                        stop_loss = price * (1 + df.loc[idx, 'rolling_vol_20d'] / 100 * 2)  # 2x daily vol as stop
                        take_profit = price * (1 - df.loc[idx, 'rolling_vol_20d'] / 100 * 4)  # 4x daily vol as target
                        
                        signals_df.loc[idx, 'stop_loss'] = stop_loss
                        signals_df.loc[idx, 'take_profit'] = take_profit
        
        return signals_df
    
    def _generate_signals_forex(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Forex-specific volatility signal generation.
        
        For forex, considers volatility spikes around news events 
        and central bank announcements, plus session-related volatility patterns.
        """
        # First, get generic signals
        signals_df = self._generate_signals_generic(historical_data)
        
        # For forex, extreme volatility often happens around news events
        df = historical_data.copy()
        
        # Forex session-specific analysis
        if len(df) > 0 and isinstance(df.index, pd.DatetimeIndex):
            # Extract hour information from the index
            hours = df.index.hour
            
            # Define trading sessions
            # Asian session: 0-8 UTC 
            # European session: 8-16 UTC
            # American session: 13-21 UTC
            df['asian_session'] = (hours >= 0) & (hours < 8)
            df['european_session'] = (hours >= 8) & (hours < 16)
            df['american_session'] = (hours >= 13) & (hours < 21)
            
            # Session overlaps (typically higher volatility)
            df['session_overlap'] = df['european_session'] & df['american_session']
            
            # Calculate session-specific volatility
            if len(df) > 20:
                # Returns by session
                df['returns'] = df['Close'].pct_change()
                
                # Session-specific volatility
                df['asian_vol'] = df['returns'].where(df['asian_session']).rolling(window=20, min_periods=5).std()
                df['euro_vol'] = df['returns'].where(df['european_session']).rolling(window=20, min_periods=5).std()
                df['us_vol'] = df['returns'].where(df['american_session']).rolling(window=20, min_periods=5).std()
                df['overlap_vol'] = df['returns'].where(df['session_overlap']).rolling(window=20, min_periods=5).std()
                
                # Identify high volatility sessions relative to their typical values
                df['asian_high_vol'] = df['asian_vol'] > df['asian_vol'].rolling(window=60, min_periods=10).mean() * 1.5
                df['euro_high_vol'] = df['euro_vol'] > df['euro_vol'].rolling(window=60, min_periods=10).mean() * 1.5
                df['us_high_vol'] = df['us_vol'] > df['us_vol'].rolling(window=60, min_periods=10).mean() * 1.5
                df['overlap_high_vol'] = df['overlap_vol'] > df['overlap_vol'].rolling(window=60, min_periods=10).mean() * 1.5
                
                # Calculate intraday volatility ratio
                # This helps identify volatility clusters within sessions
                df['intraday_vol'] = (df['High'] - df['Low']) / df['Open']
                df['intraday_vol_ratio'] = df['intraday_vol'] / df['intraday_vol'].rolling(window=20).mean()
                
                # Extreme volatility days (top 5% of intraday ranges)
                df['extreme_range_day'] = df['intraday_vol'] > df['intraday_vol'].rolling(window=60).quantile(0.95)
                
                # Determine if we're in a high volatility cluster
                # This could be during key economic announcements or central bank decisions
                df['vol_cluster'] = (df['intraday_vol_ratio'] > 1.5) & (df['intraday_vol_ratio'].rolling(window=3).mean() > 1.3)
                
                # Adjust signals based on session volatility
                for idx in df.index:
                    if idx in signals_df.index:
                        # For signals during overlap sessions with high volatility
                        if df.loc[idx, 'session_overlap'] and df.loc[idx, 'overlap_high_vol']:
                            # We want to be aggressive with trend following during high-vol overlap periods
                            if signals_df.loc[idx, 'signal'] != 0:
                                # Keep the signal direction but adjust stops to be tighter
                                # This is typically higher risk, higher reward
                                price = df.loc[idx, 'Close']
                                current_stop = signals_df.loc[idx, 'stop_loss']
                                
                                # Make stop half as wide during volatile overlap periods
                                if pd.notnull(current_stop) and signals_df.loc[idx, 'signal'] == 1:
                                    # Tighten long stop loss
                                    old_stop_distance = price - current_stop
                                    new_stop = price - (old_stop_distance * 0.7)
                                    signals_df.loc[idx, 'stop_loss'] = new_stop
                                elif pd.notnull(current_stop) and signals_df.loc[idx, 'signal'] == -1:
                                    # Tighten short stop loss
                                    old_stop_distance = current_stop - price
                                    new_stop = price + (old_stop_distance * 0.7)
                                    signals_df.loc[idx, 'stop_loss'] = new_stop
                        
                        # For Asian session with low volatility, be cautious
                        if df.loc[idx, 'asian_session'] and not df.loc[idx, 'asian_high_vol']:
                            # Asian session typically has lower liquidity and false breakouts
                            # Filter out weak signals
                            if abs(df.loc[idx, 'returns']) < df['returns'].rolling(window=20).std():
                                signals_df.loc[idx, 'signal'] = 0
                                signals_df.loc[idx, 'stop_loss'] = None
                                signals_df.loc[idx, 'take_profit'] = None
                        
                        # For extreme volatility days, be extra cautious or aggressive
                        if df.loc[idx, 'extreme_range_day']:
                            # On extreme days, either filter out signals or be more aggressive
                            # For now, let's filter out signals if we're not in a clear trend
                            momentum = df.loc[idx, 'returns'] * 10  # Simple momentum metric
                            
                            # If we have a signal but weak momentum, consider filtering
                            if abs(momentum) < 0.5:
                                signals_df.loc[idx, 'signal'] = 0
                                signals_df.loc[idx, 'stop_loss'] = None
                                signals_df.loc[idx, 'take_profit'] = None
                
                # Also, consider additional signals for volatility clusters
                # These could be trend continuation plays during strong momentum
                for i, idx in enumerate(df.index):
                    if i > 0 and idx in signals_df.index and signals_df.loc[idx, 'signal'] == 0:
                        if df.loc[idx, 'vol_cluster']:
                            # If in volatility cluster with strong directional momentum
                            if df.loc[idx, 'returns'] > df['returns'].rolling(window=20).std() * 2:
                                # Strong up momentum in vol cluster - buy signal
                                signals_df.loc[idx, 'signal'] = 1
                                
                                # Set tight stops for these volatile conditions
                                price = df.loc[idx, 'Close']
                                signals_df.loc[idx, 'stop_loss'] = price * 0.995  # 0.5% stop
                                signals_df.loc[idx, 'take_profit'] = price * 1.01  # 1.0% target
                            
                            elif df.loc[idx, 'returns'] < -df['returns'].rolling(window=20).std() * 2:
                                # Strong down momentum in vol cluster - sell signal
                                signals_df.loc[idx, 'signal'] = -1
                                
                                # Set tight stops for these volatile conditions
                                price = df.loc[idx, 'Close']
                                signals_df.loc[idx, 'stop_loss'] = price * 1.005  # 0.5% stop
                                signals_df.loc[idx, 'take_profit'] = price * 0.99  # 1.0% target
        
        return signals_df 
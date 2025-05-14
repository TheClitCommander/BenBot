"""
Equity Momentum Strategy.

A specialized momentum strategy for equity markets, optimized for
bullish and trending market regimes.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from trading_bot.core.strategies.multi_asset_strategy import MultiAssetStrategy
from trading_bot.core.evolution.market_adapter import MarketRegime

logger = logging.getLogger(__name__)

class MomentumEquityStrategy(MultiAssetStrategy):
    """
    Specialized momentum strategy for equity markets, particularly
    effective in bullish or trending regimes.
    
    This strategy:
    1. Uses relative strength for stock selection
    2. Employs adaptive lookback periods based on market volatility
    3. Includes volatility-based position sizing
    4. Optimizes entries based on pullbacks from highs
    """
    
    @staticmethod
    def get_parameter_schema() -> Dict[str, Any]:
        """
        Returns parameters schema for the momentum strategy.
        """
        return {
            # Momentum measurement
            "momentum_period": {
                "type": "int", 
                "min": 20, 
                "max": 252, 
                "default": 90,
                "description": "Lookback period for momentum calculation"
            },
            "volume_confirmation": {
                "type": "bool", 
                "default": True,
                "description": "Whether to use volume confirmation"
            },
            "volatility_adjustment": {
                "type": "bool", 
                "default": True,
                "description": "Whether to adjust signals based on volatility"
            },
            "volatility_lookback": {
                "type": "int", 
                "min": 20, 
                "max": 100, 
                "default": 63,
                "description": "Lookback period for volatility calculation"
            },
            # Pullback entry parameters
            "use_pullback_entry": {
                "type": "bool", 
                "default": True,
                "description": "Whether to wait for pullbacks before entry"
            },
            "pullback_threshold": {
                "type": "float", 
                "min": 1.0, 
                "max": 10.0, 
                "default": 3.0,
                "description": "Minimum pullback required for entry (percentage)"
            },
            # Position management
            "trailing_stop_atr_multiple": {
                "type": "float", 
                "min": 1.0, 
                "max": 5.0, 
                "default": 2.5,
                "description": "Multiple of ATR for trailing stop distance"
            },
            "atr_period": {
                "type": "int", 
                "min": 5, 
                "max": 30, 
                "default": 14,
                "description": "Period for ATR calculation"
            },
            "profit_target_pct": {
                "type": "float", 
                "min": 5.0, 
                "max": 50.0, 
                "default": 20.0,
                "description": "Profit target percentage"
            },
            # Regime-specific parameters
            "preferred_regimes": {
                "type": "list",
                "default": ["bullish", "trending"],
                "description": "Market regimes this strategy is optimized for"
            }
        }
    
    def generate_signals(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the momentum strategy.
        
        Args:
            historical_data: Historical OHLCV data
            
        Returns:
            DataFrame with signals
        """
        # Check if we have enough data
        if historical_data.empty or len(historical_data) < 20:
            return pd.DataFrame(index=historical_data.index, columns=['signal']).fillna(0)
        
        # Copy to avoid modifying original
        df = historical_data.copy()
        
        # Calculate momentum indicators
        df = self._calculate_indicators(df)
        
        # Generate signals
        signals_df = self._generate_momentum_signals(df)
        
        return signals_df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate momentum and technical indicators.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            DataFrame with added indicators
        """
        # Get parameters
        momentum_period = self.parameters.get("momentum_period", 90)
        volatility_lookback = self.parameters.get("volatility_lookback", 63)
        atr_period = self.parameters.get("atr_period", 14)
        
        # Momentum (relative performance over period)
        df['momentum'] = df['Close'] / df['Close'].shift(momentum_period) - 1
        
        # Moving averages
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['sma_200'] = df['Close'].rolling(window=200).mean()
        
        # Volume indicators
        if 'Volume' in df.columns:
            df['volume_sma'] = df['Volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_sma']
        else:
            df['volume_ratio'] = 1.0  # Neutral if no volume data
        
        # Volatility indicators
        df['returns'] = df['Close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=volatility_lookback).std() * np.sqrt(252)  # Annualized
        df['avg_volatility'] = df['volatility'].rolling(window=volatility_lookback*2).mean()
        df['vol_ratio'] = df['volatility'] / df['avg_volatility']
        
        # ATR for stops
        df['tr'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=atr_period).mean()
        
        # Pullback indicators
        df['high_watermark'] = df['Close'].rolling(window=20).max()
        df['pullback_pct'] = (df['high_watermark'] - df['Close']) / df['high_watermark'] * 100
        
        # Market regime indicators
        df['bullish'] = (df['Close'] > df['sma_200']) & (df['sma_50'] > df['sma_200'])
        df['bearish'] = (df['Close'] < df['sma_200']) & (df['sma_50'] < df['sma_200'])
        
        return df
    
    def _generate_momentum_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate momentum signals.
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            DataFrame with trading signals
        """
        # Initialize signals DataFrame
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        signals['stop_loss'] = None
        signals['take_profit'] = None
        
        # Get parameters
        use_pullback_entry = self.parameters.get("use_pullback_entry", True)
        pullback_threshold = self.parameters.get("pullback_threshold", 3.0)
        trailing_stop_atr_multiple = self.parameters.get("trailing_stop_atr_multiple", 2.5)
        profit_target_pct = self.parameters.get("profit_target_pct", 20.0)
        volume_confirmation = self.parameters.get("volume_confirmation", True)
        volatility_adjustment = self.parameters.get("volatility_adjustment", True)
        
        # Base momentum signal
        momentum_signal = (df['momentum'] > 0.05) & (df['Close'] > df['sma_50'])
        
        # Additional filters
        volume_filter = df['volume_ratio'] > 1.0 if volume_confirmation else True
        
        # Pullback entry filter
        pullback_filter = df['pullback_pct'] >= pullback_threshold if use_pullback_entry else True
        
        # Volatility adjustment
        if volatility_adjustment:
            # Avoid high volatility periods
            volatility_filter = df['vol_ratio'] <= 1.5
        else:
            volatility_filter = True
        
        # Generate long signals
        long_condition = momentum_signal & volume_filter & pullback_filter & volatility_filter & df['bullish']
        signals.loc[long_condition, 'signal'] = 1
        
        # Apply stops and targets
        for i, idx in enumerate(signals.index):
            if signals.loc[idx, 'signal'] == 1:
                # Place stops at ATR-based distance
                if pd.notna(df.loc[idx, 'atr']):
                    stop_distance = df.loc[idx, 'atr'] * trailing_stop_atr_multiple
                    signals.loc[idx, 'stop_loss'] = df.loc[idx, 'Close'] - stop_distance
                else:
                    # Fallback to fixed percentage if ATR is not available
                    signals.loc[idx, 'stop_loss'] = df.loc[idx, 'Close'] * 0.95  # 5% stop
                
                # Set profit target
                signals.loc[idx, 'take_profit'] = df.loc[idx, 'Close'] * (1 + profit_target_pct/100)
        
        return signals
    
    def is_suitable_for_regime(self, regime: str) -> bool:
        """
        Check if this strategy is suitable for the current market regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            True if suitable, False otherwise
        """
        preferred_regimes = self.parameters.get("preferred_regimes", [
            MarketRegime.BULLISH, 
            MarketRegime.TRENDING
        ])
        
        # Convert string regimes to actual regimes if needed
        if isinstance(preferred_regimes[0], str):
            preferred_regimes = [getattr(MarketRegime, r.upper()) for r in preferred_regimes]
        
        return regime in preferred_regimes 
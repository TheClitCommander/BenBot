"""
General Trading Strategies module.

This package contains strategies that can work across multiple asset classes.
"""

from trading_bot.core.strategies.general.trend_following_strategy import TrendFollowingStrategy
from trading_bot.core.strategies.general.mean_reversion_strategy import MeanReversionStrategy
from trading_bot.core.strategies.general.volatility_strategy import VolatilityStrategy

__all__ = [
    "TrendFollowingStrategy",
    "MeanReversionStrategy",
    "VolatilityStrategy"
] 
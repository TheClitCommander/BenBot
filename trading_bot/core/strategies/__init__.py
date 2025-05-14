"""
Initialize the strategies package.
This file handles strategy registration and factory initialization.
"""

# Import the factory
from trading_bot.core.strategies.strategy_factory import strategy_factory, StrategyFactory
from trading_bot.core.strategies.base_strategy import BaseStrategy

# Import strategy helpers
import importlib

# Initialize the factory by discovering all strategies
try:
    num_strategies = strategy_factory.discover_strategies()
except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"Error during strategy discovery: {e}")
    num_strategies = 0

# Expose public API
__all__ = [
    "BaseStrategy",
    "StrategyFactory",
    "strategy_factory",
]

# Example (will be filled later):
# from .equity.some_equity_strategy import SomeEquityStrategy
# from .crypto.some_crypto_strategy import SomeCryptoStrategy
# from .forex.some_forex_strategy import SomeForexStrategy

# __all__ = ["SomeEquityStrategy", "SomeCryptoStrategy", "SomeForexStrategy"]

# For now, just make it a package
pass 
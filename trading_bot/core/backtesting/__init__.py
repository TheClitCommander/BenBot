# trading_bot/core/backtesting/__init__.py
# This file makes Python treat the `backtesting` directory as a package.

from .base_backtester import BaseBacktester
# We will add specific backtester imports here as they are implemented
# from .historical_equity_backtester import HistoricalEquityBacktester
# from .historical_crypto_backtester import HistoricalCryptoBacktester
# from .historical_forex_backtester import HistoricalForexBacktester

__all__ = [
    "BaseBacktester",
    # "HistoricalEquityBacktester",
    # "HistoricalCryptoBacktester",
    # "HistoricalForexBacktester"
] 
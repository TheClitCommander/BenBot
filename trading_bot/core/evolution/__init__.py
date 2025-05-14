"""
Evolution Package for BensBot.

This package contains the evolution engine and related components
for evolving trading strategies across different asset classes.
"""

from trading_bot.core.evolution.evo_trader import EvoTrader
from trading_bot.core.evolution.market_adapter import MarketAdapter, MarketRegime

__all__ = ["EvoTrader", "MarketAdapter", "MarketRegime"] 
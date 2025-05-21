"""
Evolution Package for BensBot.

This package contains the evolution engine and related components
for evolving trading strategies across different asset classes.
"""

from trading_bot.core.evolution.evo_trader import EvoTrader, StrategyGenome
from trading_bot.core.evolution.market_adapter import MarketAdapter, MarketRegime
from trading_bot.core.evolution.backtest_grid import BacktestGrid

__all__ = ["EvoTrader", "MarketAdapter", "MarketRegime", "BacktestGrid", "StrategyGenome"] 
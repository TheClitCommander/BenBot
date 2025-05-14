"""
Strategy evolution module for automated trading strategy improvement.

This module provides:
- Genetic algorithm-based strategy evolution
- Performance-based strategy selection
- Strategy parameter optimization
- Auto-promotion of successful strategies
"""

from trading_bot.core.evolution.evo_trader import EvoTrader, EvolutionConfig, StrategyGenome
from trading_bot.core.evolution.backtest_grid import BacktestGrid

__all__ = ["EvoTrader", "EvolutionConfig", "StrategyGenome", "BacktestGrid"] 
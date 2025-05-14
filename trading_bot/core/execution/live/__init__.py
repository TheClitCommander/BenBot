"""
Live Execution Package for BensBot.

This package contains the execution adapters for live trading
across different asset classes and brokers.
"""

from trading_bot.core.execution.live.base_executor import BaseExecutor
from trading_bot.core.execution.live.alpaca_executor import AlpacaExecutor
from trading_bot.core.execution.live.binance_executor import BinanceExecutor
from trading_bot.core.execution.live.oanda_executor import OandaExecutor
from trading_bot.core.execution.live.executor_factory import ExecutorFactory
from trading_bot.core.execution.live.strategy_guardian import LiveStrategyGuardian

__all__ = [
    "BaseExecutor",
    "AlpacaExecutor",
    "BinanceExecutor", 
    "OandaExecutor",
    "ExecutorFactory",
    "LiveStrategyGuardian"
] 
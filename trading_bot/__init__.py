"""
BensBot Trading System.

A multi-asset trading system with evolutionary algorithm capabilities.
"""

import os
from typing import Dict, Any, Optional
import logging

# Set up logging first
from trading_bot.utils.logging_setup import setup_logging, get_component_logger

# Default logging configuration
DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), ".benbot", "logs")

# Setup logging with default settings
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_DIR, "benbot.log")
setup_logging(
    log_level="INFO",
    log_file=DEFAULT_LOG_FILE,
    component_levels={
        "trading_bot.core.evolution": "DEBUG",
        "trading_bot.core.backtesting": "INFO",
        "trading_bot.core.strategies": "INFO"
    }
)

logger = get_component_logger(__name__)
logger.info("Initializing BensBot Trading System")

__version__ = "0.2.0"

# Initialize strategy factory
from trading_bot.core.strategies import strategy_factory
logger.info(f"Strategy factory initialized with {len(strategy_factory.get_all_metadata())} strategies")

def initialize_system(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize the BensBot trading system with the provided configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Dictionary of initialized components
    """
    from trading_bot.core.data.historical_data_fetcher import HistoricalDataFetcher
    
    # Initialize data fetcher
    data_fetcher = HistoricalDataFetcher()
    logger.info("Initialized historical data fetcher")
    
    # Initialize backtesting engines
    from trading_bot.core.backtesting.historical_equity_backtester import HistoricalEquityBacktester
    from trading_bot.core.backtesting.historical_crypto_backtester import HistoricalCryptoBacktester
    from trading_bot.core.backtesting.historical_forex_backtester import HistoricalForexBacktester
    
    backtester_registry = {
        "equity": HistoricalEquityBacktester(data_fetcher),
        "crypto": HistoricalCryptoBacktester(data_fetcher),
        "forex": HistoricalForexBacktester(data_fetcher)
    }
    logger.info(f"Initialized backtester registry with {len(backtester_registry)} backtester types")
    
    # Initialize evolution engine
    from trading_bot.core.evolution.evo_trader import EvoTrader
    evo_trader = EvoTrader(
        config_path="./config/evolution.json", 
        data_dir="./data/evolution",
        backtester_registry=backtester_registry
    )
    logger.info("Initialized evolutionary trading engine")
    
    # Initialize execution components
    from trading_bot.core.execution.evo_adapter import TradeExecutor, EvoToExecAdapter
    trade_executor = TradeExecutor()
    evo_adapter = EvoToExecAdapter(trade_executor, evo_trader=evo_trader)
    logger.info("Initialized trade execution components")
    
    # Initialize orchestrator
    from trading_bot.core.orchestration.orchestrator import Orchestrator
    orchestrator = Orchestrator(
        evo_trader=evo_trader,
        adapter=evo_adapter
    )
    logger.info("Initialized orchestrator")
    
    # Return system components
    return {
        "orchestrator": orchestrator,
        "evo_trader": evo_trader,
        "adapter": evo_adapter,
        "trade_executor": trade_executor,
        "data_fetcher": data_fetcher,
        "backtester_registry": backtester_registry
    } 
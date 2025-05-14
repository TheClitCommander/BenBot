"""
Executor Factory for Live Trading.

This module provides a factory for creating the appropriate executor
based on asset class and broker.
"""

import logging
import os
from typing import Dict, Any, Optional, Type

from trading_bot.core.execution.live.base_executor import BaseExecutor
from trading_bot.core.execution.live.alpaca_executor import AlpacaExecutor
# These will be implemented later when we create these files
# from trading_bot.core.execution.live.binance_executor import BinanceExecutor
# from trading_bot.core.execution.live.oanda_executor import OandaExecutor

logger = logging.getLogger(__name__)

class ExecutorFactory:
    """
    Factory for creating live execution adapters.
    """
    
    # Default executors for each asset class
    DEFAULT_EXECUTORS = {
        "equity": AlpacaExecutor,
        # "crypto": BinanceExecutor,
        # "forex": OandaExecutor
    }
    
    # Registry of available executors
    _executor_registry: Dict[str, Dict[str, Type[BaseExecutor]]] = {
        "equity": {"alpaca": AlpacaExecutor},
        "crypto": {},
        "forex": {}
    }
    
    @classmethod
    def register_executor(
        cls,
        asset_class: str,
        broker_name: str,
        executor_class: Type[BaseExecutor]
    ) -> None:
        """
        Register an executor for a specific asset class and broker.
        
        Args:
            asset_class: Asset class (equity, crypto, forex)
            broker_name: Name of the broker
            executor_class: Executor class to register
        """
        if asset_class not in cls._executor_registry:
            cls._executor_registry[asset_class] = {}
        
        cls._executor_registry[asset_class][broker_name] = executor_class
        logger.info(f"Registered {executor_class.__name__} for {asset_class} via {broker_name}")
    
    @classmethod
    def get_executor(
        cls,
        asset_class: str,
        broker_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        paper_trading: bool = True,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseExecutor:
        """
        Get an executor for a specific asset class and broker.
        
        Args:
            asset_class: Asset class (equity, crypto, forex)
            broker_name: Name of the broker (if None, use default for asset class)
            api_key: API key for the broker (if None, try to load from environment)
            api_secret: API secret for the broker (if None, try to load from environment)
            paper_trading: Whether to use paper trading
            config: Additional configuration parameters
            
        Returns:
            Executor instance
        """
        # Check if asset class is supported
        if asset_class not in cls._executor_registry:
            raise ValueError(f"Unsupported asset class: {asset_class}")
        
        # If broker not specified, use default
        if broker_name is None:
            # Check if default executor exists for this asset class
            if asset_class in cls.DEFAULT_EXECUTORS:
                executor_class = cls.DEFAULT_EXECUTORS[asset_class]
            else:
                raise ValueError(f"No default executor for asset class: {asset_class}")
        else:
            # Check if broker is supported for this asset class
            if broker_name not in cls._executor_registry[asset_class]:
                raise ValueError(f"Unsupported broker {broker_name} for asset class {asset_class}")
            
            executor_class = cls._executor_registry[asset_class][broker_name]
        
        # Try to load API keys from environment if not provided
        if api_key is None or api_secret is None:
            # Construct environment variable names based on broker
            broker_upper = broker_name.upper() if broker_name else asset_class.upper()
            api_key_env = f"{broker_upper}_API_KEY"
            api_secret_env = f"{broker_upper}_API_SECRET"
            
            if api_key is None:
                api_key = os.environ.get(api_key_env, "")
                if not api_key:
                    logger.warning(f"No API key provided and {api_key_env} environment variable not found")
            
            if api_secret is None:
                api_secret = os.environ.get(api_secret_env, "")
                if not api_secret:
                    logger.warning(f"No API secret provided and {api_secret_env} environment variable not found")
        
        # Create and return executor
        executor = executor_class(
            api_key=api_key or "",
            api_secret=api_secret or "",
            paper_trading=paper_trading,
            config=config or {}
        )
        
        return executor 
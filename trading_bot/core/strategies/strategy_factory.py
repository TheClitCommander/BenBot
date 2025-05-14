"""
Strategy Factory for BensBot.

This module provides a factory for creating and managing trading strategies.
It centralizes strategy instantiation, registration, and discovery.
"""

import logging
import importlib
import inspect
import os
from typing import Dict, Any, Type, List, Optional, Tuple
from pathlib import Path

from trading_bot.core.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class StrategyFactory:
    """
    Factory for creating and managing trading strategies.
    
    This class provides a registry of available strategies and methods to:
    - Dynamically discover strategies in the codebase
    - Register new strategy types
    - Create strategy instances with validated parameters
    - List available strategies by asset class
    """
    
    def __init__(self):
        """Initialize the strategy factory with an empty registry."""
        self._registry: Dict[str, Type[BaseStrategy]] = {}
        self._strategy_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_strategy(self, strategy_type: str, strategy_class: Type[BaseStrategy], 
                          asset_class: str, description: str = "") -> None:
        """
        Register a strategy class with the factory.
        
        Args:
            strategy_type: Unique identifier for the strategy type (e.g., 'equity_trend_default')
            strategy_class: The strategy class to register
            asset_class: The asset class this strategy is designed for ('equity', 'crypto', 'forex')
            description: Optional description of the strategy's approach
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError(f"Strategy class must inherit from BaseStrategy, got {strategy_class.__name__}")
        
        if strategy_type in self._registry:
            logger.warning(f"Strategy type '{strategy_type}' is already registered. Overwriting.")
        
        self._registry[strategy_type] = strategy_class
        self._strategy_metadata[strategy_type] = {
            "name": strategy_class.__name__,
            "asset_class": asset_class,
            "description": description,
            "parameter_schema": strategy_class.get_parameter_schema(),
        }
        
        logger.info(f"Registered {asset_class} strategy: {strategy_type} -> {strategy_class.__name__}")
    
    def create_strategy(self, strategy_type: str, strategy_id: str, parameters: Dict[str, Any]) -> BaseStrategy:
        """
        Create a strategy instance of the specified type with the given parameters.
        
        Args:
            strategy_type: The registered type of strategy to create
            strategy_id: A unique identifier for this strategy instance
            parameters: Parameters for the strategy instance
            
        Returns:
            An instantiated strategy object
            
        Raises:
            ValueError: If the strategy type is not registered
            ValueError/TypeError: If parameter validation fails
        """
        if strategy_type not in self._registry:
            raise ValueError(f"Strategy type '{strategy_type}' is not registered")
        
        strategy_class = self._registry[strategy_type]
        
        try:
            # Let the strategy's init method and _validate_parameters handle validation
            strategy = strategy_class(strategy_id=strategy_id, parameters=parameters)
            logger.debug(f"Created strategy instance {strategy_id} of type {strategy_type}")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_id} of type {strategy_type}: {e}")
            raise
    
    def discover_strategies(self) -> int:
        """
        Auto-discover and register strategy classes from the strategies directory.
        
        Returns:
            Number of strategies registered
        """
        strategies_dir = Path(__file__).parent
        count = 0
        
        # Define asset class subdirectories to search
        asset_classes = ['equity', 'crypto', 'forex']
        
        for asset_class in asset_classes:
            asset_dir = strategies_dir / asset_class
            if not asset_dir.exists():
                logger.warning(f"Asset class directory not found: {asset_dir}")
                continue
                
            logger.info(f"Discovering strategies in {asset_dir}")
            count += self._discover_in_directory(asset_dir, asset_class)
        
        logger.info(f"Discovered and registered {count} strategies")
        return count
    
    def _discover_in_directory(self, directory: Path, asset_class: str) -> int:
        """
        Discover and register strategy classes in a specific directory.
        
        Args:
            directory: Directory to search for strategy modules
            asset_class: Asset class to associate with found strategies
            
        Returns:
            Number of strategies registered
        """
        count = 0
        
        for file_path in directory.glob('*.py'):
            if file_path.name.startswith('_'):
                continue
                
            module_path = '.'.join(['trading_bot', 'core', 'strategies', 
                                   asset_class, file_path.stem])
            
            try:
                module = importlib.import_module(module_path)
                
                # Find all subclasses of BaseStrategy in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseStrategy) and 
                        obj != BaseStrategy):
                        
                        # Generate a strategy_type ID like 'equity_trend_default'
                        strategy_type = f"{asset_class}_{obj.__name__.lower()}"
                        
                        # Get description from docstring if available
                        description = obj.__doc__.strip() if obj.__doc__ else ""
                        
                        self.register_strategy(
                            strategy_type=strategy_type,
                            strategy_class=obj,
                            asset_class=asset_class,
                            description=description
                        )
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error discovering strategies in {file_path}: {e}")
        
        return count
    
    def get_strategy_types(self, asset_class: Optional[str] = None) -> List[str]:
        """
        Get a list of registered strategy types.
        
        Args:
            asset_class: Optional filter by asset class
            
        Returns:
            List of strategy type identifiers
        """
        if asset_class:
            return [
                strategy_type for strategy_type, metadata in self._strategy_metadata.items()
                if metadata["asset_class"] == asset_class
            ]
        return list(self._registry.keys())
    
    def get_strategy_metadata(self, strategy_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific strategy type.
        
        Args:
            strategy_type: The registered strategy type
            
        Returns:
            Dictionary with strategy metadata or None if not found
        """
        return self._strategy_metadata.get(strategy_type)
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all registered strategies.
        
        Returns:
            Dictionary mapping strategy_type to metadata
        """
        return self._strategy_metadata

# Create a singleton instance
strategy_factory = StrategyFactory() 
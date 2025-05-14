"""
Multi-Asset Strategy Base Class for BensBot.

This module provides a base class for strategies that can trade across 
multiple asset classes (equity, crypto, and forex) or be transferred 
between them with minimal changes.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod

from trading_bot.core.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class MultiAssetStrategy(BaseStrategy):
    """
    Base class for strategies that can operate across multiple asset classes.
    
    This class extends BaseStrategy with additional functionality for:
    1. Asset class-specific parameter validation
    2. Dynamic indicator calculation based on asset class
    3. Supporting transfer learning between asset classes
    4. Composition of multiple sub-strategies
    """
    
    def __init__(self, strategy_id: str, parameters: Dict[str, Any], asset_class: str = "equity"):
        """
        Initialize a multi-asset strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy instance
            parameters: Dictionary of strategy parameters
            asset_class: The asset class this strategy will operate on ("equity", "crypto", "forex")
        """
        self.asset_class = asset_class
        self.sub_strategies = {}  # For strategy composition
        super().__init__(strategy_id=strategy_id, parameters=parameters)
    
    def _validate_parameters(self):
        """
        Validate parameters with asset class-specific checks.
        """
        # First run the base class validation
        super()._validate_parameters()
        
        # Then run asset class-specific validation
        method_name = f"_validate_parameters_{self.asset_class}"
        validator = getattr(self, method_name, None)
        if validator and callable(validator):
            validator()
    
    def _validate_parameters_equity(self):
        """
        Equity-specific parameter validation.
        Override in subclasses that need special equity validations.
        """
        pass
    
    def _validate_parameters_crypto(self):
        """
        Crypto-specific parameter validation.
        Override in subclasses that need special crypto validations.
        """
        pass
    
    def _validate_parameters_forex(self):
        """
        Forex-specific parameter validation.
        Override in subclasses that need special forex validations.
        """
        pass
    
    def add_sub_strategy(self, name: str, strategy: BaseStrategy, weight: float = 1.0) -> None:
        """
        Add a sub-strategy to this composite strategy.
        
        Args:
            name: Identifier for the sub-strategy
            strategy: The strategy instance to add
            weight: The weight to assign this strategy in signal composition
        """
        self.sub_strategies[name] = {"strategy": strategy, "weight": weight}
    
    def adjust_sub_strategy_weight(self, name: str, weight: float) -> bool:
        """
        Adjust the weight of a sub-strategy.
        
        Args:
            name: Identifier for the sub-strategy
            weight: The new weight to assign
            
        Returns:
            True if successful, False if sub-strategy not found
        """
        if name not in self.sub_strategies:
            return False
        self.sub_strategies[name]["weight"] = weight
        return True
    
    def remove_sub_strategy(self, name: str) -> bool:
        """
        Remove a sub-strategy.
        
        Args:
            name: Identifier for the sub-strategy
            
        Returns:
            True if successful, False if sub-strategy not found
        """
        if name not in self.sub_strategies:
            return False
        del self.sub_strategies[name]
        return True
    
    def generate_signals(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on historical data.
        
        If sub-strategies are defined, this will composite their signals.
        Otherwise, it will use the strategy-specific signal generation.
        
        Args:
            historical_data: DataFrame of OHLCV data
            
        Returns:
            DataFrame with signals
        """
        if self.sub_strategies:
            return self._generate_composite_signals(historical_data)
        else:
            # Use asset class-specific signal generation
            method_name = f"_generate_signals_{self.asset_class}"
            generator = getattr(self, method_name, None)
            if generator and callable(generator):
                return generator(historical_data)
            else:
                # Fallback to generic implementation
                return self._generate_signals_generic(historical_data)
    
    def _generate_composite_signals(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals by compositing sub-strategy signals.
        
        Args:
            historical_data: DataFrame of OHLCV data
            
        Returns:
            DataFrame with composite signals
        """
        # Initialize a signals DataFrame with the same index as historical_data
        signals = pd.DataFrame(index=historical_data.index, columns=['signal'])
        signals['signal'] = 0
        
        # Get weighted signals from each sub-strategy
        total_weight = sum(sub["weight"] for sub in self.sub_strategies.values())
        if total_weight == 0:
            logger.warning(f"Total weight of sub-strategies is zero for {self.strategy_id}")
            return signals
        
        for name, sub in self.sub_strategies.items():
            try:
                # Generate signals for this sub-strategy
                sub_signals = sub["strategy"].generate_signals(historical_data)
                if 'signal' in sub_signals.columns:
                    # Apply the weight and add to composite signals
                    weight = sub["weight"] / total_weight
                    signals['signal'] += sub_signals['signal'] * weight
                else:
                    logger.warning(f"Sub-strategy {name} did not generate a 'signal' column")
            except Exception as e:
                logger.error(f"Error generating signals for sub-strategy {name}: {e}")
        
        # Threshold the signals to get discrete buy/sell decisions
        # This is a simple approach - more sophisticated voting or consensus 
        # mechanisms could be implemented
        signals['signal'] = np.round(signals['signal'])
        signals['signal'] = signals['signal'].clip(-1, 1)  # Ensure signals are in [-1, 0, 1]
        
        return signals
    
    @abstractmethod
    def _generate_signals_generic(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generic signal generation method that works across asset classes.
        Must be implemented by concrete strategy classes.
        
        Args:
            historical_data: DataFrame of OHLCV data
            
        Returns:
            DataFrame with signals
        """
        pass
    
    def _generate_signals_equity(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Equity-specific signal generation.
        Override in subclasses to provide specialized equity strategies.
        
        By default, falls back to generic implementation.
        """
        return self._generate_signals_generic(historical_data)
    
    def _generate_signals_crypto(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crypto-specific signal generation.
        Override in subclasses to provide specialized crypto strategies.
        
        By default, falls back to generic implementation.
        """
        return self._generate_signals_generic(historical_data)
    
    def _generate_signals_forex(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Forex-specific signal generation.
        Override in subclasses to provide specialized forex strategies.
        
        By default, falls back to generic implementation.
        """
        return self._generate_signals_generic(historical_data)
    
    def adapt_to_asset_class(self, asset_class: str, preserve_params: bool = True) -> Dict[str, Any]:
        """
        Adapt this strategy to a different asset class.
        This implements a simple transfer learning mechanism.
        
        Args:
            asset_class: The new asset class ("equity", "crypto", "forex")
            preserve_params: Whether to preserve existing parameters or reset to defaults
            
        Returns:
            Dictionary of changes made during adaptation
        """
        changes = {"previous_asset_class": self.asset_class, "new_asset_class": asset_class}
        
        if not preserve_params:
            # Reset to default parameters for the new asset class
            schema = self.get_parameter_schema()
            old_params = self.parameters.copy()
            self.parameters = {k: v.get("default") for k, v in schema.items() if "default" in v}
            changes["parameter_changes"] = {
                "old": old_params,
                "new": self.parameters
            }
        
        # Apply any asset class-specific adaptations
        method_name = f"_adapt_to_{asset_class}"
        adapter = getattr(self, method_name, None)
        if adapter and callable(adapter):
            adapter_changes = adapter()
            if adapter_changes:
                changes["adapter_changes"] = adapter_changes
        
        self.asset_class = asset_class
        return changes
    
    def _adapt_to_equity(self) -> Dict[str, Any]:
        """
        Adapt strategy parameters for equity markets.
        Override in subclasses to implement specialized adaptations.
        """
        return {}
    
    def _adapt_to_crypto(self) -> Dict[str, Any]:
        """
        Adapt strategy parameters for cryptocurrency markets.
        Override in subclasses to implement specialized adaptations.
        """
        return {}
    
    def _adapt_to_forex(self) -> Dict[str, Any]:
        """
        Adapt strategy parameters for forex markets.
        Override in subclasses to implement specialized adaptations.
        """
        return {}
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the strategy instance.
        """
        info = super().get_info()
        info["asset_class"] = self.asset_class
        
        # Include sub-strategy information if available
        if self.sub_strategies:
            info["sub_strategies"] = {
                name: {
                    "strategy_id": sub["strategy"].strategy_id,
                    "weight": sub["weight"]
                }
                for name, sub in self.sub_strategies.items()
            }
        
        return info 
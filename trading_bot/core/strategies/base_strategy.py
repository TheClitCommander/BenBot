"""
Base Strategy Interface for BensBot.

All strategy engines for different asset classes or archetypes should ideally
inherit from this base class or implement a similar interface to ensure
consistency in how they are handled by the EvoTrader and Backtesting modules.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, Optional

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    """

    def __init__(self, strategy_id: str, parameters: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.parameters = parameters
        self._validate_parameters() # Call validation upon initialization

    @staticmethod
    @abstractmethod
    def get_parameter_schema() -> Dict[str, Any]:
        """
        Returns a schema defining the parameters this strategy uses,
        their types, ranges, and default values. This is crucial for
        EvoTrader parameter space definition and UI generation.

        Example:
        return {
            "sma_short": {"type": "int", "min": 5, "max": 50, "default": 10},
            "sma_long": {"type": "int", "min": 20, "max": 200, "default": 50},
            "rsi_period": {"type": "int", "min": 7, "max": 21, "default": 14},
            "stop_loss_pct": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0}
        }
        """
        pass

    def _validate_parameters(self):
        """
        Validates the provided parameters against the strategy's schema.
        Logs warnings or raises errors for invalid parameters.
        This can be overridden for more complex validation logic.
        """
        schema = self.get_parameter_schema()
        for param_name, config in schema.items():
            if param_name not in self.parameters:
                if "default" in config:
                    self.parameters[param_name] = config["default"]
                    # logger.info(f"Parameter {param_name} not provided for {self.strategy_id}, using default: {config['default']}")
                else:
                    raise ValueError(f"Required parameter {param_name} missing for strategy {self.strategy_id}")
            
            value = self.parameters[param_name]
            param_type = config.get("type")

            if param_type == "int":
                if not isinstance(value, int):
                    raise TypeError(f"Parameter {param_name} must be an integer, got {type(value)}")
                if "min" in config and value < config["min"]:
                    raise ValueError(f"Parameter {param_name} ({value}) is less than min ({config['min']})")
                if "max" in config and value > config["max"]:
                    raise ValueError(f"Parameter {param_name} ({value}) is greater than max ({config['max']})")
            elif param_type == "float":
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Parameter {param_name} must be a float, got {type(value)}")
                self.parameters[param_name] = float(value) # Ensure it's a float
                if "min" in config and value < config["min"]:
                    raise ValueError(f"Parameter {param_name} ({value}) is less than min ({config['min']})")
                if "max" in config and value > config["max"]:
                    raise ValueError(f"Parameter {param_name} ({value}) is greater than max ({config['max']})")
            elif param_type == "bool":
                if not isinstance(value, bool):
                    raise TypeError(f"Parameter {param_name} must be a boolean, got {type(value)}")
            # Add more type checks as needed (e.g., for categorical string parameters)
        # logger.debug(f"Parameters for {self.strategy_id} validated successfully.")

    @abstractmethod
    def generate_signals(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates trading signals based on historical market data and strategy parameters.

        Args:
            historical_data: A pandas DataFrame containing OHLCV data, indexed by Timestamp.
                             It should at least contain 'Open', 'High', 'Low', 'Close', 'Volume'.

        Returns:
            A pandas DataFrame with the same index as historical_data, containing at least
            a 'signal' column. Signals could be:
                1 (Buy)
               -1 (Sell)
                0 (Hold or No Signal)
            May also include other columns like 'stop_loss_price', 'take_profit_price',
            or indicators used for decision making.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Returns information about the strategy instance.
        """
        return {
            "strategy_id": self.strategy_id,
            "parameters": self.parameters,
            "parameter_schema": self.get_parameter_schema()
        } 
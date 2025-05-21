"""
Base strategy definitions and interfaces to avoid circular imports.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class StrategyType(Enum):
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion" 
    BREAKOUT = "breakout"
    SENTIMENT = "sentiment"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    ENSEMBLE = "ensemble"


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    id: str
    name: str
    type: StrategyType
    parameters: Dict[str, Any]
    instruments: List[str]
    timeframe: str
    enabled: bool = True
    priority: int = 100


class Strategy:
    """Base class for all trading strategies."""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.id = config.id
        self.name = config.name
        self.type = config.type
        self.parameters = config.parameters
        self.instruments = config.instruments
        self.timeframe = config.timeframe
        self.enabled = config.enabled
        self.priority = config.priority
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data and generate signals."""
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": "active" if self.enabled else "paused",
            "instruments": self.instruments,
            "timeframe": self.timeframe,
            "priority": self.priority
        }
    
    def enable(self) -> None:
        """Enable the strategy."""
        self.enabled = True
        
    def disable(self) -> None:
        """Disable the strategy."""
        self.enabled = False 
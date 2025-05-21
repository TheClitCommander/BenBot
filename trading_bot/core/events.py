"""
Events for BensBot trading system.

This module defines events that can be published and subscribed to via the event bus.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, TypedDict, Union
from datetime import datetime

class EventType(Enum):
    """Event types for the trading system."""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    
    # Strategy events
    STRATEGY_REGISTERED = "strategy.registered"
    STRATEGY_ACTIVATED = "strategy.activated"
    STRATEGY_DEACTIVATED = "strategy.deactivated"
    STRATEGY_ERROR = "strategy.error"
    
    # Trading events
    SIGNAL_GENERATED = "trading.signal_generated"
    ORDER_CREATED = "trading.order_created"
    ORDER_FILLED = "trading.order_filled"
    ORDER_CANCELLED = "trading.order_cancelled"
    ORDER_REJECTED = "trading.order_rejected"
    POSITION_OPENED = "trading.position_opened"
    POSITION_CLOSED = "trading.position_closed"
    
    # Safety events
    EMERGENCY_STOP_ACTIVATED = "safety.emergency_stop_activated"
    EMERGENCY_STOP_DEACTIVATED = "safety.emergency_stop_deactivated"
    CIRCUIT_BREAKER_TRIGGERED = "safety.circuit_breaker_triggered"
    CIRCUIT_BREAKER_RESET = "safety.circuit_breaker_reset"
    COOLDOWN_STARTED = "safety.cooldown_started"
    COOLDOWN_ENDED = "safety.cooldown_ended"
    
    # Evolution events
    EVOLUTION_STARTED = "evolution.started"
    EVOLUTION_COMPLETED = "evolution.completed"
    EVOLUTION_PROGRESS = "evolution.progress"
    EVOLUTION_ERROR = "evolution.error"

class Event:
    """Base event class for all system events."""
    
    def __init__(
        self, 
        event_type: Union[EventType, str],
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new event.
        
        Args:
            event_type: Type of the event
            data: Additional event data
        """
        self.event_type = event_type.value if isinstance(event_type, EventType) else event_type
        self.data = data or {}
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        """Return string representation of the event."""
        return f"Event({self.event_type}, {self.timestamp})"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }

# Trading events
class TradeSignal(Event):
    """Trade signal event."""
    
    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        direction: str,  # 'buy' or 'sell'
        confidence: float,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a trade signal event.
        
        Args:
            strategy_id: ID of the strategy generating the signal
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            confidence: Confidence level (0-1)
            target_price: Target price for the trade
            stop_loss: Stop loss price
            take_profit: Take profit price
            data: Additional signal data
        """
        signal_data = {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
        }
        
        if target_price is not None:
            signal_data["target_price"] = target_price
        
        if stop_loss is not None:
            signal_data["stop_loss"] = stop_loss
            
        if take_profit is not None:
            signal_data["take_profit"] = take_profit
            
        # Add any additional data
        if data:
            signal_data.update(data)
            
        super().__init__(EventType.SIGNAL_GENERATED, signal_data)

# Safety events
class EmergencyStopEvent(Event):
    """Emergency stop event."""
    
    def __init__(
        self,
        activated: bool,
        reason: str,
        activated_by: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an emergency stop event.
        
        Args:
            activated: True if activated, False if deactivated
            reason: Reason for activation/deactivation
            activated_by: Who/what activated the emergency stop
            data: Additional event data
        """
        event_type = EventType.EMERGENCY_STOP_ACTIVATED if activated else EventType.EMERGENCY_STOP_DEACTIVATED
        
        stop_data = {
            "reason": reason,
            "activated_by": activated_by
        }
        
        if data:
            stop_data.update(data)
            
        super().__init__(event_type, stop_data)

class CircuitBreakerEvent(Event):
    """Circuit breaker event."""
    
    def __init__(
        self,
        breaker_id: str,
        triggered: bool,
        threshold: str,
        current_value: str,
        reset_time: Optional[datetime] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a circuit breaker event.
        
        Args:
            breaker_id: ID of the circuit breaker
            triggered: True if triggered, False if reset
            threshold: Threshold value that was crossed
            current_value: Current value that triggered the breaker
            reset_time: When the breaker will reset (if applicable)
            data: Additional event data
        """
        event_type = EventType.CIRCUIT_BREAKER_TRIGGERED if triggered else EventType.CIRCUIT_BREAKER_RESET
        
        breaker_data = {
            "breaker_id": breaker_id,
            "threshold": threshold,
            "current_value": current_value
        }
        
        if reset_time:
            breaker_data["reset_time"] = reset_time.isoformat()
            
        if data:
            breaker_data.update(data)
            
        super().__init__(event_type, breaker_data) 
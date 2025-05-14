"""
Trading system safety guardrails package.

This package contains components that enforce safety guardrails for the trading system:
- Circuit breakers to prevent excessive losses
- Cooldown periods to enforce pauses after consecutive losses
- Emergency stop functionality for immediate trading halt
- Trading mode control (live vs paper trading)
"""

from trading_bot.core.safety.circuit_breakers import CircuitBreakerManager
from trading_bot.core.safety.cooldown import CooldownManager
from trading_bot.core.safety.emergency_stop import EmergencyStopManager
from trading_bot.core.safety.trading_mode import TradingModeManager
from trading_bot.core.safety.safety_manager import SafetyManager, SafetyEvent

__all__ = [
    'CircuitBreakerManager',
    'CooldownManager',
    'EmergencyStopManager',
    'TradingModeManager',
    'SafetyManager',
    'SafetyEvent'
]

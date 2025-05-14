"""
Alerts package for BensBot.

This package provides alert and notification services:
- Email notifications
- Telegram messages
- Webhook calls
- Prometheus metrics
"""

from trading_bot.core.alerts.alert_service import AlertService, AlertLevel, AlertChannel
from trading_bot.core.alerts.monitoring import MetricsExporter, EnhancedAlertService

__all__ = [
    "AlertService",
    "AlertLevel",
    "AlertChannel",
    "MetricsExporter",
    "EnhancedAlertService"
] 
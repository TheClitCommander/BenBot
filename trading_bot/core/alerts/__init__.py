"""
Trading system alerting module.

This module provides functionality for sending alerts through various channels:
- Telegram messages
- Email notifications
- Webhook triggers
"""

from trading_bot.core.alerts.alert_service import AlertService, AlertLevel, AlertChannel

__all__ = ["AlertService", "AlertLevel", "AlertChannel"] 
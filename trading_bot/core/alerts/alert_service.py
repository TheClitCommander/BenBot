"""
Alert service for the trading system.

This module provides the AlertService class that handles:
- Sending Telegram notifications
- Sending email alerts
- Triggering webhooks
"""

import os
import logging
import json
import enum
import smtplib
import ssl
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable

# Configure logging
logger = logging.getLogger(__name__)

class AlertLevel(enum.Enum):
    """Alert importance levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertChannel(enum.Enum):
    """Available alert delivery channels."""
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
    CONSOLE = "CONSOLE"  # For debugging/development

class AlertService:
    """
    Service for sending alerts through various channels.
    
    This service can send notifications via:
    - Telegram messages
    - Email
    - Webhooks
    - Console logging (for development)
    """
    
    def __init__(
        self,
        config_path: str = "./config/alerts.json",
        telegram_token: Optional[str] = None,
        telegram_chat_ids: Optional[List[str]] = None,
        email_sender: Optional[str] = None,
        email_password: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        webhook_urls: Optional[Dict[str, str]] = None,
        min_level: AlertLevel = AlertLevel.INFO,
        enabled_channels: Optional[List[AlertChannel]] = None,
        callback: Optional[Callable[[str, AlertLevel, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the alert service.
        
        Args:
            config_path: Path to the alerts configuration file
            telegram_token: Telegram bot token (overrides config)
            telegram_chat_ids: List of Telegram chat IDs to send to (overrides config)
            email_sender: Email sender address (overrides config)
            email_password: Email sender password (overrides config)
            email_recipients: List of email recipients (overrides config)
            webhook_urls: Dict of webhook names and URLs (overrides config)
            min_level: Minimum alert level to send
            enabled_channels: List of enabled alert channels (default: all)
            callback: Optional callback function for alert handling
        """
        self.config_path = config_path
        self.min_level = min_level
        self.callback = callback
        
        # Load default config (if file exists)
        self.config = self._load_config()
        
        # Apply supplied parameters (override config)
        if telegram_token:
            self.config["telegram"]["token"] = telegram_token
        if telegram_chat_ids:
            self.config["telegram"]["chat_ids"] = telegram_chat_ids
        if email_sender:
            self.config["email"]["sender"] = email_sender
        if email_password:
            self.config["email"]["password"] = email_password
        if email_recipients:
            self.config["email"]["recipients"] = email_recipients
        if webhook_urls:
            self.config["webhooks"]["urls"] = webhook_urls
        
        # Set enabled channels
        self.enabled_channels = enabled_channels or [
            AlertChannel.TELEGRAM,
            AlertChannel.EMAIL,
            AlertChannel.WEBHOOK,
            AlertChannel.CONSOLE
        ]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration from file."""
        default_config = {
            "telegram": {
                "enabled": False,
                "token": "",
                "chat_ids": []
            },
            "email": {
                "enabled": False,
                "sender": "",
                "password": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "recipients": []
            },
            "webhooks": {
                "enabled": False,
                "urls": {}
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    merged_config = default_config.copy()
                    for section in config:
                        if section in merged_config:
                            merged_config[section].update(config[section])
                    return merged_config
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default alert config at {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading alert config: {e}")
        
        return default_config
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved alert config to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving alert config: {e}")
            return False
    
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> Dict[AlertChannel, bool]:
        """
        Send an alert through configured channels.
        
        Args:
            message: The alert message
            level: Alert importance level
            data: Additional structured data for the alert
            channels: Specific channels to use (default: all enabled)
            
        Returns:
            Dict with results for each channel
        """
        # Skip if below minimum level
        if level.value < self.min_level.value:
            return {channel: False for channel in (channels or self.enabled_channels)}
        
        # Add timestamp to data
        alert_data = data or {}
        alert_data["timestamp"] = datetime.utcnow().isoformat()
        alert_data["level"] = level.value
        
        # Determine which channels to use
        channels_to_use = channels or self.enabled_channels
        
        # Send through each channel
        results = {}
        
        for channel in channels_to_use:
            if channel == AlertChannel.TELEGRAM and self.config["telegram"]["enabled"]:
                results[channel] = self._send_telegram(message, level, alert_data)
            elif channel == AlertChannel.EMAIL and self.config["email"]["enabled"]:
                results[channel] = self._send_email(message, level, alert_data)
            elif channel == AlertChannel.WEBHOOK and self.config["webhooks"]["enabled"]:
                results[channel] = self._send_webhook(message, level, alert_data)
            elif channel == AlertChannel.CONSOLE:
                results[channel] = self._log_console(message, level, alert_data)
        
        # Call the callback if set
        if self.callback:
            try:
                self.callback(message, level, alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        return results
    
    def _send_telegram(self, message: str, level: AlertLevel, data: Dict[str, Any]) -> bool:
        """Send alert via Telegram."""
        try:
            token = self.config["telegram"]["token"]
            chat_ids = self.config["telegram"]["chat_ids"]
            
            if not token or not chat_ids:
                logger.warning("Telegram not configured with token and chat_ids")
                return False
            
            # Format message with level emoji
            emoji = "🔵" if level == AlertLevel.INFO else "🟠" if level == AlertLevel.WARNING else "🔴"
            formatted_message = f"{emoji} *{level.value}*: {message}\n\n"
            
            # Add timestamp in readable format
            formatted_message += f"🕒 {datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            
            # Add data if present
            if data and data.keys() - {'timestamp', 'level'}:
                formatted_message += "📊 *Details:*\n"
                for key, value in data.items():
                    if key not in {'timestamp', 'level'}:
                        formatted_message += f"• {key}: {value}\n"
            
            # Send to all chat IDs
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": formatted_message,
                    "parse_mode": "Markdown"
                }
                response = requests.post(url, json=payload)
                response.raise_for_status()
            
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    def _send_email(self, message: str, level: AlertLevel, data: Dict[str, Any]) -> bool:
        """Send alert via email."""
        try:
            sender = self.config["email"]["sender"]
            password = self.config["email"]["password"]
            recipients = self.config["email"]["recipients"]
            smtp_server = self.config["email"]["smtp_server"]
            smtp_port = self.config["email"]["smtp_port"]
            
            if not sender or not password or not recipients:
                logger.warning("Email not configured with sender, password, and recipients")
                return False
            
            # Create email
            email = MIMEMultipart("alternative")
            email["Subject"] = f"[BensBot] {level.value} Alert: {message[:50]}..."
            email["From"] = sender
            email["To"] = ", ".join(recipients)
            
            # Create HTML content
            level_color = "#3498db" if level == AlertLevel.INFO else "#f39c12" if level == AlertLevel.WARNING else "#e74c3c"
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: {level_color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                    .content {{ border: 1px solid #ddd; border-top: none; padding: 15px; border-radius: 0 0 5px 5px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                    .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                    .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .data-table th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{level.value} Alert</h2>
                    </div>
                    <div class="content">
                        <p><strong>Message:</strong> {message}</p>
                        <p><strong>Time:</strong> {datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        
                        <h3>Details</h3>
                        <table class="data-table">
                            <tr>
                                <th>Property</th>
                                <th>Value</th>
                            </tr>
            """
            
            # Add data rows
            for key, value in data.items():
                if key not in {'timestamp', 'level'}:
                    html += f"""
                            <tr>
                                <td>{key}</td>
                                <td>{value}</td>
                            </tr>
                    """
            
            # Close HTML
            html += """
                        </table>
                    </div>
                    <div class="footer">
                        <p>This is an automated alert from BensBot Trading System.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach parts
            text_part = MIMEText(f"{level.value} Alert: {message}\n\nTime: {data['timestamp']}\n\nDetails: {data}", "plain")
            html_part = MIMEText(html, "html")
            email.attach(text_part)
            email.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender, password)
                server.sendmail(sender, recipients, email.as_string())
            
            return True
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def _send_webhook(self, message: str, level: AlertLevel, data: Dict[str, Any]) -> bool:
        """Send alert via webhook."""
        try:
            webhook_urls = self.config["webhooks"]["urls"]
            
            if not webhook_urls:
                logger.warning("No webhook URLs configured")
                return False
            
            # Prepare payload
            payload = {
                "message": message,
                "level": level.value,
                "timestamp": data["timestamp"],
                "data": {k: v for k, v in data.items() if k not in {'timestamp', 'level'}}
            }
            
            # Send to all webhook URLs
            results = []
            for name, url in webhook_urls.items():
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    results.append(True)
                except Exception as e:
                    logger.error(f"Error sending to webhook {name}: {e}")
                    results.append(False)
            
            return any(results) if results else False
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return False
    
    def _log_console(self, message: str, level: AlertLevel, data: Dict[str, Any]) -> bool:
        """Log alert to console (useful for development)."""
        try:
            log_level = logging.INFO if level == AlertLevel.INFO else logging.WARNING if level == AlertLevel.WARNING else logging.ERROR
            
            logger.log(log_level, f"ALERT [{level.value}]: {message}")
            if data and data.keys() - {'timestamp', 'level'}:
                details = {k: v for k, v in data.items() if k not in {'timestamp', 'level'}}
                logger.log(log_level, f"ALERT DETAILS: {details}")
            
            return True
        except Exception as e:
            logger.error(f"Error logging alert to console: {e}")
            return False
    
    def configure_telegram(self, token: str, chat_ids: List[str], enabled: bool = True) -> bool:
        """Configure Telegram alerts."""
        try:
            self.config["telegram"]["token"] = token
            self.config["telegram"]["chat_ids"] = chat_ids
            self.config["telegram"]["enabled"] = enabled
            return self.save_config()
        except Exception as e:
            logger.error(f"Error configuring Telegram: {e}")
            return False
    
    def configure_email(
        self,
        sender: str,
        password: str,
        recipients: List[str],
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        enabled: bool = True
    ) -> bool:
        """Configure email alerts."""
        try:
            self.config["email"]["sender"] = sender
            self.config["email"]["password"] = password
            self.config["email"]["recipients"] = recipients
            self.config["email"]["smtp_server"] = smtp_server
            self.config["email"]["smtp_port"] = smtp_port
            self.config["email"]["enabled"] = enabled
            return self.save_config()
        except Exception as e:
            logger.error(f"Error configuring email: {e}")
            return False
    
    def configure_webhook(self, webhook_urls: Dict[str, str], enabled: bool = True) -> bool:
        """Configure webhook alerts."""
        try:
            self.config["webhooks"]["urls"] = webhook_urls
            self.config["webhooks"]["enabled"] = enabled
            return self.save_config()
        except Exception as e:
            logger.error(f"Error configuring webhooks: {e}")
            return False
    
    def is_channel_configured(self, channel: AlertChannel) -> bool:
        """Check if a channel is properly configured."""
        if channel == AlertChannel.TELEGRAM:
            return (self.config["telegram"]["enabled"] and 
                    self.config["telegram"]["token"] and 
                    self.config["telegram"]["chat_ids"])
        elif channel == AlertChannel.EMAIL:
            return (self.config["email"]["enabled"] and 
                    self.config["email"]["sender"] and 
                    self.config["email"]["password"] and 
                    self.config["email"]["recipients"])
        elif channel == AlertChannel.WEBHOOK:
            return (self.config["webhooks"]["enabled"] and 
                    bool(self.config["webhooks"]["urls"]))
        elif channel == AlertChannel.CONSOLE:
            return True
        return False 
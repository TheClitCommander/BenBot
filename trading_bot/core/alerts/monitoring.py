"""
Enhanced Monitoring and Logging for BensBot.

This module extends the AlertService with:
1. Prometheus metrics export
2. Integration with monitoring tools
3. Additional alerting channels
"""

import logging
import os
import time
import json
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime
import threading

from trading_bot.core.alerts.alert_service import AlertService, AlertLevel, AlertChannel

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class MetricsExporter:
    """
    Exports metrics for monitoring systems like Prometheus.
    """
    
    def __init__(
        self,
        export_prometheus: bool = True,
        prometheus_port: int = 8000,
        metrics_prefix: str = "bensbot",
        enable_http_server: bool = True,
        metrics_dir: str = "./data/metrics"
    ):
        """
        Initialize the metrics exporter.
        
        Args:
            export_prometheus: Whether to export Prometheus metrics
            prometheus_port: Port for the Prometheus HTTP server
            metrics_prefix: Prefix for metrics names
            enable_http_server: Whether to start the Prometheus HTTP server
            metrics_dir: Directory for storing metrics files
        """
        self.export_prometheus = export_prometheus and PROMETHEUS_AVAILABLE
        self.prometheus_port = prometheus_port
        self.metrics_prefix = metrics_prefix
        self.enable_http_server = enable_http_server
        self.metrics_dir = metrics_dir
        
        # Create metrics directory
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Initialize counters
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        
        # Initialize Prometheus metrics if available
        if self.export_prometheus:
            if not PROMETHEUS_AVAILABLE:
                logger.warning("Prometheus client not available. Install with: pip install prometheus-client")
            else:
                self._init_prometheus_metrics()
                
                # Start HTTP server if enabled
                if self.enable_http_server:
                    try:
                        start_http_server(self.prometheus_port)
                        logger.info(f"Prometheus HTTP server started on port {self.prometheus_port}")
                    except Exception as e:
                        logger.error(f"Failed to start Prometheus HTTP server: {e}")
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # Trading metrics
        self.gauges["active_strategies"] = Gauge(
            f"{self.metrics_prefix}_active_strategies",
            "Number of active trading strategies",
            ["asset_class"]
        )
        
        self.counters["trades_executed"] = Counter(
            f"{self.metrics_prefix}_trades_executed_total",
            "Total number of trades executed",
            ["asset_class", "strategy_type", "result"]
        )
        
        self.counters["strategy_errors"] = Counter(
            f"{self.metrics_prefix}_strategy_errors_total",
            "Total number of strategy errors",
            ["asset_class", "strategy_type", "error_type"]
        )
        
        self.gauges["portfolio_value"] = Gauge(
            f"{self.metrics_prefix}_portfolio_value",
            "Current portfolio value",
            ["asset_class"]
        )
        
        self.histograms["trade_pnl"] = Histogram(
            f"{self.metrics_prefix}_trade_pnl",
            "Trade profit and loss distribution",
            ["asset_class", "strategy_type"],
            buckets=[-10.0, -5.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # System metrics
        self.gauges["system_status"] = Gauge(
            f"{self.metrics_prefix}_system_status",
            "System operational status (1=operational, 0=issue)",
            ["component"]
        )
        
        self.counters["alerts_sent"] = Counter(
            f"{self.metrics_prefix}_alerts_sent_total",
            "Total number of alerts sent",
            ["level", "channel"]
        )
    
    def record_trade(
        self,
        asset_class: str,
        strategy_type: str,
        strategy_id: str,
        result: str,
        pnl: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a trade execution.
        
        Args:
            asset_class: Asset class of the trade
            strategy_type: Type of strategy
            strategy_id: Strategy ID
            result: Result of the trade ('win', 'loss', 'scratch')
            pnl: Profit/loss of the trade (percentage)
            metadata: Additional trade metadata
        """
        if not self.export_prometheus:
            return
            
        try:
            # Increment trade counter
            self.counters["trades_executed"].labels(
                asset_class=asset_class,
                strategy_type=strategy_type,
                result=result
            ).inc()
            
            # Record PnL in histogram
            self.histograms["trade_pnl"].labels(
                asset_class=asset_class,
                strategy_type=strategy_type
            ).observe(pnl)
            
            # Store trade in metrics file
            self._store_metric("trades", {
                "timestamp": datetime.now().isoformat(),
                "asset_class": asset_class,
                "strategy_type": strategy_type,
                "strategy_id": strategy_id,
                "result": result,
                "pnl": pnl,
                **metadata or {}
            })
        except Exception as e:
            logger.error(f"Error recording trade metric: {e}")
    
    def update_portfolio_value(
        self,
        asset_class: str,
        value: float
    ) -> None:
        """
        Update portfolio value metric.
        
        Args:
            asset_class: Asset class
            value: Portfolio value
        """
        if not self.export_prometheus:
            return
            
        try:
            self.gauges["portfolio_value"].labels(
                asset_class=asset_class
            ).set(value)
        except Exception as e:
            logger.error(f"Error updating portfolio value metric: {e}")
    
    def update_active_strategies(
        self,
        asset_class: str,
        count: int
    ) -> None:
        """
        Update active strategies count.
        
        Args:
            asset_class: Asset class
            count: Number of active strategies
        """
        if not self.export_prometheus:
            return
            
        try:
            self.gauges["active_strategies"].labels(
                asset_class=asset_class
            ).set(count)
        except Exception as e:
            logger.error(f"Error updating active strategies metric: {e}")
    
    def record_strategy_error(
        self,
        asset_class: str,
        strategy_type: str,
        error_type: str
    ) -> None:
        """
        Record a strategy error.
        
        Args:
            asset_class: Asset class
            strategy_type: Strategy type
            error_type: Type of error
        """
        if not self.export_prometheus:
            return
            
        try:
            self.counters["strategy_errors"].labels(
                asset_class=asset_class,
                strategy_type=strategy_type,
                error_type=error_type
            ).inc()
        except Exception as e:
            logger.error(f"Error recording strategy error metric: {e}")
    
    def record_alert_sent(
        self,
        level: AlertLevel,
        channel: AlertChannel
    ) -> None:
        """
        Record an alert being sent.
        
        Args:
            level: Alert level
            channel: Alert channel
        """
        if not self.export_prometheus:
            return
            
        try:
            self.counters["alerts_sent"].labels(
                level=level.value,
                channel=channel.value
            ).inc()
        except Exception as e:
            logger.error(f"Error recording alert metric: {e}")
    
    def set_system_status(
        self,
        component: str,
        status: bool
    ) -> None:
        """
        Set system operational status.
        
        Args:
            component: System component
            status: Operational status (True=operational, False=issue)
        """
        if not self.export_prometheus:
            return
            
        try:
            self.gauges["system_status"].labels(
                component=component
            ).set(1 if status else 0)
        except Exception as e:
            logger.error(f"Error setting system status metric: {e}")
    
    def _store_metric(self, metric_type: str, data: Dict[str, Any]) -> None:
        """
        Store a metric in a file for persistence.
        
        Args:
            metric_type: Type of metric
            data: Metric data
        """
        try:
            # Create directory if it doesn't exist
            metric_dir = os.path.join(self.metrics_dir, metric_type)
            os.makedirs(metric_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{metric_type}_{timestamp}.jsonl"
            file_path = os.path.join(metric_dir, filename)
            
            # Append to file
            with open(file_path, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.error(f"Error storing metric: {e}")

class EnhancedAlertService:
    """
    Enhanced alert service with additional features:
    1. Integration with metrics
    2. Support for Slack and Discord
    3. Rate limiting and batching
    """
    
    def __init__(
        self,
        alert_service: AlertService,
        metrics_exporter: Optional[MetricsExporter] = None,
        slack_webhook: Optional[str] = None,
        discord_webhook: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enhanced alert service.
        
        Args:
            alert_service: Base alert service
            metrics_exporter: Metrics exporter
            slack_webhook: Slack webhook URL
            discord_webhook: Discord webhook URL
            config: Additional configuration
        """
        self.alert_service = alert_service
        self.metrics_exporter = metrics_exporter
        self.config = config or {}
        
        # Configure additional channels
        self.slack_webhook = slack_webhook
        self.discord_webhook = discord_webhook
        
        # Rate limiting
        self.rate_limit_window = self.config.get("rate_limit_window", 60)  # 1 minute
        self.max_alerts_per_window = self.config.get("max_alerts_per_window", 10)
        self.recent_alerts: List[Dict[str, Any]] = []
        
        # Alert batching
        self.batching_enabled = self.config.get("batching_enabled", False)
        self.batching_interval = self.config.get("batching_interval", 300)  # 5 minutes
        self.alert_batch: Dict[str, List[Dict[str, Any]]] = {
            AlertLevel.INFO.value: [],
            AlertLevel.WARNING.value: [],
            AlertLevel.CRITICAL.value: []
        }
        self.last_batch_time = datetime.now()
        
        # Start batching thread if enabled
        if self.batching_enabled:
            self.batch_thread = threading.Thread(
                target=self._batch_processing_loop,
                daemon=True
            )
            self.batch_thread.start()
    
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[AlertChannel]] = None,
        skip_batching: bool = False
    ) -> Dict[str, Any]:
        """
        Send an alert through all configured channels.
        
        Args:
            message: Alert message
            level: Alert level
            data: Additional data
            channels: Channels to use (default: all)
            skip_batching: Whether to skip batching for this alert
            
        Returns:
            Dictionary with sending results
        """
        # Check rate limiting
        if self._is_rate_limited():
            logger.warning("Alert rate limited")
            return {"status": "rate_limited", "message": "Too many alerts in time window"}
        
        # Record alert in recent alerts for rate limiting
        self.recent_alerts.append({
            "timestamp": datetime.now(),
            "level": level.value,
            "message": message
        })
        
        # Trim recent alerts list
        self._cleanup_recent_alerts()
        
        # Handle batching
        if self.batching_enabled and not skip_batching and level != AlertLevel.CRITICAL:
            self._add_to_batch(message, level, data)
            
            # Critical alerts are always sent immediately
            if level != AlertLevel.CRITICAL:
                return {"status": "batched", "message": "Alert added to batch"}
        
        # Send through base alert service
        result = self.alert_service.send_alert(message, level, data, channels)
        
        # Send through additional channels
        if self.slack_webhook and (not channels or AlertChannel.WEBHOOK in channels):
            slack_result = self._send_slack_alert(message, level, data)
            result["slack"] = slack_result
        
        if self.discord_webhook and (not channels or AlertChannel.WEBHOOK in channels):
            discord_result = self._send_discord_alert(message, level, data)
            result["discord"] = discord_result
        
        # Record metrics
        if self.metrics_exporter:
            for channel in result.keys():
                if channel in [c.value for c in AlertChannel]:
                    if result[channel]:
                        self.metrics_exporter.record_alert_sent(
                            level=level,
                            channel=AlertChannel(channel)
                        )
        
        return result
    
    def _send_slack_alert(
        self,
        message: str,
        level: AlertLevel,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send alert to Slack webhook."""
        if not self.slack_webhook:
            return False
            
        try:
            import requests
            
            # Determine color based on level
            color = "#3498db" if level == AlertLevel.INFO else "#f39c12" if level == AlertLevel.WARNING else "#e74c3c"
            
            # Create payload
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "pretext": f"*{level.value} Alert*",
                        "text": message,
                        "fields": []
                    }
                ]
            }
            
            # Add fields from data
            if data:
                for key, value in data.items():
                    if key not in {"timestamp", "level"}:
                        payload["attachments"][0]["fields"].append({
                            "title": key,
                            "value": str(value),
                            "short": len(str(value)) < 20
                        })
            
            # Add timestamp
            payload["attachments"][0]["ts"] = int(time.time())
            
            # Send to webhook
            response = requests.post(
                self.slack_webhook,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def _send_discord_alert(
        self,
        message: str,
        level: AlertLevel,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send alert to Discord webhook."""
        if not self.discord_webhook:
            return False
            
        try:
            import requests
            
            # Determine color based on level (Discord uses decimal color codes)
            color = 0x3498db if level == AlertLevel.INFO else 0xf39c12 if level == AlertLevel.WARNING else 0xe74c3c
            
            # Create payload
            payload = {
                "embeds": [
                    {
                        "title": f"{level.value} Alert",
                        "description": message,
                        "color": color,
                        "fields": [],
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            # Add fields from data
            if data:
                for key, value in data.items():
                    if key not in {"timestamp", "level"}:
                        payload["embeds"][0]["fields"].append({
                            "name": key,
                            "value": str(value),
                            "inline": len(str(value)) < 20
                        })
            
            # Send to webhook
            response = requests.post(
                self.discord_webhook,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False
    
    def _is_rate_limited(self) -> bool:
        """Check if alerts are currently rate limited."""
        # Calculate time window
        window_start = datetime.now().timestamp() - self.rate_limit_window
        
        # Count alerts in window
        alerts_in_window = sum(
            1 for alert in self.recent_alerts
            if alert["timestamp"].timestamp() >= window_start
        )
        
        return alerts_in_window >= self.max_alerts_per_window
    
    def _cleanup_recent_alerts(self) -> None:
        """Clean up old alerts from recent alerts list."""
        window_start = datetime.now().timestamp() - self.rate_limit_window
        self.recent_alerts = [
            alert for alert in self.recent_alerts
            if alert["timestamp"].timestamp() >= window_start
        ]
    
    def _add_to_batch(
        self,
        message: str,
        level: AlertLevel,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an alert to the batch."""
        self.alert_batch[level.value].append({
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def _batch_processing_loop(self) -> None:
        """Process batched alerts periodically."""
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                now = datetime.now()
                elapsed = (now - self.last_batch_time).total_seconds()
                
                if elapsed >= self.batching_interval:
                    self._process_alert_batch()
                    self.last_batch_time = now
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
    
    def _process_alert_batch(self) -> None:
        """Process and send batched alerts."""
        for level_str, alerts in self.alert_batch.items():
            if not alerts:
                continue
                
            level = AlertLevel(level_str)
            
            # Group alerts by type
            alert_groups: Dict[str, List[Dict[str, Any]]] = {}
            for alert in alerts:
                # Create a simple type based on the first few words of the message
                words = alert["message"].split()[:3]
                alert_type = " ".join(words)
                
                if alert_type not in alert_groups:
                    alert_groups[alert_type] = []
                    
                alert_groups[alert_type].append(alert)
            
            # Send summary for each group
            for alert_type, group_alerts in alert_groups.items():
                if len(group_alerts) == 1:
                    # Just send the single alert directly
                    alert = group_alerts[0]
                    self.send_alert(
                        message=alert["message"],
                        level=level,
                        data=alert["data"],
                        skip_batching=True
                    )
                else:
                    # Send a summary
                    summary_message = f"{len(group_alerts)} similar alerts of type '{alert_type}'"
                    summary_data = {
                        "alert_count": len(group_alerts),
                        "alert_type": alert_type,
                        "first_timestamp": group_alerts[0]["timestamp"],
                        "last_timestamp": group_alerts[-1]["timestamp"],
                        "examples": [a["message"] for a in group_alerts[:3]]
                    }
                    
                    self.send_alert(
                        message=summary_message,
                        level=level,
                        data=summary_data,
                        skip_batching=True
                    )
            
            # Clear the batch for this level
            self.alert_batch[level_str] = [] 
"""
System Health Monitor for BensBot.

This daemon continuously monitors system health, data feed quality,
and execution loop performance to ensure reliable operation.
"""

import logging
import time
import threading
import os
import json
import signal
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable

from trading_bot.core.alerts.alert_service import AlertService, AlertLevel
from trading_bot.core.alerts.monitoring import MetricsExporter

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """
    Monitors critical system components and alerts on issues.
    """
    
    def __init__(
        self,
        alert_service: Optional[AlertService] = None,
        metrics_exporter: Optional[MetricsExporter] = None,
        config_path: str = "./config/health_monitor.json",
        health_check_interval: int = 60,  # seconds
        data_dir: str = "./data/health_monitor"
    ):
        """Initialize the system health monitor."""
        self.alert_service = alert_service
        self.metrics_exporter = metrics_exporter
        self.config_path = config_path
        self.health_check_interval = health_check_interval
        self.data_dir = data_dir
        
        # Load config
        self.config = self._load_config()
        
        # Runtime state
        self.running = False
        self.monitor_thread = None
        self.last_check_time = datetime.now()
        
        # Component status tracking
        self.component_status = {}
        self.data_feed_latency = {}
        self.execution_loop_stats = {}
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "components": {
                "data_feed": {
                    "enabled": True,
                    "max_latency_ms": 5000,
                    "check_interval_sec": 120,
                    "data_sources": ["alpaca", "yahoo", "binance"]
                },
                "strategy_execution": {
                    "enabled": True,
                    "max_cycle_time_ms": 2000,
                    "min_cycles_per_minute": 1
                },
                "portfolio_allocation": {
                    "enabled": True,
                    "max_cycle_time_ms": 5000,
                    "check_interval_sec": 300
                },
                "disk_space": {
                    "enabled": True,
                    "min_free_space_mb": 1000,
                    "check_interval_sec": 3600
                },
                "memory_usage": {
                    "enabled": True,
                    "max_usage_percent": 85,
                    "check_interval_sec": 300
                }
            },
            "actions": {
                "auto_restart_on_failure": False,
                "max_restart_attempts": 3,
                "cool_down_period_sec": 300
            },
            "reporting": {
                "log_to_file": True,
                "report_interval_sec": 3600,
                "keep_history_days": 7
            },
            "alerts": {
                "levels": {
                    "data_feed_latency": "WARNING",
                    "strategy_execution_delay": "WARNING",
                    "disk_space_low": "WARNING",
                    "memory_usage_high": "WARNING",
                    "component_failure": "CRITICAL"
                }
            }
        }
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for section in default_config:
                        if section in config:
                            for key in default_config[section]:
                                if key not in config[section]:
                                    config[section][key] = default_config[section][key]
                        else:
                            config[section] = default_config[section]
                    return config
            except Exception as e:
                logger.error(f"Error loading health monitor config: {e}")
        
        # Create default config file
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default health monitor config at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
        
        return default_config
    
    def start(self) -> bool:
        """
        Start the health monitoring thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Health monitor already running")
            return False
        
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("System health monitor started")
        return True
    
    def stop(self) -> bool:
        """
        Stop the health monitoring thread.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Health monitor not running")
            return False
        
        self.running = False
        
        # Wait for thread to exit
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)
        
        logger.info("System health monitor stopped")
        return True
    
    def _handle_shutdown(self, signum, frame):
        """Handle system shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down health monitor")
        self.stop()
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        while self.running:
            try:
                # Run health checks
                self._check_system_health()
                
                # Run component-specific checks based on their intervals
                self._run_scheduled_checks()
                
                # Save current status
                self._save_health_status()
                
                # Generate periodic report if needed
                self._generate_report_if_needed()
                
                # Sleep until next check
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(60)  # Shorter sleep on error
    
    def _check_system_health(self) -> None:
        """Check overall system health."""
        now = datetime.now()
        self.last_check_time = now
        
        # Basic system metrics
        self._check_disk_space()
        self._check_memory_usage()
        self._check_cpu_usage()
        
        # Update metrics if exporter is available
        if self.metrics_exporter:
            for component, status in self.component_status.items():
                self.metrics_exporter.set_system_status(
                    component=component,
                    status=status.get("healthy", False)
                )
    
    def _run_scheduled_checks(self) -> None:
        """Run component checks based on their scheduled intervals."""
        now = datetime.now()
        
        # Check data feed if enabled
        if self.config["components"]["data_feed"]["enabled"]:
            check_interval = self.config["components"]["data_feed"]["check_interval_sec"]
            last_check = self.component_status.get("data_feed", {}).get("last_check_time")
            
            if not last_check or (now - last_check).total_seconds() >= check_interval:
                self._check_data_feed_latency()
        
        # Check portfolio allocation if enabled
        if self.config["components"]["portfolio_allocation"]["enabled"]:
            check_interval = self.config["components"]["portfolio_allocation"]["check_interval_sec"]
            last_check = self.component_status.get("portfolio_allocation", {}).get("last_check_time")
            
            if not last_check or (now - last_check).total_seconds() >= check_interval:
                self._check_portfolio_allocation()
    
    def _check_disk_space(self) -> None:
        """Check available disk space."""
        if not self.config["components"]["disk_space"]["enabled"]:
            return
            
        try:
            # Get disk usage statistics
            import shutil
            total, used, free = shutil.disk_usage("/")
            
            # Convert to MB
            free_mb = free / (1024 * 1024)
            min_free_mb = self.config["components"]["disk_space"]["min_free_space_mb"]
            
            # Check if we're below threshold
            is_healthy = free_mb >= min_free_mb
            usage_percent = (used / total) * 100
            
            # Update status
            self.component_status["disk_space"] = {
                "healthy": is_healthy,
                "free_mb": free_mb,
                "usage_percent": usage_percent,
                "last_check_time": datetime.now()
            }
            
            # Alert if unhealthy
            if not is_healthy:
                self._send_alert(
                    "disk_space_low",
                    f"Low disk space: {free_mb:.2f}MB free (minimum: {min_free_mb}MB)",
                    {"free_mb": free_mb, "usage_percent": usage_percent}
                )
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            self.component_status["disk_space"] = {
                "healthy": False,
                "error": str(e),
                "last_check_time": datetime.now()
            }
    
    def _check_memory_usage(self) -> None:
        """Check memory usage."""
        if not self.config["components"]["memory_usage"]["enabled"]:
            return
            
        try:
            # Get memory usage
            import psutil
            memory = psutil.virtual_memory()
            
            # Check if we're below threshold
            max_usage_percent = self.config["components"]["memory_usage"]["max_usage_percent"]
            is_healthy = memory.percent < max_usage_percent
            
            # Update status
            self.component_status["memory_usage"] = {
                "healthy": is_healthy,
                "usage_percent": memory.percent,
                "available_mb": memory.available / (1024 * 1024),
                "last_check_time": datetime.now()
            }
            
            # Alert if unhealthy
            if not is_healthy:
                self._send_alert(
                    "memory_usage_high",
                    f"High memory usage: {memory.percent:.1f}% (maximum: {max_usage_percent}%)",
                    {"usage_percent": memory.percent, "available_mb": memory.available / (1024 * 1024)}
                )
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            self.component_status["memory_usage"] = {
                "healthy": False,
                "error": str(e),
                "last_check_time": datetime.now()
            }
    
    def _check_cpu_usage(self) -> None:
        """Check CPU usage."""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Update status
            self.component_status["cpu_usage"] = {
                "healthy": True,  # We just track it, no threshold by default
                "usage_percent": cpu_percent,
                "last_check_time": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error checking CPU usage: {e}")
            self.component_status["cpu_usage"] = {
                "healthy": False,
                "error": str(e),
                "last_check_time": datetime.now()
            }
    
    def _check_data_feed_latency(self) -> None:
        """Check data feed latency."""
        for source in self.config["components"]["data_feed"]["data_sources"]:
            try:
                # Measure response time for the data source
                start_time = time.time()
                
                # Call appropriate data source check function
                if source == "alpaca":
                    latency_ms = self._check_alpaca_latency()
                elif source == "yahoo":
                    latency_ms = self._check_yahoo_latency()
                elif source == "binance":
                    latency_ms = self._check_binance_latency()
                else:
                    logger.warning(f"Unknown data source: {source}")
                    continue
                
                # Update data feed latency
                self.data_feed_latency[source] = {
                    "latency_ms": latency_ms,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Check against threshold
                max_latency = self.config["components"]["data_feed"]["max_latency_ms"]
                is_healthy = latency_ms <= max_latency
                
                # Update status
                self.component_status[f"data_feed_{source}"] = {
                    "healthy": is_healthy,
                    "latency_ms": latency_ms,
                    "last_check_time": datetime.now()
                }
                
                # Alert if unhealthy
                if not is_healthy:
                    self._send_alert(
                        "data_feed_latency",
                        f"High latency for {source} data feed: {latency_ms:.1f}ms (maximum: {max_latency}ms)",
                        {"source": source, "latency_ms": latency_ms}
                    )
            except Exception as e:
                logger.error(f"Error checking {source} data feed: {e}")
                self.component_status[f"data_feed_{source}"] = {
                    "healthy": False,
                    "error": str(e),
                    "last_check_time": datetime.now()
                }
    
    def _check_alpaca_latency(self) -> float:
        """Check Alpaca API latency in milliseconds."""
        try:
            import requests
            
            # Simple check - just get the API status
            start_time = time.time()
            response = requests.get("https://api.alpaca.markets/v2/account/activities", 
                                    headers={"APCA-API-KEY-ID": "demo", "APCA-API-SECRET-KEY": "demo"})
            end_time = time.time()
            
            # Return latency in milliseconds
            return (end_time - start_time) * 1000
        except Exception as e:
            logger.warning(f"Error checking Alpaca latency: {e}")
            return 9999.0  # High value indicates an error
    
    def _check_yahoo_latency(self) -> float:
        """Check Yahoo Finance API latency in milliseconds."""
        try:
            import requests
            
            # Simple check - just get a stock quote
            start_time = time.time()
            response = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d")
            end_time = time.time()
            
            # Return latency in milliseconds
            return (end_time - start_time) * 1000
        except Exception as e:
            logger.warning(f"Error checking Yahoo latency: {e}")
            return 9999.0  # High value indicates an error
    
    def _check_binance_latency(self) -> float:
        """Check Binance API latency in milliseconds."""
        try:
            import requests
            
            # Simple check - just get the server time
            start_time = time.time()
            response = requests.get("https://api.binance.com/api/v3/time")
            end_time = time.time()
            
            # Return latency in milliseconds
            return (end_time - start_time) * 1000
        except Exception as e:
            logger.warning(f"Error checking Binance latency: {e}")
            return 9999.0  # High value indicates an error
    
    def _check_portfolio_allocation(self) -> None:
        """Check portfolio allocation system."""
        try:
            # In a real implementation, you would:
            # 1. Check if allocation cycle is running on schedule
            # 2. Verify allocations sum to expected total
            # 3. Check for any allocation anomalies
            
            # For now, just record that we checked
            self.component_status["portfolio_allocation"] = {
                "healthy": True,
                "last_check_time": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error checking portfolio allocation: {e}")
            self.component_status["portfolio_allocation"] = {
                "healthy": False,
                "error": str(e),
                "last_check_time": datetime.now()
            }
    
    def _send_alert(self, alert_type: str, message: str, data: Dict[str, Any]) -> None:
        """Send an alert through the alert service."""
        if not self.alert_service:
            logger.warning(f"Alert service not available. Alert: {message}")
            return
        
        # Get alert level from config
        level_str = self.config["alerts"]["levels"].get(alert_type, "WARNING")
        level = AlertLevel.WARNING
        
        if level_str == "INFO":
            level = AlertLevel.INFO
        elif level_str == "CRITICAL":
            level = AlertLevel.CRITICAL
        
        # Add timestamp and alert type
        alert_data = {
            **data,
            "alert_type": alert_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send alert
        self.alert_service.send_alert(
            message=message,
            level=level,
            data=alert_data
        )
    
    def _save_health_status(self) -> None:
        """Save current health status to file."""
        try:
            # Generate status report
            status_report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if all(c.get("healthy", False) for c in self.component_status.values()) else "unhealthy",
                "components": self.component_status,
                "data_feed_latency": self.data_feed_latency
            }
            
            # Save to file
            filename = os.path.join(self.data_dir, "current_status.json")
            with open(filename, 'w') as f:
                json.dump(status_report, f, indent=2)
                
            # Also save to timestamped history
            history_dir = os.path.join(self.data_dir, "history")
            os.makedirs(history_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            history_file = os.path.join(history_dir, f"status_{timestamp}.json")
            with open(history_file, 'w') as f:
                json.dump(status_report, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving health status: {e}")
    
    def _generate_report_if_needed(self) -> None:
        """Generate periodic health report if scheduled."""
        now = datetime.now()
        report_interval = self.config["reporting"]["report_interval_sec"]
        last_report = getattr(self, "last_report_time", None)
        
        if not last_report or (now - last_report).total_seconds() >= report_interval:
            self._generate_health_report()
            self.last_report_time = now
    
    def _generate_health_report(self) -> None:
        """Generate a comprehensive health report."""
        try:
            # Get overall system health
            all_healthy = all(c.get("healthy", False) for c in self.component_status.values())
            
            # Generate report content
            report = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy" if all_healthy else "unhealthy",
                "components": {
                    name: {
                        "status": "healthy" if status.get("healthy", False) else "unhealthy",
                        "last_checked": status.get("last_check_time").isoformat() if status.get("last_check_time") else None,
                        **{k: v for k, v in status.items() if k not in {"healthy", "last_check_time"}}
                    }
                    for name, status in self.component_status.items()
                },
                "data_feeds": self.data_feed_latency
            }
            
            # Save report to file
            report_dir = os.path.join(self.data_dir, "reports")
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            report_file = os.path.join(report_dir, f"health_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Generated health report: {report_file}")
            
            # Clean up old reports
            self._cleanup_old_reports()
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
    
    def _cleanup_old_reports(self) -> None:
        """Clean up old reports and history files."""
        try:
            # Get retention period
            keep_days = self.config["reporting"]["keep_history_days"]
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # Clean up history directory
            history_dir = os.path.join(self.data_dir, "history")
            if os.path.exists(history_dir):
                for filename in os.listdir(history_dir):
                    file_path = os.path.join(history_dir, filename)
                    
                    # Check file modification time
                    if os.path.isfile(file_path):
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if mtime < cutoff_date:
                            os.remove(file_path)
            
            # Clean up reports directory
            reports_dir = os.path.join(self.data_dir, "reports")
            if os.path.exists(reports_dir):
                for filename in os.listdir(reports_dir):
                    file_path = os.path.join(reports_dir, filename)
                    
                    # Check file modification time
                    if os.path.isfile(file_path):
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if mtime < cutoff_date:
                            os.remove(file_path)
                            
        except Exception as e:
            logger.error(f"Error cleaning up old reports: {e}")
            
    def register_execution_cycle(self, component_name: str, execution_time_ms: float) -> None:
        """
        Register an execution cycle completion to track performance.
        
        Args:
            component_name: Name of the component (e.g., "strategy_execution")
            execution_time_ms: Time taken to complete the cycle in milliseconds
        """
        if component_name not in self.execution_loop_stats:
            self.execution_loop_stats[component_name] = {
                "cycles": [],
                "last_cycle_time": None,
                "avg_cycle_time_ms": 0.0,
                "max_cycle_time_ms": 0.0,
                "total_cycles": 0
            }
        
        # Add new cycle
        now = datetime.now()
        self.execution_loop_stats[component_name]["cycles"].append({
            "timestamp": now,
            "execution_time_ms": execution_time_ms
        })
        
        # Update statistics
        stats = self.execution_loop_stats[component_name]
        stats["last_cycle_time"] = now
        stats["total_cycles"] += 1
        
        # Keep only recent cycles for average calculation
        recent_cycles = [c for c in stats["cycles"] 
                        if (now - c["timestamp"]).total_seconds() < 3600]  # Last hour
        
        if recent_cycles:
            stats["avg_cycle_time_ms"] = sum(c["execution_time_ms"] for c in recent_cycles) / len(recent_cycles)
            stats["max_cycle_time_ms"] = max(c["execution_time_ms"] for c in recent_cycles)
        
        # Limit list size
        if len(stats["cycles"]) > 1000:
            stats["cycles"] = stats["cycles"][-1000:]
        
        # Check if execution time is too long
        if component_name in self.config["components"] and "max_cycle_time_ms" in self.config["components"][component_name]:
            max_time = self.config["components"][component_name]["max_cycle_time_ms"]
            if execution_time_ms > max_time:
                self._send_alert(
                    "strategy_execution_delay",
                    f"Slow execution cycle for {component_name}: {execution_time_ms:.1f}ms (maximum: {max_time}ms)",
                    {
                        "component": component_name,
                        "execution_time_ms": execution_time_ms,
                        "max_allowed_ms": max_time,
                        "avg_cycle_time_ms": stats["avg_cycle_time_ms"]
                    }
                )
                
                # Update component status
                self.component_status[component_name] = {
                    "healthy": False,
                    "execution_time_ms": execution_time_ms,
                    "avg_cycle_time_ms": stats["avg_cycle_time_ms"],
                    "last_check_time": now
                }
            else:
                # Update component status
                self.component_status[component_name] = {
                    "healthy": True,
                    "execution_time_ms": execution_time_ms,
                    "avg_cycle_time_ms": stats["avg_cycle_time_ms"],
                    "last_check_time": now
                } 
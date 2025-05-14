"""
Live Strategy Guardian for BensBot.

This module provides automatic monitoring of live strategies:
1. Detects underperforming strategies
2. Can automatically disable strategies that exceed risk thresholds
3. Optionally replaces disabled strategies with alternatives
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import threading

from trading_bot.core.alerts.alert_service import AlertService, AlertLevel
from trading_bot.core.portfolio.allocator import PortfolioAllocator

logger = logging.getLogger(__name__)

class LiveStrategyGuardian:
    """
    Guardian component that monitors live strategies and takes
    protective actions when risk thresholds are exceeded.
    """
    
    def __init__(
        self,
        portfolio_allocator: PortfolioAllocator,
        alert_service: Optional[AlertService] = None,
        config: Optional[Dict[str, Any]] = None,
        data_dir: str = "./data/strategy_guardian"
    ):
        """
        Initialize the strategy guardian.
        
        Args:
            portfolio_allocator: Portfolio allocator instance
            alert_service: Alert service for notifications
            config: Configuration dictionary
            data_dir: Directory for storing data
        """
        self.portfolio_allocator = portfolio_allocator
        self.alert_service = alert_service
        self.config = config or {}
        self.data_dir = data_dir
        
        # Default thresholds
        self.max_drawdown_threshold = self.config.get("max_drawdown_threshold", 15.0)  # 15%
        self.consecutive_losses_threshold = self.config.get("consecutive_losses_threshold", 5)
        self.sharpe_ratio_threshold = self.config.get("sharpe_ratio_threshold", 0.0)  # Negative Sharpe is bad
        self.auto_disable = self.config.get("auto_disable", True)
        self.auto_replace = self.config.get("auto_replace", False)
        
        # Tracking for strategies
        self.strategy_monitoring: Dict[str, Dict[str, Any]] = {}
        self.disabled_strategies: Set[str] = set()
        
        # Trading session
        self.session_start = datetime.now()
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = self.config.get("monitor_interval", 15 * 60)  # 15 minutes
    
    def start_monitoring(self) -> bool:
        """
        Start the monitoring thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return False
        
        self.session_start = datetime.now()
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Strategy guardian monitoring started")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop the monitoring thread.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.monitoring_active:
            logger.warning("Monitoring not active")
            return False
        
        self.monitoring_active = False
        
        # Wait for thread to exit
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)
        
        logger.info("Strategy guardian monitoring stopped")
        return True
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        while self.monitoring_active:
            try:
                self.check_all_strategies()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Short sleep on error
    
    def register_strategy(
        self,
        strategy_id: str,
        asset_class: str,
        strategy_type: str,
        initial_performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a strategy for monitoring.
        
        Args:
            strategy_id: Unique identifier for the strategy
            asset_class: Asset class of the strategy
            strategy_type: Type of strategy
            initial_performance: Initial performance metrics
            
        Returns:
            Dictionary with registration status
        """
        # Initialize monitoring record
        monitoring_data = {
            "strategy_id": strategy_id,
            "asset_class": asset_class,
            "strategy_type": strategy_type,
            "registered_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "consecutive_losses": 0,
            "trade_history": [],
            "performance_snapshots": [],
            "warnings": [],
            "status": "active"
        }
        
        # Add initial performance if provided
        if initial_performance:
            monitoring_data["current_performance"] = initial_performance
            monitoring_data["performance_snapshots"].append({
                "timestamp": datetime.now().isoformat(),
                "metrics": initial_performance
            })
        
        # Store in monitoring dict
        self.strategy_monitoring[strategy_id] = monitoring_data
        
        return {
            "status": "success",
            "message": f"Strategy {strategy_id} registered for monitoring",
            "data": monitoring_data
        }
    
    def update_strategy_performance(
        self,
        strategy_id: str,
        performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update performance metrics for a monitored strategy.
        
        Args:
            strategy_id: Strategy ID
            performance: Performance metrics dictionary
            
        Returns:
            Dictionary with update status and thresholds check
        """
        # Check if strategy is being monitored
        if strategy_id not in self.strategy_monitoring:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found in monitoring"
            }
        
        # Update monitoring data
        monitoring_data = self.strategy_monitoring[strategy_id]
        monitoring_data["current_performance"] = performance
        monitoring_data["last_updated"] = datetime.now().isoformat()
        
        # Add to performance history
        monitoring_data["performance_snapshots"].append({
            "timestamp": datetime.now().isoformat(),
            "metrics": performance
        })
        
        # Limit history size
        if len(monitoring_data["performance_snapshots"]) > 100:
            monitoring_data["performance_snapshots"] = monitoring_data["performance_snapshots"][-100:]
        
        # Check thresholds
        threshold_results = self._check_thresholds(strategy_id)
        
        return {
            "status": "success",
            "message": f"Performance updated for {strategy_id}",
            "threshold_check": threshold_results
        }
    
    def record_trade(
        self,
        strategy_id: str,
        trade_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record a trade for a monitored strategy.
        
        Args:
            strategy_id: Strategy ID
            trade_result: Trade result dictionary
            
        Returns:
            Dictionary with update status
        """
        # Check if strategy is being monitored
        if strategy_id not in self.strategy_monitoring:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found in monitoring"
            }
        
        # Update monitoring data
        monitoring_data = self.strategy_monitoring[strategy_id]
        
        # Add trade to history
        trade_data = {
            **trade_result,
            "timestamp": datetime.now().isoformat()
        }
        monitoring_data["trade_history"].append(trade_data)
        
        # Limit history size
        if len(monitoring_data["trade_history"]) > 100:
            monitoring_data["trade_history"] = monitoring_data["trade_history"][-100:]
        
        # Update consecutive losses counter
        pnl = trade_result.get("pnl", 0)
        if pnl < 0:
            monitoring_data["consecutive_losses"] += 1
        else:
            monitoring_data["consecutive_losses"] = 0
        
        # Check thresholds
        threshold_results = self._check_thresholds(strategy_id)
        
        return {
            "status": "success",
            "message": f"Trade recorded for {strategy_id}",
            "consecutive_losses": monitoring_data["consecutive_losses"],
            "threshold_check": threshold_results
        }
    
    def _check_thresholds(self, strategy_id: str) -> Dict[str, Any]:
        """
        Check if strategy has breached any risk thresholds.
        
        Args:
            strategy_id: Strategy ID to check
            
        Returns:
            Dictionary with threshold check results
        """
        monitoring_data = self.strategy_monitoring[strategy_id]
        performance = monitoring_data.get("current_performance", {})
        consecutive_losses = monitoring_data.get("consecutive_losses", 0)
        
        warnings = []
        thresholds_breached = False
        
        # Check maximum drawdown
        max_drawdown = abs(performance.get("max_drawdown", 0))
        if max_drawdown > self.max_drawdown_threshold:
            warnings.append(f"Max drawdown threshold breached: {max_drawdown:.2f}% > {self.max_drawdown_threshold:.2f}%")
            thresholds_breached = True
        
        # Check consecutive losses
        if consecutive_losses >= self.consecutive_losses_threshold:
            warnings.append(f"Consecutive losses threshold breached: {consecutive_losses} >= {self.consecutive_losses_threshold}")
            thresholds_breached = True
        
        # Check Sharpe ratio
        sharpe_ratio = performance.get("sharpe_ratio", 1.0)
        if sharpe_ratio < self.sharpe_ratio_threshold:
            warnings.append(f"Sharpe ratio threshold breached: {sharpe_ratio:.2f} < {self.sharpe_ratio_threshold:.2f}")
            thresholds_breached = True
        
        # Record warnings
        if warnings:
            monitoring_data["warnings"].extend(warnings)
            timestamp = datetime.now().isoformat()
            
            # Send alerts if alert service is available
            if self.alert_service:
                for warning in warnings:
                    self.alert_service.send_alert(
                        message=f"Strategy {strategy_id} warning: {warning}",
                        level=AlertLevel.WARNING,
                        data={
                            "strategy_id": strategy_id,
                            "asset_class": monitoring_data.get("asset_class"),
                            "strategy_type": monitoring_data.get("strategy_type"),
                            "warning": warning,
                            "current_performance": performance
                        }
                    )
            
            # Take action if thresholds breached and auto-disable is enabled
            if thresholds_breached and self.auto_disable:
                self.disable_strategy(strategy_id, reason="; ".join(warnings))
        
        return {
            "strategy_id": strategy_id,
            "thresholds_breached": thresholds_breached,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
    
    def disable_strategy(
        self, 
        strategy_id: str, 
        reason: str = "Manual disable"
    ) -> Dict[str, Any]:
        """
        Disable a strategy.
        
        Args:
            strategy_id: Strategy ID to disable
            reason: Reason for disabling
            
        Returns:
            Dictionary with disable status
        """
        # Check if strategy is being monitored
        if strategy_id not in self.strategy_monitoring:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found in monitoring"
            }
        
        # Check if already disabled
        if strategy_id in self.disabled_strategies:
            return {
                "status": "warning",
                "message": f"Strategy {strategy_id} already disabled"
            }
        
        # Update monitoring status
        monitoring_data = self.strategy_monitoring[strategy_id]
        monitoring_data["status"] = "disabled"
        monitoring_data["disabled_at"] = datetime.now().isoformat()
        monitoring_data["disable_reason"] = reason
        
        # Add to disabled set
        self.disabled_strategies.add(strategy_id)
        
        # Deactivate in portfolio allocator
        try:
            self.portfolio_allocator.set_strategy_active_status(strategy_id, False)
        except Exception as e:
            logger.error(f"Error deactivating strategy in portfolio allocator: {e}")
        
        # Send alert if alert service is available
        if self.alert_service:
            self.alert_service.send_alert(
                message=f"Strategy {strategy_id} disabled: {reason}",
                level=AlertLevel.WARNING,
                data={
                    "strategy_id": strategy_id,
                    "asset_class": monitoring_data.get("asset_class"),
                    "strategy_type": monitoring_data.get("strategy_type"),
                    "disable_reason": reason,
                    "current_performance": monitoring_data.get("current_performance", {})
                }
            )
        
        # Check if we should auto-replace
        replacement_info = None
        if self.auto_replace:
            replacement_info = self._find_replacement_strategy(strategy_id)
        
        return {
            "status": "success",
            "message": f"Strategy {strategy_id} disabled",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "replacement": replacement_info
        }
    
    def _find_replacement_strategy(self, disabled_strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a replacement for a disabled strategy.
        
        Args:
            disabled_strategy_id: ID of the disabled strategy
            
        Returns:
            Replacement strategy information if found, None otherwise
        """
        # Get information about the disabled strategy
        disabled_data = self.strategy_monitoring.get(disabled_strategy_id, {})
        asset_class = disabled_data.get("asset_class")
        strategy_type = disabled_data.get("strategy_type")
        
        if not asset_class or not strategy_type:
            return None
        
        # Find potential replacements of the same asset class and type
        candidates = []
        for s_id, data in self.strategy_monitoring.items():
            if s_id == disabled_strategy_id or s_id in self.disabled_strategies:
                continue
                
            if (data.get("asset_class") == asset_class and 
                data.get("strategy_type") == strategy_type and
                data.get("status") != "disabled"):
                candidates.append((s_id, data))
        
        if not candidates:
            return None
        
        # Sort by performance (using Sharpe ratio as primary metric)
        candidates.sort(
            key=lambda x: x[1].get("current_performance", {}).get("sharpe_ratio", 0),
            reverse=True
        )
        
        # Get best candidate
        best_id, best_data = candidates[0]
        
        # Activate in portfolio allocator if not already active
        try:
            self.portfolio_allocator.set_strategy_active_status(best_id, True)
        except Exception as e:
            logger.error(f"Error activating replacement strategy in portfolio allocator: {e}")
        
        return {
            "strategy_id": best_id,
            "asset_class": best_data.get("asset_class"),
            "strategy_type": best_data.get("strategy_type"),
            "performance": best_data.get("current_performance")
        }
    
    def check_all_strategies(self) -> Dict[str, Any]:
        """
        Check all monitored strategies against thresholds.
        
        Returns:
            Dictionary with check results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "strategies_checked": 0,
            "thresholds_breached": 0,
            "strategies_disabled": 0,
            "detailed_results": {}
        }
        
        for strategy_id in list(self.strategy_monitoring.keys()):
            # Skip already disabled strategies
            if strategy_id in self.disabled_strategies:
                continue
                
            # Check thresholds
            check_result = self._check_thresholds(strategy_id)
            results["strategies_checked"] += 1
            
            if check_result["thresholds_breached"]:
                results["thresholds_breached"] += 1
                
                # Check if strategy was disabled
                if strategy_id in self.disabled_strategies:
                    results["strategies_disabled"] += 1
            
            results["detailed_results"][strategy_id] = check_result
        
        return results
    
    def get_monitoring_status(self, strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get monitoring status for a strategy or all strategies.
        
        Args:
            strategy_id: Optional strategy ID (if None, return all)
            
        Returns:
            Dictionary with monitoring status
        """
        if strategy_id:
            if strategy_id not in self.strategy_monitoring:
                return {
                    "status": "error",
                    "message": f"Strategy {strategy_id} not found in monitoring"
                }
            
            return {
                "status": "success",
                "monitoring_data": self.strategy_monitoring[strategy_id]
            }
        
        # Return summary for all strategies
        active_count = sum(1 for s_id in self.strategy_monitoring if s_id not in self.disabled_strategies)
        disabled_count = len(self.disabled_strategies)
        
        return {
            "status": "success",
            "active_strategies": active_count,
            "disabled_strategies": disabled_count,
            "monitoring_active": self.monitoring_active,
            "session_start": self.session_start.isoformat(),
            "thresholds": {
                "max_drawdown": self.max_drawdown_threshold,
                "consecutive_losses": self.consecutive_losses_threshold,
                "sharpe_ratio": self.sharpe_ratio_threshold
            },
            "auto_disable": self.auto_disable,
            "auto_replace": self.auto_replace
        }
    
    def update_thresholds(
        self,
        max_drawdown: Optional[float] = None,
        consecutive_losses: Optional[int] = None,
        sharpe_ratio: Optional[float] = None,
        auto_disable: Optional[bool] = None,
        auto_replace: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update monitoring thresholds.
        
        Args:
            max_drawdown: Maximum drawdown threshold
            consecutive_losses: Consecutive losses threshold
            sharpe_ratio: Sharpe ratio threshold
            auto_disable: Whether to auto-disable strategies
            auto_replace: Whether to auto-replace disabled strategies
            
        Returns:
            Dictionary with update status
        """
        if max_drawdown is not None:
            self.max_drawdown_threshold = max_drawdown
            
        if consecutive_losses is not None:
            self.consecutive_losses_threshold = consecutive_losses
            
        if sharpe_ratio is not None:
            self.sharpe_ratio_threshold = sharpe_ratio
            
        if auto_disable is not None:
            self.auto_disable = auto_disable
            
        if auto_replace is not None:
            self.auto_replace = auto_replace
        
        return {
            "status": "success",
            "message": "Thresholds updated",
            "current_thresholds": {
                "max_drawdown": self.max_drawdown_threshold,
                "consecutive_losses": self.consecutive_losses_threshold,
                "sharpe_ratio": self.sharpe_ratio_threshold,
                "auto_disable": self.auto_disable,
                "auto_replace": self.auto_replace
            }
        } 
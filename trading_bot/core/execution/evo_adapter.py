"""
Adapter to convert evolved strategies to executable trading instructions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from trading_bot.core.evolution import StrategyGenome

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    Mock Trade Executor class for executing trades.
    In a real implementation, this would connect to exchanges.
    """
    
    def __init__(self):
        self.active_strategies = {}
    
    def register_strategy(self, strategy_id: str, strategy_type: str, parameters: Dict[str, Any]) -> bool:
        """Register a strategy with the executor."""
        self.active_strategies[strategy_id] = {
            "type": strategy_type,
            "parameters": parameters,
            "active": True,
            "registered_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Registered strategy {strategy_id} for execution")
        return True
    
    def unregister_strategy(self, strategy_id: str) -> bool:
        """Unregister a strategy from the executor."""
        if strategy_id in self.active_strategies:
            del self.active_strategies[strategy_id]
            logger.info(f"Unregistered strategy {strategy_id}")
            return True
        return False
    
    def get_active_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get all active strategies."""
        return self.active_strategies

class EvoToExecAdapter:
    """Converts evolved strategies to executable trading instructions."""
    
    def __init__(self, trade_executor: TradeExecutor, evo_trader=None, safety_manager=None):
        """Initialize the adapter with execution and evolution services."""
        self.trade_executor = trade_executor
        self.evo_trader = evo_trader
        self.safety_manager = safety_manager
        self.active_strategies: Dict[str, Any] = {}
    
    def activate_strategy(self, strategy_id: str) -> bool:
        """Activate a strategy for live trading."""
        if not self.evo_trader:
            logger.error("EvoTrader not configured")
            return False
            
        # Check if trading is allowed
        if self.safety_manager:
            trading_allowed, reason = self.safety_manager.check_trading_allowed()
            if not trading_allowed:
                logger.warning(f"Trading not allowed: {reason}")
                return False
            
        strategy = self.evo_trader.get_strategy_details(strategy_id)
        if not strategy:
            logger.error(f"Strategy {strategy_id} not found")
            return False
            
        # Convert to StrategyGenome object if it's a dict
        if isinstance(strategy, dict):
            from trading_bot.core.evolution.evo_trader import StrategyGenome
            strategy = StrategyGenome(**strategy)
        
        # Perform risk checks before activation
        if not self._perform_risk_checks(strategy):
            logger.warning(f"Strategy {strategy_id} failed risk checks")
            return False
        
        # Register with execution engine
        success = self._register_with_executor(strategy)
        if success:
            self.active_strategies[strategy_id] = strategy
            logger.info(f"Strategy {strategy_id} activated for live trading")
            
            # Call notification service
            self._notify_strategy_activation(strategy)
        
        return success
    
    def activate_auto_promoted(self, min_performance: float = 5.0) -> List[str]:
        """Activate auto-promoted strategies meeting minimum performance criteria."""
        if not self.evo_trader:
            logger.error("EvoTrader not configured")
            return []
        
        # Check if trading is allowed
        if self.safety_manager:
            trading_allowed, reason = self.safety_manager.check_trading_allowed()
            if not trading_allowed:
                logger.warning(f"Trading not allowed: {reason}")
                return []    
        
        promoted = self.evo_trader.auto_promote_strategies(min_performance)
        activated_ids = []
        
        for strategy_data in promoted:
            strategy_id = strategy_data.get('id')
            
            # Convert to StrategyGenome if it's a dict
            if isinstance(strategy_data, dict):
                from trading_bot.core.evolution.evo_trader import StrategyGenome
                strategy = StrategyGenome(**strategy_data)
            else:
                strategy = strategy_data
            
            # Perform risk checks before activation
            if not self._perform_risk_checks(strategy):
                logger.warning(f"Strategy {strategy_id} failed risk checks")
                continue
                
            if strategy_id and self.activate_strategy(strategy_id):
                activated_ids.append(strategy_id)
        
        return activated_ids
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """Deactivate a strategy from live trading."""
        if strategy_id not in self.active_strategies:
            logger.warning(f"Strategy {strategy_id} is not active")
            return False
        
        # Unregister from execution engine
        success = self._unregister_from_executor(strategy_id)
        if success:
            del self.active_strategies[strategy_id]
            logger.info(f"Strategy {strategy_id} deactivated from live trading")
        
        return success
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """Get all active strategies."""
        result = []
        for strategy_id, strategy in self.active_strategies.items():
            # Convert to dict if it's a StrategyGenome
            if hasattr(strategy, '__dict__'):
                strategy_data = {k: v for k, v in strategy.__dict__.items()}
            else:
                strategy_data = dict(strategy)
                
            strategy_data["trade_status"] = "active"
            result.append(strategy_data)
            
        return result
    
    def _perform_risk_checks(self, strategy) -> bool:
        """
        Perform risk management checks before strategy activation.
        
        Args:
            strategy: Strategy to check
        
        Returns:
            Boolean indicating whether the strategy passed all risk checks
        """
        try:
            # Get performance metrics if available
            performance = {}
            if hasattr(strategy, 'performance'):
                performance = strategy.performance or {}
            else:
                performance = strategy.get('performance', {})
            
            # Check minimum performance metrics
            total_return = performance.get('total_return', 0)
            if total_return < 5.0:  # Minimum 5% return
                logger.warning(f"Strategy total return {total_return} below minimum threshold")
                return False
            
            # Check maximum drawdown
            max_drawdown = performance.get('max_drawdown', 0)
            if max_drawdown < -25.0:  # Maximum 25% drawdown
                logger.warning(f"Strategy max drawdown {max_drawdown} exceeds threshold")
                return False
            
            # Check Sharpe ratio
            sharpe = performance.get('sharpe_ratio', 0)
            if sharpe < 0.5:  # Minimum Sharpe ratio of 0.5
                logger.warning(f"Strategy Sharpe ratio {sharpe} below minimum threshold")
                return False
            
            # Check win rate
            win_rate = performance.get('win_rate', 0)
            if win_rate < 0.4:  # Minimum 40% win rate
                logger.warning(f"Strategy win rate {win_rate} below minimum threshold")
                return False
            
            # If we made it here, all checks passed
            return True
        except Exception as e:
            logger.error(f"Error during risk checks: {e}")
            return False
    
    def _register_with_executor(self, strategy) -> bool:
        """Register strategy with the execution engine."""
        try:
            # Map strategy parameters to execution parameters
            exec_config = self._map_to_execution_config(strategy)
            
            # Register with executor
            self.trade_executor.register_strategy(
                strategy_id=strategy.id,
                strategy_type=strategy.type,
                parameters=exec_config
            )
            return True
        except Exception as e:
            logger.error(f"Failed to register strategy {strategy.id}: {e}")
            return False
    
    def _unregister_from_executor(self, strategy_id: str) -> bool:
        """Unregister strategy from the execution engine."""
        try:
            self.trade_executor.unregister_strategy(strategy_id)
            return True
        except Exception as e:
            logger.error(f"Failed to unregister strategy {strategy_id}: {e}")
            return False
    
    def _map_to_execution_config(self, strategy) -> Dict[str, Any]:
        """Map strategy genome parameters to execution configuration."""
        # Start with the strategy parameters
        if hasattr(strategy, 'parameters'):
            exec_config = strategy.parameters.copy()
        else:
            exec_config = strategy.get('parameters', {}).copy()
        
        # Add metadata
        if hasattr(strategy, 'id'):
            strategy_id = strategy.id
            strategy_name = strategy.name
            strategy_type = strategy.type
            generation = strategy.generation
        else:
            strategy_id = strategy.get('id', 'unknown')
            strategy_name = strategy.get('name', 'unknown')
            strategy_type = strategy.get('type', 'unknown')
            generation = strategy.get('generation', 0)
            
        exec_config['strategy_name'] = strategy_name
        exec_config['evolved'] = True
        exec_config['evolution_id'] = strategy_id
        exec_config['generation'] = generation
        exec_config['activated_at'] = datetime.utcnow().isoformat()
        
        # Strategy-specific mappings
        if strategy_type == 'mean_reversion':
            # Apply specific mappings for mean reversion
            if 'lookback_period' in exec_config:
                exec_config['lookback'] = exec_config['lookback_period']
            
            # Ensure all parameters are properly set
            exec_config.setdefault('overbought_threshold', 70)
            exec_config.setdefault('oversold_threshold', 30)
            
        elif strategy_type == 'trend_following':
            # Apply specific mappings for trend following
            if 'fast_period' in exec_config and 'slow_period' in exec_config:
                # Ensure proper ordering
                if exec_config['fast_period'] > exec_config['slow_period']:
                    exec_config['fast_period'], exec_config['slow_period'] = \
                        exec_config['slow_period'], exec_config['fast_period']
            
            # Set defaults for trend following
            exec_config.setdefault('trend_strength', 0.2)
            
        elif strategy_type == 'breakout':
            # Apply specific mappings for breakout
            if 'channel_period' in exec_config:
                exec_config['range_period'] = exec_config['channel_period']
            
            # Set defaults for breakout
            exec_config.setdefault('breakout_threshold', 1.5)
        
        # Add safety parameters
        exec_config.setdefault('max_position_size', 0.1)  # Max 10% of capital
        exec_config.setdefault('stop_loss_pct', 2.0)      # 2% stop loss
        exec_config.setdefault('take_profit_pct', 5.0)    # 5% take profit
        
        return exec_config
    
    def _notify_strategy_activation(self, strategy) -> None:
        """Notify about strategy activation via appropriate channels."""
        try:
            from trading_bot.core.alerts import AlertService, AlertLevel
            
            # Import at function level to avoid circular imports
            alert_service = AlertService()
            
            # Prepare strategy details
            if hasattr(strategy, 'id'):
                strategy_id = strategy.id
                strategy_name = strategy.name
                strategy_type = strategy.type
                performance = strategy.performance or {}
            else:
                strategy_id = strategy.get('id', 'unknown')
                strategy_name = strategy.get('name', 'unknown') 
                strategy_type = strategy.get('type', 'unknown')
                performance = strategy.get('performance', {})
            
            # Create alert message
            message = f"Strategy Activated: {strategy_name} (ID: {strategy_id})"
            
            # Add performance details if available
            performance_details = {}
            for key, value in performance.items():
                if isinstance(value, (int, float)):
                    performance_details[key] = f"{value:.2f}" if isinstance(value, float) else str(value)
            
            # Send alert with details
            alert_service.send_alert(
                message=message,
                level=AlertLevel.INFO,
                data={
                    "strategy_id": strategy_id,
                    "strategy_name": strategy_name,
                    "strategy_type": strategy_type,
                    "performance": performance_details,
                    "action": "strategy_activation"
                }
            )
        except Exception as e:
            logger.error(f"Failed to send strategy activation notification: {e}") 
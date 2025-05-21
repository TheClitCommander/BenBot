"""
Strategy Rotator Module.

This module handles dynamic rotation between different trading strategies
based on market conditions and performance metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from trading_bot.strategy.base import Strategy, StrategyConfig, StrategyType
from trading_bot.strategy.ai_sentiment_strategy import AiSentimentStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StrategyRotator")

class StrategyRotator:
    """
    Manages and rotates between multiple trading strategies based on 
    market conditions and performance.
    """
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.active_strategy_id: Optional[str] = None
        self.rotation_history: List[Dict[str, Any]] = []
        logger.info("Strategy Rotator initialized")
    
    def add_strategy(self, strategy: Strategy) -> None:
        """
        Add a strategy to the rotator.
        
        Args:
            strategy: Strategy instance to add
        """
        self.strategies[strategy.id] = strategy
        logger.info(f"Added strategy {strategy.id} ({strategy.name}) to rotator")
        
        # If this is the first strategy or has higher priority, make it active
        if (self.active_strategy_id is None or 
            strategy.priority > self.strategies[self.active_strategy_id].priority):
            self.set_active_strategy(strategy.id)
    
    def register_strategies_from_config(self, configs: List[StrategyConfig]) -> None:
        """
        Register multiple strategies from configuration objects.
        
        Args:
            configs: List of strategy configurations
        """
        for config in configs:
            if not config.enabled:
                logger.info(f"Skipping disabled strategy {config.id}")
                continue
                
            if config.type == StrategyType.REINFORCEMENT_LEARNING:
                # Can be implemented when we have RL strategy
                logger.warning(f"RL strategy type not yet implemented: {config.id}")
            elif config.type == StrategyType.SENTIMENT:
                self.add_strategy(AiSentimentStrategy(config))
            # Add more strategy types as needed
            else:
                logger.warning(f"Unknown strategy type for {config.id}: {config.type}")
    
    def set_active_strategy(self, strategy_id: str) -> bool:
        """
        Set the active strategy by ID.
        
        Args:
            strategy_id: ID of the strategy to activate
            
        Returns:
            True if successful, False otherwise
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
            
        if self.active_strategy_id != strategy_id:
            old_strategy = self.active_strategy_id
            self.active_strategy_id = strategy_id
            
            # Record the rotation in history
            self.rotation_history.append({
                "timestamp": datetime.now().isoformat(),
                "from_strategy": old_strategy,
                "to_strategy": strategy_id,
                "reason": "manual_selection"  # Can be updated for automatic rotation
            })
            
            logger.info(f"Activated strategy: {strategy_id}")
        return True
    
    def evaluate_strategies(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate all strategies against current market data.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with evaluation results for each strategy
        """
        results = {}
        for strategy_id, strategy in self.strategies.items():
            if not strategy.enabled:
                continue
                
            try:
                analysis = strategy.analyze(market_data)
                results[strategy_id] = {
                    "name": strategy.name,
                    "type": strategy.type.value,
                    "analysis": analysis,
                    "is_active": strategy_id == self.active_strategy_id
                }
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy_id}: {e}")
                results[strategy_id] = {
                    "name": strategy.name,
                    "type": strategy.type.value,
                    "error": str(e),
                    "is_active": strategy_id == self.active_strategy_id
                }
                
        return results
    
    def auto_rotate(self, market_data: Dict[str, Any]) -> bool:
        """
        Automatically rotate strategies based on market conditions.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            True if rotation occurred, False otherwise
        """
        if not self.strategies:
            logger.warning("No strategies available for rotation")
            return False
            
        # Evaluate all strategies
        evaluations = self.evaluate_strategies(market_data)
        
        # Simple scoring for now - in production this would be more sophisticated
        best_score = -float('inf')
        best_strategy_id = None
        
        for strategy_id, eval_data in evaluations.items():
            if "error" in eval_data:
                continue
                
            # Extract sentiment or confidence as score
            score = 0
            analysis = eval_data.get("analysis", {})
            
            # For AI sentiment strategy
            if "sentiment" in analysis:
                # Use absolute sentiment as we care about conviction, not direction
                score = abs(analysis["sentiment"]) 
            
            # For other strategies (to be expanded)
            elif "signals" in analysis:
                # Average confidence of signals
                signals = analysis["signals"]
                if signals:
                    score = sum(s.get("confidence", 0) for s in signals) / len(signals)
            
            # Adjust score by strategy priority
            strategy = self.strategies[strategy_id]
            priority_factor = strategy.priority / 100  # Normalize to 0-1
            adjusted_score = score * priority_factor
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_strategy_id = strategy_id
        
        # Rotate if we found a better strategy
        if best_strategy_id and best_strategy_id != self.active_strategy_id:
            old_strategy = self.active_strategy_id
            self.active_strategy_id = best_strategy_id
            
            # Record the rotation
            self.rotation_history.append({
                "timestamp": datetime.now().isoformat(),
                "from_strategy": old_strategy,
                "to_strategy": best_strategy_id,
                "reason": "auto_rotation",
                "score": best_score
            })
            
            logger.info(f"Auto-rotated from {old_strategy} to {best_strategy_id} with score {best_score:.4f}")
            return True
            
        return False
    
    def get_active_strategy(self) -> Optional[Strategy]:
        """
        Get the currently active strategy.
        
        Returns:
            The active strategy or None if no active strategy
        """
        if not self.active_strategy_id:
            return None
        return self.strategies.get(self.active_strategy_id)
    
    def get_active_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get signals from the active strategy.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with signals from active strategy
        """
        active_strategy = self.get_active_strategy()
        if not active_strategy:
            logger.warning("No active strategy to generate signals")
            return {"signals": [], "status": "no_active_strategy"}
            
        try:
            analysis = active_strategy.analyze(market_data)
            return {
                "strategy_id": active_strategy.id,
                "strategy_name": active_strategy.name,
                "strategy_type": active_strategy.type.value,
                **analysis
            }
        except Exception as e:
            logger.error(f"Error getting signals from {active_strategy.id}: {e}")
            return {
                "strategy_id": active_strategy.id,
                "strategy_name": active_strategy.name,
                "strategy_type": active_strategy.type.value,
                "signals": [],
                "error": str(e),
                "status": "error"
            }
    
    def get_rotation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent strategy rotation history.
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            List of rotation history items
        """
        return self.rotation_history[-limit:] 
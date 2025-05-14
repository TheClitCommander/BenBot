"""
Dynamic Capital Allocator for BensBot.

This module provides intelligent capital allocation based on:
1. Monte Carlo confidence scores
2. Market regime shifts
3. Strategy risk profiles
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from trading_bot.core.portfolio.allocator import PortfolioAllocator
from trading_bot.core.evolution.market_adapter import MarketAdapter
from trading_bot.core.simulation.monte_carlo import MonteCarloSimulator

logger = logging.getLogger(__name__)

class DynamicAllocator:
    """
    Dynamically allocates capital across strategies based on:
    1. Strategy confidence scores from Monte Carlo simulations
    2. Market regime suitability
    3. Recent performance metrics
    4. Risk budget constraints
    """
    
    def __init__(
        self,
        portfolio_allocator: PortfolioAllocator,
        market_adapter: MarketAdapter,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the dynamic allocator."""
        self.portfolio_allocator = portfolio_allocator
        self.market_adapter = market_adapter
        self.config = config or {}
        
        # Default configuration
        self.min_confidence_score = self.config.get("min_confidence_score", 0.6)
        self.max_allocation_per_strategy = self.config.get("max_allocation_per_strategy", 0.25)
        self.reserve_ratio = self.config.get("reserve_ratio", 0.15)
        self.regime_weight = self.config.get("regime_weight", 0.3)
        self.confidence_weight = self.config.get("confidence_weight", 0.4)
        self.performance_weight = self.config.get("performance_weight", 0.3)
        
        # Allocation history
        self.allocation_history = []
        
        # Strategy activation tracking
        self.active_strategies = set()
        
        # Time-based weights - strategies that performed well recently get higher weight
        self.recency_decay = self.config.get("recency_decay", 0.9)  # Weight decay factor for older performance
    
    def calculate_strategy_scores(self, strategies: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate allocation scores for each strategy.
        
        Args:
            strategies: List of strategy dictionaries with performance metrics
            
        Returns:
            Dictionary mapping strategy IDs to allocation scores
        """
        scores = {}
        current_regimes = self.market_adapter.current_regimes
        
        for strategy in strategies:
            strategy_id = strategy.get("strategy_id")
            asset_class = strategy.get("asset_class")
            strategy_type = strategy.get("strategy_type")
            performance = strategy.get("performance", {})
            
            # Skip strategies with no performance data
            if not performance:
                scores[strategy_id] = 0.0
                continue
            
            # 1. Base score from performance metrics
            sharpe_ratio = performance.get("sharpe_ratio", 0.0)
            return_value = performance.get("total_return", 0.0) / 100.0  # Convert from percentage
            win_rate = performance.get("win_rate", 50.0) / 100.0  # Convert from percentage
            max_drawdown = abs(performance.get("max_drawdown", 0.0) / 100.0)  # Convert from percentage
            
            # Combine performance metrics
            performance_score = (
                0.4 * max(0, sharpe_ratio) +
                0.3 * max(0, return_value) +
                0.2 * win_rate -
                0.1 * max_drawdown
            )
            
            # 2. Regime suitability
            regime_score = 0.5  # Neutral default
            if asset_class in current_regimes:
                current_regime = current_regimes[asset_class].get("primary_regime")
                
                # Check if strategy has regime suitability info
                if "suitable_regimes" in strategy:
                    suitable_regimes = strategy.get("suitable_regimes", [])
                    regime_score = 1.0 if current_regime in suitable_regimes else 0.25
                # For momentum equity strategy, use its built-in regime check
                elif strategy_type == "momentum_equity" and "preferred_regimes" in strategy.get("parameters", {}):
                    preferred_regimes = strategy.get("parameters", {}).get("preferred_regimes", [])
                    regime_score = 1.0 if current_regime in preferred_regimes else 0.25
            
            # 3. Confidence score from Monte Carlo simulations
            confidence_score = performance.get("consistency_score", 0.5)
            
            # 4. Out-of-sample performance
            oos_factor = 1.0
            if "oos_sharpe_ratio" in performance and "sharpe_ratio" in performance:
                oos_sharpe = performance.get("oos_sharpe_ratio", 0.0)
                is_sharpe = performance.get("sharpe_ratio", 0.0)
                
                # If out-of-sample performance is significantly worse, penalize
                if oos_sharpe < is_sharpe * 0.7:
                    oos_factor = 0.6
                # If out-of-sample performance is better, reward
                elif oos_sharpe > is_sharpe:
                    oos_factor = 1.2
            
            # Calculate final score with weights
            final_score = (
                self.performance_weight * performance_score * oos_factor +
                self.regime_weight * regime_score +
                self.confidence_weight * confidence_score
            )
            
            # Minimum score threshold
            final_score = max(0.0, final_score)
            
            scores[strategy_id] = final_score
        
        return scores
    
    def allocate_capital(
        self,
        force_reallocation: bool = False,
        min_change_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Dynamically allocate capital based on strategy scores.
        
        Args:
            force_reallocation: Whether to force reallocation regardless of thresholds
            min_change_threshold: Minimum change threshold to trigger reallocation
            
        Returns:
            Dictionary with allocation results
        """
        # Get all registered strategies
        strategies = []
        for strategy_id in self.portfolio_allocator.current_allocations:
            allocation = self.portfolio_allocator.get_strategy_allocation(strategy_id)
            if allocation:
                strategies.append(allocation)
        
        # Calculate scores
        strategy_scores = self.calculate_strategy_scores(strategies)
        
        # Check if any strategy's score has changed significantly
        significant_changes = False
        if not force_reallocation and self.allocation_history:
            last_scores = self.allocation_history[-1].get("strategy_scores", {})
            for strategy_id, score in strategy_scores.items():
                if strategy_id in last_scores:
                    change = abs(score - last_scores[strategy_id])
                    if change > min_change_threshold:
                        significant_changes = True
                        break
                else:
                    # New strategy
                    significant_changes = True
                    break
        
        # If no significant changes and not forcing, skip reallocation
        if not force_reallocation and not significant_changes and self.allocation_history:
            return {
                "status": "skipped",
                "message": "No significant changes in strategy scores",
                "timestamp": datetime.now().isoformat()
            }
        
        # Determine active strategies based on scores
        active_strategy_ids = []
        for strategy_id, score in strategy_scores.items():
            # Only include strategies with scores above minimum confidence
            if score >= self.min_confidence_score:
                active_strategy_ids.append(strategy_id)
                self.active_strategies.add(strategy_id)
            elif strategy_id in self.active_strategies:
                # Deactivate strategies that fell below threshold
                self.portfolio_allocator.set_strategy_active_status(strategy_id, False)
                self.active_strategies.remove(strategy_id)
        
        # If no strategies are active, keep a reserve
        if not active_strategy_ids:
            logger.warning("No strategies have scores above minimum confidence threshold")
            return {
                "status": "reserve",
                "message": "All capital allocated to reserve - no strategies meet criteria",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate allocation weights based on scores
        total_score = sum(strategy_scores[s_id] for s_id in active_strategy_ids)
        if total_score <= 0:
            logger.warning("Total strategy score is zero or negative")
            return {
                "status": "error",
                "message": "Cannot allocate - total strategy score is zero or negative",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate weighted allocations based on scores
        allocation_weights = {}
        for strategy_id in active_strategy_ids:
            weight = strategy_scores[strategy_id] / total_score
            allocation_weights[strategy_id] = weight
        
        # Perform the allocation using the portfolio allocator
        allocation_result = self.portfolio_allocator.allocate_capital(
            strategies=active_strategy_ids,
            allocation_model="performance_weighted",  # We've prepared our own weights
            force_rebalance=True
        )
        
        # Record allocation history
        self.allocation_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy_scores": strategy_scores,
            "allocation_weights": allocation_weights,
            "allocation_result": allocation_result
        })
        
        # Trim history if it gets too large
        if len(self.allocation_history) > 100:
            self.allocation_history = self.allocation_history[-100:]
        
        return {
            "status": "success",
            "strategy_scores": strategy_scores,
            "active_strategies": active_strategy_ids,
            "allocation_result": allocation_result,
            "message": f"Dynamic allocation completed with {len(active_strategy_ids)} active strategies",
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_regime_change(self, old_regimes: Dict[str, Any], new_regimes: Dict[str, Any]) -> Dict[str, Any]:
        """
        React to a market regime change by reallocating capital.
        
        Args:
            old_regimes: Previous market regimes
            new_regimes: New market regimes
            
        Returns:
            Dictionary with reallocation results
        """
        # Check if there's a significant regime change
        regime_changed = False
        changed_assets = []
        
        for asset_class in new_regimes:
            if asset_class not in old_regimes:
                regime_changed = True
                changed_assets.append(asset_class)
                continue
                
            old_regime = old_regimes[asset_class].get("primary_regime")
            new_regime = new_regimes[asset_class].get("primary_regime")
            
            if old_regime != new_regime:
                regime_changed = True
                changed_assets.append(asset_class)
        
        if not regime_changed:
            return {
                "status": "skipped",
                "message": "No significant regime change detected",
                "timestamp": datetime.now().isoformat()
            }
        
        # Force reallocation
        logger.info(f"Regime change detected for: {', '.join(changed_assets)}. Reallocating capital.")
        result = self.allocate_capital(force_reallocation=True)
        
        # Add regime change information
        result["regime_change"] = {
            "changed_asset_classes": changed_assets,
            "old_regimes": old_regimes,
            "new_regimes": new_regimes
        }
        
        return result
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current dynamic allocation.
        
        Returns:
            Dictionary with allocation summary
        """
        # Get base allocation summary
        base_summary = self.portfolio_allocator.get_allocation_summary()
        
        # Add dynamic allocation specific information
        summary = {
            **base_summary,
            "dynamic_allocation": {
                "active_strategies_count": len(self.active_strategies),
                "min_confidence_threshold": self.min_confidence_score,
                "current_regimes": self.market_adapter.current_regimes,
                "last_reallocation": self.allocation_history[-1]["timestamp"] if self.allocation_history else None,
                "strategy_score_history": {
                    s_id: [h["strategy_scores"].get(s_id, 0) for h in self.allocation_history[-5:]]
                    for s_id in self.active_strategies
                } if self.allocation_history else {}
            }
        }
        
        return summary 
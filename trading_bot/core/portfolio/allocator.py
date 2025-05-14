"""
Portfolio Allocator for BensBot.

This module provides capital allocation services across
multiple strategies and asset classes.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AllocationTarget:
    """Represents a capital allocation target for a strategy."""
    strategy_id: str
    strategy_type: str
    asset_class: str
    allocation_pct: float
    allocation_amount: float
    is_active: bool = True
    performance: Optional[Dict[str, Any]] = None
    last_updated: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PortfolioAllocator:
    """
    A sophisticated portfolio allocator that distributes capital
    across strategies and asset classes based on various allocation models.
    """
    
    def __init__(
        self,
        total_capital: float,
        allocation_model: str = "equal_weight",
        min_allocation_pct: float = 0.05,  # 5% minimum per strategy
        max_allocation_pct: float = 0.30,  # 30% maximum per strategy
        asset_class_limits: Optional[Dict[str, float]] = None,
        rebalance_threshold_pct: float = 0.1,  # 10% drift before rebalancing
        reserve_capital_pct: float = 0.2,  # 20% cash reserve
    ):
        """
        Initialize the portfolio allocator.
        
        Args:
            total_capital: Total capital to allocate
            allocation_model: Model to use for allocation (equal_weight, risk_parity, etc.)
            min_allocation_pct: Minimum allocation percentage per strategy
            max_allocation_pct: Maximum allocation percentage per strategy
            asset_class_limits: Dictionary of maximum allocations per asset class
            rebalance_threshold_pct: Percentage drift before triggering rebalance
            reserve_capital_pct: Percentage of capital to keep in reserve (not allocated)
        """
        self.total_capital = total_capital
        self.allocation_model = allocation_model
        self.min_allocation_pct = min_allocation_pct
        self.max_allocation_pct = max_allocation_pct
        
        # Default asset class limits if none provided
        self.asset_class_limits = asset_class_limits or {
            "equity": 0.6,    # Max 60% in equities
            "crypto": 0.3,    # Max 30% in crypto
            "forex": 0.4      # Max 40% in forex
        }
        
        self.rebalance_threshold_pct = rebalance_threshold_pct
        self.reserve_capital_pct = reserve_capital_pct
        
        # Available capital after reserve
        self.available_capital = total_capital * (1 - reserve_capital_pct)
        
        # Current allocations
        self.current_allocations: Dict[str, AllocationTarget] = {}
        
        # Performance history for adaptive allocation
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Last allocation timestamp
        self.last_allocation_time = None
    
    def update_total_capital(self, new_total_capital: float) -> Dict[str, Any]:
        """
        Update the total capital and recalculate allocations.
        
        Args:
            new_total_capital: New total capital amount
            
        Returns:
            Dictionary with allocation changes
        """
        old_total = self.total_capital
        self.total_capital = new_total_capital
        self.available_capital = new_total_capital * (1 - self.reserve_capital_pct)
        
        # Calculate and return changes
        capital_change_pct = (new_total_capital / old_total) - 1
        
        changes = {
            "old_capital": old_total,
            "new_capital": new_total_capital,
            "change_pct": capital_change_pct,
            "new_available": self.available_capital
        }
        
        # If the change is significant, trigger a rebalance
        if abs(capital_change_pct) > self.rebalance_threshold_pct:
            logger.info(f"Capital change of {capital_change_pct:.2%} exceeds threshold. Rebalancing...")
            # We don't actually rebalance here, just flag it
            changes["rebalance_needed"] = True
        
        return changes
    
    def register_strategy(
        self,
        strategy_id: str,
        strategy_type: str,
        asset_class: str,
        performance: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new strategy for allocation.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_type: Type of the strategy
            asset_class: Asset class (equity, crypto, forex)
            performance: Optional performance metrics
            metadata: Optional additional information
            
        Returns:
            Dictionary with registration details
        """
        if strategy_id in self.current_allocations:
            logger.warning(f"Strategy {strategy_id} already registered. Updating.")
            
            # Update existing allocation with new metadata
            self.current_allocations[strategy_id].strategy_type = strategy_type
            self.current_allocations[strategy_id].asset_class = asset_class
            if performance:
                self.current_allocations[strategy_id].performance = performance
            if metadata:
                self.current_allocations[strategy_id].metadata = metadata
            
            # Update timestamp
            self.current_allocations[strategy_id].last_updated = datetime.utcnow().isoformat()
            
            return {
                "status": "updated",
                "strategy_id": strategy_id,
                "message": "Strategy registration updated"
            }
        
        # Create a new allocation target with zero allocation
        # Actual allocation will be done in allocate_capital method
        new_target = AllocationTarget(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            asset_class=asset_class,
            allocation_pct=0.0,
            allocation_amount=0.0,
            is_active=True,
            performance=performance,
            last_updated=datetime.utcnow().isoformat(),
            metadata=metadata
        )
        
        self.current_allocations[strategy_id] = new_target
        
        # Initialize performance history
        if strategy_id not in self.performance_history:
            self.performance_history[strategy_id] = []
        
        if performance:
            self.performance_history[strategy_id].append({
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": performance
            })
        
        return {
            "status": "registered",
            "strategy_id": strategy_id,
            "message": "Strategy registered successfully"
        }
    
    def unregister_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Unregister a strategy and remove its allocation.
        
        Args:
            strategy_id: ID of the strategy to unregister
            
        Returns:
            Dictionary with unregistration details
        """
        if strategy_id not in self.current_allocations:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found"
            }
        
        # Get current allocation amount to be freed
        freed_capital = self.current_allocations[strategy_id].allocation_amount
        
        # Remove from allocations
        del self.current_allocations[strategy_id]
        
        # Keep performance history for reference
        # self.performance_history[strategy_id] stays intact
        
        return {
            "status": "unregistered",
            "strategy_id": strategy_id,
            "freed_capital": freed_capital,
            "message": "Strategy unregistered and allocation removed"
        }
    
    def update_strategy_performance(
        self,
        strategy_id: str,
        performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update performance metrics for a strategy.
        
        Args:
            strategy_id: ID of the strategy
            performance: Dictionary of performance metrics
            
        Returns:
            Dictionary with update status
        """
        if strategy_id not in self.current_allocations:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found"
            }
        
        # Update performance in current allocation
        self.current_allocations[strategy_id].performance = performance
        self.current_allocations[strategy_id].last_updated = datetime.utcnow().isoformat()
        
        # Add to performance history
        if strategy_id not in self.performance_history:
            self.performance_history[strategy_id] = []
        
        self.performance_history[strategy_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": performance
        })
        
        return {
            "status": "updated",
            "strategy_id": strategy_id,
            "message": "Performance updated successfully"
        }
    
    def allocate_capital(
        self,
        strategies: Optional[List[str]] = None,
        allocation_model: Optional[str] = None,
        force_rebalance: bool = False
    ) -> Dict[str, Any]:
        """
        Allocate capital across registered strategies.
        
        Args:
            strategies: Optional list of strategy IDs to allocate to (if None, use all)
            allocation_model: Override the default allocation model
            force_rebalance: Force rebalancing even if thresholds not met
            
        Returns:
            Dictionary with allocation results
        """
        model = allocation_model or self.allocation_model
        target_strategies = strategies or list(self.current_allocations.keys())
        
        # Filter to only include active strategies
        target_strategies = [
            s_id for s_id in target_strategies
            if s_id in self.current_allocations and self.current_allocations[s_id].is_active
        ]
        
        if not target_strategies:
            return {
                "status": "error",
                "message": "No active strategies to allocate capital to"
            }
        
        # Check if rebalancing is needed based on drift
        need_rebalance = force_rebalance or self._check_rebalance_needed(target_strategies)
        
        if not need_rebalance and self.last_allocation_time:
            return {
                "status": "skipped",
                "message": "Rebalance not needed based on thresholds",
                "last_allocation": self.last_allocation_time
            }
        
        # Calculate new allocations based on the selected model
        if model == "equal_weight":
            new_allocations = self._allocate_equal_weight(target_strategies)
        elif model == "risk_parity":
            new_allocations = self._allocate_risk_parity(target_strategies)
        elif model == "performance_weighted":
            new_allocations = self._allocate_performance_weighted(target_strategies)
        elif model == "asset_class_balanced":
            new_allocations = self._allocate_asset_class_balanced(target_strategies)
        else:
            logger.warning(f"Unknown allocation model: {model}. Using equal weight.")
            new_allocations = self._allocate_equal_weight(target_strategies)
        
        # Apply allocation changes and track results
        allocation_changes = []
        
        for strategy_id, new_alloc in new_allocations.items():
            if strategy_id not in self.current_allocations:
                logger.warning(f"Strategy {strategy_id} not found in current allocations. Skipping.")
                continue
            
            old_alloc = self.current_allocations[strategy_id].allocation_amount
            self.current_allocations[strategy_id].allocation_pct = new_alloc["allocation_pct"]
            self.current_allocations[strategy_id].allocation_amount = new_alloc["allocation_amount"]
            
            allocation_changes.append({
                "strategy_id": strategy_id,
                "asset_class": self.current_allocations[strategy_id].asset_class,
                "old_amount": old_alloc,
                "new_amount": new_alloc["allocation_amount"],
                "change_amount": new_alloc["allocation_amount"] - old_alloc,
                "new_pct": new_alloc["allocation_pct"]
            })
        
        self.last_allocation_time = datetime.utcnow().isoformat()
        
        return {
            "status": "success",
            "allocation_model": model,
            "allocated_capital": sum(a["allocation_amount"] for a in new_allocations.values()),
            "available_capital": self.available_capital,
            "reserve_capital": self.total_capital * self.reserve_capital_pct,
            "allocation_changes": allocation_changes,
            "timestamp": self.last_allocation_time
        }
    
    def _check_rebalance_needed(self, strategies: List[str]) -> bool:
        """
        Check if rebalancing is needed based on drift thresholds.
        
        Args:
            strategies: List of strategy IDs to check
            
        Returns:
            True if rebalancing is needed, False otherwise
        """
        if not self.last_allocation_time:
            return True  # First allocation
        
        # Check if any strategy has drifted beyond threshold
        for strategy_id in strategies:
            if strategy_id not in self.current_allocations:
                continue
                
            allocation = self.current_allocations[strategy_id]
            
            # If strategy has no allocation yet but is active, we need to allocate
            if allocation.allocation_amount == 0 and allocation.is_active:
                return True
            
            # If it has allocation, check for drift from target percentage
            current_pct = allocation.allocation_amount / self.total_capital
            if abs(current_pct - allocation.allocation_pct) > self.rebalance_threshold_pct:
                return True
        
        # Also check total allocation - if there's significant unallocated capital
        total_allocated = sum(a.allocation_amount for a in self.current_allocations.values())
        target_allocated = self.available_capital
        
        if abs(total_allocated - target_allocated) / self.total_capital > self.rebalance_threshold_pct:
            return True
            
        return False
    
    def _allocate_equal_weight(self, strategies: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Allocate capital equally across strategies, respecting constraints.
        
        Args:
            strategies: List of strategy IDs to allocate to
            
        Returns:
            Dictionary mapping strategy IDs to allocation details
        """
        # Count strategies by asset class
        asset_class_counts = {}
        for strategy_id in strategies:
            asset_class = self.current_allocations[strategy_id].asset_class
            asset_class_counts[asset_class] = asset_class_counts.get(asset_class, 0) + 1
        
        # Start with equal weights
        equal_weight = 1.0 / len(strategies) if strategies else 0
        
        # Initialize allocations with equal weight
        allocations = {}
        for strategy_id in strategies:
            allocations[strategy_id] = {
                "allocation_pct": equal_weight,
                "allocation_amount": equal_weight * self.available_capital
            }
        
        # Adjust for asset class limits
        for asset_class, limit in self.asset_class_limits.items():
            asset_class_strategies = [
                s_id for s_id in strategies
                if self.current_allocations[s_id].asset_class == asset_class
            ]
            
            if not asset_class_strategies:
                continue
                
            # Total allocation to this asset class
            total_alloc = sum(allocations[s_id]["allocation_pct"] for s_id in asset_class_strategies)
            
            # If over limit, scale down proportionally
            if total_alloc > limit:
                scale_factor = limit / total_alloc
                for s_id in asset_class_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        # Adjust for min/max allocation per strategy
        for strategy_id in strategies:
            if allocations[strategy_id]["allocation_pct"] < self.min_allocation_pct:
                # Skip this strategy if it would get too small an allocation
                # We'll prefer to allocate meaningful amounts rather than spread too thin
                allocations[strategy_id]["allocation_pct"] = 0
                allocations[strategy_id]["allocation_amount"] = 0
            elif allocations[strategy_id]["allocation_pct"] > self.max_allocation_pct:
                # Cap at maximum allocation
                allocations[strategy_id]["allocation_pct"] = self.max_allocation_pct
                allocations[strategy_id]["allocation_amount"] = self.max_allocation_pct * self.available_capital
        
        # Normalize remaining allocations to use available capital
        active_strategies = [s_id for s_id in strategies if allocations[s_id]["allocation_pct"] > 0]
        
        if active_strategies:
            # Sum of current allocations for active strategies
            current_total_pct = sum(allocations[s_id]["allocation_pct"] for s_id in active_strategies)
            
            # If we're not at 100%, rescale
            if current_total_pct > 0 and abs(current_total_pct - 1.0) > 0.01:
                scale_factor = 1.0 / current_total_pct
                for s_id in active_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        return allocations
    
    def _allocate_risk_parity(self, strategies: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Allocate capital using risk parity principles.
        Each strategy gets capital inversely proportional to its volatility.
        
        Args:
            strategies: List of strategy IDs to allocate to
            
        Returns:
            Dictionary mapping strategy IDs to allocation details
        """
        # Calculate inverse volatility for each strategy
        inverse_volatilities = {}
        for strategy_id in strategies:
            allocation = self.current_allocations[strategy_id]
            
            # Get volatility from performance if available, or use default
            volatility = 0.15  # Default volatility
            
            if allocation.performance and "volatility" in allocation.performance:
                volatility = allocation.performance["volatility"]
            elif allocation.asset_class == "equity":
                volatility = 0.15  # Default for equities
            elif allocation.asset_class == "crypto":
                volatility = 0.50  # Default for crypto (higher)
            elif allocation.asset_class == "forex":
                volatility = 0.10  # Default for forex (lower)
            
            # Inverse volatility - lower risk gets more capital
            inverse_volatilities[strategy_id] = 1.0 / max(volatility, 0.01)  # Avoid division by zero
        
        # Calculate weights based on inverse volatility
        total_inverse_vol = sum(inverse_volatilities.values())
        if total_inverse_vol <= 0:
            # Fallback to equal weight if we can't calculate inverse vol
            return self._allocate_equal_weight(strategies)
            
        # Initial risk parity weights
        allocations = {}
        for strategy_id in strategies:
            weight = inverse_volatilities[strategy_id] / total_inverse_vol
            allocations[strategy_id] = {
                "allocation_pct": weight,
                "allocation_amount": weight * self.available_capital
            }
        
        # Now apply constraints similar to equal weight method
        # (min/max allocations and asset class limits)
        
        # Adjust for asset class limits
        for asset_class, limit in self.asset_class_limits.items():
            asset_class_strategies = [
                s_id for s_id in strategies
                if self.current_allocations[s_id].asset_class == asset_class
            ]
            
            if not asset_class_strategies:
                continue
                
            # Total allocation to this asset class
            total_alloc = sum(allocations[s_id]["allocation_pct"] for s_id in asset_class_strategies)
            
            # If over limit, scale down proportionally
            if total_alloc > limit:
                scale_factor = limit / total_alloc
                for s_id in asset_class_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        # Adjust for min/max allocation per strategy
        for strategy_id in strategies:
            if allocations[strategy_id]["allocation_pct"] < self.min_allocation_pct:
                # Skip this strategy if it would get too small an allocation
                allocations[strategy_id]["allocation_pct"] = 0
                allocations[strategy_id]["allocation_amount"] = 0
            elif allocations[strategy_id]["allocation_pct"] > self.max_allocation_pct:
                # Cap at maximum allocation
                allocations[strategy_id]["allocation_pct"] = self.max_allocation_pct
                allocations[strategy_id]["allocation_amount"] = self.max_allocation_pct * self.available_capital
        
        # Normalize remaining allocations
        active_strategies = [s_id for s_id in strategies if allocations[s_id]["allocation_pct"] > 0]
        
        if active_strategies:
            # Sum of current allocations for active strategies
            current_total_pct = sum(allocations[s_id]["allocation_pct"] for s_id in active_strategies)
            
            # If we're not at 100%, rescale
            if current_total_pct > 0 and abs(current_total_pct - 1.0) > 0.01:
                scale_factor = 1.0 / current_total_pct
                for s_id in active_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        return allocations
    
    def _allocate_performance_weighted(self, strategies: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Allocate capital based on past performance metrics.
        Better-performing strategies get higher allocations.
        
        Args:
            strategies: List of strategy IDs to allocate to
            
        Returns:
            Dictionary mapping strategy IDs to allocation details
        """
        # Calculate performance score for each strategy
        performance_scores = {}
        
        for strategy_id in strategies:
            allocation = self.current_allocations[strategy_id]
            
            # Default score if no performance data
            score = 1.0
            
            if allocation.performance:
                # Blend of different performance metrics
                # 1. Sharpe ratio (risk-adjusted return) - major component
                sharpe = allocation.performance.get("sharpe_ratio", 0)
                
                # 2. Total return - moderate component
                total_return = allocation.performance.get("total_return", 0) / 100  # Convert from percentage
                
                # 3. Win rate - minor component
                win_rate = allocation.performance.get("win_rate", 50) / 100  # Convert from percentage
                
                # Combine into a weighted score
                score = max(0, (0.6 * sharpe) + (0.3 * total_return) + (0.1 * win_rate))
                
                # If negative Sharpe ratio, severely penalize
                if sharpe < 0:
                    score *= 0.1
                
                # Ensure minimum positive score
                score = max(0.1, score)
            
            performance_scores[strategy_id] = score
        
        # If all strategies have zero score, fall back to equal weight
        if sum(performance_scores.values()) <= 0:
            return self._allocate_equal_weight(strategies)
        
        # Normalize scores to get allocation percentages
        total_score = sum(performance_scores.values())
        
        # Initial performance-weighted allocations
        allocations = {}
        for strategy_id in strategies:
            weight = performance_scores[strategy_id] / total_score
            allocations[strategy_id] = {
                "allocation_pct": weight,
                "allocation_amount": weight * self.available_capital
            }
        
        # Apply constraints as in other allocation methods
        # (min/max allocations and asset class limits)
        
        # Adjust for asset class limits
        for asset_class, limit in self.asset_class_limits.items():
            asset_class_strategies = [
                s_id for s_id in strategies
                if self.current_allocations[s_id].asset_class == asset_class
            ]
            
            if not asset_class_strategies:
                continue
                
            # Total allocation to this asset class
            total_alloc = sum(allocations[s_id]["allocation_pct"] for s_id in asset_class_strategies)
            
            # If over limit, scale down proportionally
            if total_alloc > limit:
                scale_factor = limit / total_alloc
                for s_id in asset_class_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        # Adjust for min/max allocation per strategy
        for strategy_id in strategies:
            if allocations[strategy_id]["allocation_pct"] < self.min_allocation_pct:
                # Skip this strategy if it would get too small an allocation
                allocations[strategy_id]["allocation_pct"] = 0
                allocations[strategy_id]["allocation_amount"] = 0
            elif allocations[strategy_id]["allocation_pct"] > self.max_allocation_pct:
                # Cap at maximum allocation
                allocations[strategy_id]["allocation_pct"] = self.max_allocation_pct
                allocations[strategy_id]["allocation_amount"] = self.max_allocation_pct * self.available_capital
        
        # Normalize remaining allocations
        active_strategies = [s_id for s_id in strategies if allocations[s_id]["allocation_pct"] > 0]
        
        if active_strategies:
            # Sum of current allocations for active strategies
            current_total_pct = sum(allocations[s_id]["allocation_pct"] for s_id in active_strategies)
            
            # If we're not at 100%, rescale
            if current_total_pct > 0 and abs(current_total_pct - 1.0) > 0.01:
                scale_factor = 1.0 / current_total_pct
                for s_id in active_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        return allocations
    
    def _allocate_asset_class_balanced(self, strategies: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Allocate capital to maintain balance across asset classes.
        Provides diversification benefit.
        
        Args:
            strategies: List of strategy IDs to allocate to
            
        Returns:
            Dictionary mapping strategy IDs to allocation details
        """
        # First, determine asset class target weights
        # Start with equal allocation across available asset classes
        asset_classes = set(self.current_allocations[s_id].asset_class for s_id in strategies)
        asset_class_weights = {ac: 1.0 / len(asset_classes) for ac in asset_classes}
        
        # Adjust based on predefined asset class preferences if needed
        # This could be adjusted based on market conditions
        if "equity" in asset_class_weights and "crypto" in asset_class_weights and "forex" in asset_class_weights:
            # If all three asset classes are present, use predefined weights
            asset_class_weights = {
                "equity": 0.45,  # 45% to equities
                "crypto": 0.25,  # 25% to crypto
                "forex": 0.30    # 30% to forex
            }
        
        # Ensure weights respect asset class limits
        for asset_class, weight in list(asset_class_weights.items()):
            if weight > self.asset_class_limits.get(asset_class, 1.0):
                # Cap at limit
                asset_class_weights[asset_class] = self.asset_class_limits[asset_class]
        
        # Normalize weights to sum to 1.0
        total_weight = sum(asset_class_weights.values())
        if total_weight > 0:
            asset_class_weights = {ac: w / total_weight for ac, w in asset_class_weights.items()}
        
        # Now distribute capital within each asset class
        allocations = {}
        
        # Group strategies by asset class
        strategies_by_class = {}
        for strategy_id in strategies:
            asset_class = self.current_allocations[strategy_id].asset_class
            if asset_class not in strategies_by_class:
                strategies_by_class[asset_class] = []
            strategies_by_class[asset_class].append(strategy_id)
        
        # Allocate within each asset class
        for asset_class, asset_strategies in strategies_by_class.items():
            if not asset_strategies:
                continue
                
            asset_class_allocation = asset_class_weights.get(asset_class, 0) * self.available_capital
            
            # Equal weight within asset class as a starting point
            strategy_weight = 1.0 / len(asset_strategies)
            
            for strategy_id in asset_strategies:
                allocations[strategy_id] = {
                    "allocation_pct": asset_class_weights.get(asset_class, 0) * strategy_weight,
                    "allocation_amount": asset_class_allocation * strategy_weight
                }
        
        # Apply min/max constraints per strategy
        for strategy_id in strategies:
            if strategy_id not in allocations:
                allocations[strategy_id] = {
                    "allocation_pct": 0,
                    "allocation_amount": 0
                }
            elif allocations[strategy_id]["allocation_pct"] < self.min_allocation_pct:
                # Skip this strategy if it would get too small an allocation
                allocations[strategy_id]["allocation_pct"] = 0
                allocations[strategy_id]["allocation_amount"] = 0
            elif allocations[strategy_id]["allocation_pct"] > self.max_allocation_pct:
                # Cap at maximum allocation
                allocations[strategy_id]["allocation_pct"] = self.max_allocation_pct
                allocations[strategy_id]["allocation_amount"] = self.max_allocation_pct * self.available_capital
        
        # Normalize within each asset class again
        for asset_class, asset_strategies in strategies_by_class.items():
            active_strategies = [s_id for s_id in asset_strategies if allocations[s_id]["allocation_pct"] > 0]
            
            if not active_strategies:
                continue
                
            # Total allocation for this asset class
            target_weight = asset_class_weights.get(asset_class, 0)
            current_weight = sum(allocations[s_id]["allocation_pct"] for s_id in active_strategies)
            
            if current_weight > 0 and abs(current_weight - target_weight) > 0.01:
                scale_factor = target_weight / current_weight
                for s_id in active_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        # Final normalization of all allocations
        active_strategies = [s_id for s_id in strategies if allocations[s_id]["allocation_pct"] > 0]
        
        if active_strategies:
            current_total_pct = sum(allocations[s_id]["allocation_pct"] for s_id in active_strategies)
            
            if current_total_pct > 0 and abs(current_total_pct - 1.0) > 0.01:
                scale_factor = 1.0 / current_total_pct
                for s_id in active_strategies:
                    allocations[s_id]["allocation_pct"] *= scale_factor
                    allocations[s_id]["allocation_amount"] = allocations[s_id]["allocation_pct"] * self.available_capital
        
        return allocations
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current allocations.
        
        Returns:
            Dictionary with allocation summary
        """
        total_allocated = sum(a.allocation_amount for a in self.current_allocations.values())
        
        # Group by asset class
        asset_class_totals = {}
        for strategy_id, allocation in self.current_allocations.items():
            asset_class = allocation.asset_class
            if asset_class not in asset_class_totals:
                asset_class_totals[asset_class] = 0
            asset_class_totals[asset_class] += allocation.allocation_amount
        
        # Group by strategy type
        strategy_type_totals = {}
        for strategy_id, allocation in self.current_allocations.items():
            strategy_type = allocation.strategy_type
            if strategy_type not in strategy_type_totals:
                strategy_type_totals[strategy_type] = 0
            strategy_type_totals[strategy_type] += allocation.allocation_amount
        
        # Calculate percentages
        asset_class_pcts = {ac: amt / self.total_capital for ac, amt in asset_class_totals.items()}
        strategy_type_pcts = {st: amt / self.total_capital for st, amt in strategy_type_totals.items()}
        
        return {
            "total_capital": self.total_capital,
            "allocated_capital": total_allocated,
            "reserve_capital": self.total_capital * self.reserve_capital_pct,
            "unallocated_capital": self.available_capital - total_allocated,
            "allocation_model": self.allocation_model,
            "asset_class_allocation": {
                "amounts": asset_class_totals,
                "percentages": asset_class_pcts
            },
            "strategy_type_allocation": {
                "amounts": strategy_type_totals,
                "percentages": strategy_type_pcts
            },
            "allocation_count": len(self.current_allocations),
            "last_updated": self.last_allocation_time
        }
    
    def get_strategy_allocation(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get allocation details for a specific strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            Dictionary with allocation details or None if not found
        """
        if strategy_id not in self.current_allocations:
            return None
        
        allocation = self.current_allocations[strategy_id]
        
        return {
            "strategy_id": strategy_id,
            "strategy_type": allocation.strategy_type,
            "asset_class": allocation.asset_class,
            "allocation_pct": allocation.allocation_pct,
            "allocation_amount": allocation.allocation_amount,
            "is_active": allocation.is_active,
            "performance": allocation.performance,
            "last_updated": allocation.last_updated,
            "metadata": allocation.metadata
        }
    
    def set_strategy_active_status(self, strategy_id: str, is_active: bool) -> Dict[str, Any]:
        """
        Set a strategy as active or inactive for allocation.
        
        Args:
            strategy_id: ID of the strategy
            is_active: Whether the strategy should be active
            
        Returns:
            Dictionary with status information
        """
        if strategy_id not in self.current_allocations:
            return {
                "status": "error",
                "message": f"Strategy {strategy_id} not found"
            }
        
        old_status = self.current_allocations[strategy_id].is_active
        self.current_allocations[strategy_id].is_active = is_active
        
        status_change = "no change" if old_status == is_active else "activated" if is_active else "deactivated"
        
        # If deactivating, clear allocation
        if not is_active and self.current_allocations[strategy_id].allocation_amount > 0:
            freed_capital = self.current_allocations[strategy_id].allocation_amount
            self.current_allocations[strategy_id].allocation_pct = 0
            self.current_allocations[strategy_id].allocation_amount = 0
            
            return {
                "status": "updated",
                "strategy_id": strategy_id,
                "status_change": status_change,
                "freed_capital": freed_capital,
                "message": f"Strategy {strategy_id} deactivated and allocation removed"
            }
        
        return {
            "status": "updated",
            "strategy_id": strategy_id,
            "status_change": status_change,
            "message": f"Strategy {strategy_id} {status_change}"
        } 
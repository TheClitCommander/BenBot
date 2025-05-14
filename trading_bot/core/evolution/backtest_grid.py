"""
Backtest grid for visualizing strategy performance across parameters.

This module provides functionality to:
- Test strategies across parameter ranges
- Generate performance heatmaps
- Identify optimal parameter combinations
"""

import numpy as np
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class BacktestGrid:
    """
    Service for testing strategies across parameter grids.
    
    This class allows testing of strategies with different parameter
    combinations to visualize performance landscapes and identify
    optimal parameters.
    """
    
    def __init__(self, backtester=None, data_dir="./data/backtest_grid"):
        """
        Initialize the backtest grid service.
        
        Args:
            backtester: Reference to backtesting service
            data_dir: Directory for storing results
        """
        self.backtester = backtester
        self.data_dir = data_dir
        self.results = {}
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
    
    def create_parameter_grid(
        self,
        param1_name: str,
        param1_range: List[Any],
        param2_name: str,
        param2_range: List[Any],
        fixed_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a parameter grid for backtesting.
        
        Args:
            param1_name: Name of first parameter to vary
            param1_range: Range of values for first parameter
            param2_name: Name of second parameter to vary
            param2_range: Range of values for second parameter
            fixed_params: Fixed parameters for all tests
            
        Returns:
            Grid configuration
        """
        grid_id = f"grid_{param1_name}_{param2_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        grid_config = {
            "id": grid_id,
            "param1": {
                "name": param1_name,
                "values": param1_range
            },
            "param2": {
                "name": param2_name,
                "values": param2_range
            },
            "fixed_params": fixed_params or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save grid configuration
        with open(os.path.join(self.data_dir, f"{grid_id}_config.json"), 'w') as f:
            json.dump(grid_config, f, indent=2)
        
        return grid_config
    
    def run_grid_backtest(
        self,
        grid_config: Dict[str, Any],
        strategy_type: str,
        market_data: Dict[str, Any],
        metric: str = "total_return"
    ) -> Dict[str, Any]:
        """
        Run backtests for an entire parameter grid.
        
        Args:
            grid_config: Grid configuration
            strategy_type: Type of strategy to test
            market_data: Market data for backtesting
            metric: Performance metric to track
            
        Returns:
            Grid results
        """
        if not self.backtester:
            raise ValueError("Backtester not configured")
        
        grid_id = grid_config["id"]
        param1_name = grid_config["param1"]["name"]
        param1_values = grid_config["param1"]["values"]
        param2_name = grid_config["param2"]["name"]
        param2_values = grid_config["param2"]["values"]
        fixed_params = grid_config["fixed_params"]
        
        # Create results grid
        results_grid = {
            "grid_id": grid_id,
            "strategy_type": strategy_type,
            "param1": {
                "name": param1_name,
                "values": param1_values
            },
            "param2": {
                "name": param2_name,
                "values": param2_values
            },
            "metric": metric,
            "grid_data": [],
            "best_params": None,
            "worst_params": None,
            "completed_at": None
        }
        
        # Initialize grid data structure
        grid_data = []
        
        # Tracking best and worst performance
        best_value = float('-inf')
        best_params = None
        worst_value = float('inf')
        worst_params = None
        
        # Run backtest for each parameter combination
        for i, value1 in enumerate(param1_values):
            row_data = []
            for j, value2 in enumerate(param2_values):
                # Set parameters for this run
                parameters = fixed_params.copy()
                parameters[param1_name] = value1
                parameters[param2_name] = value2
                
                # Run backtest
                try:
                    result = self.backtester.run_backtest(
                        strategy_type=strategy_type,
                        parameters=parameters,
                        market_data=market_data
                    )
                    
                    # Extract performance metric
                    performance = result.get("performance", {})
                    metric_value = performance.get(metric, 0)
                    
                    # Check if this is best or worst
                    if metric_value > best_value:
                        best_value = metric_value
                        best_params = {param1_name: value1, param2_name: value2}
                    
                    if metric_value < worst_value:
                        worst_value = metric_value
                        worst_params = {param1_name: value1, param2_name: value2}
                    
                    # Add to row
                    row_data.append({
                        "value": metric_value,
                        "performance": performance
                    })
                except Exception as e:
                    logger.error(f"Error running backtest for {param1_name}={value1}, {param2_name}={value2}: {e}")
                    row_data.append({
                        "value": None,
                        "error": str(e)
                    })
            
            # Add row to grid
            grid_data.append(row_data)
        
        # Update results
        results_grid["grid_data"] = grid_data
        results_grid["best_params"] = best_params
        results_grid["worst_params"] = worst_params
        results_grid["completed_at"] = datetime.utcnow().isoformat()
        
        # Save results
        with open(os.path.join(self.data_dir, f"{grid_id}_results.json"), 'w') as f:
            json.dump(results_grid, f, indent=2)
        
        # Store in memory
        self.results[grid_id] = results_grid
        
        return results_grid
    
    def get_grid_results(self, grid_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for a specific grid.
        
        Args:
            grid_id: ID of the grid
            
        Returns:
            Grid results or None if not found
        """
        # Check if in memory
        if grid_id in self.results:
            return self.results[grid_id]
        
        # Try to load from disk
        try:
            results_file = os.path.join(self.data_dir, f"{grid_id}_results.json")
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results = json.load(f)
                self.results[grid_id] = results
                return results
        except Exception as e:
            logger.error(f"Error loading grid results: {e}")
        
        return None
    
    def list_available_grids(self) -> List[Dict[str, Any]]:
        """
        List all available backtest grids.
        
        Returns:
            List of grid summaries
        """
        grids = []
        
        # Look for grid result files
        for filename in os.listdir(self.data_dir):
            if filename.endswith("_results.json"):
                grid_id = filename.replace("_results.json", "")
                try:
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        results = json.load(f)
                    
                    # Add a summary to the list
                    grids.append({
                        "id": grid_id,
                        "strategy_type": results.get("strategy_type", "unknown"),
                        "param1": results.get("param1", {}).get("name", ""),
                        "param2": results.get("param2", {}).get("name", ""),
                        "best_params": results.get("best_params"),
                        "completed_at": results.get("completed_at")
                    })
                except Exception as e:
                    logger.error(f"Error loading grid results {filename}: {e}")
        
        # Sort by completion time (newest first)
        grids.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
        
        return grids 
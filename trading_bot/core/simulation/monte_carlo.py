"""
Monte Carlo Simulation for Strategy Validation.

This module provides tools for performing Monte Carlo simulations on trading strategies.
These simulations help assess the robustness of strategies by creating multiple
alternative return sequences based on the original returns.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class MonteCarloSimulator:
    """
    Performs Monte Carlo simulations on strategy returns to evaluate robustness.
    """
    
    def __init__(
        self,
        num_simulations: int = 1000,
        confidence_interval: float = 0.95,
        preserve_autocorrelation: bool = True,
        block_size: Optional[int] = None,
        random_seed: Optional[int] = None
    ):
        """
        Initialize the Monte Carlo simulator.
        
        Args:
            num_simulations: Number of simulations to run
            confidence_interval: Confidence interval for results (0-1)
            preserve_autocorrelation: Whether to use block bootstrapping to preserve return autocorrelation
            block_size: Size of blocks for bootstrapping (if None, auto-calculated)
            random_seed: Random seed for reproducibility
        """
        self.num_simulations = num_simulations
        self.confidence_interval = confidence_interval
        self.preserve_autocorrelation = preserve_autocorrelation
        self.block_size = block_size
        
        # Set random seed if provided
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def simulate(
        self,
        returns: pd.Series,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on a series of returns.
        
        Args:
            returns: Series of period returns (not cumulative)
            initial_capital: Starting capital amount
            
        Returns:
            Dictionary with simulation results
        """
        if returns.empty:
            return {
                "status": "error",
                "message": "Empty returns series provided"
            }
        
        # Store original equity curve for comparison
        original_equity_curve = self._returns_to_equity(returns, initial_capital)
        
        # Run simulations
        simulated_equity_curves = []
        
        for i in range(self.num_simulations):
            if self.preserve_autocorrelation:
                # Block bootstrap to preserve autocorrelation
                simulated_returns = self._block_bootstrap(returns)
            else:
                # Simple random sampling with replacement
                simulated_returns = returns.sample(n=len(returns), replace=True)
            
            # Convert returns to equity curve
            equity_curve = self._returns_to_equity(simulated_returns, initial_capital)
            simulated_equity_curves.append(equity_curve)
        
        # Calculate statistics and percentiles
        results = self._calculate_statistics(simulated_equity_curves, original_equity_curve)
        
        return {
            "status": "success",
            "original_equity": original_equity_curve,
            "simulation_result": results,
            "percentiles": results["percentiles"],
            "drawdown_distribution": results["drawdown_distribution"],
            "final_equity_distribution": results["final_equity_distribution"],
            "plot_base64": self._generate_plot(simulated_equity_curves, original_equity_curve)
        }
    
    def _block_bootstrap(self, returns: pd.Series) -> pd.Series:
        """
        Perform block bootstrapping on returns to preserve autocorrelation.
        
        Args:
            returns: Original returns series
            
        Returns:
            Bootstrapped returns series
        """
        # Auto-calculate block size if not provided
        if self.block_size is None:
            # Rough heuristic: square root of series length
            self.block_size = int(np.sqrt(len(returns)))
        
        n = len(returns)
        blocks_needed = int(np.ceil(n / self.block_size))
        
        # Generate random starting points for blocks
        max_start = n - self.block_size + 1
        
        if max_start <= 0:
            # If series is too short, fall back to simple bootstrap
            return returns.sample(n=n, replace=True)
        
        start_indices = np.random.randint(0, max_start, size=blocks_needed)
        
        # Extract and concatenate blocks
        resampled_blocks = []
        for start in start_indices:
            end = min(start + self.block_size, n)
            block = returns.iloc[start:end]
            resampled_blocks.append(block)
        
        # Combine blocks and trim to original length
        result = pd.concat(resampled_blocks)
        return result.iloc[:n].copy()
    
    def _returns_to_equity(self, returns: pd.Series, initial_capital: float) -> pd.Series:
        """
        Convert a series of returns to an equity curve.
        
        Args:
            returns: Series of period returns (as decimal, not percentage)
            initial_capital: Starting capital
            
        Returns:
            Equity curve series
        """
        # Convert to compounding factors (1 + r)
        factors = 1 + returns
        
        # Calculate cumulative return using cumprod
        cumulative_returns = factors.cumprod()
        
        # Convert to equity values
        equity_curve = initial_capital * cumulative_returns
        return equity_curve
    
    def _calculate_statistics(
        self,
        simulated_equity_curves: List[pd.Series],
        original_equity_curve: pd.Series
    ) -> Dict[str, Any]:
        """
        Calculate statistics from simulated equity curves.
        
        Args:
            simulated_equity_curves: List of simulated equity curves
            original_equity_curve: Original equity curve
            
        Returns:
            Dictionary with statistics
        """
        # Stack equity curves into a DataFrame for analysis
        equity_df = pd.DataFrame(simulated_equity_curves).T
        
        # Calculate percentiles at each point
        lower_percentile = (1 - self.confidence_interval) / 2
        upper_percentile = 1 - lower_percentile
        
        percentiles = {
            "lower": equity_df.quantile(lower_percentile, axis=1),
            "median": equity_df.quantile(0.5, axis=1),
            "upper": equity_df.quantile(upper_percentile, axis=1)
        }
        
        # Calculate drawdowns for each simulation
        drawdowns = []
        for i in range(equity_df.shape[1]):
            curve = equity_df.iloc[:, i]
            drawdown = self._calculate_drawdown(curve)
            drawdowns.append(drawdown)
        
        # Calculate original drawdown
        original_drawdown = self._calculate_drawdown(original_equity_curve)
        
        # Calculate final equity distribution
        final_equities = equity_df.iloc[-1, :].values
        
        # Calculate statistics
        stats = {
            "percentiles": percentiles,
            "drawdown_distribution": {
                "mean": np.mean(drawdowns),
                "median": np.median(drawdowns),
                "95th_percentile": np.percentile(drawdowns, 95),
                "original": original_drawdown
            },
            "final_equity_distribution": {
                "mean": np.mean(final_equities),
                "median": np.median(final_equities),
                "lower": np.percentile(final_equities, lower_percentile * 100),
                "upper": np.percentile(final_equities, upper_percentile * 100),
                "original": original_equity_curve.iloc[-1]
            },
            "consistency_score": self._calculate_consistency_score(
                final_equities, original_equity_curve.iloc[-1], drawdowns, original_drawdown
            )
        }
        
        return stats
    
    def _calculate_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown for an equity curve.
        
        Args:
            equity_curve: Equity curve series
            
        Returns:
            Maximum drawdown as a decimal (not percentage)
        """
        # Calculate running maximum
        running_max = equity_curve.cummax()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        # Return maximum drawdown (as a positive number)
        return abs(drawdown.min())
    
    def _calculate_consistency_score(
        self,
        final_equities: np.ndarray,
        original_final_equity: float,
        drawdowns: List[float],
        original_drawdown: float
    ) -> float:
        """
        Calculate a consistency score based on how the original strategy
        compares to the distribution of simulated outcomes.
        
        Args:
            final_equities: Array of final equity values from simulations
            original_final_equity: Final equity of original strategy
            drawdowns: List of maximum drawdowns from simulations
            original_drawdown: Maximum drawdown of original strategy
            
        Returns:
            Consistency score (0-1, higher is better)
        """
        # Percentile of original strategy's final equity in the distribution
        final_equity_percentile = sum(original_final_equity >= final_equities) / len(final_equities)
        
        # Percentile of original strategy's drawdown in the distribution (reversed - lower is better)
        drawdown_percentile = sum(original_drawdown <= np.array(drawdowns)) / len(drawdowns)
        
        # Combined score: blend of final equity and drawdown percentiles
        # Higher = better performance than most simulations
        consistency_score = 0.7 * final_equity_percentile + 0.3 * drawdown_percentile
        
        return consistency_score
    
    def _generate_plot(
        self,
        simulated_equity_curves: List[pd.Series],
        original_equity_curve: pd.Series
    ) -> str:
        """
        Generate a plot of the simulation results and return as base64.
        
        Args:
            simulated_equity_curves: List of simulated equity curves
            original_equity_curve: Original equity curve
            
        Returns:
            Base64-encoded PNG image
        """
        try:
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Plot simulated equity curves (light gray)
            for curve in simulated_equity_curves[:100]:  # Limit to 100 curves for visibility
                plt.plot(curve.index, curve, color='lightgray', alpha=0.2)
            
            # Stack equity curves into a DataFrame for percentiles
            equity_df = pd.DataFrame(simulated_equity_curves).T
            
            # Calculate percentiles
            lower_percentile = (1 - self.confidence_interval) / 2
            upper_percentile = 1 - lower_percentile
            
            lower_curve = equity_df.quantile(lower_percentile, axis=1)
            median_curve = equity_df.quantile(0.5, axis=1)
            upper_curve = equity_df.quantile(upper_percentile, axis=1)
            
            # Plot percentile curves
            plt.plot(lower_curve.index, lower_curve, color='blue', alpha=0.7, linestyle='--', label=f"{lower_percentile*100:.1f}th Percentile")
            plt.plot(median_curve.index, median_curve, color='blue', alpha=0.8, linestyle='-', label="Median")
            plt.plot(upper_curve.index, upper_curve, color='blue', alpha=0.7, linestyle='--', label=f"{upper_percentile*100:.1f}th Percentile")
            
            # Plot original equity curve
            plt.plot(original_equity_curve.index, original_equity_curve, color='red', linewidth=2, label="Original Strategy")
            
            # Add labels and title
            plt.title("Monte Carlo Simulation of Strategy Performance")
            plt.xlabel("Date")
            plt.ylabel("Equity")
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save to BytesIO object
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            plt.close()
            
            # Convert to base64
            buf.seek(0)
            img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            return img_base64
        except Exception as e:
            logger.error(f"Error generating Monte Carlo plot: {e}")
            return "" 
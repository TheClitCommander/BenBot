"""
Base Backtester Interface for BensBot.

All asset-specific backtesting modules should inherit from this class
or implement a similar interface. This allows EvoTrader to use them
polymorphically.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import numpy as np
import logging
from datetime import datetime

from trading_bot.core.simulation.monte_carlo import MonteCarloSimulator

logger = logging.getLogger(__name__)

# Forward reference for StrategyGenome if needed, or use a more generic type for strategy_details
# from trading_bot.core.evolution.evo_trader import StrategyGenome 

class PerformanceMetrics(Dict[str, Any]):
    """TypedDict or Pydantic model could be used here for stricter metric definitions"""
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    trades: Optional[int] = None
    # Add out-of-sample and Monte Carlo metrics
    oos_total_return: Optional[float] = None
    oos_sharpe_ratio: Optional[float] = None
    oos_max_drawdown: Optional[float] = None
    consistency_score: Optional[float] = None
    monte_carlo_percentile_5: Optional[float] = None
    monte_carlo_percentile_95: Optional[float] = None
    monte_carlo_max_dd_percentile_95: Optional[float] = None
    # Add other common metrics as needed

class BacktestResult(Dict[str, Any]):
    """TypedDict or Pydantic model for stricter backtest result definitions"""
    status: str # e.g., "success", "failure", "error"
    strategy_id: str
    strategy_type: str # The type of strategy that was backtested (e.g., "equity_trend", "crypto_breakout")
    parameters: Dict[str, Any]
    performance: PerformanceMetrics
    error_message: Optional[str] = None
    # Optional: trade_log: Optional[List[Dict[str, Any]]] = None
    # Optional: equity_curve: Optional[pd.Series] = None
    monte_carlo_plot: Optional[str] = None  # Base64 encoded plot

class BaseBacktester(ABC):
    """
    Abstract Base Class for all backtesting engines.
    """

    def __init__(self, historical_data_fetcher: Any):
        """
        Args:
            historical_data_fetcher: An instance of HistoricalDataFetcher.
        """
        self.data_fetcher = historical_data_fetcher
        # self.trade_log = [] # Optional: for detailed trade logging
        
        # Create Monte Carlo simulator instance
        self.monte_carlo = MonteCarloSimulator(
            num_simulations=1000,
            confidence_interval=0.95,
            preserve_autocorrelation=True
        )
        
        # Default out-of-sample split
        self.oos_split = 0.3  # 30% for out-of-sample testing
        
        # Default minimum data points required for valid backtest
        self.min_data_points = 30

    @abstractmethod
    def run_backtest(
        self,
        strategy_id: str, # A unique ID for this particular strategy instance/genome
        strategy_class: Any, # The actual strategy class (e.g., EquityTrendStrategy)
        parameters: Dict[str, Any], # Parameters for the strategy instance
        asset_class: str, # e.g., "equity", "crypto", "forex"
        symbol: str, # The specific symbol to backtest on (e.g., "SPY", "BTC/USDT")
        start_date: str, # YYYY-MM-DD
        end_date: str,   # YYYY-MM-DD
        interval: str,   # Data interval (e.g., "1d", "1h")
        initial_capital: float = 100000.0,
        commission_pct: float = 0.001, # 0.1% commission per trade
        slippage_pct: float = 0.0005,  # 0.05% slippage per trade
        run_oos_validation: bool = True,  # Whether to run out-of-sample validation
        run_monte_carlo: bool = True      # Whether to run Monte Carlo simulation
    ) -> BacktestResult:
        """
        Runs a backtest for a given strategy, parameters, and market data.

        Args:
            strategy_id: Unique identifier for the strategy being tested.
            strategy_class: The strategy class to instantiate and test.
            parameters: Dictionary of parameters for the strategy.
            asset_class: The asset class of the symbol.
            symbol: The trading symbol to backtest on.
            start_date: Backtest start date.
            end_date: Backtest end date.
            interval: Data interval for the backtest.
            initial_capital: Starting capital for the backtest.
            commission_pct: Commission percentage per trade.
            slippage_pct: Slippage percentage per trade.
            run_oos_validation: Whether to run out-of-sample validation.
            run_monte_carlo: Whether to run Monte Carlo simulation.

        Returns:
            A BacktestResult dictionary containing performance metrics and status.
        """
        pass
    
    def _split_data_for_oos(
        self, 
        historical_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split historical data into in-sample and out-of-sample portions.
        
        Args:
            historical_data: Full historical data
            
        Returns:
            Tuple of (in_sample_data, out_of_sample_data)
        """
        if len(historical_data) < self.min_data_points:
            # Not enough data for meaningful split, use all as in-sample
            return historical_data, pd.DataFrame()
        
        split_idx = int(len(historical_data) * (1 - self.oos_split))
        
        in_sample = historical_data.iloc[:split_idx].copy()
        out_of_sample = historical_data.iloc[split_idx:].copy()
        
        logger.info(f"Split data into {len(in_sample)} in-sample and {len(out_of_sample)} out-of-sample records")
        
        return in_sample, out_of_sample
    
    def _run_monte_carlo_simulation(
        self,
        equity_curve: pd.Series,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on the backtest results.
        
        Args:
            equity_curve: The equity curve from the backtest
            initial_capital: Initial capital used in the backtest
            
        Returns:
            Dictionary with Monte Carlo simulation results
        """
        if equity_curve.empty or len(equity_curve) < self.min_data_points:
            return {
                "status": "error", 
                "message": f"Not enough data points for Monte Carlo simulation (need at least {self.min_data_points})"
            }
        
        # Calculate daily returns from equity curve
        returns = equity_curve.pct_change().dropna()
        
        # Run Monte Carlo simulation
        mc_result = self.monte_carlo.simulate(returns, initial_capital)
        
        if mc_result["status"] != "success":
            logger.warning(f"Monte Carlo simulation failed: {mc_result.get('message', 'Unknown error')}")
            return mc_result
        
        # Return the results
        return mc_result

    def _calculate_performance_metrics(
        self, 
        equity_curve: pd.Series, 
        trades: pd.DataFrame, # DataFrame of trades: [entry_time, exit_time, entry_price, exit_price, type, pnl, pnl_pct]
        initial_capital: float,
        oos_equity_curve: Optional[pd.Series] = None,
        oos_trades: Optional[pd.DataFrame] = None,
        monte_carlo_results: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetrics:
        """
        Calculates standard performance metrics from an equity curve and trade log.
        This is a helper that can be used by concrete backtester implementations.
        
        Args:
            equity_curve: Series of portfolio values over time
            trades: DataFrame of trades executed
            initial_capital: Initial capital for the backtest
            oos_equity_curve: Out-of-sample equity curve (if available)
            oos_trades: Out-of-sample trades (if available)
            monte_carlo_results: Results from Monte Carlo simulation (if available)
            
        Returns:
            PerformanceMetrics dictionary with calculated metrics
        """
        metrics = PerformanceMetrics()
        if equity_curve.empty:
            return metrics

        metrics["total_return"] = ((equity_curve.iloc[-1] / initial_capital) - 1) * 100
        
        daily_returns = equity_curve.pct_change().dropna()
        if not daily_returns.empty:
            # Assuming risk-free rate is 0 for simplicity for Sharpe Ratio
            # And assuming daily data for annualization factor of 252 trading days
            # This needs to be adjusted based on actual data frequency (e.g. for hourly data)
            annualization_factor = 252 # TODO: Make this dependent on interval
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(annualization_factor)
            metrics["sharpe_ratio"] = sharpe_ratio if pd.notnull(sharpe_ratio) else 0.0
        else:
            metrics["sharpe_ratio"] = 0.0

        # Max Drawdown
        cumulative_max = equity_curve.cummax()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        metrics["max_drawdown"] = drawdown.min() * 100 if pd.notnull(drawdown.min()) else 0.0

        if not trades.empty:
            metrics["trades"] = len(trades)
            winning_trades = trades[trades['pnl'] > 0]
            metrics["win_rate"] = (len(winning_trades) / len(trades)) * 100 if len(trades) > 0 else 0.0
        else:
            metrics["trades"] = 0
            metrics["win_rate"] = 0.0
            
        # Calculate out-of-sample metrics if available
        if oos_equity_curve is not None and not oos_equity_curve.empty:
            oos_initial = oos_equity_curve.iloc[0]
            metrics["oos_total_return"] = ((oos_equity_curve.iloc[-1] / oos_initial) - 1) * 100
            
            oos_daily_returns = oos_equity_curve.pct_change().dropna()
            if not oos_daily_returns.empty:
                oos_sharpe = (oos_daily_returns.mean() / oos_daily_returns.std()) * np.sqrt(annualization_factor)
                metrics["oos_sharpe_ratio"] = oos_sharpe if pd.notnull(oos_sharpe) else 0.0
            else:
                metrics["oos_sharpe_ratio"] = 0.0
            
            # OOS Max Drawdown
            oos_cumulative_max = oos_equity_curve.cummax()
            oos_drawdown = (oos_equity_curve - oos_cumulative_max) / oos_cumulative_max
            metrics["oos_max_drawdown"] = oos_drawdown.min() * 100 if pd.notnull(oos_drawdown.min()) else 0.0
        
        # Add Monte Carlo metrics if available
        if monte_carlo_results and monte_carlo_results.get("status") == "success":
            # Consistency score from Monte Carlo
            metrics["consistency_score"] = monte_carlo_results["simulation_result"].get("consistency_score", 0.0)
            
            # Final equity percentiles
            final_equity_dist = monte_carlo_results["final_equity_distribution"]
            metrics["monte_carlo_percentile_5"] = final_equity_dist.get("lower")
            metrics["monte_carlo_percentile_95"] = final_equity_dist.get("upper")
            
            # Max drawdown percentiles
            dd_dist = monte_carlo_results["drawdown_distribution"]
            metrics["monte_carlo_max_dd_percentile_95"] = dd_dist.get("95th_percentile", 0.0) * 100  # Convert to percentage
            
        logger.debug(f"Calculated performance metrics: {metrics}")
        return metrics
        
    def _apply_slippage_and_commission(
        self, 
        price: float, 
        side: str, 
        slippage_pct: float, 
        commission_pct: float,
        is_entry: bool = True
    ) -> float:
        """
        Apply slippage and commission to a trade price.
        
        Args:
            price: Original price
            side: 'buy' or 'sell'
            slippage_pct: Percentage slippage
            commission_pct: Percentage commission
            is_entry: Whether this is an entry trade
            
        Returns:
            Effective price after slippage and commission
        """
        # Slippage makes buy prices higher and sell prices lower
        if side.lower() == 'buy':
            # For buy: increase price by slippage
            price_with_slippage = price * (1 + slippage_pct)
            # Add commission (increases effective buy price)
            effective_price = price_with_slippage * (1 + commission_pct)
        else:  # 'sell'
            # For sell: decrease price by slippage
            price_with_slippage = price * (1 - slippage_pct)
            # Subtract commission (decreases effective sell price)
            effective_price = price_with_slippage * (1 - commission_pct)
            
        return effective_price 
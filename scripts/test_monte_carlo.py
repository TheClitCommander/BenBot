#!/usr/bin/env python3
"""
Test script for the Monte Carlo simulation module.

This script:
1. Loads historical data for a symbol
2. Runs a simple strategy backtest
3. Passes the results to the Monte Carlo simulator
4. Visualizes and prints the simulation results
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import components
from trading_bot.utils.logging_setup import setup_logging, get_component_logger
from trading_bot.core.simulation.monte_carlo import MonteCarloSimulator
from trading_bot.core.data.historical_data_fetcher import HistoricalDataFetcher
from trading_bot.core.strategies.general.trend_following_strategy import TrendFollowingStrategy

# Setup logging
setup_logging()
logger = get_component_logger('scripts.test_monte_carlo')

def simple_backtest(historical_data, initial_capital=10000.0):
    """
    Run a simple moving average crossover backtest.
    
    Args:
        historical_data: DataFrame with OHLCV data
        initial_capital: Initial capital
        
    Returns:
        Tuple of (equity_curve, trade_log)
    """
    # Create strategy
    strategy = TrendFollowingStrategy(
        strategy_id="test_trend_following",
        parameters={
            "fast_ma_period": 20,
            "slow_ma_period": 50,
            "trend_strength_threshold": 0.0,
            "stop_loss_pct": 2.0
        },
        asset_class="equity"
    )
    
    # Generate signals
    signals_df = strategy.generate_signals(historical_data)
    
    # Simple portfolio simulation
    positions = pd.Series(index=historical_data.index, dtype=float).fillna(0.0)
    equity_curve = pd.Series(index=historical_data.index, dtype=float).fillna(initial_capital)
    cash = initial_capital
    shares = 0
    trade_log = []
    
    # Simulate trading
    for i, idx in enumerate(historical_data.index):
        if i == 0:
            continue  # Skip the first day
            
        current_price = historical_data.loc[idx, 'Close']
        signal = signals_df.loc[idx, 'signal'] if idx in signals_df.index else 0
        
        # Update portfolio value
        equity_curve.loc[idx] = cash + shares * current_price
        
        # Process signals
        if signal == 1 and shares == 0:  # Buy signal
            shares = cash / current_price
            cash = 0
            trade_log.append({
                'entry_date': idx,
                'entry_price': current_price,
                'shares': shares,
                'direction': 'long'
            })
        elif signal == -1 and shares > 0:  # Sell signal
            cash = shares * current_price
            trade_log.append({
                'exit_date': idx,
                'exit_price': current_price,
                'shares': shares,
                'direction': 'long',
                'pnl': cash - trade_log[-1].get('shares', 0) * trade_log[-1].get('entry_price', 0)
            })
            shares = 0
    
    return equity_curve, trade_log

def run_monte_carlo_test(symbol, asset_class, start_date, end_date, initial_capital=10000.0, 
                        num_simulations=1000, preserve_autocorrelation=True):
    """
    Run Monte Carlo simulation on a simple backtest.
    
    Args:
        symbol: Symbol to test
        asset_class: Asset class
        start_date: Start date
        end_date: End date
        initial_capital: Initial capital
        num_simulations: Number of Monte Carlo simulations
        preserve_autocorrelation: Whether to preserve return autocorrelation
        
    Returns:
        Monte Carlo simulation results
    """
    # Initialize data fetcher
    data_fetcher = HistoricalDataFetcher()
    
    # Fetch historical data
    logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
    historical_data = data_fetcher.fetch(
        symbol=symbol,
        asset_class=asset_class,
        start_date=start_date,
        end_date=end_date,
        interval='1d'
    )
    
    if historical_data is None or historical_data.empty:
        logger.error(f"Failed to fetch data for {symbol}")
        return None
    
    logger.info(f"Running backtest for {symbol}")
    equity_curve, trade_log = simple_backtest(historical_data, initial_capital)
    
    # Create and run Monte Carlo simulator
    logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")
    simulator = MonteCarloSimulator(
        num_simulations=num_simulations,
        confidence_interval=0.95,
        preserve_autocorrelation=preserve_autocorrelation
    )
    
    # Calculate returns from equity curve
    returns = equity_curve.pct_change().dropna()
    
    # Run simulation
    mc_results = simulator.simulate(returns, initial_capital)
    
    if mc_results["status"] == "success":
        # Print simulation results
        logger.info("Monte Carlo Simulation Results")
        
        consistency = mc_results["simulation_result"]["consistency_score"]
        logger.info(f"Consistency Score: {consistency:.2f}")
        
        drawdown_dist = mc_results["drawdown_distribution"]
        logger.info(f"Original Max Drawdown: {drawdown_dist['original'] * 100:.2f}%")
        logger.info(f"95th Percentile Max Drawdown: {drawdown_dist['95th_percentile'] * 100:.2f}%")
        
        equity_dist = mc_results["final_equity_distribution"]
        logger.info(f"Original Final Equity: ${equity_dist['original']:.2f}")
        logger.info(f"Median Final Equity: ${equity_dist['median']:.2f}")
        logger.info(f"5th Percentile Final Equity: ${equity_dist['lower']:.2f}")
        logger.info(f"95th Percentile Final Equity: ${equity_dist['upper']:.2f}")
        
        # Save the plot if it was generated
        if mc_results.get("plot_base64"):
            import base64
            
            plot_data = base64.b64decode(mc_results["plot_base64"])
            with open(f"monte_carlo_{symbol}_{datetime.now().strftime('%Y%m%d')}.png", "wb") as f:
                f.write(plot_data)
                logger.info("Monte Carlo plot saved to file")
    else:
        logger.error(f"Monte Carlo simulation failed: {mc_results.get('message', 'Unknown error')}")
    
    return mc_results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Monte Carlo simulation")
    
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="SPY",
        help="Symbol to test"
    )
    
    parser.add_argument(
        "--asset_class", 
        type=str, 
        default="equity",
        choices=["equity", "crypto", "forex"],
        help="Asset class"
    )
    
    parser.add_argument(
        "--days", 
        type=int, 
        default=365,
        help="Number of days of historical data to use"
    )
    
    parser.add_argument(
        "--capital", 
        type=float, 
        default=10000.0,
        help="Initial capital"
    )
    
    parser.add_argument(
        "--simulations", 
        type=int, 
        default=1000,
        help="Number of Monte Carlo simulations"
    )
    
    parser.add_argument(
        "--no-autocorrelation", 
        action="store_true",
        help="Disable autocorrelation preservation"
    )
    
    args = parser.parse_args()
    
    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    # Run test
    results = run_monte_carlo_test(
        symbol=args.symbol,
        asset_class=args.asset_class,
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital,
        num_simulations=args.simulations,
        preserve_autocorrelation=not args.no_autocorrelation
    )
    
    return results

if __name__ == "__main__":
    main() 
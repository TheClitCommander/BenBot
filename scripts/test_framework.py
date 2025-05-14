#!/usr/bin/env python3
"""
Test script for the enhanced BensBot trading framework.

This script tests:
1. Backtesting the TrendFollowingStrategy across asset classes
2. Parallel backtesting with a large population
3. Strategy transfer learning between markets
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the project root to sys.path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import BensBot components
from trading_bot import initialize_system
from trading_bot.utils.logging_setup import setup_logging, get_component_logger
from trading_bot.core.strategies.general.trend_following_strategy import TrendFollowingStrategy
from trading_bot.core.strategies.strategy_factory import strategy_factory
from trading_bot.core.strategies.multi_asset_strategy import MultiAssetStrategy
from trading_bot.core.evolution.evo_trader import StrategyGenome

# Setup logging
logger = get_component_logger('scripts.test_framework')
logger.info("Starting framework test script")

def test_trend_following_across_assets(system_components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test the TrendFollowingStrategy across different asset classes.
    
    Args:
        system_components: Dictionary of initialized system components
        
    Returns:
        Dictionary of test results
    """
    logger.info("Testing TrendFollowingStrategy across asset classes")
    
    # Get components
    data_fetcher = system_components["data_fetcher"]
    backtester_registry = system_components["backtester_registry"]
    
    # Define test parameters
    test_period_days = 180  # 6 months
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=test_period_days)).strftime('%Y-%m-%d')
    
    # Test assets for each class
    test_assets = {
        "equity": "SPY",     # S&P 500 ETF
        "crypto": "BTC/USDT", # Bitcoin
        "forex": "EURUSD=X"   # Euro/USD
    }
    
    results = {}
    
    # Test each asset class
    for asset_class, symbol in test_assets.items():
        logger.info(f"Testing {asset_class} strategy on {symbol}")
        
        # Create strategy instance for this asset class
        strategy_id = f"test_trend_following_{asset_class}_{int(time.time())}"
        
        # Use default parameters from the strategy
        parameters = {}
        for name, config in TrendFollowingStrategy.get_parameter_schema().items():
            if "default" in config:
                parameters[name] = config["default"]
        
        # Create strategy instance
        strategy = TrendFollowingStrategy(
            strategy_id=strategy_id,
            parameters=parameters,
            asset_class=asset_class
        )
        
        # Get appropriate backtester
        backtester = backtester_registry.get(asset_class)
        if not backtester:
            logger.error(f"No backtester found for asset class: {asset_class}")
            results[asset_class] = {"status": "error", "message": "No backtester found"}
            continue
        
        # Run backtest
        backtest_result = backtester.run_backtest(
            strategy_id=strategy_id,
            strategy_class=TrendFollowingStrategy,
            parameters=parameters,
            asset_class=asset_class,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="1d",
            initial_capital=10000.0
        )
        
        # Store results
        results[asset_class] = backtest_result
        
        # Log performance metrics
        if backtest_result["status"] == "success":
            performance = backtest_result["performance"]
            logger.info(f"{asset_class} backtest results:")
            logger.info(f"  Total Return: {performance.get('total_return', 'N/A'):.2f}%")
            logger.info(f"  Sharpe Ratio: {performance.get('sharpe_ratio', 'N/A'):.2f}")
            logger.info(f"  Max Drawdown: {performance.get('max_drawdown', 'N/A'):.2f}%")
            logger.info(f"  Win Rate: {performance.get('win_rate', 'N/A'):.2f}%")
            logger.info(f"  Total Trades: {performance.get('trades', 'N/A')}")
        else:
            logger.error(f"{asset_class} backtest failed: {backtest_result.get('error_message', 'Unknown error')}")
    
    return results

def test_strategy_transfer_learning(system_components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test transfer learning by adapting a strategy between asset classes.
    
    Args:
        system_components: Dictionary of initialized system components
        
    Returns:
        Dictionary of test results
    """
    logger.info("Testing strategy transfer learning between markets")
    
    # Get components
    data_fetcher = system_components["data_fetcher"]
    backtester_registry = system_components["backtester_registry"]
    
    # Define test parameters
    test_period_days = 180  # 6 months
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=test_period_days)).strftime('%Y-%m-%d')
    
    # Test assets
    test_assets = {
        "equity": "SPY",     # S&P 500 ETF
        "crypto": "BTC/USDT", # Bitcoin
        "forex": "EURUSD=X"   # Euro/USD
    }
    
    # Test transfer paths
    transfer_paths = [
        ("equity", "crypto"),
        ("crypto", "forex"),
        ("forex", "equity")
    ]
    
    results = {}
    
    for source, target in transfer_paths:
        logger.info(f"Testing transfer learning from {source} to {target}")
        
        # Create strategy instance for source asset class
        strategy_id = f"transfer_test_{source}_to_{target}_{int(time.time())}"
        
        # Use default parameters from the strategy
        parameters = {}
        for name, config in TrendFollowingStrategy.get_parameter_schema().items():
            if "default" in config:
                parameters[name] = config["default"]
        
        # Create strategy instance with source asset class
        strategy = TrendFollowingStrategy(
            strategy_id=strategy_id,
            parameters=parameters,
            asset_class=source
        )
        
        # Test on source asset class first
        source_backtester = backtester_registry.get(source)
        source_result = source_backtester.run_backtest(
            strategy_id=strategy_id,
            strategy_class=TrendFollowingStrategy,
            parameters=parameters,
            asset_class=source,
            symbol=test_assets[source],
            start_date=start_date,
            end_date=end_date,
            interval="1d",
            initial_capital=10000.0
        )
        
        # Log source results
        if source_result["status"] == "success":
            performance = source_result["performance"]
            logger.info(f"Source ({source}) performance:")
            logger.info(f"  Total Return: {performance.get('total_return', 'N/A'):.2f}%")
            logger.info(f"  Sharpe Ratio: {performance.get('sharpe_ratio', 'N/A'):.2f}")
        
        # Now adapt the strategy to target asset class
        adaptation_changes = strategy.adapt_to_asset_class(target, preserve_params=True)
        logger.info(f"Adaptation changes: {adaptation_changes}")
        
        # Test on target asset class
        target_backtester = backtester_registry.get(target)
        target_result = target_backtester.run_backtest(
            strategy_id=f"{strategy_id}_adapted",
            strategy_class=TrendFollowingStrategy,
            parameters=strategy.parameters,  # Use the adapted parameters
            asset_class=target,
            symbol=test_assets[target],
            start_date=start_date,
            end_date=end_date,
            interval="1d",
            initial_capital=10000.0
        )
        
        # Log target results
        if target_result["status"] == "success":
            performance = target_result["performance"]
            logger.info(f"Target ({target}) performance after adaptation:")
            logger.info(f"  Total Return: {performance.get('total_return', 'N/A'):.2f}%")
            logger.info(f"  Sharpe Ratio: {performance.get('sharpe_ratio', 'N/A'):.2f}")
        
        # Store results
        results[f"{source}_to_{target}"] = {
            "source_result": source_result,
            "target_result": target_result,
            "adaptation_changes": adaptation_changes
        }
    
    return results

def test_parallel_backtesting(system_components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test parallel backtesting with a large population.
    
    Args:
        system_components: Dictionary of initialized system components
        
    Returns:
        Dictionary of test results
    """
    logger.info("Testing parallel backtesting with a large population")
    
    # Get components
    evo_trader = system_components["evo_trader"]
    
    # Test parameters
    asset_class = "equity"  # Use equity for the large population test
    symbol = "SPY"
    population_size = 50    # Use a decent-sized population to test parallelism
    test_period_days = 180  # 6 months
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=test_period_days)).strftime('%Y-%m-%d')
    
    # Register the trend following strategy if not already registered
    if "general_trendfollowingstrategy" not in strategy_factory.get_all_metadata():
        strategy_factory.register_strategy(
            strategy_type="general_trendfollowingstrategy",
            strategy_class=TrendFollowingStrategy,
            asset_class="general",
            description="Multi-asset trend following strategy"
        )
    
    # Configure evolution parameters
    backtest_config = {
        "asset_class": asset_class,
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "interval": "1d",
        "initial_capital": 10000.0
    }
    
    # Create a custom parameter space for more diverse strategies
    custom_parameter_space = {
        "fast_ma_period": {"type": "int", "min": 3, "max": 50},
        "slow_ma_period": {"type": "int", "min": 20, "max": 200},
        "trend_smoothing": {"type": "float", "min": 0.0, "max": 0.9},
        "stop_loss_pct": {"type": "float", "min": 0.5, "max": 5.0}
    }
    
    # Start evolution - this will just initialize the population
    run_id = evo_trader.start_evolution(
        strategy_type_name="general_trendfollowingstrategy",
        backtest_config=backtest_config,
        custom_parameter_space=custom_parameter_space
    )
    
    # Time the parallel backtest process
    start_time = time.time()
    
    # Run backtests using parallel processing
    result = evo_trader.run_backtest_generation(backtest_config)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Log results
    logger.info(f"Parallel backtesting completed in {duration:.2f} seconds")
    logger.info(f"Tested {result['population_size']} strategies")
    
    if result.get("best_strategy_performance"):
        best_perf = result["best_strategy_performance"]
        logger.info(f"Best strategy performance:")
        logger.info(f"  Total Return: {best_perf.get('total_return', 'N/A'):.2f}%")
        logger.info(f"  Sharpe Ratio: {best_perf.get('sharpe_ratio', 'N/A'):.2f}")
    
    # Also include average metrics
    if result.get("avg_performance"):
        avg_perf = result["avg_performance"]
        logger.info(f"Average population performance:")
        logger.info(f"  Total Return: {avg_perf.get('total_return', 'N/A'):.2f}%")
        logger.info(f"  Sharpe Ratio: {avg_perf.get('sharpe_ratio', 'N/A'):.2f}")
    
    return {
        "run_id": run_id,
        "duration": duration,
        "population_size": result["population_size"],
        "best_performance": result.get("best_strategy_performance"),
        "avg_performance": result.get("avg_performance")
    }

def main():
    """Main test function."""
    logger.info("Initializing system components...")
    
    # Initialize the system
    system_components = initialize_system()
    
    # Run the tests
    test_results = {}
    
    # Test 1: TrendFollowingStrategy across asset classes
    test_results["trend_following_test"] = test_trend_following_across_assets(system_components)
    
    # Test 2: Strategy transfer learning
    test_results["transfer_learning_test"] = test_strategy_transfer_learning(system_components)
    
    # Test 3: Parallel backtesting
    test_results["parallel_backtesting_test"] = test_parallel_backtesting(system_components)
    
    # Print summary
    logger.info("=== Framework Test Summary ===")
    
    # Trend following test summary
    tf_test = test_results["trend_following_test"]
    logger.info("Trend Following Strategy Test:")
    for asset_class, result in tf_test.items():
        status = result.get("status", "unknown")
        if status == "success":
            perf = result.get("performance", {})
            logger.info(f"  {asset_class.capitalize()}: "
                       f"Return: {perf.get('total_return', 'N/A'):.2f}%, "
                       f"Sharpe: {perf.get('sharpe_ratio', 'N/A'):.2f}")
        else:
            logger.info(f"  {asset_class.capitalize()}: Failed - {result.get('error_message', 'Unknown error')}")
    
    # Transfer learning test summary
    tf_learning = test_results["transfer_learning_test"]
    logger.info("Transfer Learning Test:")
    for path, result in tf_learning.items():
        source_result = result.get("source_result", {})
        target_result = result.get("target_result", {})
        
        src_perf = source_result.get("performance", {}) if source_result.get("status") == "success" else {}
        tgt_perf = target_result.get("performance", {}) if target_result.get("status") == "success" else {}
        
        logger.info(f"  {path}: "
                   f"Source Return: {src_perf.get('total_return', 'N/A'):.2f}%, "
                   f"Target Return: {tgt_perf.get('total_return', 'N/A'):.2f}%")
    
    # Parallel backtesting summary
    parallel_test = test_results["parallel_backtesting_test"]
    logger.info("Parallel Backtesting Test:")
    logger.info(f"  Runtime: {parallel_test.get('duration', 'N/A'):.2f} seconds")
    logger.info(f"  Population Size: {parallel_test.get('population_size', 'N/A')}")
    
    best_perf = parallel_test.get("best_performance", {})
    if best_perf:
        logger.info(f"  Best Return: {best_perf.get('total_return', 'N/A'):.2f}%, "
                   f"Sharpe: {best_perf.get('sharpe_ratio', 'N/A'):.2f}")
    
    logger.info("Framework test completed!")
    return test_results

if __name__ == "__main__":
    main() 
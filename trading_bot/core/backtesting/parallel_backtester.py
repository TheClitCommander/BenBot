"""
Parallel Backtesting Module for BensBot.

This module provides utilities for running backtests in parallel
using multiprocessing, accelerating the evaluation of strategy genomes.
"""

import logging
import time
import multiprocessing as mp
from typing import Dict, Any, List, Callable, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

from trading_bot.core.backtesting.base_backtester import BacktestResult

logger = logging.getLogger(__name__)

def _run_backtest_worker(
    backtester_constructor: Callable,
    backtester_kwargs: Dict[str, Any],
    backtest_args: Tuple
) -> Tuple[str, BacktestResult]:
    """
    Worker function that runs a single backtest in a separate process.
    
    Args:
        backtester_constructor: A function that returns a configured backtester instance
        backtester_kwargs: Keyword args for creating the backtester
        backtest_args: Tuple containing (strategy_id, strategy_class, parameters, backtest_config)
        
    Returns:
        Tuple of (strategy_id, BacktestResult)
    """
    strategy_id, strategy_class, parameters, backtest_config = backtest_args
    
    try:
        # Create the backtester instance in this process
        backtester = backtester_constructor(**backtester_kwargs)
        
        # Run the backtest
        result = backtester.run_backtest(
            strategy_id=strategy_id,
            strategy_class=strategy_class,
            parameters=parameters,
            **backtest_config
        )
        
        return strategy_id, result
    except Exception as e:
        logger.error(f"Error in backtest worker for {strategy_id}: {e}")
        # Return a failed backtest result
        error_result = BacktestResult(
            status="error",
            strategy_id=strategy_id,
            strategy_type=strategy_class.__name__ if strategy_class else "unknown",
            parameters=parameters,
            performance={},
            error_message=f"Parallel backtest error: {str(e)}"
        )
        return strategy_id, error_result

def run_parallel_backtests(
    backtester_constructor: Callable,
    backtester_kwargs: Dict[str, Any],
    strategy_genomes: List[Dict[str, Any]],
    strategy_classes: Dict[str, Any],
    backtest_config: Dict[str, Any],
    max_workers: Optional[int] = None
) -> Dict[str, BacktestResult]:
    """
    Run multiple backtests in parallel using a process pool.
    
    Args:
        backtester_constructor: A function that returns a configured backtester instance
        backtester_kwargs: Keyword args for creating the backtester (like historical_data_fetcher)
        strategy_genomes: List of strategy genome dictionaries with id, type, parameters, etc.
        strategy_classes: Dictionary mapping strategy types to actual strategy classes
        backtest_config: Configuration for the backtest (symbol, dates, etc.)
        max_workers: Maximum number of parallel processes (default: CPU count)
        
    Returns:
        Dictionary mapping strategy_id to BacktestResult
    """
    if max_workers is None:
        max_workers = mp.cpu_count()
    
    # Prepare backtest arguments
    backtest_args = []
    for genome in strategy_genomes:
        strategy_id = genome['id']
        strategy_type = genome['type']
        parameters = genome['parameters']
        
        if strategy_type not in strategy_classes:
            logger.error(f"Strategy type {strategy_type} not found in registry")
            continue
            
        strategy_class = strategy_classes[strategy_type]
        backtest_args.append((strategy_id, strategy_class, parameters, backtest_config))
    
    results = {}
    start_time = time.time()
    logger.info(f"Starting parallel backtest of {len(backtest_args)} strategies using {max_workers} workers")
    
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all backtest jobs
            future_to_id = {
                executor.submit(_run_backtest_worker, backtester_constructor, backtester_kwargs, args): args[0]
                for args in backtest_args
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_id):
                strategy_id, result = future.result()
                results[strategy_id] = result
                
                # Log progress
                if len(results) % 10 == 0 or len(results) == len(backtest_args):
                    logger.info(f"Completed {len(results)}/{len(backtest_args)} backtests")
    except Exception as e:
        logger.error(f"Error in parallel backtesting: {e}")
    
    # Check for missing results and report
    missing_ids = set(genome['id'] for genome in strategy_genomes) - set(results.keys())
    if missing_ids:
        logger.warning(f"Missing results for {len(missing_ids)} strategies: {missing_ids}")
    
    # Report timing
    duration = time.time() - start_time
    strategies_per_second = len(results) / duration if duration > 0 else 0
    logger.info(f"Parallel backtesting completed in {duration:.2f} seconds "
                f"({strategies_per_second:.2f} strategies/second)")
    
    return results

class ParallelBacktestManager:
    """
    Manager class for parallel backtesting that integrates with EvoTrader.
    """
    
    def __init__(
        self,
        backtester_constructors: Dict[str, Callable],
        backtester_constructor_kwargs: Dict[str, Dict[str, Any]]
    ):
        """
        Initialize the parallel backtest manager.
        
        Args:
            backtester_constructors: Dictionary mapping asset classes to backtester constructor functions
            backtester_constructor_kwargs: Dictionary mapping asset classes to kwargs for backtester constructors
        """
        self.backtester_constructors = backtester_constructors
        self.backtester_constructor_kwargs = backtester_constructor_kwargs
    
    def run_generation_backtests(
        self,
        strategy_genomes: List[Dict[str, Any]],
        strategy_classes: Dict[str, Any],
        backtest_config: Dict[str, Any],
        max_workers: Optional[int] = None
    ) -> Dict[str, BacktestResult]:
        """
        Run backtests for an entire generation of strategies in parallel.
        
        Args:
            strategy_genomes: List of strategy genome dictionaries
            strategy_classes: Dictionary mapping strategy types to actual strategy classes
            backtest_config: Configuration for the backtest
            max_workers: Maximum number of parallel processes
            
        Returns:
            Dictionary mapping strategy_id to BacktestResult
        """
        asset_class = backtest_config.get("asset_class")
        if not asset_class:
            raise ValueError("asset_class must be specified in backtest_config")
        
        backtester_constructor = self.backtester_constructors.get(asset_class)
        if not backtester_constructor:
            raise ValueError(f"No backtester constructor registered for asset class: {asset_class}")
        
        backtester_kwargs = self.backtester_constructor_kwargs.get(asset_class, {})
        
        return run_parallel_backtests(
            backtester_constructor=backtester_constructor,
            backtester_kwargs=backtester_kwargs,
            strategy_genomes=strategy_genomes,
            strategy_classes=strategy_classes,
            backtest_config=backtest_config,
            max_workers=max_workers
        ) 
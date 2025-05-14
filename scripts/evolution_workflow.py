#!/usr/bin/env python3
"""
Evolution Workflow for BensBot.

This script implements a complete evolution workflow that:
1. Identifies optimal asset classes based on market regimes
2. Evolves strategies tailored to current market conditions
3. Transfers successful strategies between markets
4. Manages capital allocation dynamically
"""

import os
import sys
import time
import logging
import json
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Any, Optional

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import components
from trading_bot.utils.logging_setup import setup_logging, get_component_logger
from trading_bot.core.data.historical_data_fetcher import HistoricalDataFetcher
from trading_bot.core.evolution.evo_trader import EvoTrader
from trading_bot.core.evolution.market_adapter import MarketAdapter, MarketRegime
from trading_bot.core.portfolio.allocator import PortfolioAllocator
from trading_bot.core.strategies.strategy_factory import strategy_factory
from trading_bot.core.strategies.general.trend_following_strategy import TrendFollowingStrategy
from trading_bot.core.strategies.general.mean_reversion_strategy import MeanReversionStrategy
from trading_bot.core.strategies.general.volatility_strategy import VolatilityStrategy

# Setup logging
setup_logging(log_level="INFO")
logger = get_component_logger('scripts.evolution_workflow')

class EvolutionWorkflow:
    """
    Implements a complete evolution workflow for cross-asset strategy development.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        total_capital: float = 100000.0,
        evolution_generations: int = 20,
        population_size: int = 50,
        max_strategies_per_asset_class: int = 5,
        test_period_days: int = 180
    ):
        """
        Initialize the evolution workflow.
        
        Args:
            config_path: Path to configuration file (if None, use defaults)
            total_capital: Total capital to allocate across strategies
            evolution_generations: Number of generations to evolve strategies
            population_size: Size of strategy population for evolution
            max_strategies_per_asset_class: Maximum number of active strategies per asset class
            test_period_days: Number of days for backtest evaluation
        """
        self.total_capital = total_capital
        self.evolution_generations = evolution_generations
        self.population_size = population_size
        self.max_strategies_per_asset_class = max_strategies_per_asset_class
        self.test_period_days = test_period_days
        
        # Load configuration if provided
        if config_path:
            self._load_config(config_path)
        
        # Initialize components
        self.data_fetcher = HistoricalDataFetcher()
        
        # Initialize portfolio allocator
        self.portfolio_allocator = PortfolioAllocator(
            total_capital=total_capital,
            allocation_model="asset_class_balanced",
            min_allocation_pct=0.05,
            max_allocation_pct=0.25,
            reserve_capital_pct=0.15
        )
        
        # Initialize EvoTrader
        self.evo_trader = EvoTrader()
        
        # Initialize market adapter
        self.market_adapter = MarketAdapter(
            data_fetcher=self.data_fetcher,
            evo_trader=self.evo_trader,
            portfolio_allocator=self.portfolio_allocator,
            lookback_days=90,
            update_frequency_hours=12
        )
        
        # Track active strategies by asset class
        self.active_strategies: Dict[str, List[Dict[str, Any]]] = {
            "equity": [],
            "crypto": [],
            "forex": []
        }
        
        # Track best performing strategies
        self.best_strategies: Dict[str, Dict[str, Any]] = {}
        
        # Track workflow stats
        self.workflow_stats = {
            "evolution_runs": 0,
            "successful_transfers": 0,
            "start_time": datetime.now().isoformat(),
            "last_run_time": None
        }
    
    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Override defaults with config values
            self.total_capital = config.get('total_capital', self.total_capital)
            self.evolution_generations = config.get('evolution_generations', self.evolution_generations)
            self.population_size = config.get('population_size', self.population_size)
            self.max_strategies_per_asset_class = config.get('max_strategies_per_asset_class', self.max_strategies_per_asset_class)
            self.test_period_days = config.get('test_period_days', self.test_period_days)
            
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
    
    def run_workflow(self) -> Dict[str, Any]:
        """
        Run the complete evolution workflow.
        
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        logger.info("Starting evolution workflow")
        
        # Step 1: Update market regimes
        logger.info("Updating market regimes")
        regime_update = self.market_adapter.update_market_regimes(force=True)
        
        # Step 2: Get allocation recommendations
        logger.info("Getting allocation recommendations")
        allocation_recs = self.market_adapter.recommend_strategy_allocation()
        
        # Step 3: Evolve strategies for each asset class
        evolved_strategies = {}
        
        for asset_class, regime_info in self.market_adapter.current_regimes.items():
            logger.info(f"Starting evolution for {asset_class} in {regime_info.get('primary_regime')} regime")
            
            # Select strategy types based on regime
            strategy_types = allocation_recs["strategy_type_recommendations"].get(asset_class, [])
            
            if not strategy_types:
                logger.warning(f"No strategy types recommended for {asset_class}. Skipping.")
                continue
            
            # Evolve strategies for this asset class
            evolution_result = self._evolve_strategies_for_asset_class(
                asset_class, 
                regime_info.get('primary_regime', MarketRegime.UNKNOWN),
                strategy_types
            )
            
            evolved_strategies[asset_class] = evolution_result
            
            # Update workflow stats
            self.workflow_stats["evolution_runs"] += 1
        
        # Step 4: Register best strategies with portfolio allocator
        self._register_strategies_with_allocator(evolved_strategies)
        
        # Step 5: Try transfer learning between asset classes
        transfer_results = self._perform_transfer_learning()
        
        # Step 6: Allocate capital
        allocation_result = self.portfolio_allocator.allocate_capital(
            allocation_model="performance_weighted",
            force_rebalance=True
        )
        
        # Final summary
        duration = time.time() - start_time
        self.workflow_stats["last_run_time"] = datetime.now().isoformat()
        self.workflow_stats["last_run_duration"] = duration
        
        summary = {
            "market_regimes": self.market_adapter.current_regimes,
            "evolved_strategies": evolved_strategies,
            "transfer_learning": transfer_results,
            "allocation": allocation_result,
            "workflow_stats": self.workflow_stats,
            "duration": duration
        }
        
        logger.info(f"Evolution workflow completed in {duration:.2f} seconds")
        return summary
    
    def _evolve_strategies_for_asset_class(
        self,
        asset_class: str,
        regime: str,
        strategy_types: List[str]
    ) -> Dict[str, Any]:
        """
        Evolve strategies for a specific asset class.
        
        Args:
            asset_class: Asset class to evolve strategies for
            regime: Current market regime
            strategy_types: List of strategy types to evolve
            
        Returns:
            Dictionary with evolution results
        """
        # Calculate backtest period
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.test_period_days)).strftime('%Y-%m-%d')
        
        # Select assets to use
        if asset_class == "equity":
            symbols = ["SPY"]  # Add more as needed
        elif asset_class == "crypto":
            symbols = ["BTC/USDT"]  # Add more as needed
        elif asset_class == "forex":
            symbols = ["EURUSD=X"]  # Add more as needed
        else:
            symbols = []
        
        if not symbols:
            logger.warning(f"No symbols defined for {asset_class}. Skipping evolution.")
            return {
                "status": "error",
                "message": f"No symbols defined for {asset_class}"
            }
        
        # Run evolutions for each strategy type and symbol
        evolution_results = {}
        best_strategies = []
        
        for strategy_type in strategy_types:
            for symbol in symbols:
                logger.info(f"Evolving {strategy_type} strategy for {symbol} ({asset_class})")
                
                # Configure evolution
                backtest_config = {
                    "asset_class": asset_class,
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval": "1d",
                    "initial_capital": 10000.0
                }
                
                # Select strategy class based on type
                if "trend" in strategy_type.lower():
                    strategy_class = TrendFollowingStrategy
                    strategy_type_name = "general_trendfollowingstrategy"
                elif "mean" in strategy_type.lower() or "reversion" in strategy_type.lower():
                    strategy_class = MeanReversionStrategy
                    strategy_type_name = "general_meanreversionstrategy"
                elif "vol" in strategy_type.lower():
                    strategy_class = VolatilityStrategy
                    strategy_type_name = "general_volatilitystrategy"
                else:
                    logger.warning(f"Unknown strategy type: {strategy_type}. Using TrendFollowingStrategy as default.")
                    strategy_class = TrendFollowingStrategy
                    strategy_type_name = "general_trendfollowingstrategy"
                
                # Register strategy type if not already registered
                if strategy_type_name not in strategy_factory.get_all_metadata():
                    strategy_factory.register_strategy(
                        strategy_type=strategy_type_name,
                        strategy_class=strategy_class,
                        asset_class="general",
                        description=f"Multi-asset {strategy_type} strategy"
                    )
                
                # Customize parameter space based on regime
                custom_parameter_space = self._create_parameter_space(regime, strategy_type, asset_class)
                
                # Start evolution
                run_id = self.evo_trader.start_evolution(
                    strategy_type_name=strategy_type_name,
                    backtest_config=backtest_config,
                    population_size=self.population_size,
                    custom_parameter_space=custom_parameter_space
                )
                
                # Run evolution for specified generations
                for generation in range(self.evolution_generations):
                    result = self.evo_trader.run_generation()
                    
                    # Log progress
                    if generation % 5 == 0 or generation == self.evolution_generations - 1:
                        best_fitness = result.get("best_fitness", 0)
                        avg_fitness = result.get("avg_fitness", 0)
                        logger.info(f"Generation {generation + 1}/{self.evolution_generations} "
                                   f"- Best fitness: {best_fitness:.4f}, Avg fitness: {avg_fitness:.4f}")
                
                # Get results
                final_population = self.evo_trader.get_population()
                best_genomes = sorted(
                    final_population,
                    key=lambda g: g.fitness if g.fitness is not None else -float('inf'),
                    reverse=True
                )[:3]  # Top 3 strategies
                
                # Convert genomes to dict
                best_strategies_dicts = []
                for i, genome in enumerate(best_genomes):
                    strategy_id = f"{strategy_type}_{asset_class}_{symbol}_{i}_{int(time.time())}"
                    
                    # Run detailed backtest for the best strategy
                    backtest_result = self.evo_trader.run_backtest(
                        strategy_type_name=strategy_type_name,
                        strategy_parameters=genome.parameters,
                        backtest_config=backtest_config
                    )
                    
                    strategy_dict = {
                        "strategy_id": strategy_id,
                        "strategy_type": strategy_type,
                        "asset_class": asset_class,
                        "symbol": symbol,
                        "parameters": genome.parameters,
                        "fitness": genome.fitness,
                        "rank": i + 1,
                        "performance": backtest_result.get("performance", {}),
                        "regime": regime
                    }
                    
                    best_strategies_dicts.append(strategy_dict)
                    
                    # Add to overall best strategies
                    best_strategies.append(strategy_dict)
                
                    # Register with market adapter
                    if backtest_result.get("status") == "success":
                        self.market_adapter.register_regime_performance(
                            strategy_id=strategy_id,
                            asset_class=asset_class,
                            performance=backtest_result.get("performance", {})
                        )
                
                evolution_results[f"{strategy_type}_{symbol}"] = {
                    "run_id": run_id,
                    "generations": self.evolution_generations,
                    "best_strategies": best_strategies_dicts
                }
        
        # Sort all best strategies by fitness/sharpe ratio and select top ones
        best_strategies.sort(
            key=lambda s: s.get("performance", {}).get("sharpe_ratio", 0) 
                         if s.get("performance") else s.get("fitness", 0),
            reverse=True
        )
        
        top_strategies = best_strategies[:self.max_strategies_per_asset_class]
        
        # Update active strategies
        self.active_strategies[asset_class] = top_strategies
        
        return {
            "status": "success",
            "evolution_results": evolution_results,
            "top_strategies": top_strategies,
            "asset_class": asset_class,
            "regime": regime
        }
    
    def _create_parameter_space(
        self,
        regime: str,
        strategy_type: str,
        asset_class: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create a custom parameter space based on regime and strategy type.
        
        Args:
            regime: Current market regime
            strategy_type: Strategy type
            asset_class: Asset class
            
        Returns:
            Dictionary with parameter space
        """
        # Start with default parameter space
        parameter_space = {}
        
        # Customize based on strategy type
        if "trend" in strategy_type.lower():
            # Base parameters for trend following
            parameter_space = {
                "fast_ma_period": {"type": "int", "min": 5, "max": 50},
                "slow_ma_period": {"type": "int", "min": 20, "max": 200},
                "trend_strength_threshold": {"type": "float", "min": 0.0, "max": 1.0},
                "stop_loss_pct": {"type": "float", "min": 0.5, "max": 5.0}
            }
            
            # Adjust for regime
            if regime == MarketRegime.TRENDING:
                # Longer lookbacks for strong trends
                parameter_space["fast_ma_period"]["min"] = 10
                parameter_space["slow_ma_period"]["min"] = 40
            elif regime == MarketRegime.VOLATILE:
                # Shorter lookbacks for volatile markets
                parameter_space["fast_ma_period"]["max"] = 20
                parameter_space["slow_ma_period"]["max"] = 100
                parameter_space["stop_loss_pct"]["max"] = 8.0  # Wider stops
        
        elif "mean" in strategy_type.lower() or "reversion" in strategy_type.lower():
            # Base parameters for mean reversion
            parameter_space = {
                "lookback_period": {"type": "int", "min": 5, "max": 60},
                "z_score_threshold": {"type": "float", "min": 1.0, "max": 3.0},
                "stop_loss_pct": {"type": "float", "min": 0.5, "max": 5.0},
                "mean_reversion_exit": {"type": "float", "min": 0.3, "max": 0.9}
            }
            
            # Adjust for regime
            if regime == MarketRegime.MEAN_REVERTING:
                # More sensitive thresholds for mean-reverting markets
                parameter_space["z_score_threshold"]["min"] = 0.8
            elif regime == MarketRegime.VOLATILE:
                # More conservative thresholds for volatile markets
                parameter_space["z_score_threshold"]["min"] = 1.5
                parameter_space["stop_loss_pct"]["max"] = 8.0  # Wider stops
        
        elif "vol" in strategy_type.lower():
            # Base parameters for volatility strategies
            parameter_space = {
                "volatility_lookback": {"type": "int", "min": 5, "max": 60},
                "atr_period": {"type": "int", "min": 5, "max": 30},
                "atr_stop_multiplier": {"type": "float", "min": 1.0, "max": 4.0},
                "breakout_multiplier": {"type": "float", "min": 1.0, "max": 3.0}
            }
            
            # Adjust for regime
            if regime == MarketRegime.VOLATILE:
                # More aggressive settings for volatile markets
                parameter_space["atr_stop_multiplier"]["max"] = 5.0
                parameter_space["breakout_multiplier"]["min"] = 1.5
            elif regime == MarketRegime.SIDEWAYS:
                # More conservative settings for sideways markets
                parameter_space["breakout_multiplier"]["max"] = 2.0
        
        # Adjust for asset class
        if asset_class == "crypto":
            # Crypto typically needs wider stops and more aggressive settings
            if "stop_loss_pct" in parameter_space:
                parameter_space["stop_loss_pct"]["max"] *= 1.5
            if "take_profit_pct" in parameter_space:
                parameter_space["take_profit_pct"]["max"] *= 1.5
            if "atr_stop_multiplier" in parameter_space:
                parameter_space["atr_stop_multiplier"]["max"] *= 1.2
        elif asset_class == "forex":
            # Forex typically needs tighter parameters
            if "stop_loss_pct" in parameter_space:
                parameter_space["stop_loss_pct"]["max"] *= 0.7
            if "take_profit_pct" in parameter_space:
                parameter_space["take_profit_pct"]["max"] *= 0.7
        
        return parameter_space
    
    def _register_strategies_with_allocator(self, evolved_strategies: Dict[str, Any]) -> None:
        """
        Register the best evolved strategies with the portfolio allocator.
        
        Args:
            evolved_strategies: Evolution results
        """
        # Unregister old strategies first (optional)
        # current_strategies = self.portfolio_allocator.get_allocation_summary()
        # We could unregister existing strategies here, but in this implementation
        # we'll just add the new ones
        
        for asset_class, result in evolved_strategies.items():
            if result.get("status") != "success":
                continue
                
            top_strategies = result.get("top_strategies", [])
            
            for strategy in top_strategies:
                strategy_id = strategy.get("strategy_id")
                strategy_type = strategy.get("strategy_type")
                performance = strategy.get("performance", {})
                
                # Register with portfolio allocator
                self.portfolio_allocator.register_strategy(
                    strategy_id=strategy_id,
                    strategy_type=strategy_type,
                    asset_class=asset_class,
                    performance=performance,
                    metadata={
                        "symbol": strategy.get("symbol"),
                        "parameters": strategy.get("parameters"),
                        "regime": strategy.get("regime")
                    }
                )
                
                logger.info(f"Registered strategy {strategy_id} ({strategy_type}) for {asset_class}")
    
    def _perform_transfer_learning(self) -> Dict[str, Any]:
        """
        Perform transfer learning by adapting successful strategies to other asset classes.
        
        Returns:
            Dictionary with transfer learning results
        """
        # Find best strategy for each asset class
        best_by_asset_class = {}
        
        for asset_class, strategies in self.active_strategies.items():
            if not strategies:
                continue
                
            # Sort by performance (Sharpe ratio)
            sorted_strategies = sorted(
                strategies,
                key=lambda s: s.get("performance", {}).get("sharpe_ratio", 0) 
                             if s.get("performance") else s.get("fitness", 0),
                reverse=True
            )
            
            if sorted_strategies:
                best_by_asset_class[asset_class] = sorted_strategies[0]
        
        # Define transfer paths (from -> to)
        transfer_paths = [
            ("equity", "forex"),
            ("forex", "crypto"),
            ("crypto", "equity")
        ]
        
        transfer_results = {}
        
        for source, target in transfer_paths:
            if source not in best_by_asset_class or source not in self.current_regimes or target not in self.current_regimes:
                continue
                
            source_strategy = best_by_asset_class[source]
            source_regime = self.current_regimes[source].get("primary_regime", MarketRegime.UNKNOWN)
            target_regime = self.current_regimes[target].get("primary_regime", MarketRegime.UNKNOWN)
            
            # Only transfer if regimes are compatible
            # (e.g., trend following from equity to forex makes sense if both are trending)
            if source_regime != target_regime and source_regime != MarketRegime.UNKNOWN and target_regime != MarketRegime.UNKNOWN:
                logger.info(f"Skipping transfer from {source} to {target} due to incompatible regimes ({source_regime} vs {target_regime})")
                continue
            
            logger.info(f"Attempting transfer learning from {source} to {target}")
            
            # Choose target symbol
            if target == "equity":
                target_symbol = "SPY"
            elif target == "crypto":
                target_symbol = "BTC/USDT"
            elif target == "forex":
                target_symbol = "EURUSD=X"
            else:
                continue
            
            # Extract strategy details
            strategy_type = source_strategy.get("strategy_type")
            strategy_params = source_strategy.get("parameters", {})
            
            # Select strategy class based on type
            if "trend" in strategy_type.lower():
                strategy_class = TrendFollowingStrategy
                strategy_type_name = "general_trendfollowingstrategy"
            elif "mean" in strategy_type.lower() or "reversion" in strategy_type.lower():
                strategy_class = MeanReversionStrategy
                strategy_type_name = "general_meanreversionstrategy"
            elif "vol" in strategy_type.lower():
                strategy_class = VolatilityStrategy
                strategy_type_name = "general_volatilitystrategy"
            else:
                logger.warning(f"Unknown strategy type for transfer: {strategy_type}")
                continue
            
            # Create an instance of the strategy
            source_strategy_instance = strategy_class(
                strategy_id=f"transfer_source_{source}_{target}",
                parameters=strategy_params,
                asset_class=source
            )
            
            # Adapt to target asset class
            try:
                adaptation_changes = source_strategy_instance.adapt_to_asset_class(target)
                logger.info(f"Adapted strategy from {source} to {target} with changes: {adaptation_changes}")
                
                # Prepare backtest configuration
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=self.test_period_days)).strftime('%Y-%m-%d')
                
                backtest_config = {
                    "asset_class": target,
                    "symbol": target_symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval": "1d",
                    "initial_capital": 10000.0
                }
                
                # Run backtest on adapted strategy
                adapted_params = source_strategy_instance.parameters
                
                # Register strategy type if not already registered
                if strategy_type_name not in strategy_factory.get_all_metadata():
                    strategy_factory.register_strategy(
                        strategy_type=strategy_type_name,
                        strategy_class=strategy_class,
                        asset_class="general",
                        description=f"Multi-asset {strategy_type} strategy"
                    )
                
                backtest_result = self.evo_trader.run_backtest(
                    strategy_type_name=strategy_type_name,
                    strategy_parameters=adapted_params,
                    backtest_config=backtest_config
                )
                
                # Check if transfer was successful
                if backtest_result.get("status") == "success":
                    performance = backtest_result.get("performance", {})
                    sharpe_ratio = performance.get("sharpe_ratio", 0)
                    
                    # Consider the transfer successful if Sharpe ratio is positive
                    if sharpe_ratio > 0:
                        logger.info(f"Successful transfer from {source} to {target} with Sharpe ratio {sharpe_ratio:.2f}")
                        
                        # Create strategy dict
                        transfer_strategy = {
                            "strategy_id": f"transfer_{source}_to_{target}_{int(time.time())}",
                            "strategy_type": f"transferred_{strategy_type}",
                            "asset_class": target,
                            "symbol": target_symbol,
                            "parameters": adapted_params,
                            "fitness": sharpe_ratio,
                            "performance": performance,
                            "regime": target_regime,
                            "transferred_from": {
                                "asset_class": source,
                                "strategy_id": source_strategy.get("strategy_id"),
                                "original_params": strategy_params
                            }
                        }
                        
                        # Add to active strategies for target asset class
                        self.active_strategies[target].append(transfer_strategy)
                        
                        # Register with portfolio allocator
                        self.portfolio_allocator.register_strategy(
                            strategy_id=transfer_strategy["strategy_id"],
                            strategy_type=transfer_strategy["strategy_type"],
                            asset_class=target,
                            performance=performance,
                            metadata={
                                "symbol": target_symbol,
                                "parameters": adapted_params,
                                "regime": target_regime,
                                "transferred_from": source
                            }
                        )
                        
                        # Record transfer result
                        transfer_results[f"{source}_to_{target}"] = {
                            "status": "success",
                            "strategy": transfer_strategy,
                            "performance": performance,
                            "adaptation_changes": adaptation_changes
                        }
                        
                        # Update workflow stats
                        self.workflow_stats["successful_transfers"] += 1
                    else:
                        logger.info(f"Transfer from {source} to {target} unsuccessful: Sharpe ratio {sharpe_ratio:.2f}")
                        transfer_results[f"{source}_to_{target}"] = {
                            "status": "failed",
                            "reason": f"Poor performance (Sharpe ratio: {sharpe_ratio:.2f})",
                            "adaptation_changes": adaptation_changes
                        }
                else:
                    logger.warning(f"Backtest failed for transferred strategy from {source} to {target}")
                    transfer_results[f"{source}_to_{target}"] = {
                        "status": "failed",
                        "reason": "Backtest failed",
                        "error_message": backtest_result.get("error_message", "Unknown error")
                    }
                    
            except Exception as e:
                logger.error(f"Error during transfer learning from {source} to {target}: {e}")
                transfer_results[f"{source}_to_{target}"] = {
                    "status": "error",
                    "reason": str(e)
                }
        
        return transfer_results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run the evolution workflow for BensBot")
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file (JSON)"
    )
    
    parser.add_argument(
        "--capital", 
        type=float, 
        default=100000.0,
        help="Total capital to allocate"
    )
    
    parser.add_argument(
        "--generations", 
        type=int, 
        default=20,
        help="Number of generations for strategy evolution"
    )
    
    parser.add_argument(
        "--population", 
        type=int, 
        default=50,
        help="Population size for evolution"
    )
    
    parser.add_argument(
        "--output", 
        type=str,
        help="Output file for workflow results (JSON)"
    )
    
    args = parser.parse_args()
    
    # Create and run workflow
    workflow = EvolutionWorkflow(
        config_path=args.config,
        total_capital=args.capital,
        evolution_generations=args.generations,
        population_size=args.population
    )
    
    # Run the workflow
    results = workflow.run_workflow()
    
    # Save results if output file specified
    if args.output:
        try:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Workflow results saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving workflow results: {e}")
    
    logger.info("Workflow completed")
    
    return results

if __name__ == "__main__":
    main() 
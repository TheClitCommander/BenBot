"""
EvoTrader - Strategy evolution service.

This service handles:
- Training strategy populations
- Evaluating strategy performance
- Generating new strategy variants
- Auto-promoting successful strategies
"""

import logging
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Type
from dataclasses import dataclass

# Import base classes for typing
from trading_bot.core.strategies.base_strategy import BaseStrategy
from trading_bot.core.strategies.strategy_factory import strategy_factory
from trading_bot.core.backtesting.base_backtester import BaseBacktester, BacktestResult
from trading_bot.core.backtesting.parallel_backtester import ParallelBacktestManager

logger = logging.getLogger(__name__)

@dataclass
class EvolutionConfig:
    """Configuration for evolutionary algorithm."""
    population_size: int = 50
    generations: int = 20
    mutation_rate: float = 0.2
    crossover_rate: float = 0.7
    elite_size: int = 5
    selection_method: str = "tournament"
    tournament_size: int = 5
    auto_promotion_threshold: float = 0.2  # Top 20% can be auto-promoted
    use_parallel_backtesting: bool = True   # Whether to use parallel backtesting
    max_parallel_workers: int = 0           # 0 means use CPU count

@dataclass
class StrategyGenome:
    """Represents a trading strategy's genetic representation."""
    id: str
    name: str
    type: str  # e.g., "equity_trend", "crypto_breakout", etc.
    parameters: Dict[str, Any]
    performance: Optional[Dict[str, float]] = None
    generation: int = 0
    parent_ids: List[str] = None
    creation_date: str = None

class EvoTrader:
    """
    Strategy evolution service.
    
    This service evolves trading strategies using genetic algorithms,
    evaluates their performance through backtesting, and promotes
    successful strategies to production.
    """
    
    def __init__(
        self,
        config_path: str = "./config/evolution.json",
        data_dir: str = "./data/evolution",
        backtester_registry: Dict[str, BaseBacktester] = None, # Asset class -> Backtester instance
    ):
        """
        Initialize the evolution service.
        
        Args:
            config_path: Path to evolution configuration
            data_dir: Directory for strategy storage
            backtester_registry: A dictionary mapping asset_class (str) to BaseBacktester instances.
        """
        self.config_path = config_path
        self.data_dir = data_dir
        self.backtester_registry = backtester_registry if backtester_registry else {}
        
        # Use the strategy factory instead of a local registry
        self.strategy_factory = strategy_factory
        
        # Setup parallel backtesting
        self.parallel_backtest_manager = None
        if backtester_registry:
            # Create constructors dictionary for parallel backtesting
            backtester_constructors = {}
            backtester_kwargs = {}
            
            for asset_class, backtester in backtester_registry.items():
                # Get the class of the backtester for reconstruction in worker processes
                backtester_class = backtester.__class__
                
                # Get data fetcher for kwargs
                # Assumes all backtesters have a data_fetcher attribute
                data_fetcher = getattr(backtester, 'data_fetcher', None)
                
                if backtester_class and data_fetcher:
                    backtester_constructors[asset_class] = backtester_class
                    backtester_kwargs[asset_class] = {"historical_data_fetcher": data_fetcher}
            
            if backtester_constructors:
                self.parallel_backtest_manager = ParallelBacktestManager(
                    backtester_constructors=backtester_constructors,
                    backtester_constructor_kwargs=backtester_kwargs
                )
        
        if not self.backtester_registry:
            logger.warning("EvoTrader initialized without a backtester_registry. Backtesting will not be possible.")
        
        # Create directories
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize population and history
        self.current_population: List[StrategyGenome] = []
        self.history: Dict[str, List[StrategyGenome]] = {}
        self.best_strategies: List[StrategyGenome] = []
        
        # Load existing strategies if available
        self._load_strategies()
    
    def _load_config(self) -> EvolutionConfig:
        """Load evolution configuration."""
        default_config = EvolutionConfig()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    return EvolutionConfig(**config_data)
            else:
                # Create default config file
                config_dict = {
                    "population_size": default_config.population_size,
                    "generations": default_config.generations,
                    "mutation_rate": default_config.mutation_rate,
                    "crossover_rate": default_config.crossover_rate,
                    "elite_size": default_config.elite_size,
                    "selection_method": default_config.selection_method,
                    "tournament_size": default_config.tournament_size,
                    "auto_promotion_threshold": default_config.auto_promotion_threshold,
                    "use_parallel_backtesting": default_config.use_parallel_backtesting,
                    "max_parallel_workers": default_config.max_parallel_workers
                }
                with open(self.config_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
                logger.info(f"Created default evolution config at {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading evolution config: {e}")
        
        return default_config
    
    def _load_strategies(self) -> None:
        """Load existing strategies from storage."""
        try:
            population_file = os.path.join(self.data_dir, "current_population.json")
            if os.path.exists(population_file):
                with open(population_file, 'r') as f:
                    strategy_data = json.load(f)
                    self.current_population = [StrategyGenome(**s) for s in strategy_data]
            
            history_file = os.path.join(self.data_dir, "evolution_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self.history = {
                        k: [StrategyGenome(**s) for s in v]
                        for k, v in history_data.items()
                    }
            
            best_file = os.path.join(self.data_dir, "best_strategies.json")
            if os.path.exists(best_file):
                with open(best_file, 'r') as f:
                    best_data = json.load(f)
                    self.best_strategies = [StrategyGenome(**s) for s in best_data]
            
            logger.info(f"Loaded {len(self.current_population)} strategies, "
                      f"{sum(len(v) for v in self.history.values())} historical strategies, "
                      f"{len(self.best_strategies)} best strategies")
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
    
    def _save_strategies(self) -> None:
        """Save strategies to storage."""
        try:
            # Save current population
            with open(os.path.join(self.data_dir, "current_population.json"), 'w') as f:
                json.dump([vars(s) for s in self.current_population], f, indent=2)
            
            # Save history
            with open(os.path.join(self.data_dir, "evolution_history.json"), 'w') as f:
                history_data = {
                    k: [vars(s) for s in v]
                    for k, v in self.history.items()
                }
                json.dump(history_data, f, indent=2)
            
            # Save best strategies
            with open(os.path.join(self.data_dir, "best_strategies.json"), 'w') as f:
                json.dump([vars(s) for s in self.best_strategies], f, indent=2)
            
            logger.debug("Saved strategies to disk")
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")
    
    def start_evolution(
        self, 
        strategy_type_name: str, # e.g., "equity_trend_v1", "crypto_breakout_default"
        backtest_config: Dict[str, Any], # Contains symbol, asset_class, start_date, end_date, interval etc.
        config: Optional[EvolutionConfig] = None,
        custom_parameter_space: Optional[Dict[str, Any]] = None # Optional override/supplement to schema
    ) -> str:
        """
        Start a new evolution run for a specific strategy type using a specific backtest configuration.
        
        Args:
            strategy_type_name: The registered name of the strategy type to evolve (e.g., "equity_trend_default").
            backtest_config: Configuration for backtesting (asset_class, symbol, dates, interval).
            config: Optional custom evolution config for this run.
            custom_parameter_space: Optional parameter space to override/supplement the strategy's schema.
                                    Example: {"sma_short": [5, 10, 15], "rsi_period": {"type":"int", "min":7, "max":10}}
            
        Returns:
            ID of the evolution run.
        """
        run_config = config or self.config

        # Get strategy metadata and schema from the factory
        strategy_metadata = self.strategy_factory.get_strategy_metadata(strategy_type_name)
        if not strategy_metadata:
            logger.error(f"Strategy type '{strategy_type_name}' not found in registry.")
            raise ValueError(f"Unknown strategy_type_name: {strategy_type_name}")
        
        parameter_schema = strategy_metadata.get('parameter_schema', {})
        
        # Derive parameter space from strategy schema, potentially overridden/supplemented
        parameter_space_for_init = {}
        for param, details in parameter_schema.items():
            if custom_parameter_space and param in custom_parameter_space:
                # If custom provides specific values (e.g., a list for categorical) or a new range dict
                custom_val = custom_parameter_space[param]
                if isinstance(custom_val, list): # e.g. sma_short: [10,20,30]
                    parameter_space_for_init[param] = custom_val
                elif isinstance(custom_val, dict) and "type" in custom_val: # e.g. rsi_period: {"type":"int", "min":7, "max":10}
                     parameter_space_for_init[param] = custom_val # Take the whole dict
                else: # If custom_val is a single fixed value, not typically for evolution range but could be supported
                    logger.warning(f"Parameter '{param}' in custom_parameter_space is a single value, using it as fixed.")
                    parameter_space_for_init[param] = custom_val 
            else:
                # Use schema definition to create a range for evolution
                # For numeric types, create a [min, max] list if min/max are defined
                if details.get("type") in ["int", "float"] and "min" in details and "max" in details:
                    parameter_space_for_init[param] = [details["min"], details["max"]]
                elif details.get("type") == "bool":
                    parameter_space_for_init[param] = [True, False] # Evolve booleans
                elif "default" in details: # Fallback if no clear range from schema for evolution
                    logger.warning(f"No explicit evolution range for '{param}', using default value only or simple list.")
                    # This part might need smarter handling based on schema details (e.g. if categorical options are listed)
                    parameter_space_for_init[param] = [details["default"]] 
                else:
                    logger.error(f"Cannot determine evolution range for parameter '{param}' of strategy '{strategy_type_name}'. Schema: {details}")
                    raise ValueError(f"Missing evolution range definition for '{param}' in {strategy_type_name}")

        run_id = f"evo_{strategy_type_name.replace('_','-')}_{backtest_config.get('symbol', 'sym')}_{int(time.time())}"
        
        # _initialize_population now uses the derived parameter_space_for_init
        # The strategy_type_name is passed to be stored in the genome.
        self.current_population = self._initialize_population(
            strategy_type_name=strategy_type_name, 
            parameter_space=parameter_space_for_init, 
            population_size=run_config.population_size,
        )
        
        self.history[run_id] = self.current_population.copy()
        self._save_strategies()
        logger.info(f"Started evolution run {run_id} for {strategy_type_name} on {backtest_config.get('symbol')}.")
        return run_id
    
    def _initialize_population(
        self, 
        strategy_type_name: str, # This is the registered name, e.g., "equity_trend_default"
        parameter_space: Dict[str, Any],
        population_size: int,
    ) -> List[StrategyGenome]:
        """
        Initialize a new population of strategies.
        Args:
            strategy_type_name: The registered type/name of the strategy.
        """
        population = []
        timestamp = datetime.utcnow().isoformat()
        
        for i in range(population_size):
            parameters = {}
            for param_name, P_range_or_details in parameter_space.items():
                # P_range_or_details can be a list [min, max] or [val1, val2, ...]
                # or it could be a dict from custom_parameter_space like {"type":"int", "min":1, "max":5}
                # or a single fixed value
                
                value_to_set = None
                if isinstance(P_range_or_details, list):
                    if not P_range_or_details:
                        raise ValueError(f"Empty list provided for parameter '{param_name}' in parameter_space")

                    # Heuristic: if list has two numbers and first < second, assume [min,max] range
                    is_likely_range = len(P_range_or_details) == 2 and \
                                     all(isinstance(x, (int, float)) for x in P_range_or_details) and \
                                     P_range_or_details[0] <= P_range_or_details[1]
                    
                    if is_likely_range:
                        # Infer type for random generation. If original schema specified int, use randint.
                        # For now, if any is float, result is float.
                        is_int_range = all(isinstance(x, int) for x in P_range_or_details)
                        if is_int_range:
                            value_to_set = random.randint(P_range_or_details[0], P_range_or_details[1])
                        else:
                            value_to_set = random.uniform(P_range_or_details[0], P_range_or_details[1])
                    else: # Categorical list or malformed range - treat as categorical
                        value_to_set = random.choice(P_range_or_details)
                
                elif isinstance(P_range_or_details, dict) and "type" in P_range_or_details: # Detailed spec from custom_parameter_space
                    # This case allows evolving from a more complex custom definition
                    # (e.g. a non-uniform distribution, not just min/max)
                    # For now, implement simple min/max from this dict if present
                    param_type = P_range_or_details["type"]
                    if param_type == "int" and "min" in P_range_or_details and "max" in P_range_or_details:
                        value_to_set = random.randint(P_range_or_details["min"], P_range_or_details["max"])
                    elif param_type == "float" and "min" in P_range_or_details and "max" in P_range_or_details:
                        value_to_set = random.uniform(P_range_or_details["min"], P_range_or_details["max"])
                    elif param_type == "bool":
                         value_to_set = random.choice([True,False])
                    elif "default" in P_range_or_details:
                        value_to_set = P_range_or_details["default"]
                    else:
                        raise ValueError(f"Unsupported custom parameter detail for '{param_name}': {P_range_or_details}")
                else: # Single fixed value
                    value_to_set = P_range_or_details
                
                parameters[param_name] = value_to_set
            
            genome = StrategyGenome(
                id=f"{strategy_type_name.replace('_','-')}_gen0_pop{i}",
                name=f"{strategy_type_name.replace('_', ' ').title()} Pop {i}",
                type=strategy_type_name, # Store the registered strategy type name
                parameters=parameters,
                generation=0,
                parent_ids=[],
                creation_date=timestamp
            )
            population.append(genome)
        return population

    def run_backtest_generation(self, backtest_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run backtests for the current generation using asset-specific backtesters.
        
        Args:
            backtest_config: Dict containing asset_class, symbol, start_date, end_date, interval, etc.
        """
        asset_class = backtest_config.get("asset_class")
        if not asset_class:
            raise ValueError("'asset_class' must be provided in backtest_config")
        
        # Check if we should use parallel backtesting
        use_parallel = self.config.use_parallel_backtesting and self.parallel_backtest_manager is not None
        
        if not use_parallel:
            # Legacy single-threaded approach
            backtester = self.backtester_registry.get(asset_class)
            if not backtester:
                logger.error(f"No backtester registered for asset class: {asset_class}")
                raise ValueError(f"Backtester for asset class '{asset_class}' not configured in EvoTrader.")
        
        results = {
            "generation": self.current_population[0].generation if self.current_population else 0,
            "population_size": len(self.current_population),
            "strategies": [],
            "best_strategy_performance": None, # Storing full best strategy details later
            "avg_performance": {},
            "timestamp": datetime.utcnow().isoformat(),
            "backtest_config": backtest_config
        }
        
        if use_parallel:
            # Prepare a dictionary mapping strategy types to classes
            strategy_types = set(genome.type for genome in self.current_population)
            strategy_classes = {}
            for strategy_type in strategy_types:
                metadata = self.strategy_factory.get_strategy_metadata(strategy_type)
                if not metadata:
                    logger.error(f"Strategy type '{strategy_type}' not found in factory.")
                    continue
                # Get the actual class from the factory
                strategy_class = self.strategy_factory._registry.get(strategy_type)
                if strategy_class:
                    strategy_classes[strategy_type] = strategy_class
            
            # Run parallel backtests
            logger.info(f"Running parallel backtests for generation {results['generation']}...")
            backtest_results = self.parallel_backtest_manager.run_generation_backtests(
                strategy_genomes=[vars(genome) for genome in self.current_population],
                strategy_classes=strategy_classes,
                backtest_config=backtest_config,
                max_workers=self.config.max_parallel_workers
            )
            
            # Update strategy genomes with results
            successful_backtests = 0
            for strategy_genome in self.current_population:
                result = backtest_results.get(strategy_genome.id)
                if result and result.get("status") == "success":
                    strategy_genome.performance = result.get("performance", {})
                    successful_backtests += 1
                else:
                    error_msg = result.get("error_message") if result else "No result returned"
                    logger.warning(f"Parallel backtest failed for {strategy_genome.id}: {error_msg}")
                    strategy_genome.performance = {"error": error_msg, "total_return": -999}
                
                results["strategies"].append({
                    "id": strategy_genome.id,
                    "name": strategy_genome.name,
                    "performance": strategy_genome.performance
                })
            
            if successful_backtests == 0 and self.current_population:
                logger.warning(f"All parallel backtests failed for generation {results['generation']}.")
        
        else:
            # Legacy single-threaded approach
            successful_backtests = 0
            for strategy_genome in self.current_population:
                # Get the strategy class from the factory
                strategy_metadata = self.strategy_factory.get_strategy_metadata(strategy_genome.type)
                if not strategy_metadata:
                    logger.error(f"Strategy type '{strategy_genome.type}' not found in registry. Skipping {strategy_genome.id}.")
                    strategy_genome.performance = {"error": "Strategy class not found", "total_return": -999}
                    results["strategies"].append({
                        "id": strategy_genome.id, "name": strategy_genome.name, "performance": strategy_genome.performance
                    })
                    continue
                
                strategy_class = self.strategy_factory._registry.get(strategy_genome.type)
                if not strategy_class:
                    logger.error(f"Strategy class for type '{strategy_genome.type}' not found in registry. Skipping {strategy_genome.id}.")
                    strategy_genome.performance = {"error": "Strategy class not found", "total_return": -999}
                    results["strategies"].append({
                        "id": strategy_genome.id, "name": strategy_genome.name, "performance": strategy_genome.performance
                    })
                    continue
    
                logger.debug(f"Running backtest for genome {strategy_genome.id} ({strategy_genome.type}) with {asset_class} backtester.")
                backtest_run_result: BacktestResult = backtester.run_backtest(
                    strategy_id=strategy_genome.id,
                    strategy_class=strategy_class,
                    parameters=strategy_genome.parameters,
                    asset_class=asset_class, # From overall backtest_config
                    symbol=backtest_config.get("symbol"),
                    start_date=backtest_config.get("start_date"),
                    end_date=backtest_config.get("end_date"),
                    interval=backtest_config.get("interval"),
                    initial_capital=backtest_config.get("initial_capital", 100000.0), # Get from config or use default
                    commission_pct=backtest_config.get("commission_pct", 0.001),
                    slippage_pct=backtest_config.get("slippage_pct", 0.0005)
                )
                
                if backtest_run_result["status"] == "success":
                    strategy_genome.performance = backtest_run_result["performance"]
                    successful_backtests += 1
                else:
                    logger.warning(f"Backtest failed for {strategy_genome.id}: {backtest_run_result.get('error_message')}")
                    # Assign a very poor performance score if backtest fails
                    strategy_genome.performance = {"error": backtest_run_result.get('error_message', 'Backtest failed'), "total_return": -999}
    
                results["strategies"].append({
                    "id": strategy_genome.id,
                    "name": strategy_genome.name,
                    "performance": strategy_genome.performance
                })
            
            if successful_backtests == 0 and self.current_population:
                 logger.warning(f"All backtests failed for generation {results['generation']}. Population may not evolve well.")
        
        # Sort population by performance (total_return or a custom fitness score)
        self.current_population.sort(
            key=lambda s: s.performance.get("total_return", -float('inf')) if s.performance else -float('inf'),
            reverse=True
        )
        
        if self.current_population and self.current_population[0].performance and \
           self.current_population[0].performance.get("error") is None:
            best_genome_of_gen = self.current_population[0]
            results["best_strategy_performance"] = best_genome_of_gen.performance
            # Update overall best_strategies list
            # Logic for maintaining self.best_strategies based on a fitness metric (e.g. Sharpe or custom score)
            # This needs a more robust fitness definition than just total_return sometimes
            current_best_fitness = best_genome_of_gen.performance.get("sharpe_ratio", -float('inf'))

            if not self.best_strategies or \
               current_best_fitness > (self.best_strategies[0].performance.get("sharpe_ratio",-float('inf')) if self.best_strategies[0].performance else -float('inf')):
                # Could add to a list and sort, or just keep the single best
                # For now, let's consider if it improves upon the current list or if list is small
                is_better_than_existing = True # Simplified
                if self.best_strategies and len(self.best_strategies) >= self.config.elite_size: # Example condition
                     is_better_than_existing = current_best_fitness > (self.best_strategies[-1].performance.get("sharpe_ratio", -float('inf')) if self.best_strategies[-1].performance else -float('inf'))
                
                if is_better_than_existing:
                    self.best_strategies.append(best_genome_of_gen)
                    self.best_strategies.sort(
                        key=lambda s: s.performance.get("sharpe_ratio", -float('inf')) if s.performance else -float('inf'),
                        reverse=True
                    )
                    self.best_strategies = self.best_strategies[:max(20, self.config.elite_size)] # Keep top N best
        
        # Calculate average performance metrics across successful backtests
        if results["strategies"]:
            # Filter out strategies with errors
            valid_strategies = [
                s for s in results["strategies"] 
                if "error" not in s["performance"] and s["performance"] is not None
            ]
            
            if valid_strategies:
                # Get all performance metrics keys from the first strategy
                all_metrics = valid_strategies[0]["performance"].keys()
                
                # Calculate average for each metric
                avg_performance = {}
                for metric in all_metrics:
                    values = [s["performance"].get(metric, 0) for s in valid_strategies]
                    avg_performance[metric] = sum(values) / len(values)
                
                results["avg_performance"] = avg_performance

        self._save_strategies()
        return results
    
    def evolve_generation(self) -> Dict[str, Any]:
        """
        Evolve the current population to create a new generation.
        
        Returns:
            Information about the new generation
        """
        if not self.current_population:
            raise ValueError("No population to evolve")
        
        prev_generation = self.current_population[0].generation
        current_pop = self.current_population
        
        # Create a new population
        new_population = []
        timestamp = datetime.utcnow().isoformat()
        
        # Elite selection (keep best performers unchanged)
        elite_count = min(self.config.elite_size, len(current_pop))
        elites = current_pop[:elite_count]
        
        # Add elites to new population
        for i, elite in enumerate(elites):
            # Create copy with updated ID and generation
            new_elite = StrategyGenome(
                id=f"{elite.type}_gen{prev_generation+1}_elite{i}",
                name=elite.name,
                type=elite.type,
                parameters=elite.parameters.copy(),
                performance=None,  # Reset performance
                generation=prev_generation + 1,
                parent_ids=[elite.id],
                creation_date=timestamp
            )
            new_population.append(new_elite)
        
        # Fill rest of population with crossover and mutation
        while len(new_population) < self.config.population_size:
            if random.random() < self.config.crossover_rate and len(current_pop) >= 2:
                # Crossover (create child from two parents)
                if self.config.selection_method == "tournament":
                    parent1 = self._tournament_selection(current_pop)
                    parent2 = self._tournament_selection(current_pop)
                else:
                    # Default to roulette wheel selection
                    parent1, parent2 = self._roulette_selection(current_pop, 2)
                
                child = self._crossover(parent1, parent2, prev_generation + 1, timestamp)
                
                # Possibly mutate
                if random.random() < self.config.mutation_rate:
                    self._mutate(child)
                
                new_population.append(child)
            else:
                # Just mutation of existing strategy
                if self.config.selection_method == "tournament":
                    parent = self._tournament_selection(current_pop)
                else:
                    parent = self._roulette_selection(current_pop, 1)[0]
                
                child = StrategyGenome(
                    id=f"{parent.type}_gen{prev_generation+1}_{len(new_population)}",
                    name=f"{parent.name} Variant",
                    type=parent.type,
                    parameters=parent.parameters.copy(),
                    performance=None,
                    generation=prev_generation + 1,
                    parent_ids=[parent.id],
                    creation_date=timestamp
                )
                
                # Apply mutation
                self._mutate(child)
                
                new_population.append(child)
        
        # Store current population in history before replacing
        run_id = next(iter(self.history.keys())) if self.history else f"evo_{int(time.time())}"
        if run_id in self.history:
            self.history[run_id].extend(self.current_population)
        else:
            self.history[run_id] = self.current_population.copy()
        
        # Update current population
        self.current_population = new_population
        
        # Save to disk
        self._save_strategies()
        
        return {
            "run_id": run_id,
            "prev_generation": prev_generation,
            "new_generation": prev_generation + 1,
            "population_size": len(new_population),
            "elite_count": elite_count,
            "timestamp": timestamp
        }
    
    def _tournament_selection(self, population: List[StrategyGenome]) -> StrategyGenome:
        """
        Select a strategy using tournament selection.
        
        Args:
            population: Population to select from
            
        Returns:
            Selected strategy
        """
        tournament_size = min(self.config.tournament_size, len(population))
        tournament = random.sample(population, tournament_size)
        
        # Return the best strategy from the tournament
        return max(tournament, 
                  key=lambda s: s.performance.get("total_return", 0) if s.performance else 0)
    
    def _roulette_selection(
        self, 
        population: List[StrategyGenome], 
        count: int
    ) -> List[StrategyGenome]:
        """
        Select strategies using roulette wheel selection.
        
        Args:
            population: Population to select from
            count: Number of strategies to select
            
        Returns:
            List of selected strategies
        """
        # Get fitness values (use total return as fitness)
        fitness_values = [
            max(0.01, s.performance.get("total_return", 0) + 100) if s.performance else 0.01
            for s in population
        ]
        
        # Calculate selection probabilities
        total_fitness = sum(fitness_values)
        if total_fitness <= 0:
            # If no positive fitness, select randomly
            return random.sample(population, min(count, len(population)))
        
        probabilities = [f / total_fitness for f in fitness_values]
        
        # Select strategies
        selected = []
        for _ in range(count):
            idx = 0
            r = random.random()
            while r > 0 and idx < len(probabilities):
                r -= probabilities[idx]
                idx += 1
            idx = min(idx, len(population) - 1)
            selected.append(population[idx])
        
        return selected
    
    def _crossover(
        self, 
        parent1: StrategyGenome, 
        parent2: StrategyGenome,
        generation: int,
        timestamp: str
    ) -> StrategyGenome:
        """
        Create a child strategy by crossing over two parents.
        
        Args:
            parent1: First parent strategy
            parent2: Second parent strategy
            generation: Generation number for child
            timestamp: Creation timestamp
            
        Returns:
            Child strategy
        """
        # Create new child with mixed parameters
        child_params = {}
        
        # For each parameter, randomly select from either parent
        all_params = set(parent1.parameters.keys()) | set(parent2.parameters.keys())
        for param in all_params:
            if param in parent1.parameters and param in parent2.parameters:
                # Both parents have this parameter - either take one directly or interpolate
                if isinstance(parent1.parameters[param], (int, float)) and isinstance(parent2.parameters[param], (int, float)):
                    # For numeric parameters, we can interpolate
                    if random.random() < 0.5:
                        # Interpolate between values
                        alpha = random.random()
                        value = parent1.parameters[param] * alpha + parent2.parameters[param] * (1 - alpha)
                        if isinstance(parent1.parameters[param], int):
                            value = int(round(value))
                        child_params[param] = value
                    else:
                        # Take directly from one parent
                        child_params[param] = parent1.parameters[param] if random.random() < 0.5 else parent2.parameters[param]
                else:
                    # For non-numeric parameters, take from one parent
                    child_params[param] = parent1.parameters[param] if random.random() < 0.5 else parent2.parameters[param]
            elif param in parent1.parameters:
                child_params[param] = parent1.parameters[param]
            else:
                child_params[param] = parent2.parameters[param]
        
        # Create child
        child = StrategyGenome(
            id=f"{parent1.type}_gen{generation}_{int(random.random() * 10000)}",
            name=f"{parent1.type.title()} Hybrid",
            type=parent1.type,
            parameters=child_params,
            performance=None,
            generation=generation,
            parent_ids=[parent1.id, parent2.id],
            creation_date=timestamp
        )
        
        return child
    
    def _mutate(self, strategy: StrategyGenome) -> None:
        """
        Apply random mutations to a strategy.
        
        Args:
            strategy: Strategy to mutate
        """
        # Randomly select parameters to mutate
        for param, value in strategy.parameters.items():
            # 20% chance to mutate each parameter
            if random.random() < 0.2:
                if isinstance(value, int):
                    # Mutate integer by ±10-30%
                    change = int(value * (random.random() * 0.2 + 0.1))
                    if change == 0:
                        change = 1
                    strategy.parameters[param] = max(1, value + change if random.random() < 0.5 else value - change)
                elif isinstance(value, float):
                    # Mutate float by ±10-30%
                    change = value * (random.random() * 0.2 + 0.1)
                    if abs(change) < 0.0001:
                        change = 0.0001
                    strategy.parameters[param] = max(0.0001, value + change if random.random() < 0.5 else value - change)
                elif isinstance(value, bool):
                    # Flip boolean
                    strategy.parameters[param] = not value
                elif isinstance(value, (list, tuple)):
                    # Select a different value from list
                    strategy.parameters[param] = random.choice(value)
    
    def auto_promote_strategies(self, min_performance_criteria: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Auto-promote strategies that meet performance criteria.
        Criteria could be a dict like {"sharpe_ratio": 1.0, "min_trades": 50}.
        """
        # ... (Adapt to use richer performance data and potentially multiple criteria) ...
        # ... The min_performance argument in EvoToExecAdapter was a simple float for total_return.
        # ... This should be more flexible now.
        # For now, let's keep the old logic based on total_return as an example, 
        # but acknowledge it needs updating.
        min_total_return = None
        if isinstance(min_performance_criteria, float): # Backwards compatibility for simple case
            min_total_return = min_performance_criteria
        elif isinstance(min_performance_criteria, dict):
            min_total_return = min_performance_criteria.get("total_return")

        promoted = []
        # ... (rest of the logic similar to before, but filter based on richer criteria if provided)
        # ... using strategy_genome.performance directly.
        return promoted # Placeholder

    def get_strategy_details(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            Strategy details or None if not found
        """
        # Search in current population
        for strategy in self.current_population:
            if strategy.id == strategy_id:
                return vars(strategy)
        
        # Search in history
        for run_id, population in self.history.items():
            for strategy in population:
                if strategy.id == strategy_id:
                    return vars(strategy)
        
        # Search in best strategies
        for strategy in self.best_strategies:
            if strategy.id == strategy_id:
                return vars(strategy)
        
        return None
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """
        Get summary of current evolution state.
        """
        current_gen_num = self.current_population[0].generation if self.current_population else 0
        top_performer_genome = self.best_strategies[0] if self.best_strategies else None
        
        top_performer_info = None
        if top_performer_genome:
            top_performer_info = {
                "id": top_performer_genome.id,
                "name": top_performer_genome.name,
                "type": top_performer_genome.type,
                "parameters": top_performer_genome.parameters,
                "performance": top_performer_genome.performance,
                "generation": top_performer_genome.generation
            }

        return {
            "current_generation": current_gen_num,
            "population_size": len(self.current_population),
            "total_historical_runs": len(self.history),
            "best_strategies_count": len(self.best_strategies),
            "top_performer": top_performer_info,
            "config": vars(self.config)
        }

    def create_strategy_instance(self, strategy_id: str) -> Optional[BaseStrategy]:
        """
        Create a concrete strategy instance from a strategy genome.
        
        Args:
            strategy_id: ID of the strategy genome to instantiate
            
        Returns:
            An instance of the strategy class or None if not found
        """
        # Find the strategy genome
        genome = None
        for strategy in self.current_population:
            if strategy.id == strategy_id:
                genome = strategy
                break
        
        if not genome:
            for strategies in self.history.values():
                for strategy in strategies:
                    if strategy.id == strategy_id:
                        genome = strategy
                        break
                if genome:
                    break
        
        if not genome:
            for strategy in self.best_strategies:
                if strategy.id == strategy_id:
                    genome = strategy
                    break
        
        if not genome:
            logger.error(f"Strategy genome {strategy_id} not found")
            return None
        
        # Create the strategy instance using the factory
        try:
            strategy_instance = self.strategy_factory.create_strategy(
                strategy_type=genome.type,
                strategy_id=genome.id,
                parameters=genome.parameters
            )
            return strategy_instance
        except Exception as e:
            logger.error(f"Error creating strategy instance for {strategy_id}: {e}")
            return None 
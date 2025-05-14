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
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

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

@dataclass
class StrategyGenome:
    """Represents a trading strategy's genetic representation."""
    id: str
    name: str
    type: str  # e.g., "mean_reversion", "trend_following", etc.
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
        backtester = None  # Will be linked to backtesting service
    ):
        """
        Initialize the evolution service.
        
        Args:
            config_path: Path to evolution configuration
            data_dir: Directory for strategy storage
            backtester: Reference to backtesting service
        """
        self.config_path = config_path
        self.data_dir = data_dir
        self.backtester = backtester
        
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
                    "auto_promotion_threshold": default_config.auto_promotion_threshold
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
        strategy_type: str,
        parameter_space: Dict[str, Any],
        market_data: Dict[str, Any],
        config: Optional[EvolutionConfig] = None
    ) -> str:
        """
        Start a new evolution run.
        
        Args:
            strategy_type: Type of strategy to evolve
            parameter_space: Parameter ranges for evolution
            market_data: Market data for backtesting
            config: Optional custom evolution config
            
        Returns:
            ID of the evolution run
        """
        # Use custom config if provided, else use default
        run_config = config or self.config
        
        # Generate run ID
        run_id = f"evo_{strategy_type}_{int(time.time())}"
        
        # Initialize new population
        self.current_population = self._initialize_population(
            strategy_type, parameter_space, run_config.population_size
        )
        
        # Save initial population to history
        self.history[run_id] = self.current_population.copy()
        
        # Save to disk
        self._save_strategies()
        
        # Return run ID for tracking
        return run_id
    
    def _initialize_population(
        self, 
        strategy_type: str,
        parameter_space: Dict[str, Any],
        population_size: int
    ) -> List[StrategyGenome]:
        """
        Initialize a new population of strategies.
        
        Args:
            strategy_type: Type of strategy to create
            parameter_space: Parameter ranges
            population_size: Size of population
            
        Returns:
            List of strategy genomes
        """
        population = []
        timestamp = datetime.utcnow().isoformat()
        
        for i in range(population_size):
            # Generate random parameters within ranges
            parameters = {}
            for param_name, param_range in parameter_space.items():
                if isinstance(param_range, (list, tuple)) and len(param_range) >= 2:
                    if all(isinstance(v, (int, float)) for v in param_range[:2]):
                        # Numeric parameter
                        if isinstance(param_range[0], int) and isinstance(param_range[1], int):
                            # Integer parameter
                            parameters[param_name] = random.randint(param_range[0], param_range[1])
                        else:
                            # Float parameter
                            parameters[param_name] = random.uniform(param_range[0], param_range[1])
                    elif all(isinstance(v, bool) for v in param_range[:2]):
                        # Boolean parameter
                        parameters[param_name] = random.choice([True, False])
                    else:
                        # Categorical parameter
                        parameters[param_name] = random.choice(param_range)
                else:
                    # Default value
                    parameters[param_name] = param_range
            
            # Create genome
            genome = StrategyGenome(
                id=f"{strategy_type}_gen0_{i}",
                name=f"{strategy_type.title()} Strategy #{i}",
                type=strategy_type,
                parameters=parameters,
                generation=0,
                parent_ids=[],
                creation_date=timestamp
            )
            
            population.append(genome)
        
        return population
    
    def run_backtest_generation(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run backtests for the current generation.
        
        Args:
            market_data: Market data for backtesting
            
        Returns:
            Results of the generation backtest
        """
        if not self.backtester:
            raise ValueError("Backtester not configured")
        
        # Results container
        results = {
            "generation": self.current_population[0].generation if self.current_population else 0,
            "population_size": len(self.current_population),
            "strategies": [],
            "best_strategy": None,
            "avg_performance": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run backtest for each strategy
        for strategy in self.current_population:
            # Call backtester
            backtest_result = self.backtester.run_backtest(
                strategy_type=strategy.type,
                parameters=strategy.parameters,
                market_data=market_data
            )
            
            # Store performance metrics
            strategy.performance = backtest_result.get("performance", {})
            
            # Add to results
            strategy_result = {
                "id": strategy.id,
                "name": strategy.name,
                "performance": strategy.performance
            }
            results["strategies"].append(strategy_result)
        
        # Sort by performance (assume higher return is better)
        self.current_population.sort(
            key=lambda s: s.performance.get("total_return", 0) if s.performance else 0,
            reverse=True
        )
        
        # Update best strategies list
        if self.current_population:
            best_strategy = self.current_population[0]
            results["best_strategy"] = {
                "id": best_strategy.id,
                "name": best_strategy.name,
                "performance": best_strategy.performance
            }
            
            # Add to best strategies if it's good enough
            if (not self.best_strategies or 
                best_strategy.performance.get("total_return", 0) > 
                self.best_strategies[0].performance.get("total_return", 0) * 0.9):
                self.best_strategies.append(best_strategy)
                # Keep best strategies sorted
                self.best_strategies.sort(
                    key=lambda s: s.performance.get("total_return", 0) if s.performance else 0,
                    reverse=True
                )
                # Limit the list size
                if len(self.best_strategies) > 20:
                    self.best_strategies = self.best_strategies[:20]
        
        # Calculate average performance
        if results["strategies"]:
            perf_keys = set()
            for s in results["strategies"]:
                if s.get("performance"):
                    perf_keys.update(s["performance"].keys())
            
            for key in perf_keys:
                values = [s["performance"].get(key, 0) for s in results["strategies"] 
                         if s.get("performance") and key in s["performance"]]
                if values:
                    results["avg_performance"][key] = sum(values) / len(values)
        
        # Save results
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
    
    def auto_promote_strategies(self, min_performance: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Auto-promote strategies that meet performance criteria.
        
        Args:
            min_performance: Minimum performance threshold (optional)
            
        Returns:
            List of promoted strategies
        """
        promoted = []
        
        if not self.current_population:
            return promoted
        
        # Sort by performance if not already sorted
        self.current_population.sort(
            key=lambda s: s.performance.get("total_return", 0) if s.performance else 0,
            reverse=True
        )
        
        # Determine how many strategies to consider (top X%)
        top_count = max(1, int(len(self.current_population) * self.config.auto_promotion_threshold))
        candidates = self.current_population[:top_count]
        
        # Apply minimum performance filter if specified
        if min_performance is not None:
            candidates = [s for s in candidates 
                         if s.performance and s.performance.get("total_return", 0) >= min_performance]
        
        # Convert to simplified format for return
        for strategy in candidates:
            promoted.append({
                "id": strategy.id,
                "name": strategy.name,
                "type": strategy.type,
                "parameters": strategy.parameters,
                "performance": strategy.performance,
                "generation": strategy.generation
            })
        
        return promoted
    
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
        
        Returns:
            Summary information
        """
        current_gen = self.current_population[0].generation if self.current_population else 0
        
        return {
            "current_generation": current_gen,
            "population_size": len(self.current_population),
            "historical_generations": len(self.history),
            "best_strategies_count": len(self.best_strategies),
            "top_performer": vars(self.best_strategies[0]) if self.best_strategies else None,
            "config": vars(self.config)
        } 
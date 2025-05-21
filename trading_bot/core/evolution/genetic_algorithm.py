"""
Genetic algorithm implementation for trading strategy evolution.

This module implements a robust genetic algorithm framework for evolving
trading strategies based on performance metrics.
"""

import logging
import random
import numpy as np
from typing import List, Dict, Any, Callable, Tuple, Optional, Union
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class Chromosome:
    """
    Represents a chromosome in the genetic algorithm - a single strategy implementation.
    """
    
    def __init__(
        self,
        parameters: Dict[str, Any],
        schema: Dict[str, Dict[str, Any]],
        generation: int = 0,
        parent_ids: List[str] = None,
        fitness: float = None,
        performance: Dict[str, Any] = None,
        id: Optional[str] = None,
        name: Optional[str] = None
    ):
        """
        Initialize a chromosome.
        
        Args:
            parameters: Parameter values for this strategy
            schema: Parameter definitions and constraints
            generation: Generation number
            parent_ids: IDs of parent chromosomes
            fitness: Fitness score
            performance: Performance metrics
            id: Unique ID (generated if not provided)
            name: Human-readable name
        """
        self.id = id or f"chrom_{uuid.uuid4().hex[:8]}"
        self.name = name or f"Strategy {self.id}"
        self.parameters = parameters
        self.schema = schema
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.fitness = fitness
        self.performance = performance or {}
        self.creation_date = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chromosome to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "parameters": self.parameters,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "fitness": self.fitness,
            "performance": self.performance,
            "creation_date": self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> 'Chromosome':
        """Create chromosome from dictionary."""
        return cls(
            parameters=data["parameters"],
            schema=schema,
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            fitness=data.get("fitness"),
            performance=data.get("performance", {}),
            id=data.get("id"),
            name=data.get("name")
        )

class GeneticAlgorithm:
    """
    Implementation of genetic algorithm for trading strategy evolution.
    """
    
    def __init__(
        self,
        parameter_schema: Dict[str, Dict[str, Any]],
        population_size: int = 50,
        elite_size: int = 5,
        mutation_rate: float = 0.2,
        crossover_rate: float = 0.7,
        tournament_size: int = 5,
        fitness_function: Optional[Callable[[Dict[str, Any]], float]] = None
    ):
        """
        Initialize the genetic algorithm.
        
        Args:
            parameter_schema: Schema defining parameters and constraints
            population_size: Size of the population
            elite_size: Number of top individuals to preserve unchanged
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            tournament_size: Size of tournament for selection
            fitness_function: Custom fitness function
        """
        self.parameter_schema = parameter_schema
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.fitness_function = fitness_function or self._default_fitness_function
        
        self.current_generation = 0
        self.population: List[Chromosome] = []
        self.history: Dict[int, List[Chromosome]] = {}
    
    def initialize_population(self) -> List[Chromosome]:
        """
        Initialize a random population based on the parameter schema.
        
        Returns:
            List of chromosomes in the initial population
        """
        population = []
        
        for i in range(self.population_size):
            # Generate random parameters based on schema
            parameters = self._generate_random_parameters()
            
            # Create chromosome
            chromosome = Chromosome(
                parameters=parameters,
                schema=self.parameter_schema,
                generation=0,
                name=f"Gen0_Indiv{i}"
            )
            
            population.append(chromosome)
        
        self.population = population
        self.current_generation = 0
        self.history[0] = population.copy()
        
        logger.info(f"Initialized population with {len(population)} individuals")
        return population
    
    def evolve(self) -> Tuple[List[Chromosome], Dict[str, Any]]:
        """
        Evolve the current population to create the next generation.
        
        Returns:
            Tuple of (new population, evolution metrics)
        """
        # Calculate fitness for the current population if not already done
        self._calculate_fitness()
        
        # Sort population by fitness
        self.population.sort(key=lambda x: x.fitness if x.fitness is not None else float('-inf'), reverse=True)
        
        # Store best individuals for elite selection
        elites = self.population[:self.elite_size]
        
        # Create mating pool through selection
        mating_pool = self._selection()
        
        # Create next generation through crossover and mutation
        next_generation = []
        
        # Add elites to next generation
        for elite in elites:
            next_generation.append(Chromosome(
                parameters=elite.parameters.copy(),
                schema=self.parameter_schema,
                generation=self.current_generation + 1,
                parent_ids=[elite.id],
                name=f"Elite_Gen{self.current_generation+1}_{len(next_generation)}"
            ))
        
        # Fill the rest of the population with offspring
        while len(next_generation) < self.population_size:
            # Select parents for crossover
            if random.random() < self.crossover_rate and len(mating_pool) >= 2:
                parent1 = random.choice(mating_pool)
                parent2 = random.choice(mating_pool)
                
                # Avoid using the same parent twice
                while parent2.id == parent1.id and len(mating_pool) > 1:
                    parent2 = random.choice(mating_pool)
                
                # Create offspring through crossover
                offspring = self._crossover(parent1, parent2)
                
                # Apply mutation
                if random.random() < self.mutation_rate:
                    self._mutate(offspring)
                
                next_generation.append(offspring)
            else:
                # If no crossover, just clone a parent with mutation
                parent = random.choice(mating_pool)
                offspring = Chromosome(
                    parameters=parent.parameters.copy(),
                    schema=self.parameter_schema,
                    generation=self.current_generation + 1,
                    parent_ids=[parent.id],
                    name=f"Clone_Gen{self.current_generation+1}_{len(next_generation)}"
                )
                
                # Apply mutation
                if random.random() < self.mutation_rate:
                    self._mutate(offspring)
                
                next_generation.append(offspring)
        
        # Update population and generation counter
        self.population = next_generation
        self.current_generation += 1
        self.history[self.current_generation] = next_generation.copy()
        
        # Calculate evolution metrics
        metrics = {
            "generation": self.current_generation,
            "population_size": len(next_generation),
            "best_fitness": elites[0].fitness if elites else None,
            "avg_fitness": np.mean([c.fitness for c in self.population if c.fitness is not None]) if self.population else None,
            "unique_parameter_sets": len(set(tuple(sorted(c.parameters.items())) for c in self.population)),
            "elite_count": len(elites),
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate
        }
        
        logger.info(f"Evolved to generation {self.current_generation} with {len(next_generation)} individuals")
        
        return next_generation, metrics
    
    def _calculate_fitness(self) -> None:
        """Calculate fitness for all chromosomes in the population."""
        for chromosome in self.population:
            if chromosome.fitness is None and chromosome.performance:
                chromosome.fitness = self.fitness_function(chromosome.performance)
    
    def _selection(self) -> List[Chromosome]:
        """
        Select individuals for reproduction using tournament selection.
        
        Returns:
            List of selected chromosomes
        """
        selected = []
        
        # Use tournament selection to fill the mating pool
        for _ in range(self.population_size - self.elite_size):
            tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
            winner = max(tournament, key=lambda x: x.fitness if x.fitness is not None else float('-inf'))
            selected.append(winner)
        
        return selected
    
    def _crossover(self, parent1: Chromosome, parent2: Chromosome) -> Chromosome:
        """
        Perform crossover between two parents to create an offspring.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
            
        Returns:
            New chromosome from crossover
        """
        child_params = {}
        
        # Different crossover strategies based on parameter type
        for param_name, param_schema in self.parameter_schema.items():
            param_type = param_schema.get("type", "float")
            
            # Randomly select from which parent to inherit each parameter
            # or use a mixing strategy for numeric parameters
            if param_type in ["int", "float"] and random.random() < 0.5:
                # Blend crossover for numeric parameters
                p1_val = parent1.parameters.get(param_name)
                p2_val = parent2.parameters.get(param_name)
                
                # Check if both parents have this parameter
                if p1_val is not None and p2_val is not None:
                    # Blend with some random variation
                    alpha = random.uniform(-0.1, 1.1)  # Allow slight extrapolation
                    blend = p1_val + alpha * (p2_val - p1_val)
                    
                    # Enforce parameter constraints
                    min_val = param_schema.get("min")
                    max_val = param_schema.get("max")
                    
                    if min_val is not None:
                        blend = max(min_val, blend)
                    if max_val is not None:
                        blend = min(max_val, blend)
                    
                    # Convert to int if needed
                    if param_type == "int":
                        blend = int(round(blend))
                    
                    child_params[param_name] = blend
                else:
                    # If parameter is missing in one parent, inherit from the other
                    child_params[param_name] = p1_val if p1_val is not None else p2_val
            else:
                # For non-numeric or with 50% probability, inherit from one parent
                parent = parent1 if random.random() < 0.5 else parent2
                child_params[param_name] = parent.parameters.get(param_name)
        
        # Create child chromosome
        return Chromosome(
            parameters=child_params,
            schema=self.parameter_schema,
            generation=self.current_generation + 1,
            parent_ids=[parent1.id, parent2.id],
            name=f"Child_Gen{self.current_generation+1}"
        )
    
    def _mutate(self, chromosome: Chromosome) -> None:
        """
        Mutate a chromosome in place.
        
        Args:
            chromosome: Chromosome to mutate
        """
        # Randomly select parameters to mutate
        for param_name, param_schema in self.parameter_schema.items():
            # Each parameter has a chance to mutate
            if random.random() < self.mutation_rate:
                param_type = param_schema.get("type", "float")
                
                # Different mutation strategies based on parameter type
                if param_type == "int":
                    current_value = chromosome.parameters.get(param_name, 0)
                    min_val = param_schema.get("min", 0)
                    max_val = param_schema.get("max", 100)
                    
                    # Determine mutation range
                    range_size = max_val - min_val
                    mutation_size = max(1, int(range_size * 0.1))  # 10% of range or at least 1
                    
                    # Apply mutation
                    delta = random.randint(-mutation_size, mutation_size)
                    new_value = current_value + delta
                    
                    # Constrain to range
                    new_value = max(min_val, min(max_val, new_value))
                    
                    chromosome.parameters[param_name] = new_value
                
                elif param_type == "float":
                    current_value = chromosome.parameters.get(param_name, 0.0)
                    min_val = param_schema.get("min", 0.0)
                    max_val = param_schema.get("max", 1.0)
                    
                    # Determine mutation range
                    range_size = max_val - min_val
                    mutation_size = range_size * 0.1  # 10% of range
                    
                    # Apply mutation
                    delta = random.uniform(-mutation_size, mutation_size)
                    new_value = current_value + delta
                    
                    # Constrain to range
                    new_value = max(min_val, min(max_val, new_value))
                    
                    chromosome.parameters[param_name] = new_value
                
                elif param_type == "bool":
                    # Flip boolean
                    current_value = chromosome.parameters.get(param_name, False)
                    chromosome.parameters[param_name] = not current_value
                
                elif param_type == "categorical":
                    # Select a random category
                    categories = param_schema.get("categories", [])
                    if categories:
                        chromosome.parameters[param_name] = random.choice(categories)
    
    def _generate_random_parameters(self) -> Dict[str, Any]:
        """
        Generate random parameters based on the schema.
        
        Returns:
            Dictionary of parameter values
        """
        parameters = {}
        
        for param_name, param_schema in self.parameter_schema.items():
            param_type = param_schema.get("type", "float")
            
            if param_type == "int":
                min_val = param_schema.get("min", 0)
                max_val = param_schema.get("max", 100)
                parameters[param_name] = random.randint(min_val, max_val)
            
            elif param_type == "float":
                min_val = param_schema.get("min", 0.0)
                max_val = param_schema.get("max", 1.0)
                parameters[param_name] = random.uniform(min_val, max_val)
            
            elif param_type == "bool":
                parameters[param_name] = random.choice([True, False])
            
            elif param_type == "categorical":
                categories = param_schema.get("categories", [])
                if categories:
                    parameters[param_name] = random.choice(categories)
                else:
                    parameters[param_name] = None
            
            # Set default value if nothing else applies
            elif "default" in param_schema:
                parameters[param_name] = param_schema["default"]
        
        return parameters
    
    def _default_fitness_function(self, performance: Dict[str, Any]) -> float:
        """
        Default fitness function based on a combination of metrics.
        
        Args:
            performance: Dictionary of performance metrics
            
        Returns:
            Fitness score (higher is better)
        """
        if not performance:
            return float('-inf')
        
        # Extract metrics with fallbacks to 0
        total_return = performance.get("total_return", 0)
        sharpe_ratio = performance.get("sharpe_ratio", 0)
        max_drawdown = performance.get("max_drawdown", 0)
        win_rate = performance.get("win_rate", 0)
        trades_count = performance.get("trades_count", 0)
        
        # Handle case with no trades
        if trades_count == 0:
            return float('-inf')
        
        # Bad performance cases
        if total_return <= -90 or max_drawdown >= 90:
            return float('-inf')
        
        # Basic fitness: return * sharpe - (drawdown penalty)
        fitness = total_return * max(0.1, sharpe_ratio) - (max_drawdown * 0.5)
        
        # Slight boost for strategies with more trades (more statistically significant)
        # but don't overweight this aspect
        trade_factor = min(1.0, trades_count / 50)  # Cap at 50 trades
        fitness *= (0.8 + 0.2 * trade_factor)
        
        # Boost for high win rate strategies
        win_rate_factor = win_rate / 50  # Convert percentage to factor
        fitness *= (0.8 + 0.2 * win_rate_factor)
        
        return fitness
    
    def get_best_individuals(self, count: int = 1) -> List[Chromosome]:
        """
        Get the best individuals from the current population.
        
        Args:
            count: Number of individuals to return
            
        Returns:
            List of best chromosomes
        """
        # Calculate fitness for any chromosomes without fitness
        self._calculate_fitness()
        
        # Sort by fitness
        sorted_population = sorted(
            self.population,
            key=lambda x: x.fitness if x.fitness is not None else float('-inf'),
            reverse=True
        )
        
        return sorted_population[:count] 
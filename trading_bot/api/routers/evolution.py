"""
API routes for the strategy evolution system.

This module provides endpoints for:
- Managing strategy evolution
- Running backtests
- Visualizing performance
- Auto-promoting strategies
- LLM-guided fitness evaluation
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import time
import random
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/evolution",
    tags=["evolution"],
    responses={404: {"description": "Not found"}},
)

# Mock in-memory store for running backtest
running_backtests = {}

# Models for API requests/responses
class EvolutionConfig(BaseModel):
    population_size: int = 50
    generations: int = 20
    mutation_rate: float = 0.2
    crossover_rate: float = 0.7
    elite_size: int = 5
    selection_method: str = "tournament"
    tournament_size: int = 5
    auto_promotion_threshold: float = 0.2

class StrategyParameters(BaseModel):
    type: str
    parameter_space: Dict[str, Any]

class GridConfig(BaseModel):
    param1_name: str
    param1_range: List[Any]
    param2_name: str
    param2_range: List[Any]
    fixed_params: Optional[Dict[str, Any]] = None
    strategy_type: str
    metric: str = "total_return"

class LLMEvaluationRequest(BaseModel):
    strategy_id: Optional[str] = Field(None, description="Strategy ID for caching")
    strategy_type: str = Field(..., description="Type of strategy")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Market conditions during testing")

class LLMBatchEvaluationRequest(BaseModel):
    strategies: List[Dict[str, Any]] = Field(..., description="List of strategies to evaluate")

class LLMImprovementRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID")
    strategy_type: str = Field(..., description="Type of strategy")
    parameters: Dict[str, Any] = Field(..., description="Current parameters")
    performance_history: List[Dict[str, Any]] = Field(..., description="List of historical performance data")

class BacktestRequest(BaseModel):
    """Request model for backtesting an evolutionary strategy."""
    strategy_type: str
    parameters: Dict[str, Any]
    symbols: List[str]
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 10000.0

class StrategyOptimizationRequest(BaseModel):
    """Request model for optimizing strategy parameters."""
    strategy_type: str
    parameter_ranges: Dict[str, Dict[str, Any]]
    symbols: List[str]
    start_date: str
    end_date: str
    timeframe: str = "1d"
    initial_capital: float = 10000.0
    generations: int = 10
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    fitness_metric: str = "sharpe_ratio"  # or "total_return", "calmar_ratio", etc.

# Create EvoTrader and BacktestGrid instances
# We'll create these here so they can be imported by the main app
from trading_bot.core.evolution import EvoTrader, BacktestGrid
from trading_bot.core.evolution.llm_evaluator import LLMEvaluator

# These will be initialized when the main app loads
evo_trader = None
backtest_grid = None
llm_evaluator = None

# Initialization function to be called by the main app
def init_evolution_services(backtester=None):
    global evo_trader, backtest_grid, llm_evaluator
    
    # Create a backtester registry
    backtester_registry = {}
    if backtester:
        # Using a generic 'default' key for the backtester
        backtester_registry['default'] = backtester
    
    # Initialize with the registry instead of direct backtester
    evo_trader = EvoTrader(
        config_path="./config/evolution.json",
        data_dir="./data/evolution",
        backtester_registry=backtester_registry
    )
    
    # BacktestGrid still uses direct backtester
    backtest_grid = BacktestGrid(backtester=backtester)
    
    # Initialize LLM evaluator
    llm_evaluator = LLMEvaluator(
        data_dir="./data/llm_evaluation",
        cache_results=True
    )
    
    return evo_trader

# Endpoints

@router.get("/status")
async def get_evolution_status():
    """Get current evolution status and summary."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        summary = evo_trader.get_evolution_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"Error getting evolution status: {e}")
        return {"success": False, "error": str(e)}

@router.post("/start")
async def start_evolution(params: StrategyParameters, config: Optional[EvolutionConfig] = None):
    """Start a new evolution run."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        # Mock market data - in production, this would come from a data service
        market_data = {"data_source": "mock", "timeframe": "1h", "start_date": "2023-01-01"}
        
        if config:
            evolution_config = evo_trader.config.__class__(**config.dict())
        else:
            evolution_config = None
        
        run_id = evo_trader.start_evolution(
            strategy_type=params.type,
            parameter_space=params.parameter_space,
            market_data=market_data,
            config=evolution_config
        )
        
        return {"success": True, "data": {"run_id": run_id}}
    except Exception as e:
        logger.error(f"Error starting evolution: {e}")
        return {"success": False, "error": str(e)}

@router.post("/backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Run a backtest for a trading strategy."""
    try:
        # Generate a unique ID for this backtest
        backtest_id = f"bt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        # In a real implementation, this would run a backtest using actual
        # historical data and the specified strategy/parameters
        logger.info(f"Starting backtest {backtest_id} with {request.strategy_type} strategy")
        
        # Add to running backtests
        running_backtests[backtest_id] = {
            "status": "running",
            "progress": 0,
            "request": request.dict(),
            "start_time": datetime.now().isoformat()
        }
        
        # Run backtest in background
        background_tasks.add_task(simulate_backtest, backtest_id)
        
        return {
            "backtest_id": backtest_id,
            "status": "started",
            "message": f"Backtest for {request.strategy_type} on {', '.join(request.symbols)} started"
        }
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting backtest: {str(e)}")

@router.get("/backtest/{backtest_id}")
async def get_backtest_status(backtest_id: str) -> Dict[str, Any]:
    """Get the status of a running or completed backtest."""
    if backtest_id not in running_backtests:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    return running_backtests[backtest_id]

@router.post("/evolve")
async def evolve_generation():
    """Evolve the current generation to create a new one."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        result = evo_trader.evolve_generation()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error evolving generation: {e}")
        return {"success": False, "error": str(e)}

@router.get("/strategies")
async def get_strategies(generation: Optional[int] = None, limit: int = 50):
    """Get strategies from current population."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        population = evo_trader.current_population
        if generation is not None:
            population = [s for s in population if s.generation == generation]
        
        # Convert to dictionaries and limit
        strategies = [vars(s) for s in population[:limit]]
        
        return {"success": True, "data": strategies}
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return {"success": False, "error": str(e)}

@router.get("/best")
async def get_best_strategies(limit: int = 10):
    """Get the best strategies found so far."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        strategies = [vars(s) for s in evo_trader.best_strategies[:limit]]
        return {"success": True, "data": strategies}
    except Exception as e:
        logger.error(f"Error getting best strategies: {e}")
        return {"success": False, "error": str(e)}

@router.get("/strategy/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get details of a specific strategy."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        details = evo_trader.get_strategy_details(strategy_id)
        if not details:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"success": True, "data": details}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting strategy details: {e}")
        return {"success": False, "error": str(e)}

@router.post("/promote")
async def auto_promote_strategies(min_performance: Optional[float] = None):
    """Auto-promote strategies that meet performance criteria."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        promoted = evo_trader.auto_promote_strategies(min_performance)
        return {"success": True, "data": promoted}
    except Exception as e:
        logger.error(f"Error promoting strategies: {e}")
        return {"success": False, "error": str(e)}

@router.post("/grid")
async def create_backtest_grid(config: GridConfig, background_tasks: BackgroundTasks):
    """Create and run a backtest parameter grid."""
    if not backtest_grid:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        # Create grid configuration
        grid_config = backtest_grid.create_parameter_grid(
            param1_name=config.param1_name,
            param1_range=config.param1_range,
            param2_name=config.param2_name,
            param2_range=config.param2_range,
            fixed_params=config.fixed_params
        )
        
        # Mock market data - in production, this would come from a data service
        market_data = {"data_source": "mock", "timeframe": "1h", "start_date": "2023-01-01"}
        
        # This could be a long-running task, so run in background
        def run_grid():
            try:
                backtest_grid.run_grid_backtest(
                    grid_config=grid_config,
                    strategy_type=config.strategy_type,
                    market_data=market_data,
                    metric=config.metric
                )
            except Exception as e:
                logger.error(f"Error in background grid backtest: {e}")
        
        background_tasks.add_task(run_grid)
        
        return {
            "success": True, 
            "data": {"grid_id": grid_config["id"]},
            "message": "Grid backtest started in background"
        }
    except Exception as e:
        logger.error(f"Error creating backtest grid: {e}")
        return {"success": False, "error": str(e)}

@router.get("/grid/{grid_id}")
async def get_grid_results(grid_id: str):
    """Get results of a backtest grid."""
    if not backtest_grid:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        results = backtest_grid.get_grid_results(grid_id)
        if not results:
            raise HTTPException(status_code=404, detail="Grid not found")
        return {"success": True, "data": results}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting grid results: {e}")
        return {"success": False, "error": str(e)}

@router.get("/grids")
async def list_grids():
    """List all available backtest grids."""
    if not backtest_grid:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        grids = backtest_grid.list_available_grids()
        return {"success": True, "data": grids}
    except Exception as e:
        logger.error(f"Error listing grids: {e}")
        return {"success": False, "error": str(e)}

@router.post("/evaluate/llm")
async def evaluate_strategy_with_llm(request: LLMEvaluationRequest):
    """Evaluate a strategy using LLM guidance."""
    if not llm_evaluator:
        return {"success": False, "error": "LLM evaluator not initialized"}
    
    try:
        evaluation = llm_evaluator.evaluate_strategy(
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            performance=request.performance,
            strategy_id=request.strategy_id,
            market_conditions=request.market_conditions
        )
        
        return {"success": True, "data": evaluation}
    except Exception as e:
        logger.error(f"Error evaluating strategy with LLM: {e}")
        return {"success": False, "error": str(e)}

@router.post("/evaluate/llm/batch")
async def batch_evaluate_strategies(request: LLMBatchEvaluationRequest, background_tasks: BackgroundTasks):
    """Evaluate multiple strategies using LLM guidance."""
    if not llm_evaluator:
        return {"success": False, "error": "LLM evaluator not initialized"}
    
    try:
        # For larger batches, run in background
        if len(request.strategies) > 5:
            task_id = f"batch_eval_{int(time.time())}"
            
            def run_batch_eval():
                try:
                    llm_evaluator.batch_evaluate(request.strategies)
                except Exception as e:
                    logger.error(f"Error in background batch evaluation: {e}")
            
            background_tasks.add_task(run_batch_eval)
            
            return {
                "success": True,
                "message": f"Batch evaluation started in background for {len(request.strategies)} strategies",
                "task_id": task_id
            }
        else:
            # For smaller batches, run synchronously
            evaluations = llm_evaluator.batch_evaluate(request.strategies)
            return {"success": True, "data": evaluations}
    except Exception as e:
        logger.error(f"Error batch evaluating strategies with LLM: {e}")
        return {"success": False, "error": str(e)}

@router.post("/improve/llm")
async def get_improvement_recommendations(request: LLMImprovementRequest):
    """Get recommendations to improve a strategy based on its performance history."""
    if not llm_evaluator:
        return {"success": False, "error": "LLM evaluator not initialized"}
    
    try:
        recommendations = llm_evaluator.get_improvement_recommendations(
            strategy_id=request.strategy_id,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            performance_history=request.performance_history
        )
        
        return {"success": True, "data": recommendations}
    except Exception as e:
        logger.error(f"Error getting improvement recommendations: {e}")
        return {"success": False, "error": str(e)}

@router.post("/optimize")
async def optimize_strategy(request: StrategyOptimizationRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Run a genetic algorithm to optimize strategy parameters."""
    try:
        # Generate a unique ID for this optimization
        optimization_id = f"opt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        # In a real implementation, this would run a genetic algorithm to optimize 
        # strategy parameters based on historical performance
        logger.info(f"Starting optimization {optimization_id} for {request.strategy_type} strategy")
        
        # Add to running backtests with optimization flag
        running_backtests[optimization_id] = {
            "status": "running",
            "progress": 0,
            "is_optimization": True,
            "request": request.dict(),
            "start_time": datetime.now().isoformat()
        }
        
        # Run optimization in background
        background_tasks.add_task(simulate_optimization, optimization_id)
        
        return {
            "optimization_id": optimization_id,
            "status": "started",
            "message": f"Optimization for {request.strategy_type} started"
        }
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting optimization: {str(e)}")

# Internal simulation functions
async def simulate_backtest(backtest_id: str):
    """Simulate a backtest running in the background."""
    import asyncio
    import random
    
    # Simulate progress
    for progress in range(0, 101, 10):
        running_backtests[backtest_id]["progress"] = progress
        await asyncio.sleep(0.5)  # Simulate work
    
    # Generate mock results
    running_backtests[backtest_id] = {
        **running_backtests[backtest_id],
        "status": "completed",
        "progress": 100,
        "end_time": datetime.now().isoformat(),
        "results": {
            "total_return": round(random.uniform(-10, 40), 2),
            "sharpe_ratio": round(random.uniform(0.5, 3.0), 2),
            "max_drawdown": round(random.uniform(-30, -5), 2),
            "win_rate": round(random.uniform(40, 80), 2),
            "trades": random.randint(20, 200),
            "equity_curve": [10000 * (1 + random.uniform(-0.01, 0.02)) for _ in range(100)]
        }
    }

async def simulate_optimization(optimization_id: str):
    """Simulate a strategy optimization running in the background."""
    import asyncio
    import random
    
    # Simulate progress
    for progress in range(0, 101, 5):
        running_backtests[optimization_id]["progress"] = progress
        
        # Add more detailed status updates for optimization
        if progress % 20 == 0:
            running_backtests[optimization_id]["current_generation"] = progress // 5
            running_backtests[optimization_id]["best_fitness"] = round(0.5 + progress/100, 2)
        
        await asyncio.sleep(1)  # Optimization is slower
    
    # Generate mock optimization results
    running_backtests[optimization_id] = {
        **running_backtests[optimization_id],
        "status": "completed",
        "progress": 100,
        "end_time": datetime.now().isoformat(),
        "results": {
            "best_parameters": {
                "lookback_period": random.randint(10, 40),
                "entry_threshold": round(random.uniform(0.5, 2.5), 2),
                "exit_threshold": round(random.uniform(0.2, 1.0), 2),
                "stop_loss": round(random.uniform(1.0, 5.0), 2),
                "take_profit": round(random.uniform(2.0, 10.0), 2),
            },
            "best_fitness": round(random.uniform(1.5, 4.0), 2),
            "generations": random.randint(8, 15),
            "population_size": random.randint(40, 60),
            "convergence_generation": random.randint(5, 12),
            "optimization_metric": "sharpe_ratio"
        }
    } 
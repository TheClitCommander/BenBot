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

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/evolution",
    tags=["evolution"],
    responses={404: {"description": "Not found"}},
)

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
    evo_trader = EvoTrader(backtester=backtester)
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
async def run_backtest_generation(background_tasks: BackgroundTasks):
    """Run backtests for the current generation."""
    if not evo_trader:
        return {"success": False, "error": "Evolution services not initialized"}
    
    try:
        # Mock market data - in production, this would come from a data service
        market_data = {"data_source": "mock", "timeframe": "1h", "start_date": "2023-01-01"}
        
        # This could be a long-running task, so we can run it in the background
        def run_backtest():
            try:
                evo_trader.run_backtest_generation(market_data)
            except Exception as e:
                logger.error(f"Error in background backtest: {e}")
        
        background_tasks.add_task(run_backtest)
        
        return {
            "success": True, 
            "message": "Backtest started in background"
        }
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return {"success": False, "error": str(e)}

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
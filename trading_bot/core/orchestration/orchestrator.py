"""
Central Orchestrator for the BensBot Trading System.

This module coordinates EvolutionScheduler, EvoTrader, EvoToExecAdapter, and SafetyManager.
"""
import logging
from typing import Dict, Any, List, Optional

# Forward references for type hinting to avoid circular imports at runtime
# These will be actual imports within methods or if needed for Pydantic models
# from trading_bot.core.evolution.evo_trader import EvoTrader, StrategyGenome
# from trading_bot.core.execution.scheduler import EvolutionScheduler
# from trading_bot.core.execution.evo_adapter import EvoToExecAdapter
# from trading_bot.core.safety.safety_manager import SafetyManager

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Coordinates trading system components for autonomous operation and UI.
    """
    def __init__(
        self,
        evo_trader: Any, # Actual type: EvoTrader
        scheduler: Any, # Actual type: EvolutionScheduler
        adapter: Any,   # Actual type: EvoToExecAdapter
        safety: Any,    # Actual type: SafetyManager
        # Potentially add LLMEvaluator if direct interaction is needed often
        # llm_evaluator: Optional[Any] = None 
    ):
        """
        Initialize the Orchestrator with references to core services.
        """
        self.evo_trader = evo_trader
        self.scheduler = scheduler
        self.adapter = adapter
        self.safety_manager = safety
        # self.llm_evaluator = llm_evaluator
        logger.info("Orchestrator initialized with core services.")

    async def schedule_evolution_run(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedules a new strategy evolution run.
        The UI will send schedule_config which matches EvolutionScheduler.add_schedule requirements.
        """
        if not self.scheduler:
            logger.error("EvolutionScheduler not available in Orchestrator.")
            return {"success": False, "error": "Scheduler not configured"}
        
        try:
            # Assuming schedule_config contains:
            # strategy_type, parameter_space, market_data_id, schedule_time, run_daily, etc.
            schedule_id = self.scheduler.add_schedule(**schedule_config)
            if schedule_id:
                logger.info(f"Orchestrator scheduled evolution run: {schedule_id} with config: {schedule_config}")
                return {"success": True, "schedule_id": schedule_id, "message": "Evolution run scheduled."}
            else:
                logger.error(f"Orchestrator failed to schedule evolution run with config: {schedule_config}")
                return {"success": False, "error": "Failed to schedule evolution run."}
        except Exception as e:
            logger.error(f"Error in Orchestrator scheduling evolution run: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_evolution_status(self) -> Dict[str, Any]:
        """
        Gets the current status of the strategy evolution process.
        This might involve checking active runs in scheduler or general EvoTrader status.
        """
        if not self.evo_trader:
            logger.error("EvoTrader not available in Orchestrator.")
            return {"success": False, "error": "EvoTrader not configured"}
        try:
            status = self.evo_trader.get_evolution_summary() # Assuming EvoTrader has such a method
            # We might also want to combine this with scheduler's active tasks
            scheduled_runs = self.scheduler.get_schedules() if self.scheduler else []
            active_scheduled_run = None
            for run in scheduled_runs:
                if run.get('status') == 'running' or (run.get('last_run_status') == 'running' and not run.get('next_run_time')): # Simplified logic
                    active_scheduled_run = run
                    break
            
            return {
                "success": True, 
                "evo_trader_status": status, 
                "scheduled_runs_summary": {
                    "total_scheduled": len(scheduled_runs),
                    "active_scheduled_run": active_scheduled_run
                }
            }
        except Exception as e:
            logger.error(f"Error in Orchestrator getting evolution status: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_best_strategies(self, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieves the best performing strategies from EvoTrader.
        """
        if not self.evo_trader:
            logger.error("EvoTrader not available in Orchestrator.")
            return {"success": False, "error": "EvoTrader not configured", "strategies": []}
        try:
            # EvoTrader.get_best_strategies() should return a list of StrategyGenome objects or dicts
            strategies = self.evo_trader.best_strategies # Accessing the property directly
            
            # Ensure it's a list of dicts for JSON serialization
            strategies_data = []
            for strat in strategies[:limit]:
                if hasattr(strat, 'to_dict'): # Ideal if StrategyGenome has a to_dict method
                    strategies_data.append(strat.to_dict())
                elif isinstance(strat, dict):
                    strategies_data.append(strat)
                else: # Fallback for dataclasses or other objects
                    # from trading_bot.core.evolution.evo_trader import StrategyGenome
                    # if isinstance(strat, StrategyGenome):
                    #    strategies_data.append(vars(strat)) 
                    # For now, let's assume they are already dicts or easily convertible
                    strategies_data.append(vars(strat) if not isinstance(strat, dict) else strat)


            logger.info(f"Orchestrator retrieved {len(strategies_data)} best strategies.")
            return {"success": True, "strategies": strategies_data}
        except Exception as e:
            logger.error(f"Error in Orchestrator getting best strategies: {e}", exc_info=True)
            return {"success": False, "error": str(e), "strategies": []}

    async def activate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Activates a specific strategy for (mock) trading using EvoToExecAdapter.
        """
        if not self.adapter:
            logger.error("EvoToExecAdapter not available in Orchestrator.")
            return {"success": False, "error": "Execution adapter not configured"}
        try:
            success = self.adapter.activate_strategy(strategy_id)
            if success:
                logger.info(f"Orchestrator activated strategy: {strategy_id}")
                return {"success": True, "message": f"Strategy {strategy_id} activated."}
            else:
                # EvoToExecAdapter logs detailed reasons for failure
                logger.warning(f"Orchestrator failed to activate strategy: {strategy_id}")
                return {"success": False, "error": f"Failed to activate strategy {strategy_id}. Check logs for details."}
        except Exception as e:
            logger.error(f"Error in Orchestrator activating strategy {strategy_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_active_strategies(self) -> Dict[str, Any]:
        """
        Retrieves the list of currently active (mock) trading strategies.
        """
        if not self.adapter:
            logger.error("EvoToExecAdapter not available in Orchestrator.")
            return {"success": False, "error": "Execution adapter not configured", "strategies": []}
        try:
            # EvoToExecAdapter.get_active_strategies() returns a list of dicts
            active_strategies = self.adapter.get_active_strategies()
            logger.info(f"Orchestrator retrieved {len(active_strategies)} active strategies.")
            return {"success": True, "strategies": active_strategies}
        except Exception as e:
            logger.error(f"Error in Orchestrator getting active strategies: {e}", exc_info=True)
            return {"success": False, "error": str(e), "strategies": []}

    async def get_safety_status(self) -> Dict[str, Any]:
        """
        Retrieves the current overall safety status from SafetyManager.
        """
        if not self.safety_manager:
            logger.error("SafetyManager not available in Orchestrator.")
            return {"success": False, "error": "Safety manager not configured"}
        try:
            # SafetyManager.get_safety_status() returns a dict
            status = self.safety_manager.get_safety_status()
            logger.debug("Orchestrator retrieved safety status.")
            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Error in Orchestrator getting safety status: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Provides a combined overview of the system state.
        """
        evo_status = await self.get_evolution_status()
        active_strats = await self.get_active_strategies()
        safety_status = await self.get_safety_status()
        
        return {
            "evolution_overview": evo_status.get("evo_trader_status", {}),
            "scheduled_runs_summary": evo_status.get("scheduled_runs_summary", {}),
            "active_strategies_count": len(active_strats.get("strategies", [])),
            "safety_status": safety_status.get("status", {}),
            "timestamp": logger.root.handlers[0].formatter.formatTime(logging.LogRecord(None,None,"",0,"",(),None,None)) # Get current time in log format
        }

# Placeholder for actual service types if strict type checking is desired later
# class EvoTraderPlaceholder:
#     def get_evolution_summary(self): return {}
#     best_strategies = []
# class EvolutionSchedulerPlaceholder:
#     def add_schedule(self, **kwargs): return "schedule_id_123"
#     def get_schedules(self): return []
# class EvoToExecAdapterPlaceholder:
#     def activate_strategy(self, strategy_id): return True
#     def get_active_strategies(self): return []
# class SafetyManagerPlaceholder:
#     def get_safety_status(self): return {}

# if __name__ == '__main__':
    # Basic test setup (won't run in FastAPI context like this)
    # logging.basicConfig(level=logging.INFO)
    # mock_evo_trader = EvoTraderPlaceholder()
    # mock_scheduler = EvolutionSchedulerPlaceholder()
    # mock_adapter = EvoToExecAdapterPlaceholder()
    # mock_safety = SafetyManagerPlaceholder()
    
    # orch = Orchestrator(
    #     evo_trader=mock_evo_trader,
    #     scheduler=mock_scheduler,
    #     adapter=mock_adapter,
    #     safety=mock_safety
    # )
    # import asyncio
    # print(asyncio.run(orch.get_system_overview()))
    # print(asyncio.run(orch.schedule_evolution_run({"strategy_type": "test", "schedule_time": "22:00"}))) 
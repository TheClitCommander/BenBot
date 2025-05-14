"""
Scheduler for automated strategy evolution runs.

This module provides functionality to:
- Schedule automated evolution runs during off-peak hours
- Manage recurring and one-time evolution tasks
- Track evolution progress and results
"""

import logging
import threading
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, time as dt_time
from pathlib import Path

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

class EvolutionScheduler:
    """Scheduler for automated strategy evolution runs."""
    
    def __init__(
        self, 
        evo_trader=None, 
        data_dir: str = "./data/scheduler",
        config_path: str = "./config/scheduler.json"
    ):
        """
        Initialize the scheduler.
        
        Args:
            evo_trader: Reference to evolution trader service
            data_dir: Directory for storing schedule data
            config_path: Path to scheduler configuration
        """
        self.evo_trader = evo_trader
        self.data_dir = data_dir
        self.config_path = config_path
        
        # Create directories
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Active schedules
        self.schedules: Dict[str, Dict[str, Any]] = {}
        
        # Active schedule threads
        self.active_threads: Dict[str, threading.Thread] = {}
        
        # Load existing schedules
        self._load_schedules()
        
        # Flag to control background thread
        self.running = False
        self.scheduler_thread = None
    
    def _load_schedules(self) -> None:
        """Load existing schedules from storage."""
        try:
            schedule_path = os.path.join(self.data_dir, "schedules.json")
            if os.path.exists(schedule_path):
                with open(schedule_path, 'r') as f:
                    self.schedules = json.load(f)
                logger.info(f"Loaded {len(self.schedules)} evolution schedules")
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
            self.schedules = {}
    
    def _save_schedules(self) -> None:
        """Save schedules to storage."""
        try:
            schedule_path = os.path.join(self.data_dir, "schedules.json")
            with open(schedule_path, 'w') as f:
                json.dump(self.schedules, f, indent=2)
            logger.debug("Saved evolution schedules")
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def schedule_evolution(
        self,
        schedule_id: str,
        strategy_type: str,
        parameter_space: Dict[str, Any],
        market_data_id: str,
        schedule_time: dt_time,
        run_daily: bool = True,
        auto_promote: bool = False,
        generations: int = 20,
        population_size: int = 50,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> bool:
        """
        Schedule a new evolution run.
        
        Args:
            schedule_id: Unique ID for this schedule
            strategy_type: Type of strategy to evolve
            parameter_space: Parameter ranges for evolution
            market_data_id: Market data ID for backtesting
            schedule_time: Time to run (24h format)
            run_daily: Whether to run daily or once
            auto_promote: Auto-promote successful strategies
            generations: Number of generations to run
            population_size: Population size
            background_tasks: FastAPI background tasks for immediate execution
            
        Returns:
            Success flag
        """
        if not self.evo_trader:
            logger.error("EvoTrader not configured")
            return False
        
        # Create schedule entry
        schedule = {
            "id": schedule_id,
            "strategy_type": strategy_type,
            "parameter_space": parameter_space,
            "market_data_id": market_data_id,
            "schedule_time": schedule_time.isoformat(),
            "run_daily": run_daily,
            "auto_promote": auto_promote,
            "generations": generations,
            "population_size": population_size,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": None,
            "status": "scheduled"
        }
        
        # Set next run time
        schedule["next_run"] = self._get_next_run_time(schedule_time).isoformat()
        
        # Add to schedules
        self.schedules[schedule_id] = schedule
        
        # Save schedules
        self._save_schedules()
        
        # If we should run immediately, use background tasks
        now = datetime.now().time()
        if self._is_time_close(now, schedule_time, minutes=1) and background_tasks:
            logger.info(f"Starting immediate evolution run for schedule {schedule_id}")
            background_tasks.add_task(self._run_evolution, schedule_id)
        
        # Start the scheduler thread if not running
        if not self.running:
            self.start()
            
        return True
    
    def _get_next_run_time(self, schedule_time: dt_time) -> datetime:
        """
        Get the next run time for a scheduled job.
        
        Args:
            schedule_time: Scheduled time of day
            
        Returns:
            Next datetime to run
        """
        now = datetime.now()
        today_run = datetime.combine(now.date(), schedule_time)
        
        # If it's past the scheduled time today, set for tomorrow
        if now > today_run:
            tomorrow = now.date() + datetime.timedelta(days=1)
            return datetime.combine(tomorrow, schedule_time)
        
        return today_run
    
    def _is_time_close(self, time1: dt_time, time2: dt_time, minutes: int = 5) -> bool:
        """
        Check if two times are within a certain number of minutes of each other.
        
        Args:
            time1: First time
            time2: Second time
            minutes: Maximum difference in minutes
            
        Returns:
            True if times are within specified minutes
        """
        # Convert times to minutes since midnight
        time1_minutes = time1.hour * 60 + time1.minute
        time2_minutes = time2.hour * 60 + time2.minute
        
        # Get absolute difference
        diff = abs(time1_minutes - time2_minutes)
        
        # Handle wraparound at midnight
        if diff > 720:  # More than 12 hours apart (half a day)
            diff = 1440 - diff  # 24 hours (1440 minutes) minus difference
            
        return diff <= minutes
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled evolution runs.
        
        Returns:
            List of schedule details
        """
        return list(self.schedules.values())
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a scheduled evolution run.
        
        Args:
            schedule_id: ID of the schedule to delete
            
        Returns:
            Success flag
        """
        if schedule_id not in self.schedules:
            logger.warning(f"Schedule {schedule_id} not found")
            return False
        
        # Remove from schedules
        del self.schedules[schedule_id]
        
        # Save schedules
        self._save_schedules()
        
        return True
    
    def _run_evolution(self, schedule_id: str) -> None:
        """
        Run an evolution job.
        
        Args:
            schedule_id: ID of the schedule to run
        """
        if schedule_id not in self.schedules:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        schedule = self.schedules[schedule_id]
        
        try:
            # Update status
            schedule["status"] = "running"
            schedule["last_run"] = datetime.now().isoformat()
            self._save_schedules()
            
            # Get parameters
            strategy_type = schedule["strategy_type"]
            parameter_space = schedule["parameter_space"]
            market_data_id = schedule["market_data_id"]
            generations = schedule["generations"]
            population_size = schedule["population_size"]
            auto_promote = schedule["auto_promote"]
            
            # Set up evolution config
            from trading_bot.core.evolution.evo_trader import EvolutionConfig
            config = EvolutionConfig(
                population_size=population_size,
                generations=generations,
                auto_promotion_threshold=0.1 if auto_promote else 0.0  # Enable auto-promotion if requested
            )
            
            # Get market data
            from trading_bot.core.data import MarketDataService
            data_service = MarketDataService()
            market_data = data_service.get_market_data(market_data_id)
            
            if not market_data:
                raise ValueError(f"Market data {market_data_id} not found")
            
            # Start evolution
            run_id = self.evo_trader.start_evolution(
                strategy_type=strategy_type,
                parameter_space=parameter_space,
                market_data=market_data,
                config=config
            )
            
            # Run initial backtest
            results = self.evo_trader.run_backtest_generation(market_data)
            
            # Run evolution for specified generations
            for i in range(generations - 1):
                logger.info(f"Running generation {i+2}/{generations} for schedule {schedule_id}")
                
                # Evolve
                self.evo_trader.evolve_generation()
                
                # Run backtest
                results = self.evo_trader.run_backtest_generation(market_data)
            
            # Auto-promote if requested
            promoted_ids = []
            if auto_promote:
                # Get the execution adapter
                from trading_bot.api.routers.execution import evo_adapter
                
                if evo_adapter:
                    # Promote top strategies
                    promoted_ids = evo_adapter.activate_auto_promoted(min_performance=5.0)
                    logger.info(f"Auto-promoted {len(promoted_ids)} strategies from schedule {schedule_id}")
            
            # Update schedule status
            schedule["status"] = "completed"
            schedule["last_result"] = {
                "run_id": run_id,
                "completed_at": datetime.now().isoformat(),
                "generations_run": generations,
                "best_performance": results.get("best_strategy", {}).get("performance", {}),
                "promoted_strategies": promoted_ids
            }
            
            # Update next run if recurring
            if schedule["run_daily"]:
                schedule_time = dt_time.fromisoformat(schedule["schedule_time"])
                schedule["next_run"] = self._get_next_run_time(schedule_time).isoformat()
            else:
                # One-time run, no next run
                schedule["next_run"] = None
                
            self._save_schedules()
            
        except Exception as e:
            logger.error(f"Error running evolution for schedule {schedule_id}: {e}")
            
            # Update schedule with error
            schedule["status"] = "error"
            schedule["last_error"] = str(e)
            
            # Set next run if recurring
            if schedule.get("run_daily", False):
                schedule_time = dt_time.fromisoformat(schedule["schedule_time"])
                schedule["next_run"] = self._get_next_run_time(schedule_time).isoformat()
                
            self._save_schedules()
    
    def start(self) -> None:
        """Start the scheduler thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("Evolution scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler thread."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        logger.info("Evolution scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                now = datetime.now()
                
                # Check each schedule
                for schedule_id, schedule in list(self.schedules.items()):
                    # Skip if already running or completed one-time runs
                    if schedule["status"] == "running":
                        continue
                    
                    if schedule["status"] == "completed" and not schedule.get("run_daily", True):
                        continue
                    
                    # Check if it's time to run
                    if schedule.get("next_run"):
                        next_run = datetime.fromisoformat(schedule["next_run"])
                        
                        if now >= next_run:
                            # Time to run
                            logger.info(f"Starting scheduled evolution run for {schedule_id}")
                            
                            # Run in a separate thread to not block the scheduler
                            thread = threading.Thread(
                                target=self._run_evolution,
                                args=(schedule_id,)
                            )
                            thread.daemon = True
                            thread.start()
                            
                            # Store thread reference
                            self.active_threads[schedule_id] = thread
                
                # Clean up completed threads
                for schedule_id, thread in list(self.active_threads.items()):
                    if not thread.is_alive():
                        del self.active_threads[schedule_id]
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying 
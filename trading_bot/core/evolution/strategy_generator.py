"""
GPT-driven Strategy Generator for BensBot.

This module uses large language models to generate new trading strategies
based on market context, historical performance, and other inputs.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import requests
import numpy as np

from trading_bot.core.evolution.llm_evaluator import LLMEvaluator
from trading_bot.core.evolution.market_adapter import MarketAdapter

logger = logging.getLogger(__name__)

class StrategyGenerator:
    """
    GPT-driven generator for new trading strategies.
    
    This class uses LLMs to:
    1. Generate new strategy configurations based on market context
    2. Auto-rank strategies by expected risk/return profile
    3. Submit promising candidates to the EvoTrader system
    """
    
    def __init__(
        self,
        llm_evaluator: LLMEvaluator,
        market_adapter: MarketAdapter,
        data_dir: str = "./data/strategy_generator",
        max_strategies_per_run: int = 5,
        min_quality_threshold: float = 6.5,
        api_key: Optional[str] = None,
        api_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-4"
    ):
        """
        Initialize the strategy generator.
        
        Args:
            llm_evaluator: LLM evaluator instance for strategy evaluation
            market_adapter: Market adapter for context information
            data_dir: Directory for storing generated strategies
            max_strategies_per_run: Maximum strategies to generate per run
            min_quality_threshold: Minimum quality score (0-10) to submit a strategy
            api_key: API key for LLM service (overrides environment variable)
            api_url: API URL for LLM service
            model: Model name to use
        """
        self.llm_evaluator = llm_evaluator
        self.market_adapter = market_adapter
        self.data_dir = data_dir
        self.max_strategies_per_run = max_strategies_per_run
        self.min_quality_threshold = min_quality_threshold
        
        # LLM configuration
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_url = api_url
        self.model = model
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "generated"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "submitted"), exist_ok=True)
        
        # Strategy schema
        self.strategy_schemas = self._load_strategy_schemas()
        
        # Generation history
        self.generation_history = []
    
    def _load_strategy_schemas(self) -> Dict[str, Any]:
        """Load strategy schemas for different asset classes and types."""
        # Start with sensible defaults
        default_schemas = {
            "trend_following": {
                "parameter_schema": {
                    "fast_ma_period": {"type": "int", "min": 5, "max": 50, "default": 20},
                    "slow_ma_period": {"type": "int", "min": 20, "max": 200, "default": 50},
                    "trend_strength_threshold": {"type": "float", "min": 0.0, "max": 0.5, "default": 0.0},
                    "stop_loss_pct": {"type": "float", "min": 1.0, "max": 10.0, "default": 2.0}
                }
            },
            "mean_reversion": {
                "parameter_schema": {
                    "rsi_period": {"type": "int", "min": 2, "max": 30, "default": 14},
                    "rsi_overbought": {"type": "int", "min": 60, "max": 90, "default": 70},
                    "rsi_oversold": {"type": "int", "min": 10, "max": 40, "default": 30},
                    "lookback_period": {"type": "int", "min": 5, "max": 100, "default": 20},
                    "z_score_threshold": {"type": "float", "min": 0.5, "max": 3.0, "default": 2.0}
                }
            },
            "volatility": {
                "parameter_schema": {
                    "volatility_lookback": {"type": "int", "min": 5, "max": 100, "default": 21},
                    "atr_period": {"type": "int", "min": 5, "max": 30, "default": 14},
                    "breakout_multiplier": {"type": "float", "min": 0.5, "max": 3.0, "default": 1.5},
                    "atr_stop_multiplier": {"type": "float", "min": 1.0, "max": 5.0, "default": 2.0}
                }
            },
            "momentum_equity": {
                "parameter_schema": {
                    "momentum_period": {"type": "int", "min": 20, "max": 252, "default": 90},
                    "volume_confirmation": {"type": "bool", "default": True},
                    "volatility_adjustment": {"type": "bool", "default": True},
                    "volatility_lookback": {"type": "int", "min": 20, "max": 100, "default": 63},
                    "use_pullback_entry": {"type": "bool", "default": True},
                    "pullback_threshold": {"type": "float", "min": 1.0, "max": 10.0, "default": 3.0},
                    "trailing_stop_atr_multiple": {"type": "float", "min": 1.0, "max": 5.0, "default": 2.5},
                    "atr_period": {"type": "int", "min": 5, "max": 30, "default": 14},
                    "profit_target_pct": {"type": "float", "min": 5.0, "max": 50.0, "default": 20.0},
                    "preferred_regimes": {"type": "list", "default": ["bullish", "trending"]}
                }
            }
        }
        
        # Try to load schema from actual strategy classes
        try:
            # This would import strategy modules and call get_parameter_schema()
            # to get the actual schemas, but for now we'll use the defaults
            pass
        except Exception as e:
            logger.warning(f"Error loading strategy schemas from classes: {e}")
        
        return default_schemas
    
    def generate_strategies(
        self, 
        asset_class: str,
        market_context: Optional[Dict[str, Any]] = None,
        strategy_types: Optional[List[str]] = None,
        count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate new strategies for the given asset class.
        
        Args:
            asset_class: Asset class to generate strategies for
            market_context: Optional market context
            strategy_types: Optional list of strategy types to focus on
            count: Number of strategies to generate (defaults to max_strategies_per_run)
            
        Returns:
            Dictionary with generation results
        """
        count = count or self.max_strategies_per_run
        
        # Get market context if not provided
        if not market_context:
            try:
                current_regimes = self.market_adapter.current_regimes
                market_context = {
                    "regimes": current_regimes,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting market context: {e}")
                market_context = {
                    "regimes": {},
                    "timestamp": datetime.now().isoformat(),
                    "error": "Failed to retrieve market context"
                }
        
        # Determine which strategy types to generate
        if not strategy_types:
            # Based on asset class and current regime, suggest suitable strategy types
            strategy_types = self._suggest_strategy_types(asset_class, market_context)
        
        # Generate strategies
        generated_strategies = []
        for strategy_type in strategy_types:
            # Skip if schema not available
            if strategy_type not in self.strategy_schemas:
                logger.warning(f"No schema available for strategy type: {strategy_type}")
                continue
            
            # Determine how many of this type to generate
            type_count = max(1, count // len(strategy_types))
            
            for i in range(type_count):
                # Generate strategy
                strategy = self._generate_strategy(asset_class, strategy_type, market_context)
                
                if strategy:
                    # Evaluate the strategy
                    evaluation = self._evaluate_generated_strategy(strategy)
                    strategy["evaluation"] = evaluation
                    
                    # Add to results
                    generated_strategies.append(strategy)
                    
                    # Save the strategy
                    self._save_generated_strategy(strategy)
        
        # Record generation history
        generation_record = {
            "timestamp": datetime.now().isoformat(),
            "asset_class": asset_class,
            "strategy_types": strategy_types,
            "market_context": market_context,
            "generated_count": len(generated_strategies),
            "strategy_ids": [s["strategy_id"] for s in generated_strategies]
        }
        self.generation_history.append(generation_record)
        
        return {
            "status": "success",
            "generated_strategies": generated_strategies,
            "generation_record": generation_record,
            "message": f"Generated {len(generated_strategies)} strategies for {asset_class}"
        }
    
    def _suggest_strategy_types(self, asset_class: str, market_context: Dict[str, Any]) -> List[str]:
        """Suggest suitable strategy types based on asset class and market context."""
        # Default strategy types
        all_types = list(self.strategy_schemas.keys())
        
        # Check if we have regime information
        if "regimes" in market_context and asset_class in market_context["regimes"]:
            regime = market_context["regimes"][asset_class].get("primary_regime")
            
            # Strategy type recommendations based on regime
            regime_strategy_map = {
                "bullish": ["trend_following", "momentum_equity"],
                "bearish": ["mean_reversion", "volatility"],
                "neutral": ["mean_reversion"],
                "trending": ["trend_following", "momentum_equity"],
                "volatile": ["volatility", "mean_reversion"],
                "low_volatility": ["trend_following"]
            }
            
            if regime in regime_strategy_map:
                # Filter to strategies suitable for this asset class
                suggested = regime_strategy_map[regime]
                
                # For equity-specific strategies
                if asset_class != "equity":
                    suggested = [s for s in suggested if not s.endswith("_equity")]
                
                return suggested
        
        # Default case - return all valid strategies for this asset class
        if asset_class != "equity":
            # Remove equity-specific strategies
            return [s for s in all_types if not s.endswith("_equity")]
        
        return all_types
    
    def _generate_strategy(
        self, 
        asset_class: str, 
        strategy_type: str,
        market_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a new strategy using LLM."""
        try:
            # Get parameter schema for this strategy type
            parameter_schema = self.strategy_schemas.get(strategy_type, {}).get("parameter_schema", {})
            
            # Format market context
            context_str = json.dumps(market_context, indent=2)
            
            # Format parameter schema for LLM
            schema_str = json.dumps(parameter_schema, indent=2)
            
            # Create prompt for LLM
            prompt = f"""
You are an expert algorithmic trading strategist. Your task is to generate a new {strategy_type} strategy for trading {asset_class}.

Current market context:
{context_str}

Parameter schema for {strategy_type} strategies:
{schema_str}

Based on this market context and schema, please design a {strategy_type} strategy optimized for current conditions.
You should provide:
1. A clear strategy name
2. A description of the strategy logic and why it fits the current market context
3. Parameters that conform to the schema provided
4. Expected performance characteristics (win rate, average return, etc.)
5. Suitable market regimes for this strategy
6. Risk management considerations

Format your response as a valid JSON object with these fields:
{{
    "strategy_id": "a unique identifier combining asset_class and strategy_type and a random string",
    "name": "Strategy name",
    "description": "Detailed description",
    "asset_class": "{asset_class}",
    "strategy_type": "{strategy_type}",
    "parameters": {{ schema-conforming parameters }},
    "expected_performance": {{
        "win_rate": float (0-100),
        "avg_trade_return": float,
        "max_drawdown": float,
        "sharpe_ratio": float
    }},
    "suitable_regimes": ["regime1", "regime2", ...],
    "risk_notes": "Risk management considerations"
}}

Ensure all parameters conform exactly to the schema provided, with values within the min/max ranges.
"""
            
            # Call LLM API
            response = self._call_llm_api(prompt)
            
            # Parse the strategy from response
            strategy = self._parse_strategy_from_response(response)
            
            # Validate the strategy parameters
            if strategy:
                strategy = self._validate_strategy_parameters(strategy, parameter_schema)
            
            return strategy
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return None
    
    def _call_llm_api(self, prompt: str) -> str:
        """Call the LLM API with the given prompt."""
        if not self.api_key:
            raise ValueError("API key not provided. Set OPENAI_API_KEY environment variable or pass to constructor.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7  # Allow some creativity but not too random
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30  # 30 second timeout
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                raise ValueError(f"API call failed with status {response.status_code}")
            
            # Parse response
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            raise
    
    def _parse_strategy_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the strategy JSON from the LLM response."""
        try:
            # Extract JSON part
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                logger.error("No valid JSON found in LLM response")
                return None
            
            json_str = response[start_idx:end_idx+1]
            
            # Parse JSON
            strategy = json.loads(json_str)
            
            # Check for required fields
            required_fields = ["strategy_id", "name", "description", "asset_class", 
                               "strategy_type", "parameters"]
            
            for field in required_fields:
                if field not in strategy:
                    logger.error(f"Missing required field in strategy: {field}")
                    return None
            
            return strategy
        except Exception as e:
            logger.error(f"Error parsing strategy from response: {e}")
            return None
    
    def _validate_strategy_parameters(
        self, 
        strategy: Dict[str, Any],
        parameter_schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate strategy parameters against schema."""
        valid_strategy = strategy.copy()
        parameters = valid_strategy.get("parameters", {})
        
        # Check each parameter against schema
        for param_name, schema in parameter_schema.items():
            # If parameter is missing, use default
            if param_name not in parameters and "default" in schema:
                parameters[param_name] = schema["default"]
                continue
                
            # Skip if parameter is not in schema
            if param_name not in parameters:
                continue
                
            param_value = parameters[param_name]
            param_type = schema.get("type")
            
            # Type checking and conversion
            if param_type == "int":
                try:
                    param_value = int(param_value)
                except (ValueError, TypeError):
                    # Use default if conversion fails
                    param_value = schema.get("default", 0)
                
                # Range checking
                min_val = schema.get("min")
                max_val = schema.get("max")
                
                if min_val is not None and param_value < min_val:
                    param_value = min_val
                if max_val is not None and param_value > max_val:
                    param_value = max_val
                    
            elif param_type == "float":
                try:
                    param_value = float(param_value)
                except (ValueError, TypeError):
                    # Use default if conversion fails
                    param_value = schema.get("default", 0.0)
                
                # Range checking
                min_val = schema.get("min")
                max_val = schema.get("max")
                
                if min_val is not None and param_value < min_val:
                    param_value = min_val
                if max_val is not None and param_value > max_val:
                    param_value = max_val
                    
            elif param_type == "bool" and not isinstance(param_value, bool):
                # Convert to boolean
                if isinstance(param_value, str):
                    param_value = param_value.lower() in ("true", "yes", "1")
                else:
                    param_value = bool(param_value)
            
            # Update parameter with validated value
            parameters[param_name] = param_value
        
        # Update parameters in strategy
        valid_strategy["parameters"] = parameters
        return valid_strategy
    
    def _evaluate_generated_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a generated strategy.
        
        This uses the LLMEvaluator to assess the strategy's potential quality
        before actual backtesting.
        """
        try:
            # Use expected performance as a proxy for actual performance
            expected_performance = strategy.get("expected_performance", {})
            
            # Add any additional context
            strategy_type = strategy["strategy_type"]
            parameters = strategy["parameters"]
            
            # Call LLM evaluator
            evaluation = self.llm_evaluator.evaluate_strategy(
                strategy_type=strategy_type,
                parameters=parameters,
                performance=expected_performance,
                strategy_id=strategy["strategy_id"]
            )
            
            return evaluation
        except Exception as e:
            logger.error(f"Error evaluating generated strategy: {e}")
            return {
                "error": str(e),
                "quality_score": 0.0,
                "feedback": "Error during evaluation",
                "parameter_suggestions": {}
            }
    
    def _save_generated_strategy(self, strategy: Dict[str, Any]) -> bool:
        """Save a generated strategy to disk."""
        try:
            strategy_id = strategy["strategy_id"]
            file_path = os.path.join(self.data_dir, "generated", f"{strategy_id}.json")
            
            with open(file_path, "w") as f:
                json.dump(strategy, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving generated strategy: {e}")
            return False
    
    def submit_strategies_to_evo_trader(
        self,
        evo_trader: Any,  # Avoid circular import with explicit type
        asset_class: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        max_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Submit generated strategies to EvoTrader for actual backtesting.
        
        Args:
            evo_trader: EvoTrader instance
            asset_class: Optional filter by asset class
            min_quality_score: Minimum quality score (overrides instance setting)
            max_count: Maximum number of strategies to submit
            
        Returns:
            Dictionary with submission results
        """
        min_score = min_quality_score or self.min_quality_threshold
        max_count = max_count or 3  # Default to 3 strategies at a time
        
        # Find generated strategies that haven't been submitted yet
        generated_dir = os.path.join(self.data_dir, "generated")
        submitted_dir = os.path.join(self.data_dir, "submitted")
        
        submitted_files = set(os.listdir(submitted_dir))
        
        candidates = []
        for filename in os.listdir(generated_dir):
            if filename in submitted_files:
                continue
                
            try:
                with open(os.path.join(generated_dir, filename), "r") as f:
                    strategy = json.load(f)
                
                # Filter by asset class if specified
                if asset_class and strategy.get("asset_class") != asset_class:
                    continue
                
                # Check quality score
                quality_score = strategy.get("evaluation", {}).get("quality_score", 0.0)
                if quality_score < min_score:
                    continue
                
                candidates.append(strategy)
            except Exception as e:
                logger.error(f"Error loading strategy {filename}: {e}")
        
        # Sort candidates by quality score
        candidates.sort(key=lambda s: s.get("evaluation", {}).get("quality_score", 0.0), reverse=True)
        
        # Limit to max_count
        candidates = candidates[:max_count]
        
        if not candidates:
            return {
                "status": "skipped",
                "message": "No suitable candidates found for submission",
                "timestamp": datetime.now().isoformat()
            }
        
        # Submit to EvoTrader
        submitted = []
        submission_results = []
        
        for strategy in candidates:
            try:
                # Submit to EvoTrader
                result = evo_trader.register_draft_strategy(
                    strategy_type=strategy["strategy_type"],
                    parameters=strategy["parameters"],
                    asset_class=strategy["asset_class"],
                    name=strategy["name"],
                    description=strategy["description"],
                    metadata={
                        "generated_by": "strategy_generator",
                        "generated_at": strategy.get("evaluation", {}).get("evaluation_timestamp"),
                        "quality_score": strategy.get("evaluation", {}).get("quality_score", 0.0),
                        "suitable_regimes": strategy.get("suitable_regimes", [])
                    }
                )
                
                # Mark as submitted
                if result.get("status") == "success":
                    # Copy to submitted directory
                    strategy_id = strategy["strategy_id"]
                    with open(os.path.join(submitted_dir, f"{strategy_id}.json"), "w") as f:
                        json.dump(strategy, f, indent=2)
                    
                    submitted.append(strategy_id)
                
                submission_results.append(result)
            except Exception as e:
                logger.error(f"Error submitting strategy {strategy.get('strategy_id')}: {e}")
                submission_results.append({
                    "status": "error",
                    "strategy_id": strategy.get("strategy_id"),
                    "error": str(e)
                })
        
        return {
            "status": "success" if submitted else "error",
            "submitted_count": len(submitted),
            "submitted_strategy_ids": submitted,
            "submission_results": submission_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_generation_cycle(
        self,
        evo_trader: Any,
        asset_classes: Optional[List[str]] = None,
        force_regime_check: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete generation and submission cycle.
        
        Args:
            evo_trader: EvoTrader instance
            asset_classes: Asset classes to generate strategies for (default: all)
            force_regime_check: Whether to force an update of market regimes
            
        Returns:
            Dictionary with cycle results
        """
        results = {}
        
        # Update market regimes if needed
        if force_regime_check:
            try:
                self.market_adapter.update_market_regimes(force=True)
            except Exception as e:
                logger.error(f"Error updating market regimes: {e}")
        
        # Use all asset classes if none specified
        if not asset_classes:
            asset_classes = list(self.market_adapter.current_regimes.keys())
        
        # Generate strategies for each asset class
        for asset_class in asset_classes:
            generation_result = self.generate_strategies(asset_class)
            results[f"generation_{asset_class}"] = generation_result
            
            # Let the LLM service breathe a bit to avoid rate limits
            time.sleep(2)
        
        # Submit strategies to EvoTrader
        for asset_class in asset_classes:
            submission_result = self.submit_strategies_to_evo_trader(
                evo_trader=evo_trader,
                asset_class=asset_class
            )
            results[f"submission_{asset_class}"] = submission_result
        
        return {
            "status": "success",
            "cycle_results": results,
            "timestamp": datetime.now().isoformat()
        } 
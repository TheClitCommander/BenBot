"""
LLM-guided fitness evaluation for trading strategies.

This module enhances strategy evaluation by:
- Using language models to evaluate strategy fitness beyond simple metrics
- Providing insights and feedback for improving strategies
- Suggesting parameter adjustments based on performance patterns
"""

import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

class LLMEvaluator:
    """LLM-guided evaluator for trading strategies."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-4",
        data_dir: str = "./data/llm_evaluation",
        cache_results: bool = True
    ):
        """
        Initialize the LLM evaluator.
        
        Args:
            api_key: API key for LLM service
            api_url: API URL for LLM service
            model: Model name to use
            data_dir: Directory for storing evaluation data
            cache_results: Whether to cache results
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_url = api_url
        self.model = model
        self.data_dir = data_dir
        self.cache_results = cache_results
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Cache for evaluations
        self.evaluation_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load cached evaluations
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cached evaluations from disk."""
        if not self.cache_results:
            return
            
        cache_path = os.path.join(self.data_dir, "evaluation_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    self.evaluation_cache = json.load(f)
                logger.info(f"Loaded {len(self.evaluation_cache)} cached evaluations")
            except Exception as e:
                logger.error(f"Error loading evaluation cache: {e}")
                self.evaluation_cache = {}
    
    def _save_cache(self) -> None:
        """Save cached evaluations to disk."""
        if not self.cache_results:
            return
            
        cache_path = os.path.join(self.data_dir, "evaluation_cache.json")
        try:
            with open(cache_path, 'w') as f:
                json.dump(self.evaluation_cache, f, indent=2)
            logger.debug(f"Saved {len(self.evaluation_cache)} evaluations to cache")
        except Exception as e:
            logger.error(f"Error saving evaluation cache: {e}")
    
    def evaluate_strategy(
        self, 
        strategy_type: str,
        parameters: Dict[str, Any],
        performance: Dict[str, Any],
        strategy_id: Optional[str] = None,
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a strategy using LLM guidance.
        
        Args:
            strategy_type: Type of strategy
            parameters: Strategy parameters
            performance: Performance metrics
            strategy_id: Optional ID for caching
            market_conditions: Optional market condition data
            
        Returns:
            Dictionary with evaluation results
        """
        # Generate cache key if strategy_id not provided
        if not strategy_id:
            cache_key = f"{strategy_type}_{hash(frozenset(parameters.items()))}_{hash(frozenset(performance.items()))}"
        else:
            cache_key = strategy_id
        
        # Check cache
        if self.cache_results and cache_key in self.evaluation_cache:
            logger.debug(f"Using cached evaluation for {cache_key}")
            return self.evaluation_cache[cache_key]
        
        try:
            # Prepare prompt for LLM
            prompt = self._prepare_evaluation_prompt(
                strategy_type, parameters, performance, market_conditions
            )
            
            # Call LLM API
            evaluation = self._call_llm_api(prompt)
            
            # Parse evaluation results
            parsed_results = self._parse_evaluation_results(evaluation)
            
            # Add metadata
            parsed_results["strategy_type"] = strategy_type
            parsed_results["evaluation_timestamp"] = datetime.now().isoformat()
            
            # Cache results
            if self.cache_results:
                self.evaluation_cache[cache_key] = parsed_results
                self._save_cache()
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error evaluating strategy: {e}")
            return {
                "error": str(e),
                "quality_score": 0.0,
                "feedback": "Error during evaluation",
                "parameter_suggestions": {}
            }
    
    def batch_evaluate(
        self,
        strategies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple strategies in batch.
        
        Args:
            strategies: List of strategy data dictionaries
            
        Returns:
            List of evaluation results
        """
        results = []
        for strategy in strategies:
            strategy_type = strategy.get("type")
            parameters = strategy.get("parameters", {})
            performance = strategy.get("performance", {})
            strategy_id = strategy.get("id")
            market_conditions = strategy.get("market_conditions")
            
            evaluation = self.evaluate_strategy(
                strategy_type=strategy_type,
                parameters=parameters,
                performance=performance,
                strategy_id=strategy_id,
                market_conditions=market_conditions
            )
            
            results.append({
                "strategy_id": strategy_id,
                "evaluation": evaluation
            })
            
            # Add small delay to avoid rate limits
            time.sleep(0.5)
            
        return results
    
    def _prepare_evaluation_prompt(
        self,
        strategy_type: str,
        parameters: Dict[str, Any],
        performance: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prepare prompt for LLM evaluation.
        
        Args:
            strategy_type: Type of strategy
            parameters: Strategy parameters
            performance: Performance metrics
            market_conditions: Optional market condition data
            
        Returns:
            Formatted prompt string
        """
        # Format parameters nicely
        param_str = json.dumps(parameters, indent=2)
        
        # Format performance metrics
        perf_str = ""
        for key, value in performance.items():
            if isinstance(value, float):
                perf_str += f"- {key}: {value:.4f}\n"
            else:
                perf_str += f"- {key}: {value}\n"
        
        # Format market conditions if available
        market_str = ""
        if market_conditions:
            market_str = "Market conditions during testing:\n"
            for key, value in market_conditions.items():
                market_str += f"- {key}: {value}\n"
        
        # Create prompt
        prompt = f"""
You are an expert algorithmic trading strategy evaluator. Analyze the following {strategy_type} strategy:

Strategy Parameters:
{param_str}

Performance Metrics:
{perf_str}

{market_str}

Please provide:
1. Quality Score (0-10): Rate the overall quality of this strategy
2. Strengths: List the key strengths of this strategy
3. Weaknesses: List the key weaknesses of this strategy
4. Parameter Suggestions: Recommend specific parameter adjustments to improve performance
5. Risk Assessment: Evaluate the risk profile of this strategy
6. Market Suitability: What market conditions would this strategy perform best in?

Format your response as a valid JSON object with these keys:
{{
    "quality_score": float,
    "strengths": [string, string, ...],
    "weaknesses": [string, string, ...],
    "parameter_suggestions": {{"param_name": value, ...}},
    "risk_assessment": string,
    "market_suitability": string,
    "feedback": string
}}
"""
        return prompt
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        Call LLM API with the given prompt.
        
        Args:
            prompt: The evaluation prompt
            
        Returns:
            LLM response string
        """
        if not self.api_key:
            raise ValueError("API key not provided. Set OPENAI_API_KEY environment variable or pass to constructor.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1  # Low temperature for more consistent results
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
    
    def _parse_evaluation_results(self, evaluation: str) -> Dict[str, Any]:
        """
        Parse LLM evaluation response.
        
        Args:
            evaluation: LLM response string
            
        Returns:
            Parsed evaluation dictionary
        """
        try:
            # Extract JSON part
            start_idx = evaluation.find("{")
            end_idx = evaluation.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON found in LLM response")
            
            json_str = evaluation[start_idx:end_idx+1]
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Ensure required fields
            required_fields = [
                "quality_score", "strengths", "weaknesses", 
                "parameter_suggestions", "risk_assessment", 
                "market_suitability", "feedback"
            ]
            
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = None if field == "parameter_suggestions" else ""
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing evaluation results: {e}")
            
            # Return default structure
            return {
                "quality_score": 0.0,
                "strengths": [],
                "weaknesses": ["Could not parse evaluation results"],
                "parameter_suggestions": {},
                "risk_assessment": "Unknown - parsing error",
                "market_suitability": "Unknown - parsing error",
                "feedback": f"Error parsing results: {str(e)}"
            }
    
    def get_improvement_recommendations(
        self,
        strategy_id: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get recommendations to improve a strategy based on its performance history.
        
        Args:
            strategy_id: Strategy ID
            strategy_type: Type of strategy
            parameters: Current parameters
            performance_history: List of historical performance data
            
        Returns:
            Recommendations dictionary
        """
        try:
            # Format performance history
            history_str = ""
            for i, perf in enumerate(performance_history):
                history_str += f"Run {i+1}:\n"
                for key, value in perf.items():
                    if isinstance(value, float):
                        history_str += f"- {key}: {value:.4f}\n"
                    else:
                        history_str += f"- {key}: {value}\n"
                history_str += "\n"
            
            # Prepare prompt
            prompt = f"""
You are an expert algorithmic trading strategy optimizer. Analyze the following {strategy_type} strategy and its performance history:

Strategy ID: {strategy_id}
Strategy Type: {strategy_type}

Current Parameters:
{json.dumps(parameters, indent=2)}

Performance History:
{history_str}

Based on this performance history, please provide:
1. Parameter Optimization: Recommend specific parameter adjustments to improve performance
2. Strategy Modifications: Suggest modifications to the strategy logic
3. Risk Management Improvements: Recommend risk management adjustments
4. Performance Analysis: Analyze performance patterns and identify areas for improvement

Format your response as a valid JSON object with these keys:
{{
    "parameter_optimizations": {{"param_name": value, ...}},
    "strategy_modifications": [string, string, ...],
    "risk_management_improvements": [string, string, ...],
    "performance_analysis": string,
    "overall_recommendation": string
}}
"""
            
            # Call LLM
            response = self._call_llm_api(prompt)
            
            # Parse response
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON found in LLM response")
            
            json_str = response[start_idx:end_idx+1]
            parsed = json.loads(json_str)
            
            # Add metadata
            parsed["strategy_id"] = strategy_id
            parsed["timestamp"] = datetime.now().isoformat()
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error getting improvement recommendations: {e}")
            return {
                "error": str(e),
                "parameter_optimizations": {},
                "strategy_modifications": ["Error generating recommendations"],
                "risk_management_improvements": [],
                "performance_analysis": "Error during analysis",
                "overall_recommendation": "Could not generate recommendations due to an error"
            } 
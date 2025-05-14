#!/usr/bin/env python3
"""
Comprehensive Validation Script for BensBot Enhancements.

This script tests:
1. Monte Carlo simulation on strategy results
2. Out-of-sample testing via train/test split
3. Regime-specific strategy performance 
4. Cross-asset strategy adaptation
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
from typing import Dict, Any, List, Optional
import json

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import components
from trading_bot.utils.logging_setup import setup_logging, get_component_logger
from trading_bot.core.data.historical_data_fetcher import HistoricalDataFetcher
from trading_bot.core.simulation.monte_carlo import MonteCarloSimulator
from trading_bot.core.evolution.market_adapter import MarketAdapter
from trading_bot.core.strategies.general.trend_following_strategy import TrendFollowingStrategy
from trading_bot.core.strategies.general.mean_reversion_strategy import MeanReversionStrategy
from trading_bot.core.strategies.general.volatility_strategy import VolatilityStrategy
from trading_bot.core.strategies.equity.momentum_equity_strategy import MomentumEquityStrategy
from trading_bot.core.evolution.evo_trader import EvoTrader
from trading_bot.core.portfolio.allocator import PortfolioAllocator
from trading_bot.core.backtesting.base_backtester import BaseBacktester

# Setup logging
setup_logging()
logger = get_component_logger('scripts.validate_enhancements')

class EnhancementValidator:
    """
    Class to validate the enhanced features of BensBot.
    """
    
    def __init__(self, output_dir: str = "./validation_results"):
        """Initialize the validator."""
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.data_fetcher = HistoricalDataFetcher()
        self.monte_carlo = MonteCarloSimulator()
        self.portfolio_allocator = PortfolioAllocator(total_capital=100000.0)
        self.evo_trader = EvoTrader()
        self.market_adapter = MarketAdapter(
            data_fetcher=self.data_fetcher,
            evo_trader=self.evo_trader,
            portfolio_allocator=self.portfolio_allocator
        )
        
        # Test symbols
        self.test_symbols = {
            "equity": ["SPY", "QQQ"],
            "crypto": ["BTC/USDT", "ETH/USDT"],
            "forex": ["EURUSD=X", "GBPUSD=X"]
        }
        
        # Test date ranges
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
        
        # Test strategies
        self.strategies = {
            "trend_following": TrendFollowingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "volatility": VolatilityStrategy,
            "momentum_equity": MomentumEquityStrategy
        }
        
        # Results storage
        self.results = {
            "monte_carlo": {},
            "out_of_sample": {},
            "regime_specific": {},
            "summary": {}
        }
    
    def test_monte_carlo_simulation(self) -> Dict[str, Any]:
        """
        Test Monte Carlo simulation on strategy results.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing Monte Carlo simulation")
        
        mc_results = {}
        
        # Test each asset class with a single symbol
        for asset_class, symbols in self.test_symbols.items():
            symbol = symbols[0]  # Use first symbol
            
            logger.info(f"Running Monte Carlo test for {symbol} ({asset_class})")
            
            # Fetch historical data
            historical_data = self.data_fetcher.fetch(
                symbol=symbol,
                asset_class=asset_class,
                start_date=self.start_date,
                end_date=self.end_date,
                interval='1d'
            )
            
            if historical_data is None or historical_data.empty:
                logger.error(f"Failed to fetch data for {symbol}")
                continue
            
            # Create strategy
            strategy_class = self.strategies["trend_following"]
            strategy = strategy_class(
                strategy_id=f"mc_test_{asset_class}",
                parameters={
                    "fast_ma_period": 20,
                    "slow_ma_period": 50,
                    "trend_strength_threshold": 0.0,
                    "stop_loss_pct": 2.0
                },
                asset_class=asset_class
            )
            
            # Generate signals
            signals_df = strategy.generate_signals(historical_data)
            
            # Simple backtest
            initial_capital = 10000.0
            cash = initial_capital
            position = 0
            equity_curve = pd.Series(index=historical_data.index, dtype=float).fillna(initial_capital)
            
            # Run simulation
            for i, date in enumerate(historical_data.index):
                if i == 0:
                    continue
                
                price = historical_data.loc[date, 'Close']
                signal = signals_df.loc[date, 'signal'] if date in signals_df.index else 0
                
                if signal == 1 and position == 0:  # Buy
                    position = cash / price
                    cash = 0
                elif signal == -1 and position > 0:  # Sell
                    cash = position * price
                    position = 0
                
                equity_curve[date] = cash + (position * price if position > 0 else 0)
            
            # Calculate returns
            returns = equity_curve.pct_change().dropna()
            
            # Run Monte Carlo simulation
            mc_result = self.monte_carlo.simulate(returns, initial_capital)
            
            if mc_result["status"] == "success":
                # Save Monte Carlo plot if available
                if mc_result.get("plot_base64"):
                    import base64
                    
                    plot_data = base64.b64decode(mc_result["plot_base64"])
                    plot_path = os.path.join(self.output_dir, f"monte_carlo_{asset_class}_{symbol}.png")
                    
                    with open(plot_path, "wb") as f:
                        f.write(plot_data)
                        logger.info(f"Monte Carlo plot saved to {plot_path}")
                
                # Extract key metrics
                mc_results[asset_class] = {
                    "symbol": symbol,
                    "consistency_score": mc_result["simulation_result"]["consistency_score"],
                    "monte_carlo_percentile_5": mc_result["final_equity_distribution"]["lower"],
                    "monte_carlo_percentile_95": mc_result["final_equity_distribution"]["upper"],
                    "monte_carlo_max_dd_percentile_95": mc_result["drawdown_distribution"]["95th_percentile"],
                    "final_equity": equity_curve.iloc[-1],
                    "plot_saved": True if mc_result.get("plot_base64") else False
                }
                
                logger.info(f"Monte Carlo results for {symbol}: consistency={mc_results[asset_class]['consistency_score']:.2f}")
            else:
                logger.error(f"Monte Carlo simulation failed for {symbol}: {mc_result.get('message')}")
        
        self.results["monte_carlo"] = mc_results
        return mc_results
    
    def test_out_of_sample(self) -> Dict[str, Any]:
        """
        Test out-of-sample validation.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing out-of-sample validation")
        
        oos_results = {}
        
        # Test each asset class with a single symbol
        for asset_class, symbols in self.test_symbols.items():
            symbol = symbols[0]  # Use first symbol
            
            logger.info(f"Running out-of-sample test for {symbol} ({asset_class})")
            
            # Fetch historical data
            historical_data = self.data_fetcher.fetch(
                symbol=symbol,
                asset_class=asset_class,
                start_date=self.start_date,
                end_date=self.end_date,
                interval='1d'
            )
            
            if historical_data is None or historical_data.empty:
                logger.error(f"Failed to fetch data for {symbol}")
                continue
            
            # Split into training and testing sets (70/30)
            split_idx = int(len(historical_data) * 0.7)
            training_data = historical_data.iloc[:split_idx].copy()
            testing_data = historical_data.iloc[split_idx:].copy()
            
            logger.info(f"Split data: training={len(training_data)}, testing={len(testing_data)}")
            
            # Test different strategy types
            asset_results = {}
            
            for strategy_name, strategy_class in self.strategies.items():
                # Skip strategies that don't apply to this asset class
                if strategy_name == "momentum_equity" and asset_class != "equity":
                    continue
                
                logger.info(f"Testing {strategy_name} strategy on {asset_class}")
                
                # Create strategy parameters
                if strategy_name == "trend_following":
                    params = {
                        "fast_ma_period": 20,
                        "slow_ma_period": 50,
                        "trend_strength_threshold": 0.0,
                        "stop_loss_pct": 2.0
                    }
                elif strategy_name == "mean_reversion":
                    params = {
                        "rsi_period": 14,
                        "rsi_overbought": 70,
                        "rsi_oversold": 30,
                        "lookback_period": 20,
                        "z_score_threshold": 2.0
                    }
                elif strategy_name == "volatility":
                    params = {
                        "volatility_lookback": 21,
                        "atr_period": 14,
                        "breakout_multiplier": 1.5,
                        "atr_stop_multiplier": 2.0
                    }
                elif strategy_name == "momentum_equity":
                    params = {
                        "momentum_period": 90,
                        "volume_confirmation": True,
                        "volatility_adjustment": True,
                        "use_pullback_entry": True
                    }
                else:
                    params = {}
                
                # Create strategy
                strategy = strategy_class(
                    strategy_id=f"oos_test_{asset_class}_{strategy_name}",
                    parameters=params,
                    asset_class=asset_class
                )
                
                # Train on training data
                train_signals = strategy.generate_signals(training_data)
                
                # Test on testing data
                test_signals = strategy.generate_signals(testing_data)
                
                # Evaluate on both datasets
                initial_capital = 10000.0
                train_equity, train_metrics = self._evaluate_strategy(training_data, train_signals, initial_capital)
                test_equity, test_metrics = self._evaluate_strategy(testing_data, test_signals, initial_capital)
                
                # Calculate in-sample vs out-of-sample performance differences
                train_return = train_metrics.get("total_return", 0)
                test_return = test_metrics.get("total_return", 0)
                return_diff = test_return - train_return
                
                train_sharpe = train_metrics.get("sharpe_ratio", 0)
                test_sharpe = test_metrics.get("sharpe_ratio", 0)
                sharpe_diff = test_sharpe - train_sharpe
                
                # Store results
                asset_results[strategy_name] = {
                    "train_metrics": train_metrics,
                    "test_metrics": test_metrics,
                    "return_difference": return_diff,
                    "sharpe_difference": sharpe_diff,
                    "overfitting_score": self._calculate_overfitting_score(train_metrics, test_metrics)
                }
                
                logger.info(f"{strategy_name} on {asset_class}: in-sample return={train_return:.2f}%, out-of-sample return={test_return:.2f}%")
            
            oos_results[asset_class] = {
                "symbol": symbol,
                "strategy_results": asset_results
            }
        
        self.results["out_of_sample"] = oos_results
        return oos_results
    
    def test_regime_specific_strategies(self) -> Dict[str, Any]:
        """
        Test regime-specific strategy performance.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing regime-specific strategies")
        
        # First, update market regimes
        market_regimes = self.market_adapter.update_market_regimes(force=True)
        
        regime_results = {}
        
        # For each asset class
        for asset_class, regime_info in self.market_adapter.current_regimes.items():
            primary_regime = regime_info.get("primary_regime", "unknown")
            logger.info(f"Current {asset_class} regime: {primary_regime}")
            
            symbol = self.test_symbols[asset_class][0]  # Use first symbol
            
            # Fetch historical data
            historical_data = self.data_fetcher.fetch(
                symbol=symbol,
                asset_class=asset_class,
                start_date=self.start_date,
                end_date=self.end_date,
                interval='1d'
            )
            
            if historical_data is None or historical_data.empty:
                logger.error(f"Failed to fetch data for {symbol}")
                continue
            
            # Test all strategies
            strategy_results = {}
            
            for strategy_name, strategy_class in self.strategies.items():
                # Skip strategies that don't apply to this asset class
                if strategy_name == "momentum_equity" and asset_class != "equity":
                    continue
                
                # Create strategy
                strategy = strategy_class(
                    strategy_id=f"regime_test_{asset_class}_{strategy_name}",
                    parameters={},  # Use default parameters
                    asset_class=asset_class
                )
                
                # Check if strategy is suitable for the current regime
                if hasattr(strategy, "is_suitable_for_regime"):
                    is_suitable = strategy.is_suitable_for_regime(primary_regime)
                else:
                    is_suitable = True  # Assume suitable if method not implemented
                
                # Generate signals
                signals = strategy.generate_signals(historical_data)
                
                # Evaluate strategy
                equity_curve, metrics = self._evaluate_strategy(historical_data, signals, 10000.0)
                
                # Store results
                strategy_results[strategy_name] = {
                    "is_suitable_for_regime": is_suitable,
                    "metrics": metrics,
                    "final_equity": float(equity_curve.iloc[-1]) if not equity_curve.empty else 0.0
                }
                
                logger.info(f"{strategy_name} on {asset_class} ({primary_regime}): suitable={is_suitable}, return={metrics.get('total_return', 0):.2f}%")
            
            # Rank strategies by performance
            ranked_strategies = sorted(
                strategy_results.items(),
                key=lambda x: x[1]["metrics"].get("sharpe_ratio", 0),
                reverse=True
            )
            
            # Store results
            regime_results[asset_class] = {
                "symbol": symbol,
                "regime": primary_regime,
                "strategy_results": strategy_results,
                "best_strategy": ranked_strategies[0][0] if ranked_strategies else None,
                "best_sharpe": ranked_strategies[0][1]["metrics"].get("sharpe_ratio", 0) if ranked_strategies else 0
            }
        
        self.results["regime_specific"] = regime_results
        return regime_results
    
    def _evaluate_strategy(self, market_data: pd.DataFrame, signals: pd.DataFrame, 
                          initial_capital: float) -> tuple:
        """
        Evaluate a strategy's performance on market data.
        
        Args:
            market_data: OHLCV market data
            signals: Strategy signals
            initial_capital: Initial capital
            
        Returns:
            Tuple of (equity_curve, metrics)
        """
        cash = initial_capital
        position = 0
        equity_curve = pd.Series(index=market_data.index, dtype=float).fillna(initial_capital)
        trades = []
        
        # Simulate trading
        for i, date in enumerate(market_data.index):
            if i == 0:
                continue
            
            price = market_data.loc[date, 'Close']
            signal = signals.loc[date, 'signal'] if date in signals.index else 0
            
            if signal == 1 and position == 0:  # Buy
                position = cash / price
                cash = 0
                trades.append({
                    'entry_date': date,
                    'entry_price': price,
                    'type': 'long'
                })
            elif signal == -1 and position > 0:  # Sell
                cash = position * price
                position = 0
                trades.append({
                    'exit_date': date,
                    'exit_price': price,
                    'type': 'long',
                    'pnl': (price / trades[-1]['entry_price'] - 1) * 100  # As percentage
                })
            
            equity_curve[date] = cash + (position * price if position > 0 else 0)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(equity_curve, trades)
        
        return equity_curve, metrics
    
    def _calculate_metrics(self, equity_curve: pd.Series, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate performance metrics from equity curve and trades.
        
        Args:
            equity_curve: Equity curve series
            trades: List of trade dictionaries
            
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        # Skip if equity curve is empty
        if equity_curve.empty:
            return metrics
        
        # Total return
        initial = equity_curve.iloc[0]
        final = equity_curve.iloc[-1]
        metrics["total_return"] = ((final / initial) - 1) * 100
        
        # Calculate daily returns for Sharpe ratio
        daily_returns = equity_curve.pct_change().dropna()
        
        if len(daily_returns) > 0:
            # Sharpe ratio (annualized, assuming 0% risk-free rate)
            avg_return = daily_returns.mean()
            std_return = daily_returns.std()
            metrics["sharpe_ratio"] = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            
            # Maximum drawdown
            peak = equity_curve.expanding().max()
            drawdown = ((equity_curve - peak) / peak)
            metrics["max_drawdown"] = drawdown.min() * 100
        
        # Trading metrics
        completed_trades = [t for t in trades if 'pnl' in t]
        if completed_trades:
            metrics["trades_count"] = len(completed_trades)
            
            # Win rate
            winning_trades = [t for t in completed_trades if t['pnl'] > 0]
            metrics["win_rate"] = (len(winning_trades) / len(completed_trades)) * 100 if completed_trades else 0
            
            # Average win/loss
            if winning_trades:
                metrics["avg_win"] = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
            
            losing_trades = [t for t in completed_trades if t['pnl'] <= 0]
            if losing_trades:
                metrics["avg_loss"] = sum(t['pnl'] for t in losing_trades) / len(losing_trades)
            
            # Profit factor
            if losing_trades and sum(t['pnl'] for t in losing_trades) != 0:
                metrics["profit_factor"] = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades))
        
        return metrics
    
    def _calculate_overfitting_score(self, train_metrics: Dict[str, float], 
                                   test_metrics: Dict[str, float]) -> float:
        """
        Calculate an overfitting score comparing in-sample and out-of-sample performance.
        
        Args:
            train_metrics: In-sample metrics
            test_metrics: Out-of-sample metrics
            
        Returns:
            Overfitting score (0-100, higher is worse)
        """
        # If no performance metrics available, return maximum score (worst case)
        if not train_metrics or not test_metrics:
            return 100.0
        
        # Primary performance metrics to compare
        train_return = train_metrics.get("total_return", 0)
        test_return = test_metrics.get("total_return", 0)
        train_sharpe = train_metrics.get("sharpe_ratio", 0)
        test_sharpe = test_metrics.get("sharpe_ratio", 0)
        
        # Calculate performance drop-off
        return_dropoff = max(0, (train_return - test_return) / max(1, abs(train_return))) * 100
        sharpe_dropoff = max(0, (train_sharpe - test_sharpe) / max(0.1, train_sharpe)) * 100
        
        # Combined score (0-100, weighted)
        overfitting_score = (0.7 * return_dropoff + 0.3 * sharpe_dropoff)
        
        return min(100, overfitting_score)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all enhancement tests.
        
        Returns:
            Dictionary with all test results
        """
        logger.info("Starting comprehensive validation of enhancements")
        
        # Run tests
        monte_carlo_results = self.test_monte_carlo_simulation()
        oos_results = self.test_out_of_sample()
        regime_results = self.test_regime_specific_strategies()
        
        # Generate summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "monte_carlo": {},
            "out_of_sample": {},
            "regime_specific": {}
        }
        
        # Monte Carlo summary
        if monte_carlo_results:
            avg_consistency = np.mean([r.get("consistency_score", 0) for r in monte_carlo_results.values()])
            summary["monte_carlo"] = {
                "average_consistency_score": avg_consistency,
                "assets_tested": list(monte_carlo_results.keys())
            }
        
        # Out-of-sample summary
        if oos_results:
            avg_overfitting = []
            best_strategies = {}
            
            for asset_class, result in oos_results.items():
                strategy_results = result.get("strategy_results", {})
                
                # Collect overfitting scores
                for strategy_name, metrics in strategy_results.items():
                    avg_overfitting.append(metrics.get("overfitting_score", 100))
                
                # Find best strategy for each asset class
                best_strategy = None
                best_oos_sharpe = -float('inf')
                
                for strategy_name, metrics in strategy_results.items():
                    oos_sharpe = metrics.get("test_metrics", {}).get("sharpe_ratio", 0)
                    if oos_sharpe > best_oos_sharpe:
                        best_oos_sharpe = oos_sharpe
                        best_strategy = strategy_name
                
                if best_strategy:
                    best_strategies[asset_class] = best_strategy
            
            summary["out_of_sample"] = {
                "average_overfitting_score": np.mean(avg_overfitting) if avg_overfitting else None,
                "best_strategies_by_oos": best_strategies
            }
        
        # Regime-specific summary
        if regime_results:
            current_regimes = {asset: result.get("regime") for asset, result in regime_results.items()}
            regime_best_match = {}
            
            for asset_class, result in regime_results.items():
                best_strategy = result.get("best_strategy")
                strategy_results = result.get("strategy_results", {})
                
                # Check if best strategy is "suitable" for the regime
                if best_strategy and best_strategy in strategy_results:
                    is_suitable = strategy_results[best_strategy].get("is_suitable_for_regime", False)
                    regime_best_match[asset_class] = {
                        "regime": result.get("regime"),
                        "best_strategy": best_strategy,
                        "is_suitable_match": is_suitable
                    }
            
            summary["regime_specific"] = {
                "current_regimes": current_regimes,
                "regime_strategy_matches": regime_best_match
            }
        
        # Store summary
        self.results["summary"] = summary
        
        # Save full results to JSON file
        results_path = os.path.join(self.output_dir, f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Full validation results saved to {results_path}")
        
        return self.results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate BensBot enhancements")
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="./validation_results",
        help="Output directory for validation results"
    )
    
    parser.add_argument(
        "--test", 
        type=str, 
        choices=["all", "monte_carlo", "out_of_sample", "regime_specific"],
        default="all",
        help="Specific test to run (default: all)"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = EnhancementValidator(output_dir=args.output)
    
    # Run tests based on argument
    if args.test == "all":
        results = validator.run_all_tests()
    elif args.test == "monte_carlo":
        results = validator.test_monte_carlo_simulation()
    elif args.test == "out_of_sample":
        results = validator.test_out_of_sample()
    elif args.test == "regime_specific":
        results = validator.test_regime_specific_strategies()
    
    return results

if __name__ == "__main__":
    main() 
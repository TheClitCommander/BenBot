"""
Real backtester implementation for BensBot.

This module provides actual backtesting capabilities using historical market data
instead of random mock data.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Type, Optional, Tuple
import os
import json

from trading_bot.core.backtesting.base_backtester import BaseBacktester, BacktestResult
from trading_bot.core.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class RealBacktester(BaseBacktester):
    """
    Real backtester implementation that uses actual historical market data
    and executes strategy logic properly.
    """
    
    def __init__(
        self,
        data_dir: str = "./data/historical",
        results_dir: str = "./data/backtest_results",
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        historical_data_fetcher=None  # Optional data fetcher service
    ):
        """
        Initialize the real backtester.
        
        Args:
            data_dir: Directory for historical data
            results_dir: Directory to store backtest results
            commission_pct: Commission percentage for trades
            slippage_pct: Slippage percentage for trades
            historical_data_fetcher: Service to fetch historical data if not available locally
        """
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.data_fetcher = historical_data_fetcher
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
    
    def run_backtest(
        self,
        strategy_id: str,
        strategy_class: Type[BaseStrategy],
        parameters: Dict[str, Any],
        asset_class: str,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        initial_capital: float = 100000.0,
        **kwargs
    ) -> BacktestResult:
        """
        Run a backtest with real historical data and actual strategy logic.
        
        Args:
            strategy_id: Unique ID for this strategy instance
            strategy_class: Class of the strategy to backtest
            parameters: Strategy parameters
            asset_class: Asset class (equity, crypto, forex)
            symbol: Trading symbol
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            interval: Candle interval ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
            initial_capital: Initial capital for the backtest
            **kwargs: Additional arguments
            
        Returns:
            Backtest result
        """
        try:
            # Load historical data
            historical_data = self._load_historical_data(
                asset_class=asset_class,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            if historical_data is None or len(historical_data) < 10:
                return {
                    "status": "error",
                    "error_message": f"Insufficient historical data for {symbol} from {start_date} to {end_date}",
                    "strategy_id": strategy_id
                }
            
            # Initialize strategy
            strategy = strategy_class(
                strategy_id=strategy_id,
                parameters=parameters
            )
            
            # Run the backtest
            logger.info(f"Running backtest for {strategy_id} on {symbol} from {start_date} to {end_date}")
            
            # Initialize result tracking
            positions = []
            trades = []
            equity_curve = [initial_capital]
            cash = initial_capital
            holdings = 0
            current_position = None
            
            # Main backtest loop
            for i in range(1, len(historical_data)):
                current_bar = historical_data.iloc[i]
                lookback_data = historical_data.iloc[:i+1]
                
                # Get the strategy's signal
                signal = strategy.generate_signal(lookback_data)
                
                # Process the signal
                if signal is not None:
                    price = current_bar['close']
                    timestamp = current_bar.name
                    
                    # Close any existing position if signal is opposite
                    if current_position is not None and signal['direction'] != current_position['direction']:
                        # Calculate PnL
                        if current_position['direction'] == 'buy':
                            pnl = holdings * (price - current_position['price']) - \
                                  (holdings * price * self.commission_pct) - \
                                  (holdings * price * self.slippage_pct)
                        else:  # 'sell'
                            pnl = holdings * (current_position['price'] - price) - \
                                  (holdings * price * self.commission_pct) - \
                                  (holdings * price * self.slippage_pct)
                        
                        # Update cash
                        cash += holdings * price + pnl
                        
                        # Record the trade
                        trades.append({
                            'entry_time': current_position['timestamp'],
                            'exit_time': timestamp,
                            'symbol': symbol,
                            'direction': current_position['direction'],
                            'entry_price': current_position['price'],
                            'exit_price': price,
                            'quantity': holdings,
                            'pnl': pnl,
                            'pnl_pct': (pnl / (holdings * current_position['price'])) * 100
                        })
                        
                        # Reset position
                        holdings = 0
                        current_position = None
                    
                    # Open a new position if there's available cash
                    position_size = min(cash * 0.95, signal.get('size', 0.1) * cash)
                    
                    if position_size > 0 and current_position is None:
                        # Calculate quantity
                        quantity = position_size / price
                        
                        # Account for commission and slippage
                        commission = position_size * self.commission_pct
                        slippage = position_size * self.slippage_pct
                        
                        # Update cash and holdings
                        cash -= position_size + commission + slippage
                        holdings = quantity
                        
                        # Record position
                        current_position = {
                            'timestamp': timestamp,
                            'symbol': symbol,
                            'direction': signal['direction'],
                            'price': price,
                            'quantity': quantity,
                            'value': position_size
                        }
                        
                        positions.append(current_position)
                
                # Update equity curve
                portfolio_value = cash
                if current_position is not None:
                    portfolio_value += holdings * current_bar['close']
                
                equity_curve.append(portfolio_value)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(
                equity_curve=equity_curve,
                trades=trades,
                start_date=start_date,
                end_date=end_date
            )
            
            # Store results
            result_file = os.path.join(
                self.results_dir,
                f"backtest_{strategy_id}_{symbol}_{start_date}_{end_date}.json"
            )
            
            backtest_result = {
                "status": "success",
                "strategy_id": strategy_id,
                "strategy_type": strategy.__class__.__name__,
                "parameters": parameters,
                "asset_class": asset_class,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "initial_capital": initial_capital,
                "performance": performance,
                "runtime_seconds": 0  # Will be filled below
            }
            
            # Extract summary trade data (limit size)
            max_trades = min(100, len(trades))
            backtest_result["trades_summary"] = trades[:max_trades]
            
            # Save to file
            with open(result_file, 'w') as f:
                json.dump(backtest_result, f, indent=2)
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": str(e),
                "strategy_id": strategy_id
            }
    
    def _load_historical_data(
        self,
        asset_class: str,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Load historical market data for the specified asset and time period.
        
        Args:
            asset_class: Asset class (equity, crypto, forex)
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Candle interval
            
        Returns:
            DataFrame with historical data or None if unavailable
        """
        # Generate path for cached data
        data_file = os.path.join(
            self.data_dir,
            f"{asset_class}_{symbol}_{interval}.csv"
        )
        
        # Check if we have the data locally
        if os.path.exists(data_file):
            logger.debug(f"Loading historical data from {data_file}")
            df = pd.read_csv(data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Filter for the requested date range
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df.index >= start) & (df.index <= end)]
            
            if len(df) > 0:
                return df
        
        # If we don't have the data locally or it doesn't cover the requested range,
        # try to fetch it if a data fetcher is available
        if self.data_fetcher is not None:
            logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            try:
                df = self.data_fetcher.fetch_historical_data(
                    asset_class=asset_class,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval
                )
                
                if df is not None and len(df) > 0:
                    # Save the data for future use
                    df.to_csv(data_file)
                    return df
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
        
        logger.warning(f"No historical data available for {symbol} from {start_date} to {end_date}")
        return None
    
    def _calculate_performance_metrics(
        self,
        equity_curve: List[float],
        trades: List[Dict[str, Any]],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from backtest results.
        
        Args:
            equity_curve: List of portfolio values over time
            trades: List of executed trades
            start_date: Start date of backtest
            end_date: End date of backtest
            
        Returns:
            Dictionary of performance metrics
        """
        if not equity_curve or len(equity_curve) < 2:
            return {"error": "Insufficient data to calculate metrics"}
        
        # Convert to numpy array for calculations
        equity = np.array(equity_curve)
        
        # Calculate returns
        returns = np.diff(equity) / equity[:-1]
        
        # Basic metrics
        total_return = (equity[-1] / equity[0]) - 1
        
        # Handle case of no trades
        if not trades:
            return {
                "total_return": total_return * 100,  # In percent
                "trades_count": 0,
                "win_rate": 0,
                "average_return": 0,
                "max_drawdown": self._calculate_max_drawdown(equity) * 100,  # In percent
                "sharpe_ratio": self._calculate_sharpe_ratio(returns) if len(returns) > 0 else 0,
                "equity_curve": equity_curve[::max(1, len(equity_curve) // 100)]  # Sample to reduce size
            }
        
        # Trade metrics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        average_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        average_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else 0
        
        # Calculate time-based metrics
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        days = (end - start).days
        
        # Annualized return
        annualized_return = ((1 + total_return) ** (365 / max(1, days))) - 1 if days > 0 else 0
        
        # Return comprehensive metrics
        return {
            "total_return": total_return * 100,  # In percent
            "annualized_return": annualized_return * 100,  # In percent
            "trades_count": len(trades),
            "win_rate": win_rate * 100,  # In percent
            "average_win": average_win,
            "average_loss": average_loss,
            "profit_factor": profit_factor,
            "max_drawdown": self._calculate_max_drawdown(equity) * 100,  # In percent
            "sharpe_ratio": self._calculate_sharpe_ratio(returns) if len(returns) > 0 else 0,
            "sortino_ratio": self._calculate_sortino_ratio(returns) if len(returns) > 0 else 0,
            "equity_curve": equity_curve[::max(1, len(equity_curve) // 100)]  # Sample to reduce size
        }
    
    def _calculate_max_drawdown(self, equity: np.ndarray) -> float:
        """
        Calculate maximum drawdown from an equity curve.
        
        Args:
            equity: Array of equity values
            
        Returns:
            Maximum drawdown as a decimal
        """
        # Find running maximum
        running_max = np.maximum.accumulate(equity)
        
        # Calculate drawdown
        drawdown = (equity - running_max) / running_max
        
        # Return maximum drawdown
        return abs(drawdown.min()) if len(drawdown) > 0 else 0
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calculate the Sharpe ratio.
        
        Args:
            returns: Array of period returns
            risk_free_rate: Annualized risk-free rate
            
        Returns:
            Sharpe ratio
        """
        # Convert risk-free rate to per-period rate (assuming daily returns)
        period_risk_free = (1 + risk_free_rate) ** (1/252) - 1
        
        # Calculate excess returns
        excess_returns = returns - period_risk_free
        
        # Calculate Sharpe ratio
        sharpe = np.mean(excess_returns) / (np.std(excess_returns) + 1e-10) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calculate the Sortino ratio, which only considers downside deviation.
        
        Args:
            returns: Array of period returns
            risk_free_rate: Annualized risk-free rate
            
        Returns:
            Sortino ratio
        """
        # Convert risk-free rate to per-period rate (assuming daily returns)
        period_risk_free = (1 + risk_free_rate) ** (1/252) - 1
        
        # Calculate excess returns
        excess_returns = returns - period_risk_free
        
        # Calculate downside deviation (only negative excess returns)
        downside_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 1e-10
        
        # Calculate Sortino ratio
        sortino = np.mean(excess_returns) / (downside_deviation + 1e-10) * np.sqrt(252)
        
        return sortino 
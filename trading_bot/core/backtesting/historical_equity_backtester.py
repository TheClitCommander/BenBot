"""
Historical Backtester for Equity Assets.
"""
import logging
import pandas as pd
from typing import Dict, Any

from trading_bot.core.backtesting.base_backtester import BaseBacktester, BacktestResult, PerformanceMetrics
# from trading_bot.core.strategies.base_strategy import BaseStrategy # Or specific equity strategies
# from trading_bot.core.data.historical_data_fetcher import HistoricalDataFetcher

logger = logging.getLogger(__name__)

class HistoricalEquityBacktester(BaseBacktester):
    def __init__(self, historical_data_fetcher: Any):
        super().__init__(historical_data_fetcher)

    def run_backtest(
        self,
        strategy_id: str,
        strategy_class: Any, # Expected to be a subclass of BaseStrategy
        parameters: Dict[str, Any],
        asset_class: str, 
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str,
        initial_capital: float = 100000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005
    ) -> BacktestResult:
        logger.info(f"Running EQUITY backtest for {strategy_id} on {symbol} from {start_date} to {end_date}")

        # 1. Fetch Data
        historical_data = self.data_fetcher.fetch(symbol, asset_class, start_date, end_date, interval)
        if historical_data is None or historical_data.empty:
            return BacktestResult(
                status="failure", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message="Failed to fetch historical data."
            )

        # 2. Instantiate Strategy
        try:
            strategy_instance = strategy_class(strategy_id=strategy_id, parameters=parameters)
        except Exception as e:
            logger.error(f"Error instantiating strategy {strategy_id} ({strategy_class.__name__}): {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Strategy instantiation error: {e}"
            )

        # 3. Generate Signals
        try:
            signals_df = strategy_instance.generate_signals(historical_data.copy()) # Pass a copy
        except Exception as e:
            logger.error(f"Error generating signals for {strategy_id}: {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Signal generation error: {e}"
            )

        # 4. Portfolio Simulation (Vectorized Backtesting Example - can be made event-driven for more realism)
        # This is a simplified example. A full backtester would handle position sizing, cash management, etc.
        positions = pd.Series(index=signals_df.index, dtype=float).fillna(0.0)
        portfolio_values = pd.Series(index=signals_df.index, dtype=float).fillna(initial_capital)
        cash = initial_capital
        current_position_qty = 0 # Number of shares/contracts
        last_signal = 0
        trades_log = []
        entry_price = 0.0

        for i, timestamp in enumerate(historical_data.index):
            signal = signals_df['signal'].iloc[i]
            current_price = historical_data['Close'].iloc[i] # Assume trading at close for simplicity
            
            # Update portfolio value for holding periods if position exists
            if i > 0:
                portfolio_values.iloc[i] = portfolio_values.iloc[i-1] # Start with previous day's value
                if current_position_qty != 0: # If holding a position
                    price_change = current_price - historical_data['Close'].iloc[i-1]
                    portfolio_values.iloc[i] += current_position_qty * price_change
            
            if signal == 1 and last_signal <= 0: # Buy signal and not already long
                if current_position_qty < 0: # Close short position first
                    buy_price_eff = self._apply_slippage_and_commission(current_price, "buy", slippage_pct, commission_pct, is_entry=False)
                    cash += abs(current_position_qty) * buy_price_eff
                    trades_log.append({'timestamp': timestamp, 'type': 'cover', 'price': buy_price_eff, 'qty': abs(current_position_qty)})
                    current_position_qty = 0
                
                # Go long
                entry_price_eff = self._apply_slippage_and_commission(current_price, "buy", slippage_pct, commission_pct, is_entry=True)
                shares_to_buy = cash / entry_price_eff # Simple: use all available cash
                if shares_to_buy > 0:
                    cash -= shares_to_buy * entry_price_eff
                    current_position_qty = shares_to_buy
                    entry_price = entry_price_eff # For P&L calculation later
                    trades_log.append({'timestamp': timestamp, 'type': 'buy', 'price': entry_price_eff, 'qty': shares_to_buy})
                    positions.iloc[i] = shares_to_buy
                portfolio_values.iloc[i] = cash + (current_position_qty * current_price) # Update with current price
                last_signal = 1

            elif signal == -1 and last_signal >= 0: # Sell signal and not already short
                if current_position_qty > 0: # Close long position first
                    sell_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct, commission_pct, is_entry=False)
                    cash += current_position_qty * sell_price_eff
                    trades_log.append({'timestamp': timestamp, 'type': 'sell', 'price': sell_price_eff, 'qty': current_position_qty})
                    current_position_qty = 0
                
                # Go short (optional, for simplicity, this example might not fully implement shorting P&L correctly)
                # entry_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct, commission_pct, is_entry=True)
                # shares_to_sell = cash / entry_price_eff # Simplified: base shares on cash / price
                # if shares_to_sell > 0:
                #     cash += shares_to_sell * entry_price_eff # Selling short increases cash initially
                #     current_position_qty = -shares_to_sell
                #     entry_price = entry_price_eff
                #     trades_log.append({'timestamp': timestamp, 'type': 'short', 'price': entry_price_eff, 'qty': shares_to_sell})
                #     positions.iloc[i] = -shares_to_sell
                portfolio_values.iloc[i] = cash # If short, value is cash minus liability of borrowed shares
                last_signal = -1
            
            elif signal == 0 and current_position_qty != 0: # Hold signal, but need to close if previous signal was exit
                 if last_signal == 1 and signals_df['signal'].iloc[i-1] == -1: # Was long, got sell signal prev, now hold -> means exit on sell
                    sell_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct, commission_pct, is_entry=False)
                    cash += current_position_qty * sell_price_eff
                    trades_log.append({'timestamp': timestamp, 'type': 'sell_exit', 'price': sell_price_eff, 'qty': current_position_qty})
                    current_position_qty = 0
                    portfolio_values.iloc[i] = cash
                    last_signal = 0
                 # Add similar logic for exiting shorts if implemented
            else:
                positions.iloc[i] = current_position_qty # Carry forward position
                if i == 0: portfolio_values.iloc[i] = initial_capital # Ensure first value is capital
                last_signal = signal # Or 0 if no new trade signal

        #Simplified trade log for performance calculation (needs more detail for PnL per trade)
        #This part needs significant enhancement for proper P&L attribution per trade.
        #For now, _calculate_performance_metrics uses the equity curve primarily.
        #A proper trade log would look like: [entry_time, exit_time, entry_price, exit_price, type, pnl, pnl_pct]
        processed_trades = []
        active_trade = None
        for trade in trades_log:
            if trade['type'] == 'buy':
                if active_trade and active_trade['type'] == 'long': continue # Already long
                active_trade = {'entry_time': trade['timestamp'], 'entry_price': trade['price'], 'type': 'long', 'qty': trade['qty']}
            elif trade['type'] == 'sell' and active_trade and active_trade['type'] == 'long':
                pnl = (trade['price'] - active_trade['entry_price']) * active_trade['qty']
                processed_trades.append({
                    **active_trade,
                    'exit_time': trade['timestamp'],
                    'exit_price': trade['price'],
                    'pnl': pnl
                })
                active_trade = None
            # Add short trade processing here
        trades_df = pd.DataFrame(processed_trades)

        # 5. Calculate Performance Metrics
        performance = self._calculate_performance_metrics(portfolio_values, trades_df, initial_capital)

        return BacktestResult(
            status="success",
            strategy_id=strategy_id,
            strategy_type=f"equity_{strategy_class.__name__}", # more specific type
            parameters=parameters,
            performance=performance
        ) 
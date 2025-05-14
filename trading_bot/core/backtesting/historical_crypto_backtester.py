"""
Historical Backtester for Crypto Assets.
"""
import logging
import pandas as pd
from typing import Dict, Any

from trading_bot.core.backtesting.base_backtester import BaseBacktester, BacktestResult, PerformanceMetrics

logger = logging.getLogger(__name__)

class HistoricalCryptoBacktester(BaseBacktester):
    def __init__(self, historical_data_fetcher: Any):
        super().__init__(historical_data_fetcher)

    def run_backtest(
        self,
        strategy_id: str,
        strategy_class: Any, 
        parameters: Dict[str, Any],
        asset_class: str, 
        symbol: str, # e.g., "BTC/USDT"
        start_date: str,
        end_date: str,
        interval: str,
        initial_capital: float = 10000.0, # Crypto often traded with smaller capital
        commission_pct: float = 0.00075,  # Binance VIP 0 maker/taker fee example or similar
        slippage_pct: float = 0.001     # Crypto can have higher slippage
    ) -> BacktestResult:
        logger.info(f"Running CRYPTO backtest for {strategy_id} on {symbol} from {start_date} to {end_date}")

        historical_data = self.data_fetcher.fetch(symbol, asset_class, start_date, end_date, interval)
        if historical_data is None or historical_data.empty:
            return BacktestResult(
                status="failure", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message="Failed to fetch crypto data."
            )
        try:
            strategy_instance = strategy_class(strategy_id=strategy_id, parameters=parameters)
        except Exception as e:
            logger.error(f"Error instantiating crypto strategy {strategy_id}: {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Strategy instantiation error: {e}"
            )
        try:
            signals_df = strategy_instance.generate_signals(historical_data.copy())
        except Exception as e:
            logger.error(f"Error generating signals for crypto strategy {strategy_id}: {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Signal generation error: {e}"
            )

        # Simplified portfolio simulation for crypto (long-only example)
        positions = pd.Series(index=signals_df.index, dtype=float).fillna(0.0)
        portfolio_values = pd.Series(index=signals_df.index, dtype=float).fillna(initial_capital)
        cash = initial_capital
        current_asset_qty = 0.0
        last_signal = 0
        trades_log = []

        for i, timestamp in enumerate(historical_data.index):
            signal = signals_df['signal'].iloc[i]
            current_price = historical_data['Close'].iloc[i]

            if i > 0:
                portfolio_values.iloc[i] = portfolio_values.iloc[i-1]
                if current_asset_qty > 0:
                    price_change = current_price - historical_data['Close'].iloc[i-1]
                    portfolio_values.iloc[i] += current_asset_qty * price_change
            
            if signal == 1 and last_signal == 0: # Buy signal and not already in a position
                entry_price_eff = self._apply_slippage_and_commission(current_price, "buy", slippage_pct, commission_pct, is_entry=True)
                asset_to_buy = cash / entry_price_eff
                if asset_to_buy > 0:
                    cash -= asset_to_buy * entry_price_eff
                    current_asset_qty = asset_to_buy
                    trades_log.append({'timestamp': timestamp, 'type': 'buy', 'price': entry_price_eff, 'qty': asset_to_buy})
                    positions.iloc[i] = current_asset_qty
                portfolio_values.iloc[i] = cash + (current_asset_qty * current_price)
                last_signal = 1
            elif signal == -1 and current_asset_qty > 0: # Sell signal and currently holding assets
                exit_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct, commission_pct, is_entry=False)
                cash += current_asset_qty * exit_price_eff
                trades_log.append({'timestamp': timestamp, 'type': 'sell', 'price': exit_price_eff, 'qty': current_asset_qty})
                current_asset_qty = 0
                positions.iloc[i] = 0 # Position is now flat
                portfolio_values.iloc[i] = cash 
                last_signal = -1 # Or 0 if strategy implies exiting and staying out
            else: # Hold or no clear signal to change position
                positions.iloc[i] = current_asset_qty
                if i == 0: portfolio_values.iloc[i] = initial_capital
                # last_signal remains unchanged unless a new trade is made or explicitly reset by strategy
                if signal == 0 : last_signal = 0 # if hold signal, reset last_signal to allow re-entry on next signal

        processed_trades = []
        active_trade = None
        for trade in trades_log:
            if trade['type'] == 'buy':
                active_trade = {'entry_time': trade['timestamp'], 'entry_price': trade['price'], 'type': 'long', 'qty': trade['qty']}
            elif trade['type'] == 'sell' and active_trade and active_trade['type'] == 'long':
                pnl = (trade['price'] - active_trade['entry_price']) * active_trade['qty']
                processed_trades.append({
                    **active_trade, 'exit_time': trade['timestamp'], 'exit_price': trade['price'], 'pnl': pnl
                })
                active_trade = None
        trades_df = pd.DataFrame(processed_trades)
        
        performance = self._calculate_performance_metrics(portfolio_values, trades_df, initial_capital)

        return BacktestResult(
            status="success", strategy_id=strategy_id, strategy_type=f"crypto_{strategy_class.__name__}",
            parameters=parameters, performance=performance
        ) 
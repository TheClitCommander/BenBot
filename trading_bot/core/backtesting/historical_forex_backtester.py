"""
Historical Backtester for Forex Assets.

Note: Forex backtesting requires careful handling of pip values, lot sizes,
leverage, and margin, which are simplified in this placeholder.
"""
import logging
import pandas as pd
from typing import Dict, Any

from trading_bot.core.backtesting.base_backtester import BaseBacktester, BacktestResult, PerformanceMetrics

logger = logging.getLogger(__name__)

class HistoricalForexBacktester(BaseBacktester):
    def __init__(self, historical_data_fetcher: Any):
        super().__init__(historical_data_fetcher)

    def run_backtest(
        self,
        strategy_id: str,
        strategy_class: Any, 
        parameters: Dict[str, Any],
        asset_class: str, 
        symbol: str, # e.g., "EURUSD"
        start_date: str,
        end_date: str,
        interval: str,
        initial_capital: float = 10000.0, # Forex often traded with leveraged accounts
        commission_pct: float = 0.00005, # Example: $5 per $100k lot, if price is 1.0, then 5/100000 = 0.00005
        slippage_pips: float = 0.5, # Slippage in pips (e.g., 0.5 pips)
        pip_value: float = 0.0001 # For most XXX/YYY pairs; JPY pairs are 0.01
        # lot_size: int = 100000 # Standard lot, or can be mini/micro
    ) -> BacktestResult:
        logger.info(f"Running FOREX backtest for {strategy_id} on {symbol} from {start_date} to {end_date}")

        # Adjust slippage_pct based on pip_value for use in the generic slippage function
        # This is an approximation; true pip-based slippage affects the price directly by pips.
        # For _apply_slippage_and_commission, we convert pips to a percentage of price.
        # This is a rough conversion and assumes an average price if not available at time of slippage calc.
        # A more robust way is to adjust price by (slippage_pips * pip_value) directly in simulation loop.
        # For now, we'll make a rough conversion for the existing helper.
        # Let's assume an average price of 1.0 for simplicity in this conversion. A better way is needed.
        average_price_for_slippage_conversion = 1.0 
        slippage_pct_from_pips = (slippage_pips * pip_value) / average_price_for_slippage_conversion

        historical_data = self.data_fetcher.fetch(symbol, asset_class, start_date, end_date, interval)
        if historical_data is None or historical_data.empty:
            return BacktestResult(
                status="failure", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message="Failed to fetch forex data."
            )
        try:
            strategy_instance = strategy_class(strategy_id=strategy_id, parameters=parameters)
        except Exception as e:
            logger.error(f"Error instantiating forex strategy {strategy_id}: {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Strategy instantiation error: {e}"
            )
        try:
            signals_df = strategy_instance.generate_signals(historical_data.copy())
        except Exception as e:
            logger.error(f"Error generating signals for forex strategy {strategy_id}: {e}", exc_info=True)
            return BacktestResult(
                status="error", strategy_id=strategy_id, strategy_type=str(strategy_class.__name__),
                parameters=parameters, performance=PerformanceMetrics(), error_message=f"Signal generation error: {e}"
            )

        # Simplified portfolio simulation for Forex (handles long/short)
        positions = pd.Series(index=signals_df.index, dtype=float).fillna(0.0) # Stores units of base currency
        portfolio_values = pd.Series(index=signals_df.index, dtype=float).fillna(initial_capital)
        cash = initial_capital
        current_units = 0.0 # Units of the base currency (e.g., EUR in EUR/USD)
        last_signal = 0
        trades_log = []
        trade_lot_size = 10000 # Example: Fixed micro lot size for each trade for simplicity

        for i, timestamp in enumerate(historical_data.index):
            signal = signals_df['signal'].iloc[i]
            current_price = historical_data['Close'].iloc[i]

            if i > 0:
                portfolio_values.iloc[i] = portfolio_values.iloc[i-1]
                if current_units != 0:
                    price_change = current_price - historical_data['Close'].iloc[i-1]
                    # P&L for forex: units * price_change (in quote currency per unit of base)
                    # If holding 10k EUR and EURUSD goes up by 0.0010, P&L = 10000 * 0.0010 = $10
                    portfolio_values.iloc[i] += current_units * price_change 
            
            # Decision to trade
            if signal == 1 and last_signal <= 0: # Buy signal
                if current_units < 0: # If short, cover first
                    buy_price_eff = self._apply_slippage_and_commission(current_price, "buy", slippage_pct_from_pips, commission_pct, is_entry=False)
                    cash_change = abs(current_units) * (entry_price - buy_price_eff) # PnL from short
                    cash += abs(current_units) * entry_price + cash_change # Add back initial margin + PnL
                    trades_log.append({'timestamp': timestamp, 'type': 'cover', 'price': buy_price_eff, 'qty': abs(current_units), 'pnl': cash_change})
                    current_units = 0
                
                units_to_buy = trade_lot_size
                entry_price_eff = self._apply_slippage_and_commission(current_price, "buy", slippage_pct_from_pips, commission_pct, is_entry=True)
                # For forex, cash doesn't decrease by units*price directly due to margin/leverage
                # We'll track units and value them. Cash is mainly for realized P&L and margin.
                # This is a simplification. A proper forex backtester needs margin calculations.
                current_units = units_to_buy
                entry_price = entry_price_eff # Store actual entry price for PnL
                trades_log.append({'timestamp': timestamp, 'type': 'buy', 'price': entry_price_eff, 'qty': units_to_buy})
                positions.iloc[i] = current_units
                last_signal = 1

            elif signal == -1 and last_signal >= 0: # Sell signal
                if current_units > 0: # If long, sell first
                    sell_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct_from_pips, commission_pct, is_entry=False)
                    cash_change = current_units * (sell_price_eff - entry_price)
                    cash += cash_change # Realized PnL from long
                    trades_log.append({'timestamp': timestamp, 'type': 'sell_long', 'price': sell_price_eff, 'qty': current_units, 'pnl': cash_change})
                    current_units = 0
                
                units_to_sell = trade_lot_size
                entry_price_eff = self._apply_slippage_and_commission(current_price, "sell", slippage_pct_from_pips, commission_pct, is_entry=True)
                current_units = -units_to_sell # Negative for short position
                entry_price = entry_price_eff # Store entry price for short
                trades_log.append({'timestamp': timestamp, 'type': 'short', 'price': entry_price_eff, 'qty': units_to_sell})
                positions.iloc[i] = current_units
                last_signal = -1
            else: # Hold
                positions.iloc[i] = current_units
                if signal == 0 : last_signal = 0

            # Update portfolio value based on current position and price
            # Realized P&L is in cash. Unrealized is units * current_price.
            # For simplicity, portfolio_values tracks cash + mark-to-market of open position.
            # If short, MTM is (entry_price_of_short - current_price) * abs(units)
            mtm_value = 0
            if current_units > 0: # Long position
                mtm_value = current_units * current_price
            elif current_units < 0: # Short position
                mtm_value = abs(current_units) * entry_price + abs(current_units) * (entry_price - current_price) 
                # This reflects initial cash from short sell + P&L on short
            
            # This is still a simplification. True margin account value is more complex.
            if i == 0: portfolio_values.iloc[i] = initial_capital
            else: portfolio_values.iloc[i] = cash + mtm_value if current_units != 0 else cash

        processed_trades = pd.DataFrame(trades_log)
        # P&L is already in trades_log for this version
        
        performance = self._calculate_performance_metrics(portfolio_values, processed_trades, initial_capital)

        return BacktestResult(
            status="success", strategy_id=strategy_id, strategy_type=f"forex_{strategy_class.__name__}",
            parameters=parameters, performance=performance
        ) 
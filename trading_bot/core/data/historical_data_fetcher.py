"""
Historical Data Fetcher for multiple asset classes.

This module provides a unified interface to download historical
market data for equities, cryptocurrencies, and forex.
"""
import logging
import pandas as pd
import yfinance
import ccxt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HistoricalDataFetcher:
    """
    Fetches historical OHLCV data for specified symbols and asset classes.
    """

    def __init__(self, crypto_exchange_name: str = 'binance'):
        """
        Initializes the fetcher.
        Args:
            crypto_exchange_name: Name of the default crypto exchange to use from ccxt.
        """
        try:
            self.crypto_exchange = getattr(ccxt, crypto_exchange_name)()
        except (AttributeError, ccxt.NetworkError) as e:
            logger.warning(
                f"Could not initialize crypto exchange {crypto_exchange_name}. "
                f"Crypto data fetching might fail or use a fallback. Error: {e}"
            )
            self.crypto_exchange = None # Fallback or handle as needed

    def fetch(
        self,
        symbol: str,
        asset_class: str,
        start_date: str, # YYYY-MM-DD
        end_date: str,   # YYYY-MM-DD
        interval: str = "1d" # e.g., 1m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk, 1mo
    ) -> Optional[pd.DataFrame]:
        """
        Fetches historical data.

        Args:
            symbol: The ticker symbol (e.g., "SPY", "BTC/USDT", "EURUSD=X").
            asset_class: "equity", "crypto", or "forex".
            start_date: Start date in "YYYY-MM-DD" format.
            end_date: End date in "YYYY-MM-DD" format.
            interval: Data frequency (yfinance/ccxt compatible).

        Returns:
            A pandas DataFrame with OHLCV data and a DatetimeIndex, or None if fetching fails.
            Columns: Open, High, Low, Close, Volume (and potentially Adj Close for yfinance).
        """
        logger.info(
            f"Fetching data for {symbol} ({asset_class}) from {start_date} to {end_date} with interval {interval}"
        )
        try:
            if asset_class == "equity":
                return self._fetch_equity(symbol, start_date, end_date, interval)
            elif asset_class == "crypto":
                return self._fetch_crypto(symbol, start_date, end_date, interval)
            elif asset_class == "forex":
                # Using yfinance for FX pairs, e.g., "EURUSD=X"
                return self._fetch_forex(symbol, start_date, end_date, interval)
            else:
                logger.error(f"Unsupported asset class: {asset_class}")
                return None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} ({asset_class}): {e}", exc_info=True)
            return None

    def _fetch_equity(self, symbol: str, start_date: str, end_date: str, interval: str) -> Optional[pd.DataFrame]:
        data = yfinance.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
        if data.empty:
            logger.warning(f"No equity data found for {symbol} in the given range/interval.")
            return None
        data.index.name = 'Timestamp' # Ensure index has a name
        return data

    def _fetch_forex(self, symbol: str, start_date: str, end_date: str, interval: str) -> Optional[pd.DataFrame]:
        # yfinance uses "=X" for forex pairs, e.g., "EURUSD=X"
        forex_symbol = symbol if symbol.endswith("=X") else f"{symbol}=X"
        data = yfinance.download(forex_symbol, start=start_date, end=end_date, interval=interval, progress=False)
        if data.empty:
            logger.warning(f"No forex data found for {forex_symbol} using yfinance.")
            return None
        data.index.name = 'Timestamp'
        return data

    def _fetch_crypto(self, symbol: str, start_date: str, end_date: str, interval: str) -> Optional[pd.DataFrame]:
        if not self.crypto_exchange or not self.crypto_exchange.has.get('fetchOHLCV'):
            logger.error(
                f"Crypto exchange {self.crypto_exchange_name if self.crypto_exchange else 'default'} "
                "not initialized properly or does not support fetchOHLCV."
            )
            return None

        # Convert yfinance interval to ccxt timeframe
        timeframe = self._convert_interval_to_ccxt_timeframe(interval)
        if not timeframe:
            logger.error(f"Unsupported interval for crypto: {interval}")
            return None
            
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # CCXT expects timestamp in milliseconds
        since = int(start_dt.timestamp() * 1000)
        limit = 1000  # Max limit per request for many exchanges; may need to paginate for long periods / small intervals
        all_ohlcv = []

        current_dt = start_dt
        while current_dt < end_dt:
            try:
                ohlcv = self.crypto_exchange.fetch_ohlcv(symbol, timeframe, since, limit)
                if not ohlcv:
                    logger.debug(f"No more crypto data for {symbol} from {since}")
                    break 
                
                all_ohlcv.extend(ohlcv)
                
                # Get timestamp of the last record to use as `since` for the next iteration
                # and to check if we have fetched all data up to end_date
                last_timestamp_ms = ohlcv[-1][0]
                since = last_timestamp_ms + self._timeframe_to_milliseconds(timeframe) # Start next fetch after the last one
                current_dt = datetime.fromtimestamp(last_timestamp_ms / 1000)

                if current_dt >= end_dt:
                    break
                
                # Respect rate limits if any (simple sleep, can be more sophisticated)
                if hasattr(self.crypto_exchange, 'rateLimit'):
                    time.sleep(self.crypto_exchange.rateLimit / 1000)

            except ccxt.NetworkError as e:
                logger.error(f"CCXT NetworkError fetching {symbol}: {e}")
                return None # Or retry logic
            except ccxt.ExchangeError as e:
                logger.error(f"CCXT ExchangeError fetching {symbol}: {e}")
                return None # Or specific handling
            except Exception as e:
                logger.error(f"Generic error fetching crypto page for {symbol}: {e}", exc_info=True)
                return None


        if not all_ohlcv:
            logger.warning(f"No crypto data found for {symbol}.")
            return None

        df = pd.DataFrame(all_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df = df.set_index('Timestamp')
        
        # Filter exact date range as pagination might fetch beyond end_date
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        if df.empty:
            logger.warning(f"No crypto data for {symbol} within the precise date range after filtering.")
            return None
            
        return df

    def _convert_interval_to_ccxt_timeframe(self, interval: str) -> Optional[str]:
        # Basic mapping, can be expanded. yfinance intervals vs ccxt timeframes
        mapping = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "60m": "1h", 
            "1d": "1d", "1wk": "1w", "1mo": "1M" 
            # Note: '1mo' for yfinance often means monthly. CCXT '1M' is calendar month.
        }
        return mapping.get(interval)

    def _timeframe_to_milliseconds(self, timeframe: str) -> int:
        multipliers = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800, 'M': 2592000} # Approximate for M
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        return value * multipliers.get(unit, 0) * 1000


if __name__ == '__main__':
    # Example Usage
    logging.basicConfig(level=logging.INFO)
    fetcher = HistoricalDataFetcher()

    # Equity
    spy_data = fetcher.fetch("SPY", "equity", "2023-01-01", "2023-03-31", "1d")
    if spy_data is not None:
        logger.info(f"SPY Data:\n{spy_data.head()}")

    # Crypto
    # Ensure you have ccxt installed: pip install ccxt
    # Some exchanges might require API keys even for public data, or might be geo-restricted.
    # Binance is generally good for public OHLCV.
    btc_data = fetcher.fetch("BTC/USDT", "crypto", "2023-01-01", "2023-01-05", "1h")
    if btc_data is not None:
        logger.info(f"BTC/USDT Data (1h):\n{btc_data.head()}")
    
    eth_data_daily = fetcher.fetch("ETH/USDT", "crypto", "2023-12-01", "2023-12-10", "1d")
    if eth_data_daily is not None:
        logger.info(f"ETH/USDT Data (Daily):\n{eth_data_daily.head()}")

    # Forex (using yfinance)
    eurusd_data = fetcher.fetch("EURUSD", "forex", "2023-01-01", "2023-03-31", "1d")
    if eurusd_data is not None:
        logger.info(f"EUR/USD Data:\n{eurusd_data.head()}")
        
    # Test unsupported interval for crypto
    # bad_crypto = fetcher.fetch("LTC/USDT", "crypto", "2023-01-01", "2023-01-02", "2h") # 2h might not be standard
    # if bad_crypto is None:
    #    logger.info("Correctly handled unsupported crypto interval.")

    # Test pagination for crypto (short interval, longer period)
    #sol_data_short_interval = fetcher.fetch("SOL/USDT", "crypto", "2023-12-01", "2023-12-03", "1m")
    #if sol_data_short_interval is not None:
    #    logger.info(f"SOL/USDT 1m Data (first 5 rows):\n{sol_data_short_interval.head()}")
    #    logger.info(f"SOL/USDT 1m Data (last 5 rows):\n{sol_data_short_interval.tail()}")
    #    logger.info(f"SOL/USDT 1m Data shape: {sol_data_short_interval.shape}") 
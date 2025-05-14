"""
Market Adapter for BensBot's Evolution System.

This module automatically selects appropriate asset classes and strategies
based on current market conditions, volatility regimes, and correlation data.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class MarketRegime:
    """Identifies the current market regime across asset classes."""
    
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    UNKNOWN = "unknown"


class MarketAdapter:
    """
    Adapts the trading system to current market conditions by
    identifying optimal asset classes and strategy types.
    """
    
    def __init__(
        self,
        data_fetcher: Any,
        evo_trader: Any,
        portfolio_allocator: Any,
        lookback_days: int = 90,
        update_frequency_hours: int = 24,
        min_data_points: int = 20,
        volatility_window: int = 21
    ):
        """
        Initialize the market adapter.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            evo_trader: EvoTrader instance for strategy management
            portfolio_allocator: PortfolioAllocator for capital allocation
            lookback_days: Number of days to look back for regime identification
            update_frequency_hours: How often to update market regime analysis
            min_data_points: Minimum data points required for analysis
            volatility_window: Window size for volatility calculations
        """
        self.data_fetcher = data_fetcher
        self.evo_trader = evo_trader
        self.portfolio_allocator = portfolio_allocator
        
        self.lookback_days = lookback_days
        self.update_frequency_hours = update_frequency_hours
        self.min_data_points = min_data_points
        self.volatility_window = volatility_window
        
        # Key market symbols to track for each asset class
        self.market_symbols = {
            "equity": ["SPY", "QQQ", "IWM"],       # Major equity indices
            "crypto": ["BTC/USDT", "ETH/USDT"],    # Major cryptocurrencies
            "forex": ["EURUSD=X", "GBPUSD=X"]      # Major forex pairs
        }
        
        # Track identified regimes
        self.current_regimes: Dict[str, Dict[str, Any]] = {}
        
        # Track correlation matrix between assets
        self.correlation_matrix: Optional[pd.DataFrame] = None
        
        # When market regime was last updated
        self.last_update_time: Optional[datetime] = None
        
        # Performance history of strategies in different regimes
        self.regime_performance: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            asset_class: {regime: [] for regime in dir(MarketRegime) if not regime.startswith("_")}
            for asset_class in self.market_symbols.keys()
        }
    
    def update_market_regimes(self, force: bool = False) -> Dict[str, Any]:
        """
        Update market regime identification for all asset classes.
        
        Args:
            force: Whether to force update even if within update frequency
            
        Returns:
            Dictionary with regime updates
        """
        now = datetime.now()
        
        # Check if update is needed
        if not force and self.last_update_time:
            hours_since_update = (now - self.last_update_time).total_seconds() / 3600
            if hours_since_update < self.update_frequency_hours:
                logger.info(f"Market regime update skipped. Last update was {hours_since_update:.1f} hours ago.")
                return {
                    "status": "skipped",
                    "message": f"Last update was {hours_since_update:.1f} hours ago",
                    "regimes": self.current_regimes
                }
        
        start_time = time.time()
        
        # Calculate lookback period
        end_date = now.strftime('%Y-%m-%d')
        start_date = (now - timedelta(days=self.lookback_days)).strftime('%Y-%m-%d')
        
        # Update regimes for each asset class
        new_regimes = {}
        market_data = {}
        
        for asset_class, symbols in self.market_symbols.items():
            asset_regimes = {}
            asset_data = {}
            
            for symbol in symbols:
                # Fetch historical data
                try:
                    data = self.data_fetcher.fetch(
                        symbol=symbol,
                        asset_class=asset_class,
                        start_date=start_date,
                        end_date=end_date,
                        interval='1d'
                    )
                    
                    if data is None or len(data) < self.min_data_points:
                        logger.warning(f"Insufficient data for {symbol} ({asset_class}). Skipping.")
                        continue
                    
                    # Store data for correlation analysis
                    asset_data[symbol] = data
                    
                    # Identify regime for this symbol
                    regime = self._identify_regime(data, symbol, asset_class)
                    asset_regimes[symbol] = regime
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol} ({asset_class}): {e}")
                    continue
            
            # Aggregate regimes for the asset class (majority vote)
            if asset_regimes:
                regime_counts = {}
                for symbol, regime_info in asset_regimes.items():
                    regime = regime_info.get("primary_regime", MarketRegime.UNKNOWN)
                    regime_counts[regime] = regime_counts.get(regime, 0) + 1
                
                # Find the most common regime
                most_common_regime = max(regime_counts.items(), key=lambda x: x[1])[0]
                
                # Store overall asset class regime
                new_regimes[asset_class] = {
                    "primary_regime": most_common_regime,
                    "symbol_regimes": asset_regimes,
                    "confidence": regime_counts[most_common_regime] / len(asset_regimes) if asset_regimes else 0,
                    "timestamp": now.isoformat()
                }
                
                # Log the identified regime
                logger.info(f"Identified {asset_class} regime: {most_common_regime} (Confidence: {new_regimes[asset_class]['confidence']:.2f})")
            
            # Store market data for this asset class
            market_data[asset_class] = asset_data
        
        # Calculate cross-asset correlations
        if market_data:
            self._update_correlations(market_data)
        
        # Update current regimes
        self.current_regimes = new_regimes
        self.last_update_time = now
        
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "message": f"Market regimes updated in {duration:.2f} seconds",
            "regimes": new_regimes,
            "timestamp": now.isoformat()
        }
    
    def _identify_regime(
        self, 
        data: pd.DataFrame, 
        symbol: str, 
        asset_class: str
    ) -> Dict[str, Any]:
        """
        Identify the market regime for a specific symbol.
        
        Args:
            data: Historical price data
            symbol: Symbol being analyzed
            asset_class: Asset class of the symbol
            
        Returns:
            Dictionary with regime identification
        """
        # Calculate returns and volatility
        data['returns'] = data['Close'].pct_change() * 100  # in percent
        data['volatility'] = data['returns'].rolling(window=self.volatility_window).std()
        
        # Calculate SMA for trend detection
        data['sma_50'] = data['Close'].rolling(window=50).mean()
        data['sma_20'] = data['Close'].rolling(window=20).mean()
        
        # Calculate recent performance
        recent_return = (data['Close'].iloc[-1] / data['Close'].iloc[-min(len(data), 20)] - 1) * 100
        
        # Trending vs Mean-Reverting detection
        # Calculate autocorrelation of returns
        if len(data) > 20:
            # Autocorrelation of returns (lag 1) - negative suggests mean reversion
            returns_autocorr = data['returns'].dropna().autocorr(lag=1)
            
            # Hurst exponent estimation (simplified)
            # H < 0.5 suggests mean-reverting, H > 0.5 suggests trending
            # This is a simplified approximation
            returns = data['returns'].dropna().values
            lags = range(2, min(20, len(returns) // 4))
            tau = [np.sqrt(np.std(np.subtract(returns[lag:], returns[:-lag]))) for lag in lags]
            if tau and all(t > 0 for t in tau):
                m = np.polyfit(np.log(lags), np.log(tau), 1)
                hurst = m[0] / 2  # Hurst exponent estimate
            else:
                hurst = 0.5  # Default to random walk
        else:
            returns_autocorr = 0
            hurst = 0.5
        
        # Current location vs recent range
        high_52w = data['High'].rolling(window=min(252, len(data))).max().iloc[-1]
        low_52w = data['Low'].rolling(window=min(252, len(data))).min().iloc[-1]
        current_price = data['Close'].iloc[-1]
        price_range_pct = (current_price - low_52w) / (high_52w - low_52w) if (high_52w - low_52w) > 0 else 0.5
        
        # Volatility regime
        recent_vol = data['volatility'].iloc[-1]
        historical_vol = data['volatility'].mean()
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        # Trend strength
        trend_strength = (data['sma_20'].iloc[-1] / data['sma_50'].iloc[-1] - 1) * 100
        
        # Identify primary regime
        if vol_ratio > 1.5:
            primary_regime = MarketRegime.VOLATILE
        elif price_range_pct > 0.8 and trend_strength > 0:
            primary_regime = MarketRegime.BULLISH
        elif price_range_pct < 0.2 and trend_strength < 0:
            primary_regime = MarketRegime.BEARISH
        elif abs(trend_strength) < 0.5 and vol_ratio < 0.8:
            primary_regime = MarketRegime.SIDEWAYS
        elif hurst > 0.6 or (trend_strength > 1.0 and returns_autocorr > 0.1):
            primary_regime = MarketRegime.TRENDING
        elif hurst < 0.4 or returns_autocorr < -0.1:
            primary_regime = MarketRegime.MEAN_REVERTING
        else:
            primary_regime = MarketRegime.UNKNOWN
        
        # Secondary regime traits
        regime_traits = {}
        
        if vol_ratio > 1.2:
            regime_traits["elevated_volatility"] = True
        
        if abs(trend_strength) > 1.0:
            regime_traits["strong_trend"] = True
            regime_traits["trend_direction"] = "up" if trend_strength > 0 else "down"
        
        if returns_autocorr < -0.2:
            regime_traits["strong_mean_reversion"] = True
            
        if price_range_pct > 0.9:
            regime_traits["near_highs"] = True
        elif price_range_pct < 0.1:
            regime_traits["near_lows"] = True
        
        return {
            "primary_regime": primary_regime,
            "secondary_traits": regime_traits,
            "metrics": {
                "recent_return": recent_return,
                "volatility_ratio": vol_ratio,
                "autocorrelation": returns_autocorr,
                "hurst_exponent": hurst,
                "trend_strength": trend_strength,
                "price_range_percentile": price_range_pct
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _update_correlations(self, market_data: Dict[str, Dict[str, pd.DataFrame]]) -> None:
        """
        Update the correlation matrix between assets.
        
        Args:
            market_data: Dictionary of market data by asset class and symbol
        """
        # Extract close prices for all symbols
        close_data = {}
        
        for asset_class, assets in market_data.items():
            for symbol, data in assets.items():
                if not data.empty:
                    # Use asset_class:symbol as identifier
                    identifier = f"{asset_class}:{symbol}"
                    close_data[identifier] = data['Close']
        
        if close_data:
            # Merge into a single DataFrame
            merged_df = pd.DataFrame(close_data)
            
            # Calculate percent returns
            returns_df = merged_df.pct_change().dropna()
            
            # Calculate correlation matrix
            self.correlation_matrix = returns_df.corr()
    
    def recommend_strategy_allocation(self) -> Dict[str, Any]:
        """
        Recommend strategy allocations based on current market regimes.
        
        Returns:
            Dictionary with allocation recommendations
        """
        # First, make sure market regimes are up-to-date
        if not self.current_regimes or not self.last_update_time:
            self.update_market_regimes(force=True)
        elif (datetime.now() - self.last_update_time).total_seconds() / 3600 > self.update_frequency_hours:
            self.update_market_regimes()
        
        # Determine optimal asset class allocation based on regimes
        asset_class_weights = self._determine_asset_class_weights()
        
        # Select appropriate strategy types for each regime
        strategy_type_recommendations = {}
        
        for asset_class, regime_info in self.current_regimes.items():
            primary_regime = regime_info.get("primary_regime", MarketRegime.UNKNOWN)
            
            # Strategy type recommendations based on regime
            if primary_regime == MarketRegime.BULLISH:
                strategy_types = ["trend_following", "volatility"] 
            elif primary_regime == MarketRegime.BEARISH:
                strategy_types = ["volatility", "mean_reversion"]  # More defensive
            elif primary_regime == MarketRegime.TRENDING:
                strategy_types = ["trend_following"]
            elif primary_regime == MarketRegime.MEAN_REVERTING:
                strategy_types = ["mean_reversion"]
            elif primary_regime == MarketRegime.VOLATILE:
                strategy_types = ["volatility"]
            elif primary_regime == MarketRegime.SIDEWAYS:
                strategy_types = ["mean_reversion"]
            else:  # UNKNOWN
                strategy_types = ["trend_following", "mean_reversion", "volatility"]  # Balanced
            
            strategy_type_recommendations[asset_class] = strategy_types
        
        # Get all available strategies
        all_strategies = self._get_available_strategies()
        
        # Filter strategies based on recommendations
        recommended_strategies = {}
        
        for asset_class, strategy_types in strategy_type_recommendations.items():
            asset_strategies = []
            
            # Get strategies for this asset class and recommended types
            for strategy in all_strategies:
                if strategy.get("asset_class") == asset_class:
                    strategy_type = strategy.get("strategy_type", "").lower()
                    
                    # Check if any recommended type is in the strategy type
                    if any(recommended_type in strategy_type for recommended_type in strategy_types):
                        asset_strategies.append(strategy)
            
            # Sort by performance (if available)
            asset_strategies.sort(
                key=lambda s: s.get("performance", {}).get("sharpe_ratio", 0),
                reverse=True
            )
            
            recommended_strategies[asset_class] = asset_strategies
        
        # Generate final recommendations
        recommendations = {
            "asset_class_weights": asset_class_weights,
            "strategy_type_recommendations": strategy_type_recommendations,
            "recommended_strategies": recommended_strategies,
            "timestamp": datetime.now().isoformat(),
            "market_regimes": self.current_regimes
        }
        
        return recommendations
    
    def _determine_asset_class_weights(self) -> Dict[str, float]:
        """
        Determine optimal asset class weights based on current regimes.
        
        Returns:
            Dictionary mapping asset classes to recommended weights
        """
        weights = {}
        total_score = 0
        
        # Calculate a score for each asset class based on regime
        for asset_class, regime_info in self.current_regimes.items():
            primary_regime = regime_info.get("primary_regime", MarketRegime.UNKNOWN)
            confidence = regime_info.get("confidence", 0.5)
            
            # Base score
            score = 1.0
            
            # Adjust score based on regime
            if primary_regime == MarketRegime.BULLISH:
                # Favor equities and crypto in bullish regimes
                if asset_class == "equity":
                    score = 1.5
                elif asset_class == "crypto":
                    score = 1.3
                elif asset_class == "forex":
                    score = 0.7
            elif primary_regime == MarketRegime.BEARISH:
                # Reduce equity and crypto exposure in bearish regimes
                if asset_class == "equity":
                    score = 0.6
                elif asset_class == "crypto":
                    score = 0.4
                elif asset_class == "forex":
                    score = 1.2
            elif primary_regime == MarketRegime.TRENDING:
                # Trending regimes are good for all asset classes
                score = 1.2
            elif primary_regime == MarketRegime.MEAN_REVERTING:
                # Mean reverting regimes can be profitable across asset classes
                score = 1.1
            elif primary_regime == MarketRegime.VOLATILE:
                # Reduce allocation to volatile assets in volatile regimes
                if asset_class == "crypto":
                    score = 0.5
                elif asset_class == "forex":
                    score = 0.9
            elif primary_regime == MarketRegime.SIDEWAYS:
                # Sideways markets can be challenging
                score = 0.8
            
            # Adjust by confidence
            score = score * (0.5 + 0.5 * confidence)
            
            weights[asset_class] = score
            total_score += score
        
        # Normalize to get final weights
        if total_score > 0:
            weights = {asset: score / total_score for asset, score in weights.items()}
        else:
            # Default to equal weight if no scores
            num_assets = len(self.current_regimes)
            if num_assets > 0:
                equal_weight = 1.0 / num_assets
                weights = {asset: equal_weight for asset in self.current_regimes.keys()}
        
        return weights
    
    def _get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        Get all available strategies with their details.
        
        Returns:
            List of strategy details
        """
        # First check for best strategies from EvoTrader
        if hasattr(self.evo_trader, 'best_strategies') and self.evo_trader.best_strategies:
            strategies = []
            
            for strategy in self.evo_trader.best_strategies:
                # Convert to dict if it's an object
                if hasattr(strategy, '__dict__'):
                    strategy_dict = vars(strategy)
                else:
                    strategy_dict = dict(strategy)
                
                # Extract the asset class from the strategy type if not explicitly stored
                if 'asset_class' not in strategy_dict:
                    strategy_type = strategy_dict.get('type', '')
                    if 'equity' in strategy_type:
                        strategy_dict['asset_class'] = 'equity'
                    elif 'crypto' in strategy_type:
                        strategy_dict['asset_class'] = 'crypto'
                    elif 'forex' in strategy_type:
                        strategy_dict['asset_class'] = 'forex'
                    else:
                        strategy_dict['asset_class'] = 'unknown'
                
                strategies.append(strategy_dict)
            
            return strategies
        
        # Fallback to querying for strategies (interface may vary)
        if hasattr(self.evo_trader, 'get_all_strategies'):
            return self.evo_trader.get_all_strategies()
        
        # If we can't find strategies, return empty list
        logger.warning("Could not retrieve strategies from EvoTrader")
        return []
    
    def register_regime_performance(
        self,
        strategy_id: str,
        asset_class: str,
        performance: Dict[str, Any]
    ) -> None:
        """
        Register the performance of a strategy under the current regime.
        
        Args:
            strategy_id: ID of the strategy
            asset_class: Asset class of the strategy
            performance: Performance metrics
        """
        if asset_class not in self.current_regimes:
            logger.warning(f"No current regime for asset class: {asset_class}")
            return
        
        regime = self.current_regimes[asset_class].get("primary_regime", MarketRegime.UNKNOWN)
        
        if asset_class not in self.regime_performance:
            self.regime_performance[asset_class] = {}
        
        if regime not in self.regime_performance[asset_class]:
            self.regime_performance[asset_class][regime] = []
        
        self.regime_performance[asset_class][regime].append({
            "strategy_id": strategy_id,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_regime_report(self) -> Dict[str, Any]:
        """
        Get a report of current market regimes and correlations.
        
        Returns:
            Dictionary with regime report
        """
        report = {
            "market_regimes": self.current_regimes,
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
            "cross_asset_correlations": {}
        }
        
        # Extract correlation summary
        if self.correlation_matrix is not None:
            cross_asset_correlations = {}
            
            # Extract asset classes from index
            asset_classes = set(idx.split(':')[0] for idx in self.correlation_matrix.index)
            
            # Calculate average correlation between asset classes
            for ac1 in asset_classes:
                for ac2 in asset_classes:
                    if ac1 >= ac2:  # Avoid duplicates
                        continue
                    
                    # Get all symbols for these asset classes
                    ac1_symbols = [idx for idx in self.correlation_matrix.index if idx.startswith(f"{ac1}:")]
                    ac2_symbols = [idx for idx in self.correlation_matrix.index if idx.startswith(f"{ac2}:")]
                    
                    # Calculate average correlation
                    correlations = []
                    for sym1 in ac1_symbols:
                        for sym2 in ac2_symbols:
                            if sym1 in self.correlation_matrix and sym2 in self.correlation_matrix:
                                correlations.append(self.correlation_matrix.loc[sym1, sym2])
                    
                    if correlations:
                        avg_corr = sum(correlations) / len(correlations)
                        key = f"{ac1}_{ac2}"
                        cross_asset_correlations[key] = avg_corr
            
            report["cross_asset_correlations"] = cross_asset_correlations
        
        # Add strategy performance by regime
        report["strategy_performance_by_regime"] = self.regime_performance
        
        return report 
"""
AI Sentiment-based Trading Strategy.

This strategy uses the MarketContextAnalyzer to get a sentiment score
and makes trading decisions based on the market sentiment analysis.
"""

import logging
from typing import Dict, Any, List

from ai_modules.MarketContextAnalyzer import MarketContextAnalyzer
from trading_bot.strategy.base import Strategy, StrategyConfig, StrategyType

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AiSentimentStrategy")

class AiSentimentStrategy(Strategy):
    """
    A trading strategy that uses AI-generated market sentiment analysis
    to make trading decisions.
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.analyzer = MarketContextAnalyzer()
        self.last_sentiment = 0
        self.sentiment_threshold = config.parameters.get("sentiment_threshold", 0.3)
        self.position_size_factor = config.parameters.get("position_size_factor", 1.0)
        self.symbols = config.instruments
        logger.info(f"AI Sentiment Strategy initialized with {len(self.symbols)} symbols")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signals based on AI sentiment.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with trading signals
        """
        try:
            # Get market context and sentiment score
            sentiment_score = self.analyzer.get_sentiment_score(self.symbols)
            context = self.analyzer.generate_market_context(self.symbols)
            
            # Calculate sentiment change
            sentiment_change = sentiment_score - self.last_sentiment
            self.last_sentiment = sentiment_score
            
            # Generate signals based on sentiment
            signals = []
            for symbol in self.symbols:
                if symbol not in market_data:
                    logger.warning(f"Symbol {symbol} not found in market data")
                    continue
                
                # Determine position sizing based on sentiment strength
                position_size = abs(sentiment_score) * self.position_size_factor
                
                if sentiment_score > self.sentiment_threshold:
                    # Bullish signal
                    signals.append({
                        "symbol": symbol,
                        "action": "buy",
                        "confidence": sentiment_score,
                        "size": position_size,
                        "reason": f"Bullish sentiment: {sentiment_score:.2f}"
                    })
                elif sentiment_score < -self.sentiment_threshold:
                    # Bearish signal
                    signals.append({
                        "symbol": symbol,
                        "action": "sell",
                        "confidence": -sentiment_score,
                        "size": position_size,
                        "reason": f"Bearish sentiment: {sentiment_score:.2f}"
                    })
                else:
                    # Neutral - no action
                    signals.append({
                        "symbol": symbol,
                        "action": "hold",
                        "confidence": 0,
                        "size": 0,
                        "reason": f"Neutral sentiment: {sentiment_score:.2f}"
                    })
            
            return {
                "signals": signals,
                "sentiment": sentiment_score,
                "sentiment_change": sentiment_change,
                "market_context": {
                    "overall_sentiment": context["analysis"]["overall_sentiment"],
                    "market_conditions": context["analysis"]["market_conditions"],
                    "key_events": context["analysis"]["key_events"][:3],  # Top 3 events
                    "outlook": context["analysis"]["outlook"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in AI Sentiment Strategy analysis: {e}")
            return {
                "signals": [],
                "error": str(e),
                "status": "error"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy with sentiment information."""
        status = super().get_status()
        status.update({
            "last_sentiment": self.last_sentiment,
            "sentiment_threshold": self.sentiment_threshold
        })
        return status 
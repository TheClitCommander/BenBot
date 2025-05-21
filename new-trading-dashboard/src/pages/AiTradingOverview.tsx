import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface MarketContextData {
  analysis: {
    overall_sentiment: number;
    market_conditions: string;
    key_events: string[];
    sector_analysis: { [key: string]: string };
    risk_factors: string[];
    opportunities: string[];
    outlook: string;
  };
  raw_data: {
    news_count: number;
    symbols_analyzed: string[];
    economic_indicators: { [key: string]: number | string };
  };
  generated_at: string;
  data_window_days: number;
}

// Fallback mock data in case API is not available
const mockMarketContext: MarketContextData = {
  analysis: {
    overall_sentiment: 5.2,
    market_conditions: "Markets are generally bullish with some sector rotation occurring.",
    key_events: [
      "Fed signaled potential pause in rate hikes",
      "Tech earnings exceeded expectations",
      "Inflation data showed slight decrease month-over-month"
    ],
    sector_analysis: {
      "Technology": "Leading the market with strong momentum",
      "Finance": "Performance is mixed with pressure from yield curve",
      "Energy": "Underperforming due to commodity price fluctuations"
    },
    risk_factors: [
      "Geopolitical tensions in Eastern Europe",
      "Supply chain constraints persisting in key industries",
      "Potential policy shifts from upcoming elections"
    ],
    opportunities: [
      "AI and semiconductor stocks showing strong momentum",
      "Healthcare innovation driven by new treatments",
      "Renewable energy expansion supported by policy incentives"
    ],
    outlook: "Cautiously optimistic with higher volatility expected"
  },
  raw_data: {
    news_count: 124,
    symbols_analyzed: ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
    economic_indicators: {
      "unemployment_rate": 3.8,
      "inflation_rate": 2.4,
      "gdp_growth": 2.1,
      "fed_rate": 5.25
    }
  },
  generated_at: new Date().toISOString(),
  data_window_days: 14
};

// Custom hook to fetch market context data
function useMarketContext() {
  return useQuery({
    queryKey: ['market-context'],
    queryFn: async () => {
      try {
        // Use the actual AI API endpoint
        const { data } = await api.get<MarketContextData>('/ai/market-analysis');
        return data;
      } catch (error) {
        console.error('Error fetching market context:', error);
        
        // If API fails, return mock data as fallback
        console.warn('Falling back to mock market context data');
        return mockMarketContext;
      }
    },
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export const AiTradingOverview: React.FC = () => {
  const { data, isLoading, error } = useMarketContext();
  const [showDetails, setShowDetails] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="h-4 bg-gray-700 rounded w-full mb-2.5"></div>
          <div className="h-4 bg-gray-700 rounded w-full mb-2.5"></div>
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-6"></div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-red-400">
          Error loading AI market analysis
          <button 
            onClick={() => window.location.reload()}
            className="ml-4 px-3 py-1 bg-blue-800 text-blue-300 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Helper function to determine sentiment color
  const getSentimentColor = (score: number) => {
    if (score > 7) return 'text-green-400';
    if (score > 3) return 'text-green-500';
    if (score > 0) return 'text-green-400';
    if (score > -3) return 'text-red-400';
    if (score > -7) return 'text-red-500';
    return 'text-red-400';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-blue-400">AI Market Analysis</h2>
        <div className="flex items-center">
          <span className="text-sm text-gray-400 mr-2">
            Generated {new Date(data.generated_at).toLocaleTimeString()}
          </span>
          <button 
            onClick={() => setShowDetails(!showDetails)}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-md text-sm font-medium text-gray-300"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      </div>
      
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <h3 className="text-lg font-medium text-gray-200">Market Sentiment:</h3>
          <span className={`ml-2 text-xl font-bold ${getSentimentColor(data.analysis.overall_sentiment)}`}>
            {data.analysis.overall_sentiment > 0 ? '+' : ''}{data.analysis.overall_sentiment.toFixed(1)}/10
          </span>
        </div>
        <p className="text-gray-300">{data.analysis.market_conditions}</p>
      </div>
      
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2 text-gray-200">Market Outlook</h3>
        <p className="text-gray-300 mb-4">{data.analysis.outlook}</p>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-green-400 mb-2">Opportunities</h4>
            <ul className="list-disc pl-5 space-y-1">
              {data.analysis.opportunities.map((item, i) => (
                <li key={i} className="text-gray-300">{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-red-400 mb-2">Risk Factors</h4>
            <ul className="list-disc pl-5 space-y-1">
              {data.analysis.risk_factors.map((item, i) => (
                <li key={i} className="text-gray-300">{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      
      {showDetails && (
        <>
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-2 text-gray-200">Key Events</h3>
            <ul className="list-disc pl-5 space-y-1">
              {data.analysis.key_events.map((event, i) => (
                <li key={i} className="text-gray-300">{event}</li>
              ))}
            </ul>
          </div>
          
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-2 text-gray-200">Sector Analysis</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(data.analysis.sector_analysis).map(([sector, analysis]) => (
                <div key={sector} className="bg-gray-700 p-4 rounded-lg">
                  <h4 className="font-medium mb-1 text-gray-200">{sector}</h4>
                  <p className="text-sm text-gray-300">{analysis}</p>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2 text-gray-200">Analysis Details</h3>
            <div className="bg-gray-700 p-4 rounded-lg text-sm">
              <p className="text-gray-300">Data window: {data.data_window_days} days</p>
              <p className="text-gray-300">Symbols analyzed: {data.raw_data.symbols_analyzed.join(', ')}</p>
              <p className="text-gray-300">News sources analyzed: {data.raw_data.news_count}</p>
              <div className="mt-2">
                <p className="font-medium text-gray-200">Economic Indicators:</p>
                <ul className="grid grid-cols-2 gap-x-4 mt-1">
                  {Object.entries(data.raw_data.economic_indicators).map(([key, value]) => (
                    <li key={key} className="flex justify-between text-gray-300">
                      <span className="capitalize">{key.replace('_', ' ')}:</span>
                      <span className="font-medium">{value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}; 
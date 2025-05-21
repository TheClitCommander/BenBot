import React, { useState } from 'react';
import { useMarkets, useMarketHistory } from '../hooks/useMarkets';
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from 'recharts';

export const MarketCards: React.FC = () => {
  const { data: markets, isLoading, error } = useMarkets();
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const { data: history } = useMarketHistory(selectedSymbol || '');

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-gray-400">Loading market data...</p>
        </div>
      </div>
    );
  }

  if (error || !markets) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-red-400">
          Error loading market data
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

  // Format volume for display
  const formatVolume = (volume: number) => {
    if (volume >= 1_000_000_000) return `$${(volume / 1_000_000_000).toFixed(1)}B`;
    if (volume >= 1_000_000) return `$${(volume / 1_000_000).toFixed(1)}M`;
    return `$${(volume / 1_000).toFixed(0)}K`;
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4 text-blue-400">Market Data</h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {markets.map((market) => (
          <div 
            key={market.symbol}
            className="bg-gray-700 p-4 rounded-lg cursor-pointer hover:bg-gray-600 transition-shadow"
            onClick={() => setSelectedSymbol(market.symbol)}
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-medium text-white">{market.symbol}</h3>
              <span 
                className={`text-sm px-2 py-0.5 rounded ${
                  market.change_pct >= 0 ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                }`}
              >
                {formatPercentage(market.change_pct)}
              </span>
            </div>
            
            <div className="flex justify-between items-baseline">
              <p className="text-xl font-bold text-gray-200">{formatCurrency(market.price)}</p>
              <p className="text-gray-400 text-sm">Vol: {formatVolume(market.volume)}</p>
            </div>
            
            <div className="h-16 mt-2">
              {market.symbol === selectedSymbol && history ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <YAxis domain={['dataMin', 'dataMax']} hide={true} />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke={market.change_pct >= 0 ? '#4ade80' : '#f87171'} 
                      dot={false} 
                      strokeWidth={1.5} 
                    />
                    <Tooltip 
                      formatter={(value: number) => [formatCurrency(value), 'Price']}
                      labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                      contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <p className="text-xs">Click for chart</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 
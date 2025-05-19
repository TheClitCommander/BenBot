import React from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

const LiveMarketData: React.FC = () => {
  const { marketData, status } = useWebSocketContext();
  
  if (status !== 'connected' || !marketData) {
    return (
      <div className="p-4 border rounded-lg bg-gray-50">
        <h2 className="text-lg font-semibold mb-2">Live Market Data</h2>
        <div className="text-gray-400">
          {status === 'connected' ? 'Waiting for data...' : 'WebSocket disconnected'}
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold">Live Market Data</h2>
        <div className="text-xs text-gray-400">
          Last update: {new Date(marketData.timestamp * 1000).toLocaleTimeString()}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(marketData.market_data).map(([symbol, data]) => (
          <div key={symbol} className="border rounded-md p-3 shadow-sm">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">{symbol}</h3>
              <div className="text-xs bg-gray-100 px-2 py-1 rounded">
                Vol: {data.volume.toLocaleString()}
              </div>
            </div>
            <div className="text-2xl font-bold mt-2">
              ${data.price.toFixed(2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LiveMarketData; 
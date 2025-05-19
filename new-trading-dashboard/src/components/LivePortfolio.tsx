import React from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

const LivePortfolio: React.FC = () => {
  const { portfolioData, status } = useWebSocketContext();
  
  if (status !== 'connected' || !portfolioData) {
    return (
      <div className="p-4 border rounded-lg bg-gray-50">
        <h2 className="text-lg font-semibold mb-2">Portfolio Overview</h2>
        <div className="text-gray-400">
          {status === 'connected' ? 'Waiting for data...' : 'WebSocket disconnected'}
        </div>
      </div>
    );
  }
  
  const { portfolio } = portfolioData;
  const isProfitable = portfolio.day_pnl >= 0;
  
  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold">Portfolio Overview</h2>
        <div className="text-xs text-gray-400">
          Last update: {new Date(portfolioData.timestamp * 1000).toLocaleTimeString()}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
        <div>
          <div className="text-sm text-gray-500 mb-1">Total Value</div>
          <div className="text-3xl font-bold">${portfolio.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        
        <div>
          <div className="text-sm text-gray-500 mb-1">Day P&L</div>
          <div className={`text-3xl font-bold flex items-center ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
            {isProfitable ? '+' : ''}
            ${portfolio.day_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span className="text-base ml-2">
              ({isProfitable ? '+' : ''}
              {portfolio.day_pnl_percent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-500 mb-1">Cash</div>
          <div className="text-xl font-semibold">${portfolio.cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-500 mb-1">Positions Value</div>
          <div className="text-xl font-semibold">${portfolio.positions_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
      </div>
    </div>
  );
};

export default LivePortfolio; 
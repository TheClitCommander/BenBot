import React from 'react';
import { usePositions, useClosePosition } from '../hooks/usePositions';

export const PositionsTable: React.FC = () => {
  const { data: positions, isLoading, error } = usePositions();
  const closePositionMutation = useClosePosition();

  const handleClosePosition = (positionId: string) => {
    if (confirm('Are you sure you want to close this position?')) {
      closePositionMutation.mutate(positionId);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-gray-400">Loading positions...</p>
        </div>
      </div>
    );
  }

  if (error || !positions) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-red-400">
          Error loading position data
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

  if (positions.length === 0) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className="text-gray-400">No active positions</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4 text-blue-400">Active Positions</h2>
      
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Symbol</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Side</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Size</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Entry Price</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Current Price</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">P&L</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Age</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => (
              <tr key={position.id} className="border-b border-gray-700">
                <td className="px-4 py-3 text-gray-300">{position.symbol}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-md ${
                    position.side === 'LONG' 
                      ? 'bg-green-900 text-green-300' 
                      : 'bg-red-900 text-red-300'
                  }`}>
                    {position.side}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-300">{position.size}</td>
                <td className="px-4 py-3 text-gray-300">{formatCurrency(position.entry_price)}</td>
                <td className="px-4 py-3 text-gray-300">{formatCurrency(position.current_price)}</td>
                <td className={`px-4 py-3 ${position.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {position.pnl_pct >= 0 ? '+' : ''}{position.pnl_pct.toFixed(2)}% / 
                  {position.pnl_value >= 0 ? '+' : ''}{formatCurrency(position.pnl_value)}
                </td>
                <td className="px-4 py-3 text-gray-300">{position.age}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleClosePosition(position.id)}
                    className="px-3 py-1 text-xs font-medium rounded-md bg-red-900 text-red-300 hover:bg-red-800"
                    disabled={closePositionMutation.isPending}
                  >
                    {closePositionMutation.isPending ? 'Closing...' : 'Close'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}; 
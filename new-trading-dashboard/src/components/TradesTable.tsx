import React, { useState } from 'react';
import { useTrades } from '../hooks/useTrades';

export const TradesTable: React.FC = () => {
  const [limit, setLimit] = useState(20);
  const { data: trades, isLoading, error } = useTrades(limit);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const exportCSV = () => {
    if (!trades) return;
    
    const headers = ['Time', 'Symbol', 'Side', 'Size', 'Price', 'Total', 'Strategy'];
    const csvContent = [
      headers.join(','),
      ...trades.map(trade => [
        trade.time,
        trade.symbol,
        trade.side,
        trade.size,
        trade.price,
        trade.total,
        trade.strategy
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `trades_${new Date().toISOString()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-gray-400">Loading trades...</p>
        </div>
      </div>
    );
  }

  if (error || !trades) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-red-400">
          Error loading trade data
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

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-blue-400">Recent Trades</h2>
        <div className="flex space-x-2">
          <select
            className="px-3 py-1 bg-gray-700 border border-gray-600 text-gray-300 rounded-md text-sm"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          >
            <option value={10}>10 trades</option>
            <option value={20}>20 trades</option>
            <option value={50}>50 trades</option>
            <option value={100}>100 trades</option>
          </select>
          <button
            onClick={exportCSV}
            className="px-3 py-1 bg-blue-800 text-blue-300 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Export CSV
          </button>
        </div>
      </div>
      
      {trades.length === 0 ? (
        <div className="flex items-center justify-center h-48">
          <p className="text-gray-400">No trades found</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-700">
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Time</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Symbol</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Side</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Size</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Price</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Total</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Strategy</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id} className="border-b border-gray-700">
                  <td className="px-4 py-3 text-gray-300">{formatTime(trade.time)}</td>
                  <td className="px-4 py-3 text-gray-300">{trade.symbol}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 text-xs font-medium rounded-md ${
                      trade.side === 'BUY' 
                        ? 'bg-green-900 text-green-300' 
                        : 'bg-red-900 text-red-300'
                    }`}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{trade.size}</td>
                  <td className="px-4 py-3 text-gray-300">{formatCurrency(trade.price)}</td>
                  <td className="px-4 py-3 text-gray-300">{formatCurrency(trade.total)}</td>
                  <td className="px-4 py-3 text-gray-300">{trade.strategy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}; 
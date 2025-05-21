import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { Clock, Download, Filter, AlertCircle, ArrowDownUp, FileText } from 'lucide-react';

interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  size: number;
  price: number;
  total: number;
  time: string;
  strategy_id: string;
  strategy_name: string;
}

export const TradeHistory: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [symbolFilter, setSymbolFilter] = useState('');
  const [sideFilter, setSideFilter] = useState<'BUY' | 'SELL' | ''>('');
  const [dateFilter, setDateFilter] = useState('');
  
  const perPage = 10;
  
  const { data, isLoading, error } = useQuery<{trades: Trade[], total: number}>({
    queryKey: ['trades', currentPage, symbolFilter, sideFilter, dateFilter],
    queryFn: async () => {
      try {
        // In a real app, pass the filters to the API
        const response = await apiService.getTradeHistory({
          page: currentPage,
          limit: perPage,
          symbol: symbolFilter || undefined,
          side: sideFilter || undefined,
          date: dateFilter || undefined
        });
        return response.data;
      } catch (err) {
        console.error('Error fetching trade history:', err);
        throw err;
      }
    }
  });

  const trades = data?.trades || [];
  const totalTrades = data?.total || 0;
  const totalPages = Math.ceil(totalTrades / perPage);
  
  const handleExport = () => {
    console.log('Exporting trade history to CSV');
    // In a real app, this would trigger an API call to generate and download a CSV
  };
  
  const handleFilterToggle = () => {
    setShowFilters(!showFilters);
  };
  
  const applyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page when applying filters
    // The filters are already applied via the query key dependencies
  };
  
  const resetFilters = () => {
    setSymbolFilter('');
    setSideFilter('');
    setDateFilter('');
    setCurrentPage(1);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 bg-gray-200 rounded w-40"></div>
          <div className="h-8 bg-gray-200 rounded w-24"></div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="border-b border-gray-200 h-10"></div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="border-b border-gray-100 py-3 px-4 flex">
              <div className="h-5 bg-gray-200 rounded w-24 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-24 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-16 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-24 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-24"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 rounded-lg p-3 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle size={18} className="mr-2" />
          <span>Error loading trade history</span>
        </div>
      </div>
    );
  }
  
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-md font-semibold flex items-center text-gray-700">
          <Clock size={16} className="mr-2 text-indigo-500" />
          Trade History
        </h2>
        
        <div className="flex gap-2">
          <button
            className={`px-3 py-1 rounded text-sm flex items-center ${
              showFilters ? 'bg-blue-500 hover:bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            } transition-colors`}
            onClick={handleFilterToggle}
          >
            <Filter size={14} className="mr-1" />
            Filters
          </button>
          
          <button
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-sm flex items-center transition-colors"
            onClick={handleExport}
          >
            <Download size={14} className="mr-1" />
            Export
          </button>
        </div>
      </div>
      
      {showFilters && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <form onSubmit={applyFilters} className="flex flex-wrap gap-3">
            <div className="w-full sm:w-auto">
              <label htmlFor="symbol-filter" className="block text-xs font-medium mb-1 text-gray-700">Symbol</label>
              <input
                id="symbol-filter"
                type="text"
                className="w-full sm:w-32 px-3 py-1.5 text-sm border border-gray-300 rounded"
                placeholder="e.g. BTCUSDT"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
              />
            </div>
            
            <div className="w-full sm:w-auto">
              <label htmlFor="side-filter" className="block text-xs font-medium mb-1 text-gray-700">Side</label>
              <select
                id="side-filter"
                className="w-full sm:w-32 px-3 py-1.5 text-sm border border-gray-300 rounded"
                value={sideFilter}
                onChange={(e) => setSideFilter(e.target.value as any)}
              >
                <option value="">All</option>
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
              </select>
            </div>
            
            <div className="w-full sm:w-auto">
              <label htmlFor="date-filter" className="block text-xs font-medium mb-1 text-gray-700">Date</label>
              <input
                id="date-filter"
                type="date"
                className="w-full sm:w-40 px-3 py-1.5 text-sm border border-gray-300 rounded"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              />
            </div>
            
            <div className="w-full sm:w-auto flex items-end gap-2">
              <button
                type="submit"
                className="px-4 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition-colors"
              >
                Apply
              </button>
              <button
                type="button"
                className="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 rounded text-sm transition-colors"
                onClick={resetFilters}
              >
                Reset
              </button>
            </div>
          </form>
        </div>
      )}
      
      {trades.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Side</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3">Strategy</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {trades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{new Date(trade.time).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm font-medium">{trade.symbol}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                        ${trade.side === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
                      >
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{trade.size}</td>
                    <td className="px-4 py-3 text-sm">${trade.price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm">${trade.total.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm">{trade.strategy_name}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      <button
                        className="p-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                        title="View Details"
                        onClick={() => console.log(`View details for trade ${trade.id}`)}
                      >
                        <FileText size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-xs text-gray-600">
              Showing {Math.min((currentPage - 1) * perPage + 1, totalTrades)} to {Math.min(currentPage * perPage, totalTrades)} of {totalTrades} trades
            </div>
            
            <div className="flex gap-1">
              <button
                className="px-3 py-1 bg-white border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                Previous
              </button>
              
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNumber = currentPage > 3 && totalPages > 5
                  ? currentPage - 3 + i + (currentPage + 2 > totalPages ? totalPages - currentPage - 2 : 0)
                  : i + 1;
                
                if (pageNumber <= totalPages) {
                  return (
                    <button
                      key={pageNumber}
                      className={`w-8 h-8 flex items-center justify-center rounded text-sm ${
                        currentPage === pageNumber
                          ? 'bg-blue-500 text-white'
                          : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setCurrentPage(pageNumber)}
                    >
                      {pageNumber}
                    </button>
                  );
                }
                return null;
              })}
              
              <button
                className="px-3 py-1 bg-white border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={currentPage === totalPages || totalPages === 0}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 rounded-lg p-8 border border-gray-200 text-center">
          <h3 className="text-lg font-medium text-gray-700 mb-2">No trades found</h3>
          <p className="text-gray-500">
            {symbolFilter || sideFilter || dateFilter 
              ? 'Try adjusting your filters to see more results'
              : 'No trade history available yet'}
          </p>
          {(symbolFilter || sideFilter || dateFilter) && (
            <button 
              className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
              onClick={resetFilters}
            >
              Clear Filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}; 
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import {
  LineChart,
  Search,
  ChevronDown,
  AlertCircle,
  Star,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

interface Market {
  symbol: string;
  name: string;
  price: number;
  price_change_24h: number;
  price_change_24h_pct: number;
  volume_24h: number;
  market_cap?: number;
  is_favorite: boolean;
}

export const MarketsList: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<'all' | 'crypto' | 'forex' | 'stocks'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'change'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const { data: markets, isLoading, error } = useQuery<Market[]>({
    queryKey: ['markets'],
    queryFn: async () => {
      try {
        const response = await apiService.getMarkets();
        return response.data;
      } catch (err) {
        console.error('Error fetching markets data:', err);
        throw err;
      }
    }
  });

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="mb-4 flex justify-between items-center">
          <div className="h-6 bg-gray-200 rounded w-40"></div>
          <div className="h-10 bg-gray-200 rounded w-64"></div>
        </div>
        
        <div className="flex gap-2 mb-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-200 rounded w-24"></div>
          ))}
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="border-b border-gray-200 h-10"></div>
          {[...Array(8)].map((_, i) => (
            <div key={i} className="border-b border-gray-100 py-3 px-4 flex">
              <div className="h-5 bg-gray-200 rounded w-32 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-24 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-16 mr-4"></div>
              <div className="h-5 bg-gray-200 rounded w-24"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  if (error || !markets) {
    return (
      <div className="bg-red-50 rounded-lg p-3 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle size={18} className="mr-2" />
          <span>Error loading markets data</span>
        </div>
      </div>
    );
  }
  
  const handleSort = (column: 'name' | 'price' | 'change') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };
  
  const handleToggleFavorite = (symbol: string) => {
    console.log(`Toggle favorite for ${symbol}`);
    // In a real app, this would call an API to update favorites
  };
  
  let filteredMarkets = [...markets];
  
  // Filter by category
  if (activeCategory !== 'all') {
    filteredMarkets = filteredMarkets.filter(market => {
      if (activeCategory === 'crypto') {
        return market.symbol.endsWith('USDT') || market.symbol.endsWith('BTC');
      } else if (activeCategory === 'forex') {
        return /^[A-Z]{6}$/.test(market.symbol);
      } else if (activeCategory === 'stocks') {
        return !market.symbol.endsWith('USDT') && !market.symbol.endsWith('BTC') && !/^[A-Z]{6}$/.test(market.symbol);
      }
      return true;
    });
  }
  
  // Filter by search query
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    filteredMarkets = filteredMarkets.filter(
      market => market.symbol.toLowerCase().includes(query) || market.name.toLowerCase().includes(query)
    );
  }
  
  // Sort markets
  filteredMarkets.sort((a, b) => {
    if (sortBy === 'name') {
      return sortOrder === 'asc' 
        ? a.symbol.localeCompare(b.symbol) 
        : b.symbol.localeCompare(a.symbol);
    } else if (sortBy === 'price') {
      return sortOrder === 'asc' 
        ? a.price - b.price 
        : b.price - a.price;
    } else {
      // Sort by % change
      return sortOrder === 'asc' 
        ? a.price_change_24h_pct - b.price_change_24h_pct
        : b.price_change_24h_pct - a.price_change_24h_pct;
    }
  });
  
  return (
    <div>
      <div className="mb-4 flex flex-col md:flex-row md:justify-between md:items-center gap-3">
        <h2 className="text-md font-semibold flex items-center text-gray-700">
          <LineChart size={16} className="mr-2 text-blue-500" />
          Markets
        </h2>
        
        <div className="relative">
          <input
            type="text"
            placeholder="Search markets..."
            className="w-full md:w-64 pl-9 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
          <Search className="absolute left-3 top-2.5 text-gray-400" size={15} />
        </div>
      </div>
      
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          className={`px-4 py-1.5 rounded text-sm font-medium ${
            activeCategory === 'all' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          onClick={() => setActiveCategory('all')}
        >
          All Markets
        </button>
        <button
          className={`px-4 py-1.5 rounded text-sm font-medium ${
            activeCategory === 'crypto' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          onClick={() => setActiveCategory('crypto')}
        >
          Crypto
        </button>
        <button
          className={`px-4 py-1.5 rounded text-sm font-medium ${
            activeCategory === 'forex' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          onClick={() => setActiveCategory('forex')}
        >
          Forex
        </button>
        <button
          className={`px-4 py-1.5 rounded text-sm font-medium ${
            activeCategory === 'stocks' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          onClick={() => setActiveCategory('stocks')}
        >
          Stocks
        </button>
      </div>
      
      {filteredMarkets.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-xs font-medium text-gray-700 uppercase tracking-wider">
                  <th className="py-3 px-4 text-left">
                    <div className="flex items-center">
                      <button
                        className="flex items-center focus:outline-none"
                        onClick={() => handleSort('name')}
                      >
                        Market
                        <ChevronDown 
                          size={14} 
                          className={`ml-1 ${sortBy === 'name' ? 'text-blue-500' : 'text-gray-400'} ${
                            sortBy === 'name' && sortOrder === 'desc' ? 'transform rotate-180' : ''
                          }`}
                        />
                      </button>
                    </div>
                  </th>
                  <th className="py-3 px-4 text-right">
                    <button
                      className="flex items-center ml-auto focus:outline-none"
                      onClick={() => handleSort('price')}
                    >
                      Price
                      <ChevronDown 
                        size={14} 
                        className={`ml-1 ${sortBy === 'price' ? 'text-blue-500' : 'text-gray-400'} ${
                          sortBy === 'price' && sortOrder === 'desc' ? 'transform rotate-180' : ''
                        }`}
                      />
                    </button>
                  </th>
                  <th className="py-3 px-4 text-right">
                    <button
                      className="flex items-center ml-auto focus:outline-none"
                      onClick={() => handleSort('change')}
                    >
                      24h Change
                      <ChevronDown 
                        size={14} 
                        className={`ml-1 ${sortBy === 'change' ? 'text-blue-500' : 'text-gray-400'} ${
                          sortBy === 'change' && sortOrder === 'desc' ? 'transform rotate-180' : ''
                        }`}
                      />
                    </button>
                  </th>
                  <th className="py-3 px-4 text-right">24h Volume</th>
                  <th className="py-3 px-4 text-right">Chart</th>
                  <th className="py-3 px-4 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredMarkets.map(market => (
                  <tr key={market.symbol} className="hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex flex-col">
                        <span className="font-medium text-sm">{market.symbol}</span>
                        <span className="text-xs text-gray-500">{market.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      ${market.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className={`inline-flex items-center ${market.price_change_24h_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {market.price_change_24h_pct >= 0 ? (
                          <ArrowUpRight size={14} className="mr-1" />
                        ) : (
                          <ArrowDownRight size={14} className="mr-1" />
                        )}
                        {Math.abs(market.price_change_24h_pct).toFixed(2)}%
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      ${market.volume_24h.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="h-6 w-20 bg-gray-100 rounded inline-flex items-center justify-center text-xs ml-auto">
                        {market.price_change_24h_pct >= 0 ? (
                          <TrendingUp size={14} className="text-green-500" />
                        ) : (
                          <TrendingDown size={14} className="text-red-500" />
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        className="hover:bg-gray-100 p-1 rounded-full transition-colors focus:outline-none"
                        onClick={() => handleToggleFavorite(market.symbol)}
                      >
                        <Star 
                          size={16} 
                          className={market.is_favorite ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'} 
                        />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
          <h3 className="text-lg font-medium text-gray-700 mb-2">No markets found</h3>
          <p className="text-gray-500">Try adjusting your search or filters</p>
          {searchQuery && (
            <button
              className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition-colors"
              onClick={() => setSearchQuery('')}
            >
              Clear Search
            </button>
          )}
        </div>
      )}
    </div>
  );
}; 
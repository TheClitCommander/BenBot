import { useState } from 'react';
import TradingViewChart from './TradingViewChart';
import OrderBook from './OrderBook';
import OrderForm from './OrderForm';
import { apiService } from '../api/client';
import { useQuery } from '@tanstack/react-query';

interface MarketDetailProps {
  initialSymbol?: string;
}

const MarketDetail: React.FC<MarketDetailProps> = ({ initialSymbol = 'BTCUSDT' }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>(initialSymbol);
  const [chartInterval, setChartInterval] = useState<string>('60');
  
  // Fetch available markets for the dropdown
  const { data: markets } = useQuery({
    queryKey: ['markets'],
    queryFn: async () => {
      const response = await apiService.getMarketData();
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
  
  // Fetch market details
  const { data: marketDetail, isLoading } = useQuery({
    queryKey: ['marketDetail', selectedSymbol],
    queryFn: async () => {
      // This would be a real API call in production
      const marketList = await apiService.getMarketData();
      return marketList.data.find((m: any) => m.symbol === selectedSymbol);
    },
    staleTime: 30000, // 30 seconds
  });
  
  // Format price change with color
  const formatPriceChange = (change: number) => {
    const colorClass = change >= 0 ? 'text-green-600' : 'text-red-600';
    const prefix = change >= 0 ? '+' : '';
    return (
      <span className={colorClass}>
        {prefix}{change.toFixed(2)}%
      </span>
    );
  };
  
  // Handle interval change
  const handleIntervalChange = (interval: string) => {
    setChartInterval(interval);
  };
  
  return (
    <div className="h-full flex flex-col">
      {/* Market selector and info */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="mr-2 px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {markets?.map((market: any) => (
              <option key={market.symbol} value={market.symbol}>
                {market.symbol}
              </option>
            ))}
          </select>
          
          {marketDetail && (
            <div className="text-sm">
              <span className="font-semibold mr-2">{marketDetail.price.toFixed(2)}</span>
              {formatPriceChange(marketDetail.change_pct)}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-1 text-xs">
          {['15', '60', '240', 'D'].map((interval) => (
            <button
              key={interval}
              onClick={() => handleIntervalChange(interval)}
              className={`px-2 py-1 rounded ${
                chartInterval === interval 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {interval === 'D' ? '1D' : `${interval}m`}
            </button>
          ))}
        </div>
      </div>
      
      {/* Main content grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 overflow-hidden">
        {/* Chart */}
        <div className="col-span-8 bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <TradingViewChart 
            symbol={selectedSymbol} 
            interval={chartInterval} 
            autosize={true} 
          />
        </div>
        
        {/* Right sidebar - Order book and form */}
        <div className="col-span-4 grid grid-rows-2 gap-4">
          {/* Order book */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 overflow-hidden">
            <OrderBook symbol={selectedSymbol} maxDepth={10} />
          </div>
          
          {/* Order form */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 overflow-hidden">
            <OrderForm symbol={selectedSymbol} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketDetail; 
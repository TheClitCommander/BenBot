import { useState, useEffect } from 'react';
import { apiService } from '../api/client';

interface OrderBookEntry {
  price: number;
  size: number;
  total: number;
}

interface OrderBookProps {
  symbol: string;
  maxDepth?: number;
}

const OrderBook = ({ symbol = 'BTCUSDT', maxDepth = 10 }: OrderBookProps) => {
  const [asks, setAsks] = useState<OrderBookEntry[]>([]);
  const [bids, setBids] = useState<OrderBookEntry[]>([]);
  const [spread, setSpread] = useState<number>(0);
  const [spreadPercent, setSpreadPercent] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch and process order book data
  useEffect(() => {
    let intervalId: number;
    
    const fetchOrderBook = async () => {
      try {
        setLoading(true);
        
        // In a real app, this would be a WebSocket connection
        // For now, simulate with random data
        const res = await apiService.getOrderBook(symbol);
        
        if (res.data) {
          // Process asks (sell orders) - higher price = worse for buyer
          const processedAsks = res.data.asks.slice(0, maxDepth).map((ask: [number, number], index: number) => {
            const [price, size] = ask;
            const total = index === 0 ? size : res.data.asks.slice(0, index + 1).reduce((acc: number, item: [number, number]) => acc + item[1], 0);
            return { price, size, total };
          });
          
          // Process bids (buy orders) - lower price = worse for seller
          const processedBids = res.data.bids.slice(0, maxDepth).map((bid: [number, number], index: number) => {
            const [price, size] = bid;
            const total = index === 0 ? size : res.data.bids.slice(0, index + 1).reduce((acc: number, item: [number, number]) => acc + item[1], 0);
            return { price, size, total };
          });
          
          setAsks(processedAsks);
          setBids(processedBids);
          
          // Calculate spread
          if (processedAsks.length > 0 && processedBids.length > 0) {
            const lowestAsk = processedAsks[0].price;
            const highestBid = processedBids[0].price;
            const calculatedSpread = lowestAsk - highestBid;
            setSpread(calculatedSpread);
            setSpreadPercent((calculatedSpread / lowestAsk) * 100);
          }
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching order book:', error);
        setLoading(false);
      }
    };
    
    // Initial fetch
    fetchOrderBook();
    
    // Set up polling interval (simulating WebSocket)
    intervalId = window.setInterval(fetchOrderBook, 2000);
    
    // Clean up on unmount
    return () => {
      clearInterval(intervalId);
    };
  }, [symbol, maxDepth]);

  // Format price with appropriate decimals
  const formatPrice = (price: number): string => {
    return price < 1 ? price.toFixed(6) : price < 10 ? price.toFixed(4) : price < 1000 ? price.toFixed(2) : price.toFixed(1);
  };
  
  // Format size for display
  const formatSize = (size: number): string => {
    return size < 1 ? size.toFixed(4) : size < 10 ? size.toFixed(2) : size.toFixed(1);
  };

  // Scale for the depth visualization
  const maxTotal = Math.max(
    ...[...asks, ...bids].map(item => item.total)
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-2 text-xs text-gray-500">
        <div>Order Book</div>
        <div className="text-xs">
          <span className="font-semibold text-gray-700">Spread:</span>
          <span className="ml-1">{formatPrice(spread)} ({spreadPercent.toFixed(3)}%)</span>
        </div>
      </div>
      
      <div className="flex flex-col flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-700"></div>
          </div>
        ) : (
          <>
            {/* Asks (Sell Orders) */}
            <div className="flex-1 overflow-y-auto scrollbar-thin mb-1">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-white">
                  <tr className="text-gray-500">
                    <th className="text-left pl-1 py-1">Price</th>
                    <th className="text-right">Size</th>
                    <th className="text-right pr-1">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {asks.map((ask, index) => (
                    <tr key={`ask-${index}`} className="relative">
                      {/* Background depth indicator */}
                      <td className="absolute inset-0 z-0">
                        <div 
                          className="h-full bg-red-100"
                          style={{ 
                            width: `${(ask.total / maxTotal) * 100}%`,
                            marginLeft: 'auto'
                          }}
                        />
                      </td>
                      {/* Data cells */}
                      <td className="pl-1 py-1 text-red-600 relative z-10 font-mono">{formatPrice(ask.price)}</td>
                      <td className="text-right relative z-10 font-mono">{formatSize(ask.size)}</td>
                      <td className="text-right pr-1 relative z-10 font-mono">{formatSize(ask.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Bids (Buy Orders) */}
            <div className="flex-1 overflow-y-auto scrollbar-thin mt-1">
              <table className="w-full text-xs">
                <tbody>
                  {bids.map((bid, index) => (
                    <tr key={`bid-${index}`} className="relative">
                      {/* Background depth indicator */}
                      <td className="absolute inset-0 z-0">
                        <div 
                          className="h-full bg-green-100"
                          style={{ 
                            width: `${(bid.total / maxTotal) * 100}%`
                          }}
                        />
                      </td>
                      {/* Data cells */}
                      <td className="pl-1 py-1 text-green-600 relative z-10 font-mono">{formatPrice(bid.price)}</td>
                      <td className="text-right relative z-10 font-mono">{formatSize(bid.size)}</td>
                      <td className="text-right pr-1 relative z-10 font-mono">{formatSize(bid.total)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="sticky bottom-0 bg-white">
                  <tr className="text-gray-500">
                    <th className="text-left pl-1 py-1">Price</th>
                    <th className="text-right">Size</th>
                    <th className="text-right pr-1">Total</th>
                  </tr>
                </tfoot>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default OrderBook; 
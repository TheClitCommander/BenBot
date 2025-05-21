import { useState, useEffect } from 'react';
import { apiService } from '../api/client';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface OrderFormProps {
  symbol: string;
  initialSide?: 'BUY' | 'SELL';
  initialType?: 'LIMIT' | 'MARKET';
}

const OrderForm = ({ 
  symbol = 'BTCUSDT', 
  initialSide = 'BUY', 
  initialType = 'LIMIT' 
}: OrderFormProps) => {
  const [side, setSide] = useState<'BUY' | 'SELL'>(initialSide);
  const [type, setType] = useState<'LIMIT' | 'MARKET'>(initialType);
  const [price, setPrice] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [total, setTotal] = useState<string>('');
  const [marketPrice, setMarketPrice] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{text: string, type: 'success' | 'error' | 'info'} | null>(null);
  
  const queryClient = useQueryClient();
  
  // Get current market price
  useEffect(() => {
    const fetchMarketPrice = async () => {
      try {
        const res = await apiService.getMarketData();
        if (res.data) {
          const market = res.data.find((m: any) => m.symbol === symbol);
          if (market) {
            setMarketPrice(market.price);
            // Set default price to current market price
            if (!price) {
              setPrice(market.price.toString());
            }
          }
        }
      } catch (error) {
        console.error('Error fetching market price:', error);
      }
    };
    
    fetchMarketPrice();
    
    // Set up interval to update price periodically
    const intervalId = setInterval(fetchMarketPrice, 10000);
    
    return () => clearInterval(intervalId);
  }, [symbol]);
  
  // Calculate total when price or amount changes
  useEffect(() => {
    if (price && amount) {
      const calculatedTotal = parseFloat(price) * parseFloat(amount);
      setTotal(calculatedTotal.toString());
    } else {
      setTotal('');
    }
  }, [price, amount]);
  
  // Handle price change based on amount and total
  const handlePriceChange = (value: string) => {
    setPrice(value);
    if (value && amount) {
      const calculatedTotal = parseFloat(value) * parseFloat(amount);
      setTotal(calculatedTotal.toFixed(2));
    }
  };
  
  // Handle amount change based on price and total
  const handleAmountChange = (value: string) => {
    setAmount(value);
    if (value && price) {
      const calculatedTotal = parseFloat(price) * parseFloat(value);
      setTotal(calculatedTotal.toFixed(2));
    }
  };
  
  // Handle total change based on price and amount
  const handleTotalChange = (value: string) => {
    setTotal(value);
    if (value && price && parseFloat(price) > 0) {
      const calculatedAmount = parseFloat(value) / parseFloat(price);
      setAmount(calculatedAmount.toFixed(8));
    }
  };

  // Submit order mutation
  const placeOrderMutation = useMutation({
    mutationFn: async (orderData: any) => {
      return await apiService.placeOrder(orderData);
    },
    onSuccess: () => {
      // Reset form
      setAmount('');
      setTotal('');
      
      // Show success message
      setMessage({
        text: `Order successfully placed`,
        type: 'success'
      });
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000);
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
    onError: (error) => {
      setMessage({
        text: `Error placing order: ${error}`,
        type: 'error'
      });
      
      // Clear message after 5 seconds
      setTimeout(() => setMessage(null), 5000);
    }
  });

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      setMessage({
        text: 'Please enter a valid amount',
        type: 'error'
      });
      return;
    }
    
    if (type === 'LIMIT' && (!price || parseFloat(price) <= 0)) {
      setMessage({
        text: 'Please enter a valid price',
        type: 'error'
      });
      return;
    }
    
    // Prepare order data
    const orderData = {
      symbol,
      side,
      type,
      amount: parseFloat(amount),
      price: type === 'MARKET' ? undefined : parseFloat(price),
    };
    
    // Submit order
    placeOrderMutation.mutate(orderData);
  };
  
  // Calculate button color based on side
  const buttonColorClass = side === 'BUY' 
    ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500' 
    : 'bg-red-600 hover:bg-red-700 focus:ring-red-500';

  return (
    <div className="h-full flex flex-col">
      {/* Tabs for Buy/Sell */}
      <div className="flex mb-4 border-b">
        <button
          className={`flex-1 py-2 text-sm font-medium ${
            side === 'BUY' 
              ? 'text-green-600 border-b-2 border-green-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setSide('BUY')}
        >
          Buy
        </button>
        <button
          className={`flex-1 py-2 text-sm font-medium ${
            side === 'SELL' 
              ? 'text-red-600 border-b-2 border-red-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setSide('SELL')}
        >
          Sell
        </button>
      </div>
      
      {/* Order Type Selector */}
      <div className="flex mb-4">
        <button
          className={`flex-1 py-1 text-xs font-medium rounded-l-md border ${
            type === 'LIMIT' 
              ? 'bg-blue-50 text-blue-600 border-blue-600' 
              : 'text-gray-500 border-gray-300 hover:bg-gray-50'
          }`}
          onClick={() => setType('LIMIT')}
        >
          Limit
        </button>
        <button
          className={`flex-1 py-1 text-xs font-medium rounded-r-md border ${
            type === 'MARKET' 
              ? 'bg-blue-50 text-blue-600 border-blue-600' 
              : 'text-gray-500 border-gray-300 hover:bg-gray-50'
          }`}
          onClick={() => setType('MARKET')}
        >
          Market
        </button>
      </div>
      
      {/* Order Form */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        {/* Price Input - Only for Limit Orders */}
        {type === 'LIMIT' && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Price
            </label>
            <div className="relative">
              <input
                type="text"
                value={price}
                onChange={(e) => handlePriceChange(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="0.00"
                required={type === 'LIMIT'}
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <span className="text-gray-500 sm:text-sm">USDT</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Amount Input */}
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Amount
          </label>
          <div className="relative">
            <input
              type="text"
              value={amount}
              onChange={(e) => handleAmountChange(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="0.00"
              required
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <span className="text-gray-500 sm:text-sm">{symbol.replace('USDT', '')}</span>
            </div>
          </div>
        </div>
        
        {/* Total Input */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Total
          </label>
          <div className="relative">
            <input
              type="text"
              value={total}
              onChange={(e) => handleTotalChange(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="0.00"
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <span className="text-gray-500 sm:text-sm">USDT</span>
            </div>
          </div>
        </div>
        
        {/* Submit Button */}
        <button
          type="submit"
          disabled={placeOrderMutation.isPending || isLoading}
          className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${buttonColorClass} ${
            placeOrderMutation.isPending || isLoading ? 'opacity-70 cursor-not-allowed' : ''
          }`}
        >
          {placeOrderMutation.isPending || isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </span>
          ) : (
            `${side === 'BUY' ? 'Buy' : 'Sell'} ${symbol.replace('USDT', '')}`
          )}
        </button>
      </form>
      
      {/* Status Message */}
      {message && (
        <div className={`mt-3 p-2 rounded text-sm ${
          message.type === 'success' ? 'bg-green-50 text-green-700' :
          message.type === 'error' ? 'bg-red-50 text-red-700' :
          'bg-blue-50 text-blue-700'
        }`}>
          {message.text}
        </div>
      )}
    </div>
  );
};

export default OrderForm; 
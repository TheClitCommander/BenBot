import { useState } from 'react';
import { useTradierOrder } from '../hooks/useTradierOrder';
import { useTradierQuote } from '../hooks/useTradierQuote';

interface TradierOrderFormProps {
  defaultSymbol?: string;
  defaultAccountId?: string;
  onOrderSubmitted?: (orderData: any) => void;
}

export default function TradierOrderForm({
  defaultSymbol = 'AAPL',
  defaultAccountId = '',
  onOrderSubmitted
}: TradierOrderFormProps) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [accountId, setAccountId] = useState(defaultAccountId);
  const [qty, setQty] = useState(1);
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  
  const { data: quoteData } = useTradierQuote(symbol);
  const orderMutation = useTradierOrder();
  const { mutate: submitOrder } = orderMutation;
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!accountId) {
      alert('Please enter your Tradier account ID');
      return;
    }
    
    const orderData = {
      account_id: accountId,
      symbol,
      qty,
      side
    };
    
    submitOrder(orderData, {
      onSuccess: (data) => {
        console.log('Order submitted successfully:', data);
        if (onOrderSubmitted) onOrderSubmitted(data);
        
        // Reset form
        setQty(1);
      }
    });
  };
  
  return (
    <div className="border border-gray-300 rounded-lg p-4">
      <h3 className="text-lg font-medium mb-4">Tradier Order Form</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Account ID</label>
            <input
              type="text"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="Enter Tradier account ID"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="AAPL"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
            <input
              type="number"
              value={qty}
              onChange={(e) => setQty(parseInt(e.target.value) || 1)}
              min="1"
              className="w-full border border-gray-300 rounded px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Side</label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="side"
                  checked={side === 'buy'}
                  onChange={() => setSide('buy')}
                  className="mr-2"
                />
                Buy
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="side"
                  checked={side === 'sell'}
                  onChange={() => setSide('sell')}
                  className="mr-2"
                />
                Sell
              </label>
            </div>
          </div>
          
          {quoteData && (
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm">
                <span className="font-medium">Current price:</span>{' '}
                <span className="font-bold">${quoteData.last.toFixed(2)}</span>
              </div>
              
              <div className="text-sm mt-1">
                <span className="font-medium">Estimated total:</span>{' '}
                <span className="font-bold">${(quoteData.last * qty).toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>
        
        {orderMutation.isError && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
            Error: {orderMutation.error instanceof Error ? orderMutation.error.message : 'Failed to submit order'}
          </div>
        )}
        
        <button
          type="submit"
          disabled={orderMutation.isPending}
          className={`w-full py-2 px-4 rounded ${
            side === 'buy' 
              ? 'bg-green-600 text-white hover:bg-green-700' 
              : 'bg-red-600 text-white hover:bg-red-700'
          } ${orderMutation.isPending ? 'opacity-70 cursor-not-allowed' : ''}`}
        >
          {orderMutation.isPending ? 'Submitting...' : `${side === 'buy' ? 'Buy' : 'Sell'} ${symbol}`}
        </button>
      </form>
    </div>
  );
} 
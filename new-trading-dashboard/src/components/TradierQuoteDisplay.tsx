import { useTradierQuote } from '../hooks/useTradierQuote';
import { useState } from 'react';

interface TradierQuoteDisplayProps {
  defaultSymbol?: string;
}

export default function TradierQuoteDisplay({ defaultSymbol = 'AAPL' }: TradierQuoteDisplayProps) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [inputSymbol, setInputSymbol] = useState(defaultSymbol);
  const { data, isLoading, error } = useTradierQuote(symbol);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSymbol(inputSymbol.toUpperCase());
  };

  if (isLoading) return <div className="p-4 bg-gray-100 rounded-lg">Loading quote...</div>;
  if (error) return <div className="p-4 bg-red-100 rounded-lg">Error loading quote</div>;
  
  return (
    <div className="p-4 border border-gray-300 rounded-lg">
      <form onSubmit={handleSubmit} className="mb-4 flex">
        <input
          type="text"
          value={inputSymbol}
          onChange={(e) => setInputSymbol(e.target.value)}
          className="border border-gray-300 rounded-l px-3 py-2 flex-1"
          placeholder="Enter symbol"
        />
        <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded-r">
          Fetch
        </button>
      </form>
      
      {data && (
        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-xl font-semibold">{data.symbol}</h3>
            <span className={`text-xl font-bold ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${data.last.toFixed(2)}
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">Change:</span>{' '}
              <span className={data.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)} ({data.change_percentage.toFixed(2)}%)
              </span>
            </div>
            <div>
              <span className="text-gray-500">Volume:</span> {data.volume.toLocaleString()}
            </div>
            <div>
              <span className="text-gray-500">Open:</span> ${data.open.toFixed(2)}
            </div>
            <div>
              <span className="text-gray-500">Prev Close:</span> ${data.prevclose.toFixed(2)}
            </div>
            <div>
              <span className="text-gray-500">High:</span> ${data.high.toFixed(2)}
            </div>
            <div>
              <span className="text-gray-500">Low:</span> ${data.low.toFixed(2)}
            </div>
            <div>
              <span className="text-gray-500">52w High:</span> ${data.week_52_high.toFixed(2)}
            </div>
            <div>
              <span className="text-gray-500">52w Low:</span> ${data.week_52_low.toFixed(2)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 
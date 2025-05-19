import { useState, useEffect } from 'react';
import { useTradierChains } from '../hooks/useTradierChains';

interface TradierOptionsChainProps {
  symbol: string;
}

interface OptionData {
  symbol: string;
  strike: number;
  last: number;
  change: number;
  bid: number;
  ask: number;
  volume: number;
  open_interest: number;
  option_type: string;
  expiration_date: string;
  root_symbol: string;
}

interface ChainData {
  symbol: string;
  expirations: string[];
  options: {
    option: OptionData[];
  };
}

export default function TradierOptionsChain({ symbol }: TradierOptionsChainProps) {
  const [selectedExpiration, setSelectedExpiration] = useState<string | undefined>(undefined);
  const { data, isLoading, error } = useTradierChains(symbol, selectedExpiration);
  
  // Select the first expiration date when data is loaded
  useEffect(() => {
    if (data && data.expirations && data.expirations.length > 0 && !selectedExpiration) {
      setSelectedExpiration(data.expirations[0]);
    }
  }, [data, selectedExpiration]);

  if (isLoading) return <div className="p-4">Loading options chains...</div>;
  if (error) return <div className="p-4 text-red-500">Error loading options data</div>;
  if (!data) return <div className="p-4">No options data available</div>;

  const chainData = data as ChainData;

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      <div className="bg-gray-100 p-3 border-b border-gray-300">
        <h3 className="font-medium">{symbol} Options Chain</h3>
        
        {/* Expiration date selector */}
        <div className="mt-2">
          <select 
            value={selectedExpiration} 
            onChange={e => setSelectedExpiration(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 w-full"
          >
            {chainData.expirations?.map((exp: string) => (
              <option key={exp} value={exp}>{exp}</option>
            ))}
          </select>
        </div>
      </div>
      
      {/* Options table */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
              <th className="py-2 px-3 text-left">Strike</th>
              <th className="py-2 px-3 text-left">Type</th>
              <th className="py-2 px-3 text-right">Last</th>
              <th className="py-2 px-3 text-right">Bid</th>
              <th className="py-2 px-3 text-right">Ask</th>
              <th className="py-2 px-3 text-right">Change</th>
              <th className="py-2 px-3 text-right">Vol</th>
              <th className="py-2 px-3 text-right">OI</th>
            </tr>
          </thead>
          <tbody>
            {chainData.options?.option?.map((option: OptionData, index: number) => (
              <tr 
                key={option.symbol + index} 
                className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
              >
                <td className="py-2 px-3 font-medium">${option.strike.toFixed(2)}</td>
                <td className="py-2 px-3">{option.option_type.toUpperCase()}</td>
                <td className="py-2 px-3 text-right">${option.last.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">${option.bid.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">${option.ask.toFixed(2)}</td>
                <td className={`py-2 px-3 text-right ${option.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {option.change >= 0 ? '+' : ''}{option.change.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right">{option.volume}</td>
                <td className="py-2 px-3 text-right">{option.open_interest}</td>
              </tr>
            ))}
            
            {!chainData.options?.option?.length && (
              <tr>
                <td colSpan={8} className="py-4 text-center text-gray-500">
                  No options data available for this expiration
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
} 
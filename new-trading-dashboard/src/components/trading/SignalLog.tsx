import React, { useState } from 'react';
import { BellRing, Clock, TrendingUp, TrendingDown, Filter, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import metricsApi, { Signal } from '@/services/metricsApi';

// Format currency values
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

// Format date values
const formatTime = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const SignalLog: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'buy' | 'sell' | 'executed' | 'pending'>('all');
  
  // Fetch signals data
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['signals', filter],
    queryFn: () => {
      const signalType = filter === 'buy' || filter === 'sell' ? filter : undefined;
      const executed = filter === 'executed' ? true : filter === 'pending' ? false : undefined;
      return metricsApi.getSignals(50, signalType, executed);
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  // Extract signals
  const signals = data?.success && data.data ? data.data : [];
  
  // Function to get confidence color class
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-bull';
    if (confidence >= 0.6) return 'text-warningImpact';
    return 'text-bear';
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-72 flex items-center justify-center">
        <p className="text-muted-foreground">Loading signals...</p>
      </div>
    );
  }
  
  // Error state
  if (isError || !data?.success) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Signal Log</h3>
          <button
            onClick={() => refetch()}
            className="flex items-center px-3 py-1 text-xs rounded-md bg-muted 
              text-muted-foreground hover:bg-muted/80 transition-colors"
          >
            <RefreshCw size={14} className="mr-1" />
            Retry
          </button>
        </div>
        <div className="h-72 flex items-center justify-center">
          <p className="text-bear">Error loading signals</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-medium">Signal Log</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Most recent trading signals from the system
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="relative">
            <select
              className="text-xs bg-muted px-2 py-1 rounded-md border border-border appearance-none pr-6 pl-6"
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
            >
              <option value="all">All</option>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
              <option value="executed">Executed</option>
              <option value="pending">Pending</option>
            </select>
            <Filter size={12} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
          </div>
          
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="flex items-center px-3 py-1 text-xs rounded-md bg-muted 
              text-muted-foreground hover:bg-muted/80 transition-colors"
          >
            <RefreshCw size={14} className={`mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto max-h-72 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="text-muted-foreground bg-muted/30">
            <tr>
              <th className="text-left py-2 px-3">Time</th>
              <th className="text-left py-2 px-3">Symbol</th>
              <th className="text-left py-2 px-3">Type</th>
              <th className="text-right py-2 px-3">Price</th>
              <th className="text-right py-2 px-3">Confidence</th>
              <th className="text-left py-2 px-3">Source</th>
              <th className="text-center py-2 px-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {signals.map(signal => (
              <tr key={signal.id} className="border-t border-border hover:bg-muted/10">
                <td className="py-2 px-3">
                  <div className="flex items-center">
                    <Clock size={14} className="mr-1 text-muted-foreground" />
                    {formatTime(signal.timestamp)}
                  </div>
                </td>
                <td className="py-2 px-3 font-medium">{signal.symbol}</td>
                <td className="py-2 px-3">
                  <span className={`flex items-center ${signal.type === 'buy' ? 'text-bull' : 'text-bear'}`}>
                    {signal.type === 'buy' 
                      ? <TrendingUp size={14} className="mr-1" /> 
                      : <TrendingDown size={14} className="mr-1" />
                    }
                    {signal.type.toUpperCase()}
                  </span>
                </td>
                <td className="py-2 px-3 text-right">{formatCurrency(signal.price)}</td>
                <td className="py-2 px-3 text-right">
                  <span className={`${getConfidenceColor(signal.confidence)}`}>
                    {(signal.confidence * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="py-2 px-3">{signal.source}</td>
                <td className="py-2 px-3 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs 
                    ${signal.executed 
                      ? 'bg-bull/10 text-bull' 
                      : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {signal.executed ? 'Executed' : 'Pending'}
                  </span>
                </td>
              </tr>
            ))}
            
            {signals.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-muted-foreground">
                  No signals found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SignalLog; 
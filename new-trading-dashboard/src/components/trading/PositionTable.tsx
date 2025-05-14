import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, BarChart, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import metricsApi, { Position } from '@/services/metricsApi';

// Format currency values
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

// Format percentage values
const formatPercent = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

// Format date values
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

const PositionTable: React.FC = () => {
  const [sortConfig, setSortConfig] = useState<{ key: keyof Position, direction: 'ascending' | 'descending' } | null>(null);
  
  // Fetch positions data
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['positions'],
    queryFn: () => metricsApi.getPositions(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  // Extract positions
  const positions = data?.success && data.data ? data.data : [];
  
  // Calculate overall PnL of all positions
  const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);
  
  // Sort the positions based on the sort config
  const sortedPositions = React.useMemo(() => {
    const positionsCopy = [...positions];
    if (sortConfig !== null) {
      positionsCopy.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return positionsCopy;
  }, [positions, sortConfig]);
  
  // Handle sorting when a column header is clicked
  const requestSort = (key: keyof Position) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };
  
  // Get the sort direction icon for a column
  const getSortDirectionIcon = (key: keyof Position) => {
    if (!sortConfig || sortConfig.key !== key) {
      return null;
    }
    return sortConfig.direction === 'ascending' ? '↑' : '↓';
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-72 flex items-center justify-center">
        <p className="text-muted-foreground">Loading positions...</p>
      </div>
    );
  }
  
  // Error state
  if (isError || !data?.success) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Current Positions</h3>
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
          <p className="text-bear">Error loading positions</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-medium">Current Positions</h3>
          <div className="flex items-center mt-1">
            <span className={`text-xl font-semibold ${totalPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
              {formatCurrency(totalPnL)}
            </span>
            <span className="ml-2 text-muted-foreground text-sm">
              Total P&L ({positions.length} positions)
            </span>
          </div>
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
      
      <div className="overflow-x-auto max-h-72 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="text-muted-foreground bg-muted/30">
            <tr>
              <th 
                className="text-left py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('symbol')}
              >
                Symbol {getSortDirectionIcon('symbol')}
              </th>
              <th 
                className="text-left py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('side')}
              >
                Side {getSortDirectionIcon('side')}
              </th>
              <th 
                className="text-right py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('quantity')}
              >
                Qty {getSortDirectionIcon('quantity')}
              </th>
              <th 
                className="text-right py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('entryPrice')}
              >
                Entry {getSortDirectionIcon('entryPrice')}
              </th>
              <th 
                className="text-right py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('currentPrice')}
              >
                Current {getSortDirectionIcon('currentPrice')}
              </th>
              <th 
                className="text-right py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('pnl')}
              >
                P&L {getSortDirectionIcon('pnl')}
              </th>
              <th 
                className="text-right py-2 px-3 cursor-pointer hover:bg-muted/50" 
                onClick={() => requestSort('strategy')}
              >
                Strategy {getSortDirectionIcon('strategy')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedPositions.map(position => (
              <tr key={position.id} className="border-t border-border hover:bg-muted/10">
                <td className="py-2 px-3 font-medium">{position.symbol}</td>
                <td className="py-2 px-3">
                  <span className={`flex items-center ${position.side === 'long' ? 'text-bull' : 'text-bear'}`}>
                    {position.side === 'long' 
                      ? <ArrowUpRight size={14} className="mr-1" /> 
                      : <ArrowDownRight size={14} className="mr-1" />
                    }
                    {position.side.charAt(0).toUpperCase() + position.side.slice(1)}
                  </span>
                </td>
                <td className="py-2 px-3 text-right">{position.quantity}</td>
                <td className="py-2 px-3 text-right">{formatCurrency(position.entryPrice)}</td>
                <td className="py-2 px-3 text-right">{formatCurrency(position.currentPrice)}</td>
                <td className="py-2 px-3 text-right">
                  <div className={position.pnl >= 0 ? 'text-bull' : 'text-bear'}>
                    <div>{formatCurrency(position.pnl)}</div>
                    <div className="text-xs opacity-80">{formatPercent(position.pnlPercent)}</div>
                  </div>
                </td>
                <td className="py-2 px-3 text-right">
                  <div className="flex items-center justify-end">
                    <BarChart size={14} className="mr-1 text-muted-foreground" />
                    {position.strategy}
                  </div>
                </td>
              </tr>
            ))}
            
            {positions.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-muted-foreground">
                  No open positions
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PositionTable; 
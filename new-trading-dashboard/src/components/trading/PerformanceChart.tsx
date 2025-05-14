import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Legend, ReferenceLine, Area, ComposedChart
} from 'recharts';
import { Calendar, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import metricsApi, { EquityPoint } from '@/services/metricsApi';

// Format currency values
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-card p-3 border border-border rounded-md shadow-md">
        <p className="font-medium">{new Date(data.timestamp).toLocaleDateString()}</p>
        <p className="text-sm">
          <span className="text-muted-foreground">Equity: </span>
          <span className="font-medium">{formatCurrency(data.equity)}</span>
        </p>
        <p className="text-sm">
          <span className="text-muted-foreground">Daily P&L: </span>
          <span className={`font-medium ${data.daily_pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
            {formatCurrency(data.daily_pnl)}
          </span>
        </p>
        {data.trades > 0 && (
          <>
            <p className="text-sm">
              <span className="text-muted-foreground">Trades: </span>
              <span className="font-medium">{data.trades}</span>
              {data.winningTrades !== undefined && (
                <span> ({data.winningTrades} W / {data.trades - data.winningTrades} L)</span>
              )}
            </p>
            {data.winRate !== undefined && (
              <p className="text-sm">
                <span className="text-muted-foreground">Win Rate: </span>
                <span className="font-medium">{data.winRate.toFixed(1)}%</span>
              </p>
            )}
          </>
        )}
      </div>
    );
  }
  return null;
};

interface TimeRangeButtonProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const TimeRangeButton: React.FC<TimeRangeButtonProps> = ({ label, active, onClick }) => (
  <button
    className={`px-3 py-1 text-xs rounded-full font-medium ${
      active 
        ? 'bg-primary text-primary-foreground' 
        : 'bg-muted text-muted-foreground hover:bg-muted/80'
    }`}
    onClick={onClick}
  >
    {label}
  </button>
);

// Main component
const PerformanceChart: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'7d' | '1m' | '3m' | 'ytd' | 'all'>('1m');
  
  // Convert timeRange to API format
  const getApiTimeframe = () => {
    switch (timeRange) {
      case '7d': return '1w';
      case '1m': return '1m';
      case '3m': return '3m';
      case 'ytd': {
        // Calculate start of year
        const now = new Date();
        const startOfYear = new Date(now.getFullYear(), 0, 1).toISOString();
        return 'custom';
      }
      case 'all': return 'all';
      default: return '1m';
    }
  };
  
  // Get equity curve data based on timeframe
  const { data: equityData, isLoading, isError, refetch } = useQuery({
    queryKey: ['equityCurve', timeRange],
    queryFn: async () => {
      const apiTimeframe = getApiTimeframe();
      
      // For "ytd", we need to pass start date
      if (timeRange === 'ytd') {
        const now = new Date();
        const startOfYear = new Date(now.getFullYear(), 0, 1).toISOString();
        return metricsApi.getEquityCurve('custom', startOfYear);
      }
      
      return metricsApi.getEquityCurve(apiTimeframe);
    },
    refetchInterval: 60000, // Refetch every minute
  });
  
  // Get performance summary
  const { data: summaryData } = useQuery({
    queryKey: ['performanceSummary'],
    queryFn: () => metricsApi.getPerformanceSummary(),
    refetchInterval: 60000, // Refetch every minute
  });
  
  // Extract equity curve data points
  const equityPoints = equityData?.success && equityData.data ? equityData.data : [];
  
  // Calculate total PnL
  const totalPnL = summaryData?.success && summaryData.data 
    ? summaryData.data.total_pnl
    : (equityPoints.length > 0 
      ? equityPoints[equityPoints.length - 1].total_pnl 
      : 0);
  
  // Calculate total percent change
  const totalPnLPercent = summaryData?.success && summaryData.data 
    ? summaryData.data.total_pnl_percent
    : (equityPoints.length > 0 && equityPoints[0].equity > 0
      ? (equityPoints[equityPoints.length - 1].equity / equityPoints[0].equity - 1) * 100
      : 0);
  
  // Handle loading state
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-80 flex items-center justify-center">
        <p className="text-muted-foreground">Loading performance data...</p>
      </div>
    );
  }
  
  // Handle error state
  if (isError || !equityData?.success) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Equity Curve</h3>
          <button
            onClick={() => refetch()}
            className="flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            <RefreshCw size={14} className="mr-1" />
            Retry
          </button>
        </div>
        <div className="h-80 flex items-center justify-center">
          <p className="text-bear">Error loading performance data</p>
        </div>
      </div>
    );
  }
  
  // Handle empty data
  if (equityPoints.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Equity Curve</h3>
          <div className="flex items-center space-x-2">
            <TimeRangeButton 
              label="7D" 
              active={timeRange === '7d'} 
              onClick={() => setTimeRange('7d')} 
            />
            <TimeRangeButton 
              label="1M" 
              active={timeRange === '1m'} 
              onClick={() => setTimeRange('1m')} 
            />
            <TimeRangeButton 
              label="3M" 
              active={timeRange === '3m'} 
              onClick={() => setTimeRange('3m')} 
            />
            <TimeRangeButton 
              label="YTD" 
              active={timeRange === 'ytd'} 
              onClick={() => setTimeRange('ytd')} 
            />
            <TimeRangeButton 
              label="ALL" 
              active={timeRange === 'all'} 
              onClick={() => setTimeRange('all')} 
            />
          </div>
        </div>
        <div className="h-80 flex items-center justify-center">
          <p className="text-muted-foreground">No performance data available for the selected period</p>
        </div>
      </div>
    );
  }
  
  // Get the starting equity value
  const startingEquity = equityPoints[0].equity;
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-medium">Equity Curve</h3>
          <div className="flex items-center mt-1">
            <span className={`text-xl font-semibold ${totalPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
              {formatCurrency(totalPnL)}
            </span>
            <span className="ml-2 flex items-center text-xs px-2 py-0.5 rounded-full bg-opacity-20 font-medium
              ${totalPnL >= 0 
                ? 'text-bull bg-bull/10' 
                : 'text-bear bg-bear/10'
              }"
            >
              {totalPnL >= 0 
                ? <TrendingUp size={14} className="mr-1" /> 
                : <TrendingDown size={14} className="mr-1" />
              }
              {Math.abs(totalPnLPercent).toFixed(2)}%
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <TimeRangeButton 
            label="7D" 
            active={timeRange === '7d'} 
            onClick={() => setTimeRange('7d')} 
          />
          <TimeRangeButton 
            label="1M" 
            active={timeRange === '1m'} 
            onClick={() => setTimeRange('1m')} 
          />
          <TimeRangeButton 
            label="3M" 
            active={timeRange === '3m'} 
            onClick={() => setTimeRange('3m')} 
          />
          <TimeRangeButton 
            label="YTD" 
            active={timeRange === 'ytd'} 
            onClick={() => setTimeRange('ytd')} 
          />
          <TimeRangeButton 
            label="ALL" 
            active={timeRange === 'all'} 
            onClick={() => setTimeRange('all')} 
          />
        </div>
      </div>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart 
            data={equityPoints}
            margin={{ top: 10, right: 30, left: 20, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.1)" />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getDate()}/${date.getMonth() + 1}`;
              }}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatCurrency(value)}
              domain={['dataMin - 100', 'dataMax + 100']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} />
            <ReferenceLine 
              y={startingEquity} 
              stroke="#888888" 
              strokeDasharray="3 3" 
              label={{ 
                value: "Starting Equity", 
                position: "insideBottomRight",
                fontSize: 12,
                fill: "#888888"
              }} 
            />
            <Line 
              type="monotone" 
              dataKey="equity" 
              name="Equity"
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart; 
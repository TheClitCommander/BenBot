import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import KPICard from './KPICard';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  Wallet, 
  BarChart, 
  ArrowUpDown, 
  CreditCard, 
  TrendingUp,
  Activity
} from 'lucide-react';

const PortfolioOverview: React.FC = () => {
  const { data: metricsData, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['metrics-overview'],
    queryFn: async () => {
      const response = await apiService.getMetricsOverview();
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
  
  const { data: equityCurve, isLoading: isLoadingEquity } = useQuery({
    queryKey: ['equity-curve'],
    queryFn: async () => {
      const response = await apiService.getEquityCurve(30); // 30 days
      return response.data;
    },
    staleTime: 3600000, // 1 hour
  });

  return (
    <div className="flex flex-col space-y-6">
      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Portfolio Value"
          value={isLoadingMetrics ? '–' : `$${metricsData?.portfolio_value.toLocaleString()}`}
          change={metricsData?.portfolio_change_pct}
          icon={<Wallet size={18} />}
          tooltip="Total value of all assets in portfolio"
          loading={isLoadingMetrics}
        />
        
        <KPICard
          title="Today's P&L"
          value={isLoadingMetrics ? '–' : `$${metricsData?.daily_pnl.toLocaleString()}`}
          change={metricsData?.daily_pnl_pct}
          icon={<Activity size={18} />}
          tooltip="Profit & Loss for today"
          loading={isLoadingMetrics}
        />
        
        <KPICard
          title="Active Strategies"
          value={isLoadingMetrics ? '–' : metricsData?.strategy_active_count}
          icon={<BarChart size={18} />}
          tooltip="Number of currently active trading strategies"
          loading={isLoadingMetrics}
        />
        
        <KPICard
          title="Open Positions"
          value={isLoadingMetrics ? '–' : metricsData?.position_count}
          icon={<ArrowUpDown size={18} />}
          tooltip="Total number of open positions"
          loading={isLoadingMetrics}
        />
      </div>
      
      {/* Portfolio Chart */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-md font-semibold text-gray-700 flex items-center">
            <TrendingUp size={16} className="mr-2 text-blue-500" />
            Portfolio Equity
          </h2>
          <div className="text-xs font-medium text-gray-500">Last 30 Days</div>
        </div>
        
        <div className="h-72">
          {isLoadingEquity ? (
            <div className="h-full flex items-center justify-center animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-32"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={equityCurve}
                margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
              >
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }} 
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    });
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }} 
                  domain={['dataMin - 100', 'dataMax + 100']}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <Tooltip 
                  formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
                  labelFormatter={(label) => {
                    const date = new Date(label);
                    return date.toLocaleDateString('en-US', { 
                      weekday: 'short',
                      year: 'numeric', 
                      month: 'short', 
                      day: 'numeric' 
                    });
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#3b82f6" 
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-md font-semibold mb-3 text-gray-700">Top Performing Strategy</h3>
          {isLoadingMetrics ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 rounded w-28"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
            </div>
          ) : (
            <div>
              <div className="text-sm text-gray-500 mb-1">BTC Trend Following</div>
              <div className="text-xl font-bold text-green-600 mb-1">+12.8%</div>
              <div className="text-xs text-gray-500">Active for 32 days</div>
            </div>
          )}
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-md font-semibold mb-3 text-gray-700">Most Active Market</h3>
          {isLoadingMetrics ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 rounded w-28"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
            </div>
          ) : (
            <div>
              <div className="text-sm text-gray-500 mb-1">BTCUSDT</div>
              <div className="text-xl font-bold mb-1">$45,200.75</div>
              <div className="text-xs text-green-600">+1.92% today</div>
            </div>
          )}
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-md font-semibold mb-3 text-gray-700">Largest Position</h3>
          {isLoadingMetrics ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 rounded w-28"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
            </div>
          ) : (
            <div>
              <div className="text-sm text-gray-500 mb-1">ETH (SHORT)</div>
              <div className="text-xl font-bold mb-1">$3,212.50</div>
              <div className="text-xs text-green-600">+2.42% P&L</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview; 
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell, 
  Legend, 
  Tooltip, 
  ResponsiveContainer, 
  XAxis, 
  YAxis 
} from 'recharts';
import KPICard from './KPICard';
import { 
  TrendingDown, 
  BarChart2, 
  PieChart as PieChartIcon, 
  Zap,
  AlertTriangle,
  Shield
} from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export const RiskAnalysis: React.FC = () => {
  const { data: riskData, isLoading } = useQuery({
    queryKey: ['risk-metrics'],
    queryFn: async () => {
      const response = await apiService.getRiskMetrics();
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });

  return (
    <div className="flex flex-col space-y-6">
      {/* Key Risk Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Max Drawdown"
          value={isLoading ? '–' : `${riskData?.max_drawdown}%`}
          icon={<TrendingDown size={18} />}
          tooltip="Maximum percentage decline in portfolio value"
          loading={isLoading}
        />
        
        <KPICard
          title="Sharpe Ratio"
          value={isLoading ? '–' : riskData?.sharpe_ratio.toFixed(2)}
          icon={<BarChart2 size={18} />}
          tooltip="Risk-adjusted return (higher is better)"
          loading={isLoading}
        />
        
        <KPICard
          title="Win Rate"
          value={isLoading ? '–' : `${riskData?.win_rate}%`}
          icon={<Zap size={18} />}
          tooltip="Percentage of profitable trades"
          loading={isLoading}
        />
        
        <KPICard
          title="Margin Utilization"
          value={isLoading ? '–' : `${riskData?.margin_utilization}%`}
          icon={<AlertTriangle size={18} />}
          tooltip="Percentage of available margin being used"
          loading={isLoading}
        />
      </div>
      
      {/* Risk Allocation Pie Chart & Market Exposure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center mb-4">
            <PieChartIcon size={16} className="text-blue-500 mr-2" />
            <h2 className="text-md font-semibold text-gray-700">Risk Allocation by Strategy</h2>
          </div>
          
          <div className="h-64">
            {isLoading ? (
              <div className="h-full flex items-center justify-center animate-pulse">
                <div className="h-32 w-32 bg-gray-200 rounded-full"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskData?.risk_allocation}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="allocation"
                    nameKey="strategy"
                    label={({ strategy, allocation, percent }) => `${strategy}: ${allocation}%`}
                  >
                    {riskData?.risk_allocation.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `${value}%`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center mb-4">
            <BarChart2 size={16} className="text-blue-500 mr-2" />
            <h2 className="text-md font-semibold text-gray-700">Market Exposure</h2>
          </div>
          
          <div className="h-64">
            {isLoading ? (
              <div className="h-full flex items-center justify-center animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-64"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={riskData?.market_exposure}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <XAxis type="number" domain={[-50, 50]} tickFormatter={(value) => `${Math.abs(value)}%`} />
                  <YAxis type="category" dataKey="market" />
                  <Tooltip 
                    formatter={(value: number) => [`${Math.abs(value)}%`, value >= 0 ? 'Long' : 'Short']}
                    labelFormatter={(label) => `Market: ${label}`}
                  />
                  <Bar dataKey="long" fill="#4ade80" name="Long" />
                  <Bar dataKey="short" fill="#f87171" name="Short" />
                  <Legend />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
      
      {/* Drawdown History Chart */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center mb-4">
          <TrendingDown size={16} className="text-blue-500 mr-2" />
          <h2 className="text-md font-semibold text-gray-700">Drawdown History</h2>
        </div>
        
        <div className="h-72">
          {isLoading ? (
            <div className="h-full flex items-center justify-center animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-full"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={riskData?.drawdown_history}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    });
                  }}
                />
                <YAxis 
                  domain={[0, 'dataMax + 2']}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip 
                  formatter={(value: number) => [`${value}%`, 'Drawdown']}
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
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
      
      {/* Additional Risk Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Value at Risk (95%)</h3>
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          ) : (
            <div className="flex items-center">
              <Shield className="text-blue-500 mr-2" size={18} />
              <span className="text-xl font-bold">${riskData?.var_daily_95.toLocaleString()}</span>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-2">Maximum expected daily loss with 95% confidence</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Sortino Ratio</h3>
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          ) : (
            <div className="flex items-center">
              <BarChart2 className="text-blue-500 mr-2" size={18} />
              <span className="text-xl font-bold">{riskData?.sortino_ratio.toFixed(2)}</span>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-2">Risk-adjusted return focusing on downside risk</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Profit Factor</h3>
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          ) : (
            <div className="flex items-center">
              <Zap className="text-blue-500 mr-2" size={18} />
              <span className="text-xl font-bold">{riskData?.profit_factor.toFixed(2)}</span>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-2">Ratio of gross profit to gross loss</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Max Leverage</h3>
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          ) : (
            <div className="flex items-center">
              <AlertTriangle className="text-blue-500 mr-2" size={18} />
              <span className="text-xl font-bold">{riskData?.max_leverage.toFixed(1)}x</span>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-2">Maximum leverage used across all strategies</p>
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysis; 
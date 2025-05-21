import React from 'react';
import { useRiskMetrics } from '../hooks/useRiskMetrics';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area, Cell } from 'recharts';

// Mock data for charts - in a real app, this would come from API
const equityData = Array.from({length: 30}, (_, i) => ({
  day: `Day ${i+1}`,
  value: 10000 + Math.floor(Math.random() * 1000 - 400 + i * 30)
}));

interface ReturnData {
  day: string;
  value: number;
}

const returnsData: ReturnData[] = Array.from({length: 14}, (_, i) => ({
  day: `Day ${i+1}`,
  value: Math.random() * 2 - 0.8
}));

export const RiskMetrics: React.FC = () => {
  const { data: metrics, isLoading, error } = useRiskMetrics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-gray-400">Loading risk metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-red-400">
          Error loading risk metrics
          <button 
            onClick={() => window.location.reload()}
            className="ml-4 px-3 py-1 bg-blue-800 text-blue-300 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getRiskColor = (value: number, metric: string) => {
    switch (metric) {
      case 'sharpe':
        return value >= 2 ? 'text-green-400' : value >= 1 ? 'text-yellow-400' : 'text-red-400';
      case 'drawdown':
        return value <= -20 ? 'text-red-400' : value <= -10 ? 'text-yellow-400' : 'text-green-400';
      case 'winRate':
        return value >= 60 ? 'text-green-400' : value >= 45 ? 'text-yellow-400' : 'text-red-400';
      case 'plRatio':
        return value >= 1.5 ? 'text-green-400' : value >= 1 ? 'text-yellow-400' : 'text-red-400';
      default:
        return 'text-blue-400';
    }
  };

  const getSharpeText = (value: number) => {
    if (value >= 2) return 'Excellent';
    if (value >= 1.5) return 'Very Good';
    if (value >= 1) return 'Good';
    if (value >= 0.5) return 'Average';
    return 'Poor';
  };

  const getBarColor = (entry: ReturnData) => {
    return entry.value >= 0 ? '#4ade80' : '#f87171';
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4 text-blue-400">Risk Metrics</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2 text-gray-200">Portfolio Equity Curve (30 Days)</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="day" tick={{fontSize: 10, fill: '#9ca3af'}} interval={4} />
              <YAxis 
                domain={['dataMin - 100', 'dataMax + 100']}
                tickFormatter={(value) => `$${value.toLocaleString()}`}
                tick={{fill: '#9ca3af'}}
              />
              <Tooltip 
                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']} 
                contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
              />
              <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="#1e40af" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-700 p-4 rounded-lg text-center">
          <h3 className="text-gray-300 text-sm font-medium mb-1">Sharpe Ratio</h3>
          <p className={`text-2xl font-bold ${getRiskColor(metrics.sharpe, 'sharpe')}`}>{metrics.sharpe.toFixed(1)}</p>
          <p className="text-sm text-gray-400">{getSharpeText(metrics.sharpe)}</p>
        </div>
        
        <div className="bg-gray-700 p-4 rounded-lg text-center">
          <h3 className="text-gray-300 text-sm font-medium mb-1">Max Drawdown</h3>
          <p className={`text-2xl font-bold ${getRiskColor(metrics.max_drawdown_pct, 'drawdown')}`}>{metrics.max_drawdown_pct.toFixed(1)}%</p>
          <p className="text-sm text-gray-400">Last 30 days</p>
        </div>
        
        <div className="bg-gray-700 p-4 rounded-lg text-center">
          <h3 className="text-gray-300 text-sm font-medium mb-1">Win Rate</h3>
          <p className={`text-2xl font-bold ${getRiskColor(metrics.win_rate, 'winRate')}`}>{metrics.win_rate.toFixed(0)}%</p>
          <p className="text-sm text-gray-400">From all trades</p>
        </div>
        
        <div className="bg-gray-700 p-4 rounded-lg text-center">
          <h3 className="text-gray-300 text-sm font-medium mb-1">Profit/Loss Ratio</h3>
          <p className={`text-2xl font-bold ${getRiskColor(metrics.profit_loss_ratio, 'plRatio')}`}>{metrics.profit_loss_ratio.toFixed(1)}</p>
          <p className="text-sm text-gray-400">Avg win / avg loss</p>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium mb-2 text-gray-200">Daily Returns (%) - Last 14 Days</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={returnsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="day" tick={{fontSize: 10, fill: '#9ca3af'}} interval={1} />
              <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} tick={{fill: '#9ca3af'}} />
              <Tooltip 
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']} 
                contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
              />
              <Bar 
                dataKey="value" 
                fill="#8884d8"
                stroke="#8884d8"
                fillOpacity={0.8}
                name="Return"
                isAnimationActive={true}
              >
                {returnsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}; 
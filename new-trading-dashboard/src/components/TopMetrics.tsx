import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  ChartPie,
  BarChart2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { apiService } from '../api/client';
import { useNavigation } from '../App';

export interface MetricsOverview {
  daily_pnl: number;
  weekly_pnl: number;
  monthly_pnl: number;
  active_strategies: number;
  open_positions: number;
  today_trades: number; 
}

export const TopMetrics: React.FC = () => {
  const queryClient = useQueryClient();
  const { navigate } = useNavigation();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data, isLoading, error } = useQuery<MetricsOverview>({
    queryKey: ['metricsOverview'],
    queryFn: async () => {
      try {
        const response = await apiService.getMetricsOverview();
        return response.data;
      } catch (err) {
        console.error('Error fetching metrics:', err);
        throw err;
      }
    },
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await queryClient.invalidateQueries({ queryKey: ['metricsOverview'] });
      console.log('Metrics refreshed');
    } finally {
      setTimeout(() => setIsRefreshing(false), 500); // Add a slight delay to show the refresh animation
    }
  };

  const navigateToSection = (route: string) => {
    navigate(route);
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 lg:grid-cols-6 gap-4 mb-4">
        {[...Array(6)].map((_, i) => (
          <div 
            key={i}
            className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-20 mb-3"></div>
            <div className="h-5 bg-gray-200 rounded w-16 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-12"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 rounded-lg p-3 border border-red-200 mb-4">
        <div className="flex items-center text-red-600">
          <AlertCircle size={16} className="mr-2" />
          <span>Error loading metrics</span>
        </div>
      </div>
    );
  }

  const renderPnlValue = (value: number) => {
    if (value === 0) return <span className="text-gray-500">0.0%</span>;
    
    const isPositive = value > 0;
    return (
      <div className={`flex items-center ${isPositive ? 'text-green-600' : 'text-red-600'} font-medium`}>
        {isPositive ? (
          <ArrowUpRight className="h-4 w-4 mr-1" />
        ) : (
          <ArrowDownRight className="h-4 w-4 mr-1" />
        )}
        {isPositive ? `+${value}%` : `${value}%`}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-4">
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Daily P&L</div>
          <TrendingUp className="h-4 w-4 text-gray-400" />
        </div>
        <div className="mb-1">
          {renderPnlValue(data.daily_pnl)}
        </div>
        <div>
          <button 
            onClick={() => navigateToSection('/risk-analysis')}
            className="text-xs text-blue-600 hover:underline"
          >
            View details
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Weekly P&L</div>
          <TrendingUp className="h-4 w-4 text-gray-400" />
        </div>
        <div className="mb-1">
          {renderPnlValue(data.weekly_pnl)}
        </div>
        <div>
          <button 
            onClick={() => navigateToSection('/risk-analysis')}
            className="text-xs text-blue-600 hover:underline"
          >
            View details
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Monthly P&L</div>
          <TrendingUp className="h-4 w-4 text-gray-400" />
        </div>
        <div className="mb-1">
          {renderPnlValue(data.monthly_pnl)}
        </div>
        <div>
          <button 
            onClick={() => navigateToSection('/risk-analysis')}
            className="text-xs text-blue-600 hover:underline"
          >
            View details
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Active Strategies</div>
          <BarChart2 className="h-4 w-4 text-gray-400" />
        </div>
        <div className="mb-1 font-medium">{data.active_strategies}</div>
        <div>
          <button 
            onClick={() => navigateToSection('/strategies')}
            className="text-xs text-blue-600 hover:underline"
          >
            View strategies
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Open Positions</div>
          <ChartPie className="h-4 w-4 text-gray-400" />
        </div>
        <div className="mb-1 font-medium">{data.open_positions}</div>
        <div>
          <button 
            onClick={() => navigateToSection('/positions')}
            className="text-xs text-blue-600 hover:underline"
          >
            View positions
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm text-gray-500">Trades Today</div>
          <RefreshCw 
            className={`h-4 w-4 text-gray-400 cursor-pointer hover:text-blue-500 ${isRefreshing ? 'animate-spin' : ''}`}
            onClick={handleRefresh}
          />
        </div>
        <div className="mb-1 font-medium">{data.today_trades}</div>
        <div>
          <button 
            onClick={() => navigateToSection('/trade-history')}
            className="text-xs text-blue-600 hover:underline"
          >
            Trade history
          </button>
        </div>
      </div>
    </div>
  );
}; 
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { overviewMetrics } from '../api/mockData';

export interface OverviewMetrics {
  portfolio_value: number;
  portfolio_change_pct: number;
  position_count: number;
  position_value: number;
  strategy_count: number;
  strategy_active_count: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export function useOverviewMetrics() {
  return useQuery({
    queryKey: ['overviewMetrics'],
    queryFn: async () => {
      try {
        const { data } = await apiService.getMetricsOverview();
        return data as OverviewMetrics;
      } catch (error) {
        console.error('Error fetching overview metrics:', error);
        // Return mock data as fallback
        return overviewMetrics;
      }
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });
} 
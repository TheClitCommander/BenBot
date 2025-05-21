import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { riskMetrics } from '../api/mockData';

export interface RiskMetrics {
  sharpe: number;
  sortino: number;
  max_drawdown_pct: number;
  win_rate: number;
  loss_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_loss_ratio: number;
  daily_var_pct: number;
}

export function useRiskMetrics() {
  return useQuery({
    queryKey: ['riskMetrics'],
    queryFn: async () => {
      try {
        const { data } = await apiService.getRiskMetrics();
        return data as RiskMetrics;
      } catch (error) {
        console.error('Error fetching risk metrics:', error);
        // Return mock data as fallback
        return riskMetrics;
      }
    },
    refetchInterval: 60000, // Refresh every minute
  });
} 
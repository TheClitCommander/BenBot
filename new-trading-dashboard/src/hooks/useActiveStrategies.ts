import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { activeStrategies } from '../api/mockData';

export interface Strategy {
  id: string;
  name: string;
  market: string;
  status: 'active' | 'paused' | 'error';
  type: 'trend' | 'mean-reversion' | 'momentum';
  daily_pnl_pct: number;
  total_pnl_pct: number; 
  pnl_today_pct: number;
  pnl_total_pct: number;
  position_count: number;
  last_trade_time?: string;
  created_at: string;
  current_value?: number;
  parameters?: Record<string, string | number | boolean>;
}

export function useActiveStrategies() {
  return useQuery({
    queryKey: ['activeStrategies'],
    queryFn: async () => {
      try {
        const { data } = await apiService.getActiveStrategies();
        return data as Strategy[];
      } catch (error) {
        console.error('Error fetching active strategies:', error);
        // Return mock data as fallback
        return activeStrategies;
      }
    },
    refetchInterval: 10000, // Poll every 10 seconds
  });
} 
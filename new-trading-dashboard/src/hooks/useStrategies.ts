import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export interface Strategy {
  id: string;
  name: string;
  market: string;
  status: 'active' | 'paused';
  pnl_today_pct: number;
  pnl_total_pct: number;
}

export function useStrategies() {
  return useQuery({
    queryKey: ['strategies'],
    queryFn: async () => {
      const { data } = await api.get<Strategy[]>('/orchestration/strategies');
      return data;
    },
  });
}

export function useToggleStrategy() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ strategyId, action }: { strategyId: string, action: 'pause' | 'resume' }) => {
      const { data } = await api.post(`/orchestration/strategies/${strategyId}/${action}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
  });
} 
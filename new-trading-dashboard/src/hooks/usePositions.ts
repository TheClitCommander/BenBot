import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { positions } from '../api/mockData';

export interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entry_price: number;
  current_price: number;
  pnl_pct: number;
  pnl_value: number;
  age: string;
  strategy_id: string;
}

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      try {
        const { data } = await apiService.getPositions();
        return data as Position[];
      } catch (error) {
        console.error('Error fetching positions:', error);
        // Return mock data as fallback
        return positions;
      }
    },
    refetchInterval: 5000, // Poll every 5 seconds for up-to-date position data
  });
}

export function useClosePosition() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (positionId: string) => {
      try {
        // In a real app, we would call an API to close the position
        // For demo, simulate success after small delay
        await new Promise(resolve => setTimeout(resolve, 500));
        return { success: true, positionId };
      } catch (error) {
        console.error('Error closing position:', error);
        throw new Error('Failed to close position');
      }
    },
    onSuccess: () => {
      // Invalidate cache to reload positions
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['activeStrategies'] });
    },
  });
} 
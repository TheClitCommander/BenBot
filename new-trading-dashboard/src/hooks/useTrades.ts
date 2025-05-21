import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { trades } from '../api/mockData';

export interface Trade {
  id: string;
  time: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  size: number;
  price: number;
  total: number;
  strategy: string;
}

export function useTrades(limit: number = 20) {
  return useQuery({
    queryKey: ['trades', limit],
    queryFn: async () => {
      try {
        const { data } = await apiService.getTrades();
        // Apply limit
        return (data as Trade[]).slice(0, limit);
      } catch (error) {
        console.error('Error fetching trades:', error);
        // Return mock data as fallback
        return trades.slice(0, limit);
      }
    },
    refetchInterval: 10000, // Poll every 10 seconds
  });
} 
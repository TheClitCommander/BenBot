import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { markets, marketHistory } from '../api/mockData';

export interface Market {
  symbol: string;
  price: number;
  change_pct: number;
  volume: number;
  high_24h: number;
  low_24h: number;
}

export interface MarketHistoryPoint {
  timestamp: string;
  price: number;
}

export function useMarkets() {
  return useQuery({
    queryKey: ['markets'],
    queryFn: async () => {
      try {
        const { data } = await apiService.getMarketData();
        return data as Market[];
      } catch (error) {
        console.error('Error fetching markets:', error);
        // Return mock data as fallback
        return markets;
      }
    },
    refetchInterval: 15000, // Poll every 15 seconds
  });
}

export function useMarketHistory(symbol: string) {
  return useQuery({
    queryKey: ['marketHistory', symbol],
    queryFn: async () => {
      if (!symbol) return [];
      
      try {
        // In a real app, we would call an API endpoint that returns historical data
        // For this demo, we'll use the mock data directly
        return marketHistory[symbol as keyof typeof marketHistory] || [];
      } catch (error) {
        console.error(`Error fetching history for ${symbol}:`, error);
        return [];
      }
    },
    enabled: !!symbol,
    staleTime: 60000, // Keep data fresh for 1 minute
  });
} 
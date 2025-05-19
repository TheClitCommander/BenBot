import { useQuery } from '@tanstack/react-query';
import { fetchTradierChains } from "../services/tradierApi";

export function useTradierChains(symbol: string, expiration?: string) {
  return useQuery({
    queryKey: ['tradierChains', symbol, expiration],
    queryFn: () => fetchTradierChains(symbol, expiration),
    staleTime: 60000,
    enabled: Boolean(symbol),
    refetchInterval: 300000, // Refresh every 5 minutes
  });
} 
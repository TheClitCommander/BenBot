import { useQuery } from '@tanstack/react-query';
import { fetchTradierQuote } from "../services/tradierApi";

export function useTradierQuote(symbol: string) {
  return useQuery({
    queryKey: ['tradierQuote', symbol],
    queryFn: () => fetchTradierQuote(symbol),
    staleTime: 30000,
    enabled: Boolean(symbol),
    refetchInterval: 60000, // Refresh every minute
  });
} 
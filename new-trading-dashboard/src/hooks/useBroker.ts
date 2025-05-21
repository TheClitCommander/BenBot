import { useQuery, useMutation } from '@tanstack/react-query';
import { ACTIVE_BROKER, fetchPrice, fetchOptionChains, submitOrder } from '../services/brokerApi';
import { useTradierQuote } from './useTradierQuote';
import { useTradierChains } from './useTradierChains';
import { useLivePrice } from './useLiveData';
import { useMemo } from 'react';

// Unified price hook
export function usePrice(symbol: string) {
  const tradierQuery = useTradierQuote(symbol);
  const alpacaQuery = useLivePrice(symbol);
  
  // Select query based on active broker
  return ACTIVE_BROKER === 'tradier' ? tradierQuery : alpacaQuery;
}

// Options chains hook (currently only available with Tradier)
export function useOptionChains(symbol: string, expiration?: string) {
  return useQuery({
    queryKey: ['optionChains', symbol, expiration],
    queryFn: () => fetchOptionChains(symbol, expiration),
    staleTime: 60000,
    enabled: Boolean(symbol) && ACTIVE_BROKER === 'tradier', // Only enabled for Tradier
    refetchInterval: 300000, // Refresh every 5 minutes
  });
}

// Order submission hook that works with any broker
export function useOrderSubmission() {
  return useMutation({
    mutationFn: (orderData: any) => submitOrder(orderData),
    onError: (error) => {
      console.error(`Error submitting order with ${ACTIVE_BROKER}:`, error);
    }
  });
}

// Helper to get the current broker name for display
export function useBrokerInfo() {
  return useMemo(() => ({
    name: ACTIVE_BROKER.charAt(0).toUpperCase() + ACTIVE_BROKER.slice(1),
    id: ACTIVE_BROKER,
    supportsOptions: ACTIVE_BROKER === 'tradier',
  }), []);
} 
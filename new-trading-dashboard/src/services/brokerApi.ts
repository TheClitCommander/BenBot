// Broker utilities to toggle between different brokers
import { fetchTradierQuote, fetchTradierChains, submitTradierOrder } from './tradierApi';
import { apiService } from '../api/client';

// Get active broker from environment or fallback to alpaca
export const ACTIVE_BROKER = import.meta.env.VITE_BROKER || 'alpaca';

// Unified price fetching function
export const fetchPrice = async (symbol: string) => {
  if (ACTIVE_BROKER === 'tradier') {
    return fetchTradierQuote(symbol);
  } else {
    // Alpaca price fetching
    const response = await apiService.getLivePrice(symbol);
    return response.data;
  }
};

// Unified option chains fetching function
export const fetchOptionChains = async (symbol: string, expiration?: string) => {
  if (ACTIVE_BROKER === 'tradier') {
    return fetchTradierChains(symbol, expiration);
  } else {
    // Mock response for Alpaca as it may not support options directly
    throw new Error('Options chains not supported with current broker');
  }
};

// Unified order submission function
export const submitOrder = async (orderData: any) => {
  if (ACTIVE_BROKER === 'tradier') {
    return submitTradierOrder(orderData);
  } else {
    // Alpaca order submission
    const response = await apiService.submitOrder({
      symbol: orderData.symbol,
      side: orderData.side,
      qty: orderData.qty,
      type: orderData.type || 'market',
      limit_price: orderData.limit_price
    });
    return response.data;
  }
};

// Get broker name for UI display
export const getBrokerName = () => {
  return ACTIVE_BROKER.charAt(0).toUpperCase() + ACTIVE_BROKER.slice(1);
}; 
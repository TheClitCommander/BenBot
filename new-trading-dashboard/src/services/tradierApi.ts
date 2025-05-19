import { api, apiService } from '../api/client';

// API base URL
export const TRADIER_BASE = `${api.defaults.baseURL}/tradier`;

// Mock data generator for Tradier quotes
const mockQuote = (symbol: string) => {
  const basePrice = symbol === 'AAPL' ? 170 : symbol === 'MSFT' ? 340 : 100;
  const price = basePrice + Math.random() * 5 - 2.5;
  
  return {
    symbol,
    last: price,
    change: Math.random() * 4 - 2,
    change_percentage: Math.random() * 3 - 1.5,
    volume: Math.floor(Math.random() * 1000000),
    average_volume: Math.floor(Math.random() * 3000000),
    open: price - Math.random() * 2,
    high: price + Math.random() * 3,
    low: price - Math.random() * 3,
    prevclose: price - Math.random() * 1,
    week_52_high: price + 20 + Math.random() * 10,
    week_52_low: price - 20 - Math.random() * 10,
  };
};

// Mock data generator for options chains
const mockOptionsChain = (symbol: string, expiration?: string) => {
  const basePrice = symbol === 'AAPL' ? 170 : symbol === 'MSFT' ? 340 : 100;
  const expirations = ['2025-06-20', '2025-07-18', '2025-08-15', '2025-09-19'];
  
  return {
    symbol,
    expirations: expiration ? [expiration] : expirations,
    options: {
      option: Array.from({length: 10}, (_, i) => {
        const strike = basePrice - 20 + i * 5;
        const isCall = Math.random() > 0.5;
        return {
          symbol: `${symbol}${expiration || '20250620'}${isCall ? 'C' : 'P'}${strike.toFixed(0)}000`,
          strike,
          last: Math.random() * 5,
          change: Math.random() * 1 - 0.5,
          bid: Math.random() * 4.8,
          ask: Math.random() * 5.2,
          volume: Math.floor(Math.random() * 1000),
          open_interest: Math.floor(Math.random() * 3000),
          option_type: isCall ? 'call' : 'put',
          expiration_date: expiration || '2025-06-20',
          root_symbol: symbol,
        };
      })
    }
  };
};

// Fetch Tradier quote
export const fetchTradierQuote = async (symbol: string) => {
  if (apiService.useMockData) {
    return mockQuote(symbol);
  }
  
  const response = await api.get(`${TRADIER_BASE}/quote/${symbol}`);
  return response.data;
};

// Fetch Tradier options chains
export const fetchTradierChains = async (symbol: string, expiration?: string) => {
  if (apiService.useMockData) {
    return mockOptionsChain(symbol, expiration);
  }
  
  const url = `${TRADIER_BASE}/chains/${symbol}${expiration ? `?expiration=${expiration}` : ''}`;
  const response = await api.get(url);
  return response.data;
};

// Place Tradier order
export const submitTradierOrder = async (orderData: {
  account_id: string,
  symbol: string,
  qty: number,
  side: string
}) => {
  if (apiService.useMockData) {
    return {
      id: `mock-order-${Date.now()}`,
      status: 'ok',
      ...orderData
    };
  }
  
  const response = await api.post(`${TRADIER_BASE}/order`, orderData);
  return response.data;
}; 
import axios from 'axios';

// Base API URL - ensure this matches your environment configuration
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Use mock data for development
const USE_MOCK_DATA = false;

// Mock data for development
const mockPositions = {
  positions: [
    {
      id: 'pos-1',
      symbol: 'BTCUSDT',
      side: 'LONG',
      size: 0.1,
      entry_price: 44350.5,
      current_price: 45200.75,
      pnl_usd: 85.02,
      pnl_percent: 1.91,
      timestamp: new Date().toISOString(),
      strategy_id: 'strat-btc-trend-1'
    },
    {
      id: 'pos-2',
      symbol: 'ETHUSDT',
      side: 'SHORT',
      size: 1.25,
      entry_price: 2570.0,
      current_price: 2520.5,
      pnl_usd: 61.88,
      pnl_percent: 2.42,
      timestamp: new Date().toISOString(),
      strategy_id: 'strat-eth-reversion-1'
    }
  ]
};

const mockTrades = {
  trades: [
    {
      id: 'trade-1',
      symbol: 'BTCUSDT',
      side: 'BUY',
      size: 0.1,
      price: 44350.5,
      cost: 4435.05,
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      strategy_id: 'strat-btc-trend-1',
      order_type: 'MARKET'
    },
    {
      id: 'trade-2',
      symbol: 'ETHUSDT',
      side: 'SELL',
      size: 1.25,
      price: 2570.0,
      cost: 3212.5,
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      strategy_id: 'strat-eth-reversion-1',
      order_type: 'LIMIT'
    },
    {
      id: 'trade-3',
      symbol: 'SOLUSDT',
      side: 'BUY',
      size: 10,
      price: 121.5,
      cost: 1215.0,
      timestamp: new Date(Date.now() - 14400000).toISOString(),
      strategy_id: 'strat-alt-momentum-1',
      order_type: 'MARKET'
    }
  ]
};

// Define the API service interface
interface ExecutionApiService {
  getActivePositions: () => Promise<{ positions: any[] }>;
  getRecentTrades: (limit?: number) => Promise<{ trades: any[] }>;
}

// Implement the API service
const executionApi: ExecutionApiService = {
  /**
   * Get active positions
   */
  getActivePositions: async (): Promise<{ positions: any[] }> => {
    if (USE_MOCK_DATA) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockPositions), 500);
      });
    }

    try {
      const response = await axios.get(`${apiBaseUrl}/execution/positions/active`);
      return response.data;
    } catch (error) {
      console.error('Error fetching active positions:', error);
      throw error;
    }
  },

  /**
   * Get recent trades
   */
  getRecentTrades: async (limit: number = 10): Promise<{ trades: any[] }> => {
    if (USE_MOCK_DATA) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockTrades), 500);
      });
    }

    try {
      const response = await axios.get(`${apiBaseUrl}/execution/trades/recent?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching recent trades:', error);
      throw error;
    }
  }
};

export default executionApi; 
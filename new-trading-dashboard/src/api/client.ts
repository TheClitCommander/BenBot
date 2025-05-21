import axios from 'axios';
import * as mockData from './mockData';

// Get the API base URL from environment variables or fallback to the real trading bot API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Set this to true to force using mock data even if the API is available
const FORCE_MOCK_DATA = import.meta.env.VITE_FORCE_MOCK_DATA === 'true' || false;
// Use mock data if explicitly set in env
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || FORCE_MOCK_DATA;

// Create an axios instance with the base URL and default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000, // 5 seconds timeout for faster fallback to mock data
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to track if we should use mock data (set to true if API fails)
// Export this flag as a property of apiService for debugging
let _useMockData = USE_MOCK;

// Add a request interceptor to handle authentication if needed
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`Making request to: ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    // If we get a successful response and not forcing mock data, use real data
    if (!FORCE_MOCK_DATA) {
      _useMockData = false;
      console.log('Using real API data');
    }
    return response;
  },
  (error) => {
    // Log errors to console in development
    if (import.meta.env.DEV) {
      console.error('API Error:', error);
      
      // If API is unreachable, enable mock data mode
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
        console.warn('API unreachable, switching to mock data');
        _useMockData = true;
      }
    }
    
    return Promise.reject(error);
  }
);

// Check API health on startup and periodically
const checkApiHealth = async () => {
  if (FORCE_MOCK_DATA) {
    _useMockData = true;
    console.log('Forcing mock data mode');
    return;
  }
  
  try {
    await api.get('/health');
    _useMockData = false;
    console.log('Connected to API server');
  } catch (error) {
    console.warn('API health check failed, using mock data');
    _useMockData = true;
  }
};

// Run health check on startup
checkApiHealth();

// Set up periodic health check (every minute)
setInterval(checkApiHealth, 60000);

// Helper function to mock API responses
const mockResponse = (data: any) => {
  return Promise.resolve({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {},
  });
};

// Function to generate mock order book data
const generateMockOrderBook = (symbol: string, depth: number = 20) => {
  let midPrice = 0;
  
  // Set different mid prices based on the symbol
  switch (symbol.toUpperCase()) {
    case 'BTCUSDT':
      midPrice = 45000 + (Math.random() * 1000 - 500);
      break;
    case 'ETHUSDT':
      midPrice = 2500 + (Math.random() * 100 - 50);
      break;
    case 'SOLUSDT':
      midPrice = 120 + (Math.random() * 10 - 5);
      break;
    default:
      midPrice = 100 + (Math.random() * 10 - 5);
  }
  
  // Generate asks (sell orders) - sorted by price ascending
  const asks = Array.from({ length: depth }, (_, i) => {
    const priceOffset = (i + 1) * (midPrice * 0.0001) * (1 + Math.random() * 0.5);
    const price = midPrice + priceOffset;
    const size = Math.random() * 2 + 0.1;
    return [price, size];
  });
  
  // Generate bids (buy orders) - sorted by price descending
  const bids = Array.from({ length: depth }, (_, i) => {
    const priceOffset = (i + 1) * (midPrice * 0.0001) * (1 + Math.random() * 0.5);
    const price = midPrice - priceOffset;
    const size = Math.random() * 2 + 0.1;
    return [price, size];
  });
  
  return {
    asks,
    bids,
    timestamp: Date.now(),
  };
};

// Create a function to manually toggle mock data mode (for debugging)
const setMockDataMode = (useMode: boolean) => {
  _useMockData = useMode;
  console.log(`Manually ${useMode ? 'enabled' : 'disabled'} mock data mode`);
};

// Export API service functions
export const apiService = {
  // Expose the useMockData state as a getter
  get useMockData() {
    return _useMockData;
  },
  
  // Expose method to toggle mock data
  setMockDataMode,
  
  // Health check
  health: () => _useMockData 
    ? mockResponse({ status: 'healthy' }) 
    : api.get('/health'),

  // ===== Live Data Endpoints (Alpaca) =====
  getLivePrice: (symbol: string) => _useMockData
    ? mockResponse({ symbol, price: 100 + Math.random() * 10 })
    : api.get(`/live/price/${symbol}`),
    
  getLiveAccount: () => _useMockData
    ? mockResponse(mockData.accountInfo)
    : api.get('/live/account'),
    
  getLivePositions: () => _useMockData
    ? mockResponse(mockData.positions)
    : api.get('/live/positions'),
    
  getLiveOrders: () => _useMockData
    ? mockResponse([])
    : api.get('/live/orders'),
    
  submitOrder: (orderData: {
    symbol: string, 
    side: string, 
    qty: number, 
    type?: string, 
    limit_price?: number
  }) => _useMockData
    ? mockResponse({ id: 'mock-order-' + Date.now(), status: 'filled', ...orderData })
    : api.post('/live/order', orderData),
  
  // Metrics endpoints
  getMetricsOverview: () => _useMockData 
    ? mockResponse(mockData.overviewMetrics) 
    : api.get('/metrics/overview'),
    
  getRiskMetrics: () => _useMockData 
    ? mockResponse(mockData.riskMetrics) 
    : api.get('/metrics/risk'),
    
  getEquityCurve: (days = 30) => _useMockData 
    ? mockResponse(Array.from({length: days}, (_, i) => ({
        date: new Date(Date.now() - (days - i - 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 10000 + Math.floor(Math.random() * 1000 - 400 + i * 30)
      }))) 
    : api.get(`/metrics/equity?days=${days}`),
    
  getSystemPerformance: () => _useMockData 
    ? mockResponse(mockData.systemStatus) 
    : api.get('/metrics/performance'),
    
  getMarketData: () => _useMockData 
    ? mockResponse(mockData.markets) 
    : api.get('/metrics/markets'),
  
  // Order book and market data
  getOrderBook: (symbol: string) => _useMockData
    ? mockResponse(generateMockOrderBook(symbol))
    : api.get(`/markets/orderbook/${symbol}`),
  
  // Trading/execution endpoints
  getPositions: (symbol?: string) => _useMockData 
    ? mockResponse(symbol 
        ? mockData.positions.filter(pos => pos.symbol === symbol) 
        : mockData.positions) 
    : api.get('/execution/positions', { params: { symbol } }),
    
  getOrders: (symbol?: string, status?: string) => _useMockData 
    ? mockResponse([]) 
    : api.get('/execution/orders', { params: { symbol, status } }),
    
  getTrades: (symbol?: string) => _useMockData 
    ? mockResponse(symbol 
        ? mockData.trades.filter(trade => trade.symbol === symbol) 
        : mockData.trades) 
    : api.get('/execution/trades', { params: { symbol } }),
    
  placeOrder: (orderData: any) => _useMockData 
    ? mockResponse({ id: 'mock-order-' + Date.now(), ...orderData }) 
    : api.post('/execution/orders', orderData),
    
  cancelOrder: (orderId: string) => _useMockData 
    ? mockResponse({ success: true, message: 'Order cancelled' }) 
    : api.delete(`/execution/orders/${orderId}`),
  
  // System orchestration
  getSystemStatus: () => _useMockData 
    ? mockResponse(mockData.systemStatus) 
    : api.get('/orchestration/status'),
    
  setTradingMode: (mode: string) => _useMockData 
    ? mockResponse({ success: true, mode }) 
    : api.put('/orchestration/trading-mode', { mode }),
    
  getActiveStrategies: () => _useMockData 
    ? mockResponse(mockData.activeStrategies) 
    : api.get('/orchestration/strategies/active'),
    
  activateStrategy: (strategyData: any) => _useMockData 
    ? mockResponse({ success: true, ...strategyData }) 
    : api.post('/orchestration/strategies/activate', strategyData),
    
  // Safety endpoints
  getSafetyStatus: () => _useMockData
    ? mockResponse({ circuit_breaker_enabled: true, max_drawdown_percent: 5.0 })
    : api.get('/safety/status'),
    
  updateSafetySettings: (settings: any) => _useMockData
    ? mockResponse({ success: true, ...settings })
    : api.put('/safety/settings', settings),
};

export default apiService; 
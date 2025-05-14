import axios, { AxiosRequestConfig } from 'axios';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Setup Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interface for API Response
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Equity point interface
export interface EquityPoint {
  timestamp: string;
  equity: number;
  daily_pnl: number;
  total_pnl: number;
}

// Position interface
export interface Position {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  strategy: string;
}

// Signal interface
export interface Signal {
  id: string;
  symbol: string;
  type: string;
  source: string;
  confidence: number;
  price: number;
  timestamp: string;
  executed: boolean;
  reason?: string;
}

// Performance summary interface
export interface PerformanceSummary {
  starting_equity: number;
  current_equity: number;
  total_pnl: number;
  total_pnl_percent: number;
  open_positions_count: number;
  total_trade_count: number;
  winning_trades?: number;
  losing_trades?: number;
  win_rate?: number;
  avg_daily_change_percent?: number;
  max_daily_gain_percent?: number;
  max_daily_loss_percent?: number;
}

// Generic API request handler
async function apiRequest<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
  try {
    const response = await api(config);
    return response.data as ApiResponse<T>;
  } catch (error: any) {
    return { 
      success: false, 
      error: error.response?.data?.detail || error.message || 'Unknown error' 
    };
  }
}

// Metrics API endpoints
const metricsApi = {
  // Get equity curve data
  getEquityCurve: async (
    timeframe: string = '1m',
    startTime?: string,
    endTime?: string
  ): Promise<ApiResponse<EquityPoint[]>> => {
    let params: any = { timeframe };
    if (startTime) params.start_time = startTime;
    if (endTime) params.end_time = endTime;
    
    return apiRequest<EquityPoint[]>({
      method: 'GET',
      url: '/metrics/equity-curve',
      params
    });
  },

  // Get all current positions
  getPositions: async (): Promise<ApiResponse<Position[]>> => {
    return apiRequest<Position[]>({
      method: 'GET',
      url: '/metrics/positions'
    });
  },

  // Get a specific position by ID
  getPosition: async (positionId: string): Promise<ApiResponse<Position>> => {
    return apiRequest<Position>({
      method: 'GET',
      url: `/metrics/position/${positionId}`
    });
  },

  // Get trading signals
  getSignals: async (
    limit: number = 50,
    signalType?: string,
    executed?: boolean
  ): Promise<ApiResponse<Signal[]>> => {
    let params: any = { limit };
    if (signalType) params.signal_type = signalType;
    if (executed !== undefined) params.executed = executed;
    
    return apiRequest<Signal[]>({
      method: 'GET',
      url: '/metrics/signals',
      params
    });
  },

  // Get performance summary
  getPerformanceSummary: async (): Promise<ApiResponse<PerformanceSummary>> => {
    return apiRequest<PerformanceSummary>({
      method: 'GET',
      url: '/metrics/summary'
    });
  },

  // Generate mock data (development only)
  generateMockData: async (days: number = 30): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'POST',
      url: '/metrics/generate-mock-data',
      params: { days }
    });
  }
};

export default metricsApi; 
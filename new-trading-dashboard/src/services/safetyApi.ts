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

// Safety status interface
export interface SafetyStatus {
  tradingMode: 'live' | 'paper';
  emergencyStopActive: boolean;
  circuitBreakers: {
    active: boolean;
    reason?: string;
    triggeredAt?: string;
    maxDailyLoss?: number;
    currentDailyLoss?: number;
    maxDrawdownPercent?: number;
    maxTradesPerDay?: number;
    currentTradeCount?: number;
  };
  cooldowns: {
    active: boolean;
    endsAt?: string;
    remainingSeconds?: number;
    reason?: string;
  };
  tradingAllowed: boolean;
  tradingBlockedReason?: string;
}

// Circuit breaker config interface
export interface CircuitBreakerConfig {
  enabled: boolean;
  maxDailyLoss: number;
  maxDrawdownPercent: number;
  maxTradesPerDay: number;
  maxConsecutiveLosses: number;
}

// Cooldown config interface
export interface CooldownConfig {
  enabled: boolean;
  durationSeconds: number;
  afterConsecutiveLosses: number;
  afterMaxDrawdown: boolean;
}

// Safety event interface
export interface SafetyEvent {
  id: string;
  type: string;
  action: string;
  timestamp: string;
  reason?: string;
  details?: any;
  actor?: string;
}

// Generic API request handler
async function apiRequest<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
  try {
    const response = await api(config);
    return { success: true, data: response.data };
  } catch (error: any) {
    return { 
      success: false, 
      error: error.response?.data?.detail || error.message || 'Unknown error' 
    };
  }
}

// Safety API endpoints
const safetyApi = {
  // Get the current safety status
  getSafetyStatus: async (): Promise<ApiResponse<SafetyStatus>> => {
    return apiRequest<SafetyStatus>({
      method: 'GET',
      url: '/safety/status'
    });
  },

  // Emergency stop control
  setEmergencyStop: async (active: boolean, reason?: string): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'POST',
      url: '/safety/emergency-stop',
      data: {
        active,
        reason: reason || (active ? 'Manual activation' : undefined)
      }
    });
  },

  // Trading mode control
  setTradingMode: async (mode: 'live' | 'paper'): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'POST',
      url: '/safety/trading-mode',
      data: { mode }
    });
  },

  // Circuit breaker management
  getCircuitBreakerConfig: async (): Promise<ApiResponse<CircuitBreakerConfig>> => {
    return apiRequest<CircuitBreakerConfig>({
      method: 'GET',
      url: '/safety/circuit-breakers/config'
    });
  },

  updateCircuitBreakerConfig: async (config: CircuitBreakerConfig): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'PUT',
      url: '/safety/circuit-breakers/config',
      data: config
    });
  },

  resetCircuitBreaker: async (): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'POST',
      url: '/safety/circuit-breakers/reset'
    });
  },

  // Cooldown management
  getCooldownConfig: async (): Promise<ApiResponse<CooldownConfig>> => {
    return apiRequest<CooldownConfig>({
      method: 'GET',
      url: '/safety/cooldowns/config'
    });
  },

  updateCooldownConfig: async (config: CooldownConfig): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'PUT',
      url: '/safety/cooldowns/config',
      data: config
    });
  },

  resetCooldown: async (): Promise<ApiResponse<any>> => {
    return apiRequest<any>({
      method: 'POST',
      url: '/safety/cooldowns/reset'
    });
  },

  // Safety events history
  getSafetyEvents: async (limit: number = 50, eventType?: string): Promise<ApiResponse<SafetyEvent[]>> => {
    return apiRequest<SafetyEvent[]>({
      method: 'GET',
      url: '/safety/events',
      params: {
        limit,
        event_type: eventType
      }
    });
  }
};

export default safetyApi;

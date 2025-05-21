import axios, { AxiosRequestConfig } from 'axios';

// Base API URL - ensure this matches your environment configuration
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Use mock data for development
const USE_MOCK_DATA = false;

// Mock metrics data
const mockPerformanceMetrics = {
  equityCurve: Array.from({ length: 24 }, (_, i) => {
    const baseValue = 10000;
    const randomChange = (Math.random() - 0.3) * 200; // Bias towards positive returns
    const timestamp = new Date(Date.now() - (23 - i) * 3600 * 1000).toISOString();
    return {
      timestamp,
      value: baseValue + randomChange * (i + 1) // Gradually increase over time with some volatility
    };
  }),
  dailyReturns: [
    { date: '2023-07-01', return_percent: 1.2 },
    { date: '2023-07-02', return_percent: -0.3 },
    { date: '2023-07-03', return_percent: 0.8 },
    { date: '2023-07-04', return_percent: 2.1 },
    { date: '2023-07-05', return_percent: -0.5 }
  ],
  totalReturn: 4.7,
  drawdown: -2.3,
  sharpeRatio: 1.8
};

interface MetricsApiService {
  getPerformanceMetrics: () => Promise<typeof mockPerformanceMetrics>;
  getDailyReturns: (days?: number) => Promise<{ date: string; return_percent: number }[]>;
}

// Implement the API service
const metricsApi: MetricsApiService = {
  /**
   * Get performance metrics including equity curve
   */
  getPerformanceMetrics: async () => {
    if (USE_MOCK_DATA) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockPerformanceMetrics), 500);
      });
    }

    try {
      const response = await axios.get(`${apiBaseUrl}/metrics/performance`);
      return response.data;
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      throw error;
    }
  },

  /**
   * Get daily returns for a specified number of days
   */
  getDailyReturns: async (days = 30) => {
    if (USE_MOCK_DATA) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockPerformanceMetrics.dailyReturns), 500);
      });
    }

    try {
      const response = await axios.get(`${apiBaseUrl}/metrics/returns/daily?days=${days}`);
      return response.data.returns;
    } catch (error) {
      console.error('Error fetching daily returns:', error);
      throw error;
    }
  }
};

export default metricsApi; 
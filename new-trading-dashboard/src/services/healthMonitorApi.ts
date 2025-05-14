import axios from 'axios';
import { mockHealthStatus, mockAlerts } from './mockData';

// Base API URL - ensure this matches your environment configuration
const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Use mock data for development
const USE_MOCK_DATA = true;

// --- TypeScript Interfaces for Health Monitor API ---

export interface ComponentStatus {
  healthy: boolean;
  last_check_time: string;
  error?: string;
  latency_ms?: number;
  usage_percent?: number;
  free_mb?: number;
  available_mb?: number;
  execution_time_ms?: number;
  avg_cycle_time_ms?: number;
  [key: string]: any; // For any other dynamic fields
}

export interface DataFeedLatency {
  [source: string]: {
    latency_ms: number;
    timestamp: string;
  };
}

export interface SystemHealthStatus {
  timestamp: string;
  system_status: 'healthy' | 'unhealthy';
  components: {
    [componentName: string]: ComponentStatus;
  };
  data_feed_latency: DataFeedLatency;
}

export interface HealthReportEntry {
  id: string;
  timestamp: string;
  overall_status: 'healthy' | 'unhealthy';
  report_file: string;
}

export interface HealthReportList {
  reports: HealthReportEntry[];
  count: number;
}

export interface DetailedHealthReport extends SystemHealthStatus {
  components_detail: {
    [componentName: string]: {
      status: 'healthy' | 'unhealthy';
      last_checked: string;
      [key: string]: any;
    };
  };
  data_feeds: DataFeedLatency;
}

export interface SystemResource {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
}

export interface ResourceHistoryResponse {
  resource_history: SystemResource[];
  interval: string;
  start_time: string;
  end_time: string;
}

export interface HealthAlertEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  component: string;
  resolved: boolean;
  resolved_at?: string;
}

export interface HealthAlertList {
  alerts: HealthAlertEntry[];
  count: number;
  unresolved_count: number;
}

// Define the Health Monitor API service interface
interface HealthMonitorApiService {
  getCurrentStatus: () => Promise<SystemHealthStatus>;
  getHealthReports: (limit?: number) => Promise<HealthReportList>;
  getDetailedReport: (reportId: string) => Promise<DetailedHealthReport>;
  getResourceHistory: (hours?: number) => Promise<ResourceHistoryResponse>;
  getAlerts: (limit?: number, includeResolved?: boolean) => Promise<HealthAlertList>;
  resolveAlert: (alertId: string) => Promise<{success: boolean; message?: string}>;
}

// Implement the Health Monitor API service
const healthMonitorApi: HealthMonitorApiService = {
  /**
   * Get the current system health status
   */
  getCurrentStatus: async (): Promise<SystemHealthStatus> => {
    if (USE_MOCK_DATA) {
      // Return mock data with a slight delay to simulate network request
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockHealthStatus), 500);
      });
    }

    try {
      const response = await axios.get<SystemHealthStatus>(
        `${apiBaseUrl}/health/status`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching system health status:', error);
      throw error;
    }
  },

  /**
   * Get list of health reports
   */
  getHealthReports: async (limit: number = 10): Promise<HealthReportList> => {
    if (USE_MOCK_DATA) {
      // Simple mock data for reports
      return new Promise((resolve) => {
        setTimeout(() => resolve({
          reports: [
            {
              id: '1',
              timestamp: new Date().toISOString(),
              overall_status: 'healthy',
              report_file: 'report_20230514.json'
            }
          ],
          count: 1
        }), 500);
      });
    }

    try {
      const response = await axios.get<HealthReportList>(
        `${apiBaseUrl}/health/reports?limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching health reports:', error);
      throw error;
    }
  },

  /**
   * Get a detailed health report by ID
   */
  getDetailedReport: async (reportId: string): Promise<DetailedHealthReport> => {
    if (USE_MOCK_DATA) {
      // Return mock health status as a detailed report
      return new Promise((resolve) => {
        setTimeout(() => resolve({
          ...mockHealthStatus,
          components_detail: Object.entries(mockHealthStatus.components).reduce((acc, [key, value]) => {
            acc[key] = {
              status: value.healthy ? 'healthy' : 'unhealthy',
              last_checked: value.last_check_time,
              ...value
            };
            return acc;
          }, {} as Record<string, any>),
          data_feeds: mockHealthStatus.data_feed_latency
        }), 500);
      });
    }

    try {
      const response = await axios.get<DetailedHealthReport>(
        `${apiBaseUrl}/health/reports/${reportId}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching detailed health report ${reportId}:`, error);
      throw error;
    }
  },

  /**
   * Get resource usage history
   */
  getResourceHistory: async (hours: number = 24): Promise<ResourceHistoryResponse> => {
    if (USE_MOCK_DATA) {
      // Generate mock resource history
      const history: SystemResource[] = [];
      const now = Date.now();
      const interval = hours * 60 * 60 * 1000 / 24; // 24 data points

      for (let i = 0; i < 24; i++) {
        const timestamp = new Date(now - (23 - i) * interval).toISOString();
        history.push({
          timestamp,
          cpu_usage: 30 + Math.random() * 40,
          memory_usage: 50 + Math.random() * 30,
          disk_usage: 60 + Math.random() * 15,
          network_rx_bytes: 1000000 + Math.random() * 2000000,
          network_tx_bytes: 500000 + Math.random() * 1000000
        });
      }

      return new Promise((resolve) => {
        setTimeout(() => resolve({
          resource_history: history,
          interval: `${interval / (60 * 1000)} minutes`,
          start_time: history[0].timestamp,
          end_time: history[history.length - 1].timestamp
        }), 500);
      });
    }

    try {
      const response = await axios.get<ResourceHistoryResponse>(
        `${apiBaseUrl}/health/resources/history?hours=${hours}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching resource history:', error);
      throw error;
    }
  },

  /**
   * Get health alerts
   */
  getAlerts: async (limit: number = 50, includeResolved: boolean = false): Promise<HealthAlertList> => {
    if (USE_MOCK_DATA) {
      // Return mock alerts data
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockAlerts), 500);
      });
    }

    try {
      const response = await axios.get<HealthAlertList>(
        `${apiBaseUrl}/health/alerts?limit=${limit}&include_resolved=${includeResolved}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching health alerts:', error);
      throw error;
    }
  },

  /**
   * Resolve a health alert
   */
  resolveAlert: async (alertId: string): Promise<{success: boolean; message?: string}> => {
    if (USE_MOCK_DATA) {
      return new Promise((resolve) => {
        setTimeout(() => resolve({ success: true, message: 'Alert resolved successfully' }), 500);
      });
    }

    try {
      const response = await axios.post<{success: boolean; message?: string}>(
        `${apiBaseUrl}/health/alerts/${alertId}/resolve`
      );
      return response.data;
    } catch (error) {
      console.error(`Error resolving alert ${alertId}:`, error);
      return { success: false, message: `Failed to resolve alert ${alertId}` };
    }
  }
};

export default healthMonitorApi; 
import { 
  SystemHealthStatus, 
  HealthAlertList,
  ComponentStatus
} from './healthMonitorApi';

// Mock component status data
const createMockComponentStatus = (healthy: boolean, options: Partial<ComponentStatus> = {}): ComponentStatus => {
  return {
    healthy,
    last_check_time: new Date().toISOString(),
    ...options
  };
};

// Mock health status data
export const mockHealthStatus: SystemHealthStatus = {
  timestamp: new Date().toISOString(),
  system_status: 'healthy',
  components: {
    'cpu_usage': createMockComponentStatus(true, { 
      usage_percent: 45.2
    }),
    'memory_usage': createMockComponentStatus(true, { 
      usage_percent: 68.7,
      available_mb: 4096
    }),
    'disk_space': createMockComponentStatus(true, { 
      usage_percent: 72.3,
      free_mb: 128000
    }),
    'data_feed_alpaca': createMockComponentStatus(true, { 
      latency_ms: 230
    }),
    'data_feed_yahoo': createMockComponentStatus(true, { 
      latency_ms: 420
    }),
    'data_feed_binance': createMockComponentStatus(false, { 
      latency_ms: 1200,
      error: 'High latency detected'
    }),
    'portfolio_allocation': createMockComponentStatus(true),
    'strategy_execution': createMockComponentStatus(true, {
      execution_time_ms: 450,
      avg_cycle_time_ms: 520
    })
  },
  data_feed_latency: {
    'alpaca': {
      latency_ms: 230,
      timestamp: new Date().toISOString()
    },
    'yahoo': {
      latency_ms: 420,
      timestamp: new Date().toISOString()
    },
    'binance': {
      latency_ms: 1200,
      timestamp: new Date().toISOString()
    }
  }
};

// Mock alerts data
export const mockAlerts: HealthAlertList = {
  alerts: [
    {
      id: '1',
      timestamp: new Date().toISOString(),
      level: 'CRITICAL',
      message: 'Binance data feed experiencing high latency',
      component: 'data_feed_binance',
      resolved: false
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(), // 10 minutes ago
      level: 'WARNING',
      message: 'Memory usage approaching threshold (85%)',
      component: 'memory_usage',
      resolved: true,
      resolved_at: new Date(Date.now() - 1000 * 60 * 5).toISOString() // 5 minutes ago
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), // 1 hour ago
      level: 'INFO',
      message: 'System health check completed successfully',
      component: 'system',
      resolved: true,
      resolved_at: new Date(Date.now() - 1000 * 60 * 59).toISOString()
    }
  ],
  count: 3,
  unresolved_count: 1
}; 
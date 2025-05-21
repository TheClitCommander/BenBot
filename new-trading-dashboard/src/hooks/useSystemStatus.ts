import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';

export interface SystemStatus {
  status: 'online' | 'warning' | 'critical' | 'offline';
  message?: string;
  connectionType?: string;
  cpuUsage?: number;
  memoryUsage?: number;
  uptime?: string;
  lastTradeTime?: string;
}

export const useSystemStatus = () => {
  return useQuery<SystemStatus>({
    queryKey: ['systemStatus'],
    queryFn: async () => {
      try {
        const response = await apiService.getSystemStatus();
        return response.data;
      } catch (err) {
        console.error('Error fetching system status:', err);
        // Return a default system status if the API call fails
        return {
          status: 'warning',
          message: 'Unable to fetch real-time status'
        };
      }
    },
    refetchInterval: 10000
  });
}; 
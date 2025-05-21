import React from 'react';
import { Box, Typography, Card, CardContent, Chip, CircularProgress } from '@mui/material';
import { SystemHealthStatus } from '../services/healthMonitorApi';

interface SystemHealthPanelProps {
  data: SystemHealthStatus | undefined;
  isLoading: boolean;
  error: unknown;
}

const SystemHealthPanel: React.FC<SystemHealthPanelProps> = ({ data, isLoading, error }) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', p: 3 }}>
          <CircularProgress size={30} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Loading system health data...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent>
          <Typography color="error" variant="body1">
            Error loading system health data
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">System Health</Typography>
          <Chip 
            label={data.system_status === 'healthy' ? 'Healthy' : 'Issues Detected'} 
            color={data.system_status === 'healthy' ? 'success' : 'error'}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          Last updated: {new Date(data.timestamp).toLocaleTimeString()}
        </Typography>

        <Box sx={{ mt: 2 }}>
          {data.components && Object.entries(data.components).map(([name, status]) => (
            <Box key={name} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2">{name}</Typography>
              <Chip 
                label={status.healthy ? 'OK' : 'Error'} 
                size="small" 
                color={status.healthy ? 'success' : 'error'}
                sx={{ minWidth: '60px', fontSize: '0.7rem' }}
              />
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemHealthPanel; 
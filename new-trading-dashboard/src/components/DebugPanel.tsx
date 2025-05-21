import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, List, ListItem, Button, Divider, Switch, FormControlLabel } from '@mui/material';
import { api, apiService } from '../api/client';

interface ApiEndpoint {
  name: string;
  url: string;
  method: string;
}

const ApiEndpoints: ApiEndpoint[] = [
  { name: 'Health Check', url: '/health', method: 'GET' },
  { name: 'Metrics Overview', url: '/metrics/overview', method: 'GET' },
  { name: 'System Status', url: '/orchestration/status', method: 'GET' },
  { name: 'Active Strategies', url: '/orchestration/strategies/active', method: 'GET' },
  { name: 'Positions', url: '/execution/positions', method: 'GET' },
  { name: 'Trades', url: '/execution/trades', method: 'GET' },
];

const DebugPanel: React.FC = () => {
  const [envVars, setEnvVars] = useState<Record<string, string>>({});
  const [wsStatus, setWsStatus] = useState<string>('Not connected');
  const [endpointTests, setEndpointTests] = useState<Record<string, { status: string, data: any }>>({});
  const [mockStatus, setMockStatus] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Get environment variables
    setEnvVars({
      'VITE_API_URL': import.meta.env.VITE_API_URL || 'Not set',
      'VITE_WS_URL': import.meta.env.VITE_WS_URL || 'Not set',
      'VITE_FORCE_MOCK_DATA': import.meta.env.VITE_FORCE_MOCK_DATA || 'Not set',
    });

    // Test WebSocket connection
    try {
      const ws = new WebSocket(import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws');
      
      ws.onopen = () => {
        setWsStatus('Connected');
        setTimeout(() => ws.close(1000, 'Debug test complete'), 2000);
      };
      
      ws.onerror = () => {
        setWsStatus('Error connecting');
      };
      
      ws.onclose = () => {
        if (wsStatus === 'Connected') {
          setWsStatus('Was connected, now closed');
        }
      };
    } catch (error) {
      setWsStatus(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }

    // Check mock data status
    setMockStatus(apiService.useMockData);
  }, []);

  const testEndpoint = async (endpoint: ApiEndpoint) => {
    try {
      setEndpointTests(prev => ({
        ...prev,
        [endpoint.name]: { status: 'Testing...', data: null }
      }));

      const startTime = Date.now();
      const response = await api.get(endpoint.url);
      const endTime = Date.now();

      setEndpointTests(prev => ({
        ...prev,
        [endpoint.name]: { 
          status: `OK (${endTime - startTime}ms)`, 
          data: response.data 
        }
      }));
    } catch (error) {
      setEndpointTests(prev => ({
        ...prev,
        [endpoint.name]: { 
          status: `Error: ${error instanceof Error ? error.message : String(error)}`, 
          data: null 
        }
      }));
    }
  };

  const toggleMockData = () => {
    const newMockStatus = !mockStatus;
    // Actually change the API client's mock data mode
    apiService.setMockDataMode(newMockStatus);
    setMockStatus(newMockStatus);
    
    // Refresh the page to apply changes
    if (confirm('Mock data mode has been changed. Reload page to apply changes?')) {
      window.location.reload();
    }
  };

  const testAllEndpoints = () => {
    ApiEndpoints.forEach(endpoint => testEndpoint(endpoint));
  };

  const saveMockSettingToEnv = () => {
    // Create or update .env.local file (this is just a visual indication, the real update would happen server-side)
    alert(`This would save VITE_FORCE_MOCK_DATA=${mockStatus} to your .env.local file.\n\nIn a real implementation, this would require a server endpoint to update the file.`);
  };

  if (!isExpanded) {
    return (
      <Button 
        variant="contained" 
        color="warning"
        onClick={() => setIsExpanded(true)}
        style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}
      >
        Show Debug Panel
      </Button>
    );
  }

  return (
    <Paper elevation={3} style={{ 
      position: 'fixed', 
      bottom: 20, 
      right: 20, 
      width: 400, 
      maxHeight: '80vh',
      overflowY: 'auto',
      zIndex: 1000,
      padding: 16
    }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">API Debug Panel</Typography>
        <Button variant="outlined" size="small" onClick={() => setIsExpanded(false)}>
          Close
        </Button>
      </Box>

      <Typography variant="subtitle1" gutterBottom>Environment Variables:</Typography>
      <List dense>
        {Object.entries(envVars).map(([key, value]) => (
          <ListItem key={key}>
            <Typography variant="body2">
              <strong>{key}:</strong> {value}
            </Typography>
          </ListItem>
        ))}
      </List>

      <Divider style={{ margin: '16px 0' }} />
      
      <Typography variant="subtitle1" gutterBottom>WebSocket Status: 
        <span style={{ 
          marginLeft: 8,
          color: wsStatus === 'Connected' ? 'green' : 
                 wsStatus === 'Was connected, now closed' ? 'orange' : 'red'
        }}>
          {wsStatus}
        </span>
      </Typography>

      <Divider style={{ margin: '16px 0' }} />
      
      <Box mb={2}>
        <FormControlLabel
          control={
            <Switch
              checked={mockStatus}
              onChange={toggleMockData}
              color="warning"
            />
          }
          label="Use Mock Data"
        />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Changing this setting affects the current session only.
        </Typography>
        <Button 
          variant="outlined" 
          size="small" 
          onClick={saveMockSettingToEnv}
          style={{ marginTop: 8 }}
        >
          Save Setting to .env.local
        </Button>
      </Box>

      <Divider style={{ margin: '16px 0' }} />
      
      <Box mb={2}>
        <Typography variant="subtitle1" gutterBottom>API Endpoint Tests:</Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={testAllEndpoints}
          size="small"
          style={{ marginBottom: 16 }}
        >
          Test All Endpoints
        </Button>
      </Box>

      <List dense>
        {ApiEndpoints.map(endpoint => (
          <React.Fragment key={endpoint.name}>
            <ListItem>
              <Box width="100%">
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">
                    <strong>{endpoint.name}</strong> ({endpoint.method} {endpoint.url})
                  </Typography>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    onClick={() => testEndpoint(endpoint)}
                  >
                    Test
                  </Button>
                </Box>
                {endpointTests[endpoint.name] && (
                  <Box mt={1}>
                    <Typography variant="body2" color={
                      endpointTests[endpoint.name].status.startsWith('OK') ? 'green' : 'error'
                    }>
                      Status: {endpointTests[endpoint.name].status}
                    </Typography>
                    {endpointTests[endpoint.name].data && (
                      <Box 
                        component="pre" 
                        bgcolor="#f5f5f5" 
                        p={1} 
                        mt={1} 
                        borderRadius={1}
                        style={{ 
                          maxHeight: 100, 
                          overflow: 'auto',
                          fontSize: '0.75rem'
                        }}
                      >
                        {JSON.stringify(endpointTests[endpoint.name].data, null, 2)}
                      </Box>
                    )}
                  </Box>
                )}
              </Box>
            </ListItem>
            <Divider />
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
};

export default DebugPanel; 
import React from 'react';
import { Card, CardContent, Typography, CircularProgress, Box } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PerformanceChartProps {
  data: Array<{ timestamp: string; value: number }> | undefined;
  isLoading: boolean;
  error: unknown;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ data, isLoading, error }) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', p: 3, minHeight: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Box>
            <CircularProgress size={30} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Loading performance data...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent sx={{ minHeight: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="error" variant="body1">
            Error loading performance data
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // If no data is available, show a placeholder
  if (data.length === 0) {
    return (
      <Card>
        <CardContent sx={{ minHeight: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No performance data available yet
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Format the data for the chart (if the backend returns ISO dates)
  const chartData = data.map(point => ({
    ...point,
    formattedTime: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Performance
        </Typography>
        <Box sx={{ height: 250, width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="formattedTime" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
              />
              <YAxis />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#8884d8" 
                activeDot={{ r: 8 }} 
                name="Portfolio Value"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PerformanceChart; 
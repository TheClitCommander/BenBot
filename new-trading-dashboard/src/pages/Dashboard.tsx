import React, { useEffect, useState } from 'react';
import healthMonitorApi, { SystemHealthStatus } from '../services/healthMonitorApi';
import { Grid, Box, Typography, useMediaQuery, Theme, CircularProgress, Alert } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import SystemHealthPanel from '../components/SystemHealthPanel';
import PerformanceChart from '../components/PerformanceChart';
import StrategyTable from '../components/StrategyTable';
import ActivePositionsTable from '../components/ActivePositionsTable';
import RecentTradesTable from '../components/RecentTradesTable';
import { useQuery } from '@tanstack/react-query';
import orchestrationApi from '../services/orchestrationApi';
import metricsApi from '../services/metricsApi';
import executionApi from '../services/executionApi';
import LiveMarketData from '../components/LiveMarketData';
import LivePortfolio from '../components/LivePortfolio';
import StatusBanner from '../components/StatusBanner';

// Log the API URL for debugging
console.log("API URL is:", import.meta.env.VITE_API_URL);

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery((theme: Theme) => theme.breakpoints.between('sm', 'lg'));
  
  // System health data
  const { 
    data: healthData,
    isLoading: healthLoading,
    error: healthError
  } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthMonitorApi.getCurrentStatus,
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  // Active strategies data
  const {
    data: strategiesData,
    isLoading: strategiesLoading,
    error: strategiesError
  } = useQuery({
    queryKey: ['activeStrategies'],
    queryFn: orchestrationApi.getActiveStrategies,
    refetchInterval: 60000 // Refresh every minute
  });

  // Performance metrics data
  const {
    data: performanceData,
    isLoading: performanceLoading,
    error: performanceError
  } = useQuery({
    queryKey: ['performanceMetrics'],
    queryFn: metricsApi.getPerformanceMetrics,
    refetchInterval: 120000 // Refresh every 2 minutes
  });

  // Active positions data
  const {
    data: positionsData,
    isLoading: positionsLoading,
    error: positionsError
  } = useQuery({
    queryKey: ['activePositions'],
    queryFn: executionApi.getActivePositions,
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  // Recent trades data
  const {
    data: tradesData,
    isLoading: tradesLoading,
    error: tradesError
  } = useQuery({
    queryKey: ['recentTrades'],
    queryFn: executionApi.getRecentTrades,
    refetchInterval: 60000 // Refresh every minute
  });

  // Create a responsive layout based on screen size
  const getGridLayout = () => {
    if (isMobile) {
      // Mobile layout - single column, full width
      return (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <SystemHealthPanel data={healthData} isLoading={healthLoading} error={healthError} />
          </Grid>
          <Grid item xs={12}>
            <PerformanceChart data={performanceData?.equityCurve} isLoading={performanceLoading} error={performanceError} />
          </Grid>
          <Grid item xs={12}>
            <StrategyTable strategies={strategiesData?.strategies || []} isLoading={strategiesLoading} error={strategiesError} />
          </Grid>
          <Grid item xs={12}>
            <ActivePositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} error={positionsError} />
          </Grid>
          <Grid item xs={12}>
            <RecentTradesTable trades={tradesData?.trades || []} isLoading={tradesLoading} error={tradesError} />
          </Grid>
        </Grid>
      );
    } else if (isTablet) {
      // Tablet layout - two columns
      return (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <SystemHealthPanel data={healthData} isLoading={healthLoading} error={healthError} />
          </Grid>
          <Grid item xs={12}>
            <PerformanceChart data={performanceData?.equityCurve} isLoading={performanceLoading} error={performanceError} />
          </Grid>
          <Grid item sm={6}>
            <StrategyTable strategies={strategiesData?.strategies || []} isLoading={strategiesLoading} error={strategiesError} />
          </Grid>
          <Grid item sm={6}>
            <ActivePositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} error={positionsError} />
          </Grid>
          <Grid item xs={12}>
            <RecentTradesTable trades={tradesData?.trades || []} isLoading={tradesLoading} error={tradesError} />
          </Grid>
        </Grid>
      );
    } else {
      // Desktop layout - multi-column
      return (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={4}>
            <SystemHealthPanel data={healthData} isLoading={healthLoading} error={healthError} />
          </Grid>
          <Grid item xs={12} lg={8}>
            <PerformanceChart data={performanceData?.equityCurve} isLoading={performanceLoading} error={performanceError} />
          </Grid>
          <Grid item xs={12} md={6} lg={4}>
            <StrategyTable strategies={strategiesData?.strategies || []} isLoading={strategiesLoading} error={strategiesError} />
          </Grid>
          <Grid item xs={12} md={6} lg={4}>
            <ActivePositionsTable positions={positionsData?.positions || []} isLoading={positionsLoading} error={positionsError} />
          </Grid>
          <Grid item xs={12} lg={4}>
            <RecentTradesTable trades={tradesData?.trades || []} isLoading={tradesLoading} error={tradesError} />
          </Grid>
        </Grid>
      );
    }
  };

  // Detect overall loading state
  const isLoading = healthLoading || strategiesLoading || performanceLoading || positionsLoading || tradesLoading;
  
  // Detect overall error state
  const hasError = healthError || strategiesError || performanceError || positionsError || tradesError;

  return (
    <div className="dashboard-container">
      <StatusBanner />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <LivePortfolio />
        <LiveMarketData />
      </div>
      
      <Box sx={{ padding: isMobile ? 2 : 3 }}>
        <Typography variant={isMobile ? "h5" : "h4"} component="h1" gutterBottom sx={{ mb: 3 }}>
          BensBot Trading Dashboard
        </Typography>
        
        {isLoading && !hasError && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100px' }}>
            <CircularProgress />
            <Typography variant="body1" sx={{ ml: 2 }}>
              Loading dashboard data...
            </Typography>
          </Box>
        )}
        
        {hasError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Error loading dashboard data. Please check your connection to the trading system backend.
          </Alert>
        )}
        
        {getGridLayout()}
      </Box>
    </div>
  );
};

export default Dashboard; 
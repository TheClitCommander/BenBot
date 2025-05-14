import React, { useEffect, useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  Box,
  Divider,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

// Types for allocation data
interface StrategyAllocation {
  strategy_id: string;
  strategy_type: string;
  asset_class: string;
  allocation_pct: number;
  allocation_amount: number;
  is_active: boolean;
  performance?: {
    total_return?: number;
    sharpe_ratio?: number;
    max_drawdown?: number;
    win_rate?: number;
    consistency_score?: number;
  };
}

interface AssetClassAllocation {
  asset_class: string;
  allocation_pct: number;
  allocation_amount: number;
  color: string;
}

interface AllocationSummary {
  total_capital: number;
  allocated_capital: number;
  reserve_capital: number;
  unallocated_capital: number;
  allocation_model: string;
  asset_class_allocation: {
    amounts: Record<string, number>;
    percentages: Record<string, number>;
  };
  strategy_type_allocation: {
    amounts: Record<string, number>;
    percentages: Record<string, number>;
  };
  allocation_count: number;
  last_updated: string;
}

interface AllocationOverviewProps {
  refreshInterval?: number; // in milliseconds
}

// Sample colors for asset classes
const ASSET_CLASS_COLORS: Record<string, string> = {
  equity: '#4CAF50',  // Green
  crypto: '#2196F3',  // Blue
  forex: '#FFC107',   // Amber
  reserve: '#9E9E9E', // Grey
  unallocated: '#E0E0E0', // Light Grey
};

const AllocationOverview: React.FC<AllocationOverviewProps> = ({ refreshInterval = 30000 }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [allocationSummary, setAllocationSummary] = useState<AllocationSummary | null>(null);
  const [strategies, setStrategies] = useState<StrategyAllocation[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Mock fetch allocation data - replace with actual API call
  const fetchAllocationData = async () => {
    try {
      setLoading(true);
      
      // TODO: Replace with actual API endpoints
      // const summaryResponse = await fetch('/api/portfolio/allocation/summary');
      // const strategiesResponse = await fetch('/api/portfolio/allocation/strategies');
      
      // if (!summaryResponse.ok || !strategiesResponse.ok) {
      //   throw new Error('Failed to fetch allocation data');
      // }
      
      // const summaryData = await summaryResponse.json();
      // const strategiesData = await strategiesResponse.json();
      
      // Mock data for development
      const summaryData: AllocationSummary = {
        total_capital: 100000,
        allocated_capital: 75000,
        reserve_capital: 20000,
        unallocated_capital: 5000,
        allocation_model: "performance_weighted",
        asset_class_allocation: {
          amounts: {
            equity: 40000,
            crypto: 20000,
            forex: 15000
          },
          percentages: {
            equity: 0.40,
            crypto: 0.20,
            forex: 0.15
          }
        },
        strategy_type_allocation: {
          amounts: {
            trend_following: 30000,
            mean_reversion: 25000,
            volatility: 20000
          },
          percentages: {
            trend_following: 0.30,
            mean_reversion: 0.25,
            volatility: 0.20
          }
        },
        allocation_count: 8,
        last_updated: new Date().toISOString()
      };
      
      const strategiesData: StrategyAllocation[] = [
        {
          strategy_id: "trend_equity_1",
          strategy_type: "trend_following",
          asset_class: "equity",
          allocation_pct: 0.20,
          allocation_amount: 20000,
          is_active: true,
          performance: {
            total_return: 15.2,
            sharpe_ratio: 1.8,
            max_drawdown: -5.3,
            win_rate: 62.5,
            consistency_score: 0.78
          }
        },
        {
          strategy_id: "trend_equity_2",
          strategy_type: "trend_following",
          asset_class: "equity",
          allocation_pct: 0.10,
          allocation_amount: 10000,
          is_active: true,
          performance: {
            total_return: 12.6,
            sharpe_ratio: 1.5,
            max_drawdown: -4.8,
            win_rate: 58.3,
            consistency_score: 0.72
          }
        },
        {
          strategy_id: "mean_rev_crypto",
          strategy_type: "mean_reversion",
          asset_class: "crypto",
          allocation_pct: 0.20,
          allocation_amount: 20000,
          is_active: true,
          performance: {
            total_return: 22.4,
            sharpe_ratio: 1.6,
            max_drawdown: -12.5,
            win_rate: 55.0,
            consistency_score: 0.65
          }
        },
        {
          strategy_id: "vol_forex",
          strategy_type: "volatility",
          asset_class: "forex",
          allocation_pct: 0.15,
          allocation_amount: 15000,
          is_active: true,
          performance: {
            total_return: 8.9,
            sharpe_ratio: 1.3,
            max_drawdown: -3.2,
            win_rate: 51.2,
            consistency_score: 0.81
          }
        },
        {
          strategy_id: "mean_rev_equity",
          strategy_type: "mean_reversion",
          asset_class: "equity",
          allocation_pct: 0.10,
          allocation_amount: 10000,
          is_active: true,
          performance: {
            total_return: 10.7,
            sharpe_ratio: 1.4,
            max_drawdown: -6.1,
            win_rate: 60.0,
            consistency_score: 0.70
          }
        }
      ];
      
      setAllocationSummary(summaryData);
      setStrategies(strategiesData);
      setError(null);
    } catch (err) {
      console.error('Error fetching allocation data:', err);
      setError('Failed to load allocation data');
    } finally {
      setLoading(false);
    }
  };

  // Format data for pie chart
  const preparePieChartData = (): AssetClassAllocation[] => {
    if (!allocationSummary) return [];
    
    const pieData: AssetClassAllocation[] = [];
    
    // Add asset class allocations
    Object.entries(allocationSummary.asset_class_allocation.amounts).forEach(([assetClass, amount]) => {
      pieData.push({
        asset_class: assetClass,
        allocation_pct: allocationSummary.asset_class_allocation.percentages[assetClass] || 0,
        allocation_amount: amount,
        color: ASSET_CLASS_COLORS[assetClass] || '#999999'
      });
    });
    
    // Add reserve capital
    if (allocationSummary.reserve_capital > 0) {
      pieData.push({
        asset_class: 'reserve',
        allocation_pct: allocationSummary.reserve_capital / allocationSummary.total_capital,
        allocation_amount: allocationSummary.reserve_capital,
        color: ASSET_CLASS_COLORS.reserve
      });
    }
    
    // Add unallocated capital
    if (allocationSummary.unallocated_capital > 0) {
      pieData.push({
        asset_class: 'unallocated',
        allocation_pct: allocationSummary.unallocated_capital / allocationSummary.total_capital,
        allocation_amount: allocationSummary.unallocated_capital,
        color: ASSET_CLASS_COLORS.unallocated
      });
    }
    
    return pieData;
  };

  // Load data on mount and at refresh interval
  useEffect(() => {
    fetchAllocationData();
    
    // Set up refresh interval
    const intervalId = setInterval(fetchAllocationData, refreshInterval);
    
    // Clean up interval
    return () => clearInterval(intervalId);
  }, [refreshInterval]);

  // Format currency for display
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format percentage for display
  const formatPercentage = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value);
  };

  // Render pie chart tooltip
  const renderTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box sx={{ bgcolor: 'background.paper', p: 1, border: '1px solid #ccc', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
            {data.asset_class}
          </Typography>
          <Typography variant="body2">
            {formatCurrency(data.allocation_amount)} ({formatPercentage(data.allocation_pct)})
          </Typography>
        </Box>
      );
    }
    return null;
  };

  if (loading && !allocationSummary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  const pieChartData = preparePieChartData();

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Capital Allocation
        </Typography>
        
        {allocationSummary && (
          <Grid container spacing={2}>
            {/* Left side - Pie chart */}
            <Grid item xs={12} md={5}>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="allocation_amount"
                      nameKey="asset_class"
                      label={({ asset_class }) => asset_class}
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={renderTooltip} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Grid>
            
            {/* Right side - Summary and strategies */}
            <Grid item xs={12} md={7}>
              <Typography variant="subtitle1">
                Total Capital: {formatCurrency(allocationSummary.total_capital)}
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Allocation Model: {allocationSummary.allocation_model}
                </Typography>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Active Strategies
              </Typography>
              
              <Grid container spacing={1}>
                {strategies
                  .filter(strategy => strategy.is_active)
                  .sort((a, b) => b.allocation_amount - a.allocation_amount)
                  .map(strategy => (
                    <Grid item xs={12} key={strategy.strategy_id}>
                      <Box 
                        sx={{ 
                          p: 1, 
                          border: '1px solid #eee', 
                          borderRadius: 1,
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <Box>
                          <Typography variant="body2">
                            {strategy.strategy_type.replace('_', ' ')}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <Chip 
                              label={strategy.asset_class} 
                              size="small" 
                              sx={{ 
                                bgcolor: ASSET_CLASS_COLORS[strategy.asset_class] || '#999',
                                color: 'white',
                                height: 20,
                                '& .MuiChip-label': { px: 1, py: 0 }
                              }} 
                            />
                            <Typography variant="caption" color="text.secondary">
                              {strategy.performance?.sharpe_ratio && `SR: ${strategy.performance.sharpe_ratio.toFixed(2)}`}
                            </Typography>
                          </Box>
                        </Box>
                        <Box textAlign="right">
                          <Typography variant="body2" fontWeight="bold">
                            {formatCurrency(strategy.allocation_amount)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatPercentage(strategy.allocation_pct)}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  ))}
              </Grid>
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Last updated: {new Date(allocationSummary.last_updated).toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {allocationSummary.allocation_count} strategies
                </Typography>
              </Box>
            </Grid>
          </Grid>
        )}
      </CardContent>
    </Card>
  );
};

export default AllocationOverview; 
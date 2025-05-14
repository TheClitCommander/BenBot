import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Divider,
  Tooltip
} from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

interface MonteCarloResultProps {
  strategy_id: string;
  strategy_name: string;
  asset_class: string;
  monte_carlo_data: {
    consistency_score: number;
    monte_carlo_percentile_5: number;
    monte_carlo_percentile_95: number;
    monte_carlo_max_dd_percentile_95: number;
    monte_carlo_plot?: string; // base64 encoded image
  };
  initial_capital: number;
}

// Helper function to format currency
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

// Helper function to format percentage
const formatPercentage = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value / 100); // Assuming value is in percentage points (e.g., 12.5 for 12.5%)
};

// Function to determine consistency rating
const getConsistencyRating = (score: number): { label: string; color: string } => {
  if (score >= 0.8) {
    return { label: 'Excellent', color: '#4CAF50' }; // Green
  } else if (score >= 0.7) {
    return { label: 'Good', color: '#8BC34A' }; // Light Green
  } else if (score >= 0.6) {
    return { label: 'Moderate', color: '#FFC107' }; // Amber
  } else if (score >= 0.5) {
    return { label: 'Fair', color: '#FF9800' }; // Orange
  } else {
    return { label: 'Poor', color: '#F44336' }; // Red
  }
};

const MonteCarloResult: React.FC<MonteCarloResultProps> = ({
  strategy_id,
  strategy_name,
  asset_class,
  monte_carlo_data,
  initial_capital
}) => {
  const consistency = getConsistencyRating(monte_carlo_data.consistency_score);
  
  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{strategy_name}</Typography>
          <Typography 
            variant="subtitle2"
            sx={{ 
              textTransform: 'uppercase',
              bgcolor: consistency.color,
              color: 'white',
              px: 1,
              py: 0.5,
              borderRadius: 1
            }}
          >
            {consistency.label}
          </Typography>
        </Box>
        
        <Grid container spacing={2}>
          {/* Left side - Plot if available */}
          {monte_carlo_data.monte_carlo_plot && (
            <Grid item xs={12} md={6}>
              <Box 
                component="img"
                src={`data:image/png;base64,${monte_carlo_data.monte_carlo_plot}`}
                alt="Monte Carlo Simulation"
                sx={{
                  width: '100%',
                  height: 'auto',
                  borderRadius: 1,
                  border: '1px solid #eee'
                }}
              />
            </Grid>
          )}
          
          {/* Right side - Statistics */}
          <Grid item xs={12} md={monte_carlo_data.monte_carlo_plot ? 6 : 12}>
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Monte Carlo Analysis
                <Tooltip title="Simulation results based on 1,000 alternative return sequences">
                  <HelpOutlineIcon sx={{ ml: 0.5, fontSize: 16, verticalAlign: 'text-bottom' }} />
                </Tooltip>
              </Typography>
              
              <Divider sx={{ my: 1 }} />
              
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Consistency Score:</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" fontWeight="medium">{monte_carlo_data.consistency_score.toFixed(2)}</Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    5th Percentile Outcome:
                    <Tooltip title="There's a 5% chance the strategy could perform worse than this value">
                      <HelpOutlineIcon sx={{ ml: 0.5, fontSize: 14, verticalAlign: 'text-bottom' }} />
                    </Tooltip>
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" fontWeight="medium">
                    {formatCurrency(monte_carlo_data.monte_carlo_percentile_5)}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    95th Percentile Outcome:
                    <Tooltip title="There's a 5% chance the strategy could perform better than this value">
                      <HelpOutlineIcon sx={{ ml: 0.5, fontSize: 14, verticalAlign: 'text-bottom' }} />
                    </Tooltip>
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" fontWeight="medium">
                    {formatCurrency(monte_carlo_data.monte_carlo_percentile_95)}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    95th Percentile Max Drawdown:
                    <Tooltip title="There's a 5% chance the strategy could have a worse drawdown than this value">
                      <HelpOutlineIcon sx={{ ml: 0.5, fontSize: 14, verticalAlign: 'text-bottom' }} />
                    </Tooltip>
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" fontWeight="medium" color="error">
                    {formatPercentage(monte_carlo_data.monte_carlo_max_dd_percentile_95)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
            
            <Typography variant="caption" color="text.secondary" display="block" textAlign="right">
              Initial Capital: {formatCurrency(initial_capital)}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default MonteCarloResult; 
import React from 'react';

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
  strategy_name,
  monte_carlo_data,
  initial_capital
}) => {
  const consistency = getConsistencyRating(monte_carlo_data.consistency_score);
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">{strategy_name}</h3>
        <span 
          className="px-2 py-1 text-xs font-semibold uppercase rounded"
          style={{ 
            backgroundColor: consistency.color,
            color: 'white'
          }}
        >
          {consistency.label}
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left side - Plot if available */}
        {monte_carlo_data.monte_carlo_plot && (
          <div>
            <img 
              src={`data:image/png;base64,${monte_carlo_data.monte_carlo_plot}`}
              alt="Monte Carlo Simulation"
              className="w-full h-auto rounded border border-gray-200"
            />
          </div>
        )}
        
        {/* Right side - Statistics */}
        <div>
          <div className="mb-4">
            <h4 className="font-medium mb-2 flex items-center">
              Monte Carlo Analysis
              <span className="ml-1 text-gray-500 cursor-help relative group">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <span className="invisible group-hover:visible absolute z-10 bg-black text-white text-xs p-2 rounded w-48 left-0 ml-6 -mt-1">
                  Simulation results based on 1,000 alternative return sequences
                </span>
              </span>
            </h4>
            
            <div className="border-t border-gray-200 my-2"></div>
            
            <div className="grid grid-cols-2 gap-y-2">
              <div className="text-sm text-gray-600">Consistency Score:</div>
              <div className="text-sm font-medium">{monte_carlo_data.consistency_score.toFixed(2)}</div>
              
              <div className="text-sm text-gray-600 flex items-center">
                5th Percentile Outcome:
                <span className="ml-1 text-gray-500 cursor-help relative group">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                  <span className="invisible group-hover:visible absolute z-10 bg-black text-white text-xs p-2 rounded w-48 left-0 ml-6 -mt-1">
                    There's a 5% chance the strategy could perform worse than this value
                  </span>
                </span>
              </div>
              <div className="text-sm font-medium">
                {formatCurrency(monte_carlo_data.monte_carlo_percentile_5)}
              </div>
              
              <div className="text-sm text-gray-600 flex items-center">
                95th Percentile Outcome:
                <span className="ml-1 text-gray-500 cursor-help relative group">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                  <span className="invisible group-hover:visible absolute z-10 bg-black text-white text-xs p-2 rounded w-48 left-0 ml-6 -mt-1">
                    There's a 5% chance the strategy could perform better than this value
                  </span>
                </span>
              </div>
              <div className="text-sm font-medium">
                {formatCurrency(monte_carlo_data.monte_carlo_percentile_95)}
              </div>
              
              <div className="text-sm text-gray-600 flex items-center">
                95th Percentile Max Drawdown:
                <span className="ml-1 text-gray-500 cursor-help relative group">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                  <span className="invisible group-hover:visible absolute z-10 bg-black text-white text-xs p-2 rounded w-48 left-0 ml-6 -mt-1">
                    There's a 5% chance the strategy could have a worse drawdown than this value
                  </span>
                </span>
              </div>
              <div className="text-sm font-medium text-red-600">
                {formatPercentage(monte_carlo_data.monte_carlo_max_dd_percentile_95)}
              </div>
            </div>
          </div>
          
          <div className="text-xs text-gray-500 text-right">
            Initial Capital: {formatCurrency(initial_capital)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonteCarloResult; 
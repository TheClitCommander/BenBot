import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Play, Download } from 'lucide-react';
import evolutionApi, { GridConfig, GridResult } from '../../services/evolutionApi';

// Sample parameter setups for different strategy types
const PARAMETER_TEMPLATES = {
  'mean_reversion': {
    params: {
      param1_name: 'lookback_period',
      param1_range: [5, 10, 20, 50, 100, 200],
      param2_name: 'entry_threshold',
      param2_range: [1.0, 1.5, 2.0, 2.5, 3.0],
      fixed_params: {
        exit_threshold: 0.5,
        stop_loss: 5.0,
        position_size: 0.1
      }
    },
    metrics: ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
  },
  'trend_following': {
    params: {
      param1_name: 'fast_period',
      param1_range: [5, 10, 15, 20, 30, 50],
      param2_name: 'slow_period',
      param2_range: [20, 50, 100, 150, 200],
      fixed_params: {
        signal_period: 9,
        entry_strength: 0.1,
        exit_strength: -0.1
      }
    },
    metrics: ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
  },
  'breakout': {
    params: {
      param1_name: 'channel_period',
      param1_range: [10, 20, 50, 100],
      param2_name: 'volatility_factor',
      param2_range: [1.0, 1.5, 2.0, 2.5, 3.0],
      fixed_params: {
        confirmation_bars: 2,
        profit_target: 5.0,
        max_holding_period: 20
      }
    },
    metrics: ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
  }
};

const BacktestGrid: React.FC = () => {
  const queryClient = useQueryClient();
  
  // State for grid configuration
  const [selectedType, setSelectedType] = useState<string>('mean_reversion');
  const [selectedMetric, setSelectedMetric] = useState<string>('total_return');
  const [gridParams, setGridParams] = useState<any>(PARAMETER_TEMPLATES.mean_reversion.params);
  const [selectedGridId, setSelectedGridId] = useState<string | null>(null);
  
  // Fetch available grids
  const { data: gridsData, isLoading: isGridsLoading } = useQuery({
    queryKey: ['grids'],
    queryFn: () => evolutionApi.listGrids(),
    refetchInterval: 10000
  });
  
  // Fetch selected grid results
  const { data: gridResultData, isLoading: isGridResultLoading } = useQuery({
    queryKey: ['gridResult', selectedGridId],
    queryFn: () => evolutionApi.getGridResults(selectedGridId!),
    enabled: !!selectedGridId,
    refetchInterval: selectedGridId ? 5000 : false
  });
  
  // Create grid mutation
  const createGridMutation = useMutation({
    mutationFn: (config: GridConfig) => evolutionApi.createBacktestGrid(config),
    onSuccess: (response) => {
      if (response.success && response.data?.grid_id) {
        setSelectedGridId(response.data.grid_id);
        queryClient.invalidateQueries({ queryKey: ['grids'] });
      }
    }
  });
  
  // Handle strategy type change
  const handleStrategyTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const type = e.target.value;
    setSelectedType(type);
    setGridParams(PARAMETER_TEMPLATES[type as keyof typeof PARAMETER_TEMPLATES].params);
  };
  
  // Handle creating new grid
  const handleCreateGrid = () => {
    const config: GridConfig = {
      ...gridParams,
      strategy_type: selectedType,
      metric: selectedMetric
    };
    
    createGridMutation.mutate(config);
  };
  
  // Handle selecting existing grid
  const handleSelectGrid = (gridId: string) => {
    setSelectedGridId(gridId);
  };
  
  // Render form to create a new grid
  const renderGridForm = () => {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-4">
        <h3 className="font-medium mb-4">Parameter Grid Configuration</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Strategy Type</label>
            <select
              className="w-full p-2 border border-border rounded-md bg-background"
              value={selectedType}
              onChange={handleStrategyTypeChange}
            >
              <option value="mean_reversion">Mean Reversion</option>
              <option value="trend_following">Trend Following</option>
              <option value="breakout">Breakout</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Optimization Metric</label>
            <select
              className="w-full p-2 border border-border rounded-md bg-background"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
            >
              {PARAMETER_TEMPLATES[selectedType as keyof typeof PARAMETER_TEMPLATES].metrics.map((metric) => (
                <option key={metric} value={metric}>
                  {metric.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Parameter 1: {gridParams.param1_name.replace(/_/g, ' ')}
            </label>
            <div className="p-2 border border-border rounded-md bg-background">
              {JSON.stringify(gridParams.param1_range)}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              Parameter 2: {gridParams.param2_name.replace(/_/g, ' ')}
            </label>
            <div className="p-2 border border-border rounded-md bg-background">
              {JSON.stringify(gridParams.param2_range)}
            </div>
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Fixed Parameters</label>
          <div className="p-2 border border-border rounded-md bg-background font-mono text-xs">
            {JSON.stringify(gridParams.fixed_params, null, 2)}
          </div>
        </div>
        
        <button
          className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium disabled:opacity-50"
          onClick={handleCreateGrid}
          disabled={createGridMutation.isPending}
        >
          <Play size={16} className="mr-2" />
          Run Grid Search
        </button>
        
        {createGridMutation.error && (
          <div className="flex items-center p-2 mt-4 bg-destructive/10 text-destructive rounded">
            <AlertCircle size={16} className="mr-2" />
            <span>{String(createGridMutation.error)}</span>
          </div>
        )}
      </div>
    );
  };
  
  // Render list of existing grids
  const renderExistingGrids = () => {
    if (isGridsLoading || !gridsData?.success) {
      return (
        <div className="bg-card border border-border rounded-lg p-4 mb-4">
          <h3 className="font-medium mb-2">Existing Grids</h3>
          <p className="text-muted-foreground">Loading grids...</p>
        </div>
      );
    }
    
    if (!gridsData.data?.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-4 mb-4">
          <h3 className="font-medium mb-2">Existing Grids</h3>
          <p className="text-muted-foreground">No grids found. Create one to get started.</p>
        </div>
      );
    }
    
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-4">
        <h3 className="font-medium mb-2">Existing Grids</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Strategy</th>
                <th className="text-left p-2">Parameters</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {gridsData.data.map((grid) => (
                <tr 
                  key={grid.id} 
                  className={`border-b border-border hover:bg-muted/50 ${
                    selectedGridId === grid.id ? 'bg-muted/50' : ''
                  }`}
                >
                  <td className="p-2 font-mono text-xs">{grid.id.split('_').pop()}</td>
                  <td className="p-2">{grid.strategy_type}</td>
                  <td className="p-2">{grid.param1} × {grid.param2}</td>
                  <td className="p-2">
                    {grid.completed_at ? (
                      <span className="text-bull">Completed</span>
                    ) : (
                      <span className="text-muted-foreground">Running</span>
                    )}
                  </td>
                  <td className="p-2">
                    <button
                      className="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs"
                      onClick={() => handleSelectGrid(grid.id)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };
  
  // Render heatmap of grid results
  const renderGridHeatmap = () => {
    if (!selectedGridId) {
      return (
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-medium mb-2">Parameter Grid Results</h3>
          <p className="text-muted-foreground">Select a grid to view results</p>
        </div>
      );
    }
    
    if (isGridResultLoading || !gridResultData?.success) {
      return (
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-medium mb-2">Parameter Grid Results</h3>
          <p className="text-muted-foreground">Loading grid data...</p>
        </div>
      );
    }
    
    const gridResult = gridResultData.data as GridResult;
    
    // Find min/max values for color scaling
    let minValue = Infinity;
    let maxValue = -Infinity;
    
    for (const row of gridResult.grid_data) {
      for (const cell of row) {
        if (cell.value !== null) {
          minValue = Math.min(minValue, cell.value);
          maxValue = Math.max(maxValue, cell.value);
        }
      }
    }
    
    // Normalize value to color (0-1 range)
    const normalizeValue = (value: number | null) => {
      if (value === null) return 0;
      return (value - minValue) / (maxValue - minValue);
    };
    
    // Generate color from normalized value (0-1)
    const getColor = (normalizedValue: number) => {
      // Use a gradient from red (0) to yellow (0.5) to green (1)
      if (normalizedValue < 0.5) {
        // Red to yellow
        const r = 255;
        const g = Math.round(normalizedValue * 2 * 255);
        return `rgb(${r}, ${g}, 0)`;
      } else {
        // Yellow to green
        const r = Math.round((1 - (normalizedValue - 0.5) * 2) * 255);
        const g = 255;
        return `rgb(${r}, ${g}, 0)`;
      }
    };
    
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-medium">Parameter Grid Results</h3>
          
          {gridResult.best_params && (
            <div className="text-xs">
              <span className="font-medium">Best Parameters:</span>{' '}
              {gridResult.param1.name.replace(/_/g, ' ')} = {gridResult.best_params[gridResult.param1.name]},{' '}
              {gridResult.param2.name.replace(/_/g, ' ')} = {gridResult.best_params[gridResult.param2.name]}
            </div>
          )}
        </div>
        
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <div className="text-bear font-medium">{minValue.toFixed(2)}</div>
            <div className="text-center font-medium">{gridResult.metric.replace(/_/g, ' ')}</div>
            <div className="text-bull font-medium">{maxValue.toFixed(2)}</div>
          </div>
          <div className="h-2 w-full bg-gradient-to-r from-bear via-yellow-500 to-bull rounded"></div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-2"></th>
                {gridResult.param2.values.map((value, index) => (
                  <th key={index} className="p-2 text-center text-xs font-medium">
                    {value}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gridResult.grid_data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  <td className="p-2 text-xs font-medium">
                    {gridResult.param1.values[rowIndex]}
                  </td>
                  {row.map((cell, cellIndex) => (
                    <td 
                      key={cellIndex}
                      className="p-2 text-center relative"
                      style={{ 
                        backgroundColor: cell.value !== null ? getColor(normalizeValue(cell.value)) : 'transparent',
                        color: normalizeValue(cell.value || 0) > 0.5 ? 'black' : 'white'
                      }}
                    >
                      {cell.value !== null ? cell.value.toFixed(2) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };
  
  return (
    <div>
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-1">Parameter Optimization</h2>
        <p className="text-muted-foreground">
          Find optimal strategy parameters using grid search
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          {renderGridForm()}
        </div>
        <div>
          {renderExistingGrids()}
        </div>
      </div>
      
      {renderGridHeatmap()}
    </div>
  );
};

export default BacktestGrid; 
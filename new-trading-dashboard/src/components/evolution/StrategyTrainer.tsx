import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Play, FastForward, Award, BarChart } from 'lucide-react';
import evolutionApi, { ParameterSpace } from '../../services/evolutionApi';

// Mock data
const mockStatus = {
  current_generation: 3,
  population_size: 50,
  historical_generations: 2,
  best_strategies_count: 5,
  top_performer: {
    id: 'strat-1234',
    name: 'Mean Reversion v2.3',
    type: 'mean_reversion',
    parameters: {
      lookback_period: 20,
      entry_threshold: 2.0,
      exit_threshold: 0.5,
      stop_loss: 3.5
    },
    performance: {
      total_return: 87.4,
      sharpe_ratio: 1.82,
      max_drawdown: 15.2,
      win_rate: 58.3
    },
    generation: 3,
    parent_ids: ['strat-1122', 'strat-1123'],
    creation_date: '2024-05-01T10:30:00Z'
  },
  config: {
    generations: 5,
    population_size: 50,
    mutation_rate: 0.1,
    crossover_rate: 0.7
  }
};

// Sample strategy types and their parameter spaces
const STRATEGY_TEMPLATES = {
  'mean_reversion': {
    lookback_period: [5, 200],
    entry_threshold: [1.0, 3.0],
    exit_threshold: [0.2, 1.5],
    stop_loss: [2.0, 10.0],
    position_size: [0.1, 1.0],
    use_atr: [true, false]
  },
  'trend_following': {
    fast_period: [5, 50],
    slow_period: [20, 200],
    signal_period: [5, 20],
    entry_strength: [0.1, 0.5],
    exit_strength: [-0.1, -0.3],
    trail_percent: [1.0, 10.0]
  },
  'breakout': {
    channel_period: [10, 100],
    volatility_factor: [1.0, 3.0],
    confirmation_bars: [1, 5],
    profit_target: [2.0, 10.0],
    max_holding_period: [5, 30]
  }
};

const StrategyTrainer: React.FC = () => {
  const queryClient = useQueryClient();
  
  // Use mock data in development
  const useMockData = true;
  
  // State for strategy configuration
  const [selectedType, setSelectedType] = useState<string>('mean_reversion');
  const [parameters, setParameters] = useState<Record<string, any>>(STRATEGY_TEMPLATES.mean_reversion);
  const [populationSize, setPopulationSize] = useState<number>(50);
  const [generations, setGenerations] = useState<number>(20);
  const [mutationRate, setMutationRate] = useState<number>(0.2);
  
  // Get evolution status
  const { data: statusData, isLoading: isStatusLoading } = useQuery({
    queryKey: ['evolutionStatus'],
    queryFn: () => evolutionApi.getStatus(),
    refetchInterval: 5000,
    enabled: !useMockData
  });
  
  const status = useMockData ? mockStatus : (statusData?.success ? statusData.data : null);
  
  // Current generation strategies
  const { data: strategiesData, isLoading: isStrategiesLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => evolutionApi.getStrategies(),
    enabled: !!statusData?.success && !!statusData?.data?.population_size,
    refetchInterval: 5000
  });
  
  // Start evolution mutation
  const startEvolutionMutation = useMutation({
    mutationFn: (data: ParameterSpace) => evolutionApi.startEvolution(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evolutionStatus'] });
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    }
  });
  
  // Run backtest mutation
  const runBacktestMutation = useMutation({
    mutationFn: () => evolutionApi.runBacktest(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evolutionStatus'] });
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    }
  });
  
  // Evolve generation mutation
  const evolveGenerationMutation = useMutation({
    mutationFn: () => evolutionApi.evolveGeneration(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evolutionStatus'] });
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    }
  });
  
  // Auto-promote mutation
  const autoPromoteMutation = useMutation({
    mutationFn: (minPerformance?: number) => evolutionApi.autoPromoteStrategies(minPerformance),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotedStrategies'] });
    }
  });
  
  // Handle strategy type change
  const handleStrategyTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const type = e.target.value;
    setSelectedType(type);
    setParameters(STRATEGY_TEMPLATES[type as keyof typeof STRATEGY_TEMPLATES]);
  };
  
  // Handle starting new evolution
  const handleStartEvolution = () => {
    const parameterSpace: ParameterSpace = {
      type: selectedType,
      parameter_space: parameters
    };
    
    const config = {
      population_size: populationSize,
      generations: generations,
      mutation_rate: mutationRate
    };
    
    startEvolutionMutation.mutate(parameterSpace);
  };
  
  // Handle run backtest
  const handleRunBacktest = () => {
    runBacktestMutation.mutate();
  };
  
  // Handle evolve generation
  const handleEvolveGeneration = () => {
    evolveGenerationMutation.mutate();
  };
  
  // Status card
  const renderStatusCard = () => {
    if (isStatusLoading || !statusData?.success || !statusData?.data) {
      return (
        <div className="bg-card border border-border rounded-lg p-4 mb-4">
          <h3 className="font-medium mb-2">Evolution Status</h3>
          <p className="text-muted-foreground">Loading status...</p>
        </div>
      );
    }
    
    const { current_generation = 0, population_size = 0, best_strategies_count = 0 } = statusData.data;
    
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-4">
        <h3 className="font-medium mb-2">Evolution Status</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Generation</p>
            <p className="text-xl font-semibold">{current_generation}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Population</p>
            <p className="text-xl font-semibold">{population_size}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Best Strategies</p>
            <p className="text-xl font-semibold">{best_strategies_count}</p>
          </div>
        </div>
      </div>
    );
  };
  
  // Control panel
  const renderControlPanel = () => {
    const isRunning = 
      startEvolutionMutation.isPending || 
      runBacktestMutation.isPending || 
      evolveGenerationMutation.isPending;
    
    const hasPopulation = statusData?.success && !!statusData?.data?.population_size;
    
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-4">
        <h3 className="font-medium mb-4">Training Controls</h3>
        
        {/* Training flow controls */}
        <div className="flex space-x-2 mb-4">
          <button
            className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium disabled:opacity-50"
            onClick={handleStartEvolution}
            disabled={isRunning}
          >
            <Play size={16} className="mr-2" />
            Start New
          </button>
          
          <button
            className="flex items-center px-4 py-2 bg-secondary text-secondary-foreground rounded-md font-medium disabled:opacity-50"
            onClick={handleRunBacktest}
            disabled={isRunning || !hasPopulation}
          >
            <BarChart size={16} className="mr-2" />
            Backtest
          </button>
          
          <button
            className="flex items-center px-4 py-2 bg-secondary text-secondary-foreground rounded-md font-medium disabled:opacity-50"
            onClick={handleEvolveGeneration}
            disabled={isRunning || !hasPopulation}
          >
            <FastForward size={16} className="mr-2" />
            Evolve
          </button>
          
          <button
            className="flex items-center px-4 py-2 bg-secondary text-secondary-foreground rounded-md font-medium disabled:opacity-50"
            onClick={() => autoPromoteMutation.mutate(5.0)}  // 5% minimum return
            disabled={isRunning || !hasPopulation}
          >
            <Award size={16} className="mr-2" />
            Auto Promote
          </button>
        </div>
        
        {/* Status/error messages */}
        {(startEvolutionMutation.error || runBacktestMutation.error || evolveGenerationMutation.error) && (
          <div className="flex items-center p-2 mb-4 bg-destructive/10 text-destructive rounded">
            <AlertCircle size={16} className="mr-2" />
            <span>
              {String(startEvolutionMutation.error || runBacktestMutation.error || evolveGenerationMutation.error)}
            </span>
          </div>
        )}
      </div>
    );
  };
  
  // Strategy configuration
  const renderStrategyConfig = () => {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-4">
        <h3 className="font-medium mb-4">Strategy Configuration</h3>
        
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
            <label className="block text-sm font-medium mb-1">Population Size</label>
            <input
              type="number"
              className="w-full p-2 border border-border rounded-md bg-background"
              value={populationSize}
              onChange={(e) => setPopulationSize(parseInt(e.target.value))}
              min={10}
              max={200}
            />
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Generations</label>
            <input
              type="number"
              className="w-full p-2 border border-border rounded-md bg-background"
              value={generations}
              onChange={(e) => setGenerations(parseInt(e.target.value))}
              min={5}
              max={100}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Mutation Rate</label>
            <input
              type="number"
              className="w-full p-2 border border-border rounded-md bg-background"
              value={mutationRate}
              onChange={(e) => setMutationRate(parseFloat(e.target.value))}
              min={0.01}
              max={0.5}
              step={0.01}
            />
          </div>
        </div>
        
        <h4 className="font-medium mb-2">Parameter Ranges</h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(parameters).map(([key, value]) => {
            // Check if value is a range (array) or boolean options
            if (Array.isArray(value) && value.length === 2) {
              if (typeof value[0] === 'boolean') {
                return (
                  <div key={key}>
                    <label className="block text-sm font-medium mb-1">
                      {key.replace(/_/g, ' ')}
                    </label>
                    <select
                      className="w-full p-2 border border-border rounded-md bg-background"
                      value={String(value[0])}
                      onChange={(e) => {
                        const newValue = e.target.value === 'true';
                        setParameters({
                          ...parameters,
                          [key]: [newValue, !newValue]
                        });
                      }}
                    >
                      <option value="true">True</option>
                      <option value="false">False</option>
                    </select>
                  </div>
                );
              } else {
                return (
                  <div key={key}>
                    <label className="block text-sm font-medium mb-1">
                      {key.replace(/_/g, ' ')}
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        className="w-1/2 p-2 border border-border rounded-md bg-background"
                        value={value[0]}
                        onChange={(e) => {
                          const newValue = [...value];
                          newValue[0] = parseFloat(e.target.value);
                          setParameters({
                            ...parameters,
                            [key]: newValue
                          });
                        }}
                        step={typeof value[0] === 'number' && Number.isInteger(value[0]) ? 1 : 0.1}
                      />
                      <span>to</span>
                      <input
                        type="number"
                        className="w-1/2 p-2 border border-border rounded-md bg-background"
                        value={value[1]}
                        onChange={(e) => {
                          const newValue = [...value];
                          newValue[1] = parseFloat(e.target.value);
                          setParameters({
                            ...parameters,
                            [key]: newValue
                          });
                        }}
                        step={typeof value[1] === 'number' && Number.isInteger(value[1]) ? 1 : 0.1}
                      />
                    </div>
                  </div>
                );
              }
            } else {
              return null;
            }
          })}
        </div>
      </div>
    );
  };
  
  // Population table
  const renderPopulationTable = () => {
    if (isStrategiesLoading || !strategiesData?.success || !strategiesData.data?.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-medium mb-2">Current Population</h3>
          <p className="text-muted-foreground">No strategies available</p>
        </div>
      );
    }
    
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="font-medium mb-2">Current Population</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Name</th>
                <th className="text-right p-2">Return</th>
                <th className="text-right p-2">Sharpe</th>
                <th className="text-right p-2">Max DD</th>
                <th className="text-right p-2">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {strategiesData.data.slice(0, 10).map((strategy) => (
                <tr key={strategy.id} className="border-b border-border hover:bg-muted/50">
                  <td className="p-2 font-mono text-xs">{strategy.id.split('_').pop()}</td>
                  <td className="p-2">{strategy.name}</td>
                  <td className="p-2 text-right">
                    <span className={strategy.performance?.total_return && strategy.performance.total_return >= 0 ? 'text-bull' : 'text-bear'}>
                      {strategy.performance?.total_return?.toFixed(2) || '0.00'}%
                    </span>
                  </td>
                  <td className="p-2 text-right">{strategy.performance?.sharpe_ratio?.toFixed(2) || '0.00'}</td>
                  <td className="p-2 text-right">{strategy.performance?.max_drawdown?.toFixed(2) || '0.00'}%</td>
                  <td className="p-2 text-right">{strategy.performance?.win_rate?.toFixed(2) || '0.00'}%</td>
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
        <h2 className="text-xl font-semibold mb-1">Strategy Trainer</h2>
        <p className="text-muted-foreground">
          Train and evolve trading strategies using genetic algorithms
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          {renderStatusCard()}
          {renderControlPanel()}
        </div>
        <div>
          {renderStrategyConfig()}
        </div>
      </div>
      
      {renderPopulationTable()}
    </div>
  );
};

export default StrategyTrainer; 
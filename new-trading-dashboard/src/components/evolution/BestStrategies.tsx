import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Award, ArrowUp, ArrowDown, ChevronDown, ChevronUp } from 'lucide-react';
import evolutionApi from '../../services/evolutionApi';

// Mock data for development
const mockStrategies = [
  {
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
    generation: 5,
    parent_ids: ['strat-1122', 'strat-1123'],
    creation_date: '2024-05-01T10:30:00Z'
  },
  {
    id: 'strat-1235',
    name: 'Trend Follower Alpha',
    type: 'trend_following',
    parameters: {
      fast_period: 10,
      slow_period: 50,
      signal_period: 9,
      entry_strength: 0.2
    },
    performance: {
      total_return: 122.1,
      sharpe_ratio: 2.15,
      max_drawdown: 18.7,
      win_rate: 51.2
    },
    generation: 4,
    parent_ids: ['strat-1120'],
    creation_date: '2024-04-28T14:45:00Z'
  },
  {
    id: 'strat-1236',
    name: 'Breakout Hunter',
    type: 'breakout',
    parameters: {
      channel_period: 20,
      volatility_factor: 2.0,
      confirmation_bars: 2
    },
    performance: {
      total_return: 96.8,
      sharpe_ratio: 1.95,
      max_drawdown: 12.5,
      win_rate: 45.8
    },
    generation: 3,
    parent_ids: [],
    creation_date: '2024-04-25T09:15:00Z'
  }
];

const BestStrategies: React.FC = () => {
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  
  // Use mock data in development, real API in production
  const useMockData = true;
  
  // Fetch best strategies
  const { data: strategiesData, isLoading: isStrategiesLoading } = useQuery({
    queryKey: ['bestStrategies'],
    queryFn: () => evolutionApi.getBestStrategies(10),
    refetchInterval: 30000,
    enabled: !useMockData
  });
  
  const strategies = useMockData ? mockStrategies : (strategiesData?.success ? strategiesData.data : []);
  
  // Toggle expanded strategy
  const toggleStrategy = (id: string) => {
    if (expandedStrategy === id) {
      setExpandedStrategy(null);
    } else {
      setExpandedStrategy(id);
    }
  };
  
  // Format parameter value
  const formatParamValue = (value: any) => {
    if (typeof value === 'boolean') {
      return value ? 'true' : 'false';
    } else if (typeof value === 'number') {
      return Number.isInteger(value) ? value : value.toFixed(2);
    } else {
      return String(value);
    }
  };
  
  // Sort strategies by total return
  const getSortedStrategies = () => {
    if (!strategiesData?.success || !strategiesData.data) {
      return [];
    }
    
    return [...strategiesData.data].sort((a, b) => {
      const returnA = a.performance?.total_return || 0;
      const returnB = b.performance?.total_return || 0;
      return returnB - returnA;
    });
  };
  
  // Group strategies by type
  const getStrategyGroups = () => {
    const strategies = getSortedStrategies();
    const groups: Record<string, Strategy[]> = {};
    
    strategies.forEach((strategy) => {
      if (!groups[strategy.type]) {
        groups[strategy.type] = [];
      }
      groups[strategy.type].push(strategy);
    });
    
    return groups;
  };
  
  if (isStrategiesLoading && !useMockData) {
    return (
      <div className="p-4 text-center">
        <div className="animate-pulse">Loading best strategies...</div>
      </div>
    );
  }
  
  const strategyGroups = getStrategyGroups();
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center mb-4">
        <Award className="mr-2 text-primary" size={20} />
        <h2 className="text-xl font-semibold">Best Strategies</h2>
      </div>
      
      {Object.entries(strategyGroups).map(([type, strategies]) => (
        <div key={type} className="mb-6">
          <h3 className="text-lg font-medium mb-2 border-b border-border pb-2">
            {type.replace(/_/g, ' ').split(' ').map(word => 
              word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ')}
          </h3>
          
          <div className="space-y-3">
            {strategies.map((strategy) => (
              <div 
                key={strategy.id} 
                className="border border-border rounded-lg overflow-hidden bg-card"
              >
                {/* Strategy header */}
                <div 
                  className="p-3 flex items-center justify-between cursor-pointer hover:bg-muted/50"
                  onClick={() => toggleStrategy(strategy.id)}
                >
                  <div>
                    <div className="font-medium">{strategy.name}</div>
                    <div className="text-xs text-muted-foreground">
                      Generation {strategy.generation} • ID: {strategy.id.split('_').pop()}
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <div className="mr-4 text-right">
                      <div className={`font-medium ${(strategy.performance?.total_return || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
                        {(strategy.performance?.total_return || 0).toFixed(2)}%
                        {(strategy.performance?.total_return || 0) >= 0 ? 
                          <ArrowUp className="inline ml-1" size={16} /> : 
                          <ArrowDown className="inline ml-1" size={16} />
                        }
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Sharpe: {(strategy.performance?.sharpe_ratio || 0).toFixed(2)}
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id ? 
                      <ChevronUp size={20} /> : 
                      <ChevronDown size={20} />
                    }
                  </div>
                </div>
                
                {/* Expanded details */}
                {expandedStrategy === strategy.id && (
                  <div className="p-3 border-t border-border bg-muted/20">
                    <div className="mb-2">
                      <h4 className="text-sm font-medium mb-1">Performance Metrics</h4>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="p-2 bg-background rounded">
                          <div className="text-xs text-muted-foreground">Total Return</div>
                          <div className={`font-medium ${(strategy.performance?.total_return || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
                            {(strategy.performance?.total_return || 0).toFixed(2)}%
                          </div>
                        </div>
                        <div className="p-2 bg-background rounded">
                          <div className="text-xs text-muted-foreground">Sharpe Ratio</div>
                          <div className="font-medium">
                            {(strategy.performance?.sharpe_ratio || 0).toFixed(2)}
                          </div>
                        </div>
                        <div className="p-2 bg-background rounded">
                          <div className="text-xs text-muted-foreground">Max Drawdown</div>
                          <div className="font-medium text-bear">
                            {(strategy.performance?.max_drawdown || 0).toFixed(2)}%
                          </div>
                        </div>
                        <div className="p-2 bg-background rounded">
                          <div className="text-xs text-muted-foreground">Win Rate</div>
                          <div className="font-medium">
                            {(strategy.performance?.win_rate || 0).toFixed(2)}%
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium mb-1">Parameters</h4>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                        {Object.entries(strategy.parameters).map(([key, value]) => (
                          <div key={key} className="text-xs flex justify-between">
                            <span className="text-muted-foreground">
                              {key.replace(/_/g, ' ')}:
                            </span>
                            <span className="font-medium">
                              {formatParamValue(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {strategy.parent_ids && strategy.parent_ids.length > 0 && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        <span className="font-medium">Parent IDs:</span>{' '}
                        {strategy.parent_ids.map(id => id.split('_').pop()).join(', ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default BestStrategies; 
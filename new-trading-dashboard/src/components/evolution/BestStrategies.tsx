import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Award, ArrowUp, ArrowDown, ChevronDown, ChevronUp } from 'lucide-react';
import evolutionApi, { Strategy } from '@/services/evolutionApi';

const BestStrategies: React.FC = () => {
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  
  // Fetch best strategies
  const { data: strategiesData, isLoading } = useQuery({
    queryKey: ['bestStrategies'],
    queryFn: () => evolutionApi.getBestStrategies(20),
    refetchInterval: 30000
  });
  
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
  
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center mb-4">
          <Award className="mr-2 text-primary" size={20} />
          <h2 className="text-xl font-semibold">Best Strategies</h2>
        </div>
        <p className="text-muted-foreground">Loading strategies...</p>
      </div>
    );
  }
  
  if (!strategiesData?.success || !strategiesData.data?.length) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center mb-4">
          <Award className="mr-2 text-primary" size={20} />
          <h2 className="text-xl font-semibold">Best Strategies</h2>
        </div>
        <p className="text-muted-foreground">No strategies found. Train some strategies to see them here.</p>
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
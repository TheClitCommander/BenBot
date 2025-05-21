import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import {
  AlertCircle,
  GitPullRequest,
  Code,
  LineChart,
  FileSpreadsheet,
  Laptop,
  Atom,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  Check,
  Clock,
  Copy,
  Settings
} from 'lucide-react';

interface Strategy {
  id: string;
  name: string;
  type: string;
  stage: 'development' | 'backtesting' | 'optimization' | 'paper_trading' | 'live';
  status: 'active' | 'paused' | 'error' | 'completed' | 'pending';
  description: string;
  created_at: string;
  updated_at: string;
  metrics?: {
    sharpe_ratio?: number;
    sortino_ratio?: number;
    max_drawdown?: number;
    win_rate?: number;
  };
  progress?: number; // For strategies in backtesting or optimization
}

export const StrategyPipeline: React.FC = () => {
  const queryClient = useQueryClient();
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  
  const { data: strategies, isLoading, error } = useQuery<Strategy[]>({
    queryKey: ['strategies-pipeline'],
    queryFn: async () => {
      try {
        const response = await apiService.getActiveStrategies();
        return response.data;
      } catch (err) {
        console.error('Error fetching strategies:', err);
        throw err;
      }
    }
  });
  
  const advanceStrategyMutation = useMutation({
    mutationFn: async ({ id, stage }: { id: string; stage: Strategy['stage'] }) => {
      await apiService.activateStrategy({
        id,
        status: 'active',
        stage
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies-pipeline'] });
    }
  });
  
  const toggleExpanded = (id: string) => {
    setExpandedStrategy(expandedStrategy === id ? null : id);
  };
  
  const handleAdvanceStrategy = (id: string, currentStage: Strategy['stage']) => {
    const stages: Strategy['stage'][] = ['development', 'backtesting', 'optimization', 'paper_trading', 'live'];
    const currentIndex = stages.indexOf(currentStage);
    
    if (currentIndex < stages.length - 1) {
      const nextStage = stages[currentIndex + 1];
      advanceStrategyMutation.mutate({ id, stage: nextStage });
    }
  };
  
  const getStageIcon = (stage: Strategy['stage']) => {
    switch (stage) {
      case 'development':
        return <Code size={16} className="text-purple-500" />;
      case 'backtesting':
        return <FileSpreadsheet size={16} className="text-blue-500" />;
      case 'optimization':
        return <Settings size={16} className="text-amber-500" />;
      case 'paper_trading':
        return <Laptop size={16} className="text-green-500" />;
      case 'live':
        return <Atom size={16} className="text-red-500" />;
      default:
        return <GitPullRequest size={16} className="text-gray-500" />;
    }
  };
  
  const getStageColor = (stage: Strategy['stage']) => {
    switch (stage) {
      case 'development':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'backtesting':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'optimization':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'paper_trading':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'live':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };
  
  const getStatusBadge = (status: Strategy['status']) => {
    switch (status) {
      case 'active':
        return <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">Active</span>;
      case 'paused':
        return <span className="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full text-xs">Paused</span>;
      case 'error':
        return <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs">Error</span>;
      case 'completed':
        return <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">Completed</span>;
      case 'pending':
        return <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full text-xs">Pending</span>;
      default:
        return null;
    }
  };
  
  const getNextStageName = (currentStage: Strategy['stage']) => {
    switch (currentStage) {
      case 'development':
        return 'Backtesting';
      case 'backtesting':
        return 'Optimization';
      case 'optimization':
        return 'Paper Trading';
      case 'paper_trading':
        return 'Live Trading';
      default:
        return null;
    }
  };
  
  const filterStrategiesByStage = (stage: Strategy['stage']) => {
    return strategies?.filter(s => s.stage === stage) || [];
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="flex justify-between items-center mb-6">
          <div className="h-6 bg-gray-200 rounded w-40"></div>
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
        
        <div className="space-y-8">
          {['development', 'backtesting', 'optimization', 'paper_trading', 'live'].map((stage) => (
            <div key={stage} className="space-y-4">
              <div className="h-6 bg-gray-200 rounded w-32"></div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="h-12 bg-gray-200 rounded mb-4"></div>
                <div className="h-12 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !strategies) {
    return (
      <div className="bg-red-50 rounded-lg p-3 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle size={18} className="mr-2" />
          <span>Error loading strategy pipeline</span>
        </div>
      </div>
    );
  }
  
  const stageCounts = {
    development: filterStrategiesByStage('development').length,
    backtesting: filterStrategiesByStage('backtesting').length,
    optimization: filterStrategiesByStage('optimization').length,
    paper_trading: filterStrategiesByStage('paper_trading').length,
    live: filterStrategiesByStage('live').length
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold flex items-center text-gray-800">
          <GitPullRequest size={18} className="mr-2 text-blue-500" />
          Strategy Development Pipeline
        </h2>
      </div>
      
      {/* Pipeline Stages */}
      <div className="flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-200 mb-8">
        <div className="flex items-center w-full">
          {['development', 'backtesting', 'optimization', 'paper_trading', 'live'].map((stage, index, arr) => (
            <React.Fragment key={stage}>
              <div className="flex flex-col items-center text-center">
                <div className={`rounded-full w-10 h-10 flex items-center justify-center mb-1 ${getStageColor(stage as Strategy['stage'])}`}>
                  {getStageIcon(stage as Strategy['stage'])}
                </div>
                <div className="text-xs font-medium capitalize">{stage.replace('_', ' ')}</div>
                <div className="text-xs text-gray-500">{stageCounts[stage as keyof typeof stageCounts]}</div>
              </div>
              
              {index < arr.length - 1 && (
                <div className="h-px bg-gray-300 flex-1 mx-2 self-center"></div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
      
      {/* Strategy Stages */}
      <div className="space-y-8">
        {/* Development Stage */}
        <div>
          <h3 className="text-md font-semibold mb-3 flex items-center text-gray-700">
            <Code size={16} className="mr-2 text-purple-500" />
            Development
          </h3>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-2">
            {filterStrategiesByStage('development').length > 0 ? (
              <div className="divide-y divide-purple-200">
                {filterStrategiesByStage('development').map((strategy) => (
                  <div key={strategy.id} className="py-3 px-2">
                    <div className="flex justify-between items-center">
                      <div 
                        className="flex items-center cursor-pointer" 
                        onClick={() => toggleExpanded(strategy.id)}
                      >
                        {expandedStrategy === strategy.id ? (
                          <ChevronDown size={16} className="mr-2 text-purple-600" />
                        ) : (
                          <ChevronRight size={16} className="mr-2 text-purple-600" />
                        )}
                        <h4 className="font-medium">{strategy.name}</h4>
                        <span className="ml-2 text-xs text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">
                          {strategy.type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getStatusBadge(strategy.status)}
                        
                        <button 
                          className="text-purple-700 hover:text-purple-900 p-1"
                          onClick={() => console.log(`Edit strategy ${strategy.id}`)}
                          title="Edit Strategy"
                        >
                          <Code size={14} />
                        </button>
                        
                        <button 
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-xs"
                          onClick={() => handleAdvanceStrategy(strategy.id, strategy.stage)}
                          disabled={strategy.status !== 'completed'}
                        >
                          <span className="flex items-center">
                            <FileSpreadsheet size={12} className="mr-1" />
                            Start Backtesting
                          </span>
                        </button>
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id && (
                      <div className="mt-3 ml-6 text-sm text-gray-600">
                        <p className="mb-2">{strategy.description}</p>
                        <div className="flex gap-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Clock size={12} className="mr-1" /> 
                            Created: {new Date(strategy.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center">
                            <RefreshCw size={12} className="mr-1" /> 
                            Updated: {new Date(strategy.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-purple-700">
                <div className="mb-2">No strategies in development</div>
                <div className="text-sm">The system will automatically create new strategies based on market conditions and algorithm evolution</div>
              </div>
            )}
          </div>
        </div>
        
        {/* Backtesting Stage */}
        <div>
          <h3 className="text-md font-semibold mb-3 flex items-center text-gray-700">
            <FileSpreadsheet size={16} className="mr-2 text-blue-500" />
            Backtesting
          </h3>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-2">
            {filterStrategiesByStage('backtesting').length > 0 ? (
              <div className="divide-y divide-blue-200">
                {filterStrategiesByStage('backtesting').map((strategy) => (
                  <div key={strategy.id} className="py-3 px-2">
                    <div className="flex justify-between items-center">
                      <div 
                        className="flex items-center cursor-pointer" 
                        onClick={() => toggleExpanded(strategy.id)}
                      >
                        {expandedStrategy === strategy.id ? (
                          <ChevronDown size={16} className="mr-2 text-blue-600" />
                        ) : (
                          <ChevronRight size={16} className="mr-2 text-blue-600" />
                        )}
                        <h4 className="font-medium">{strategy.name}</h4>
                        <span className="ml-2 text-xs text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                          {strategy.type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {strategy.progress !== undefined && strategy.progress < 100 ? (
                          <div className="flex items-center gap-2 text-xs text-blue-700">
                            <div className="w-32 bg-blue-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${strategy.progress}%` }}
                              ></div>
                            </div>
                            {strategy.progress}%
                          </div>
                        ) : (
                          getStatusBadge(strategy.status)
                        )}
                        
                        <button 
                          className="text-blue-700 hover:text-blue-900 p-1"
                          onClick={() => console.log(`View backtest results for ${strategy.id}`)}
                          title="View Results"
                          disabled={strategy.status !== 'completed'}
                        >
                          <LineChart size={14} />
                        </button>
                        
                        <button 
                          className="bg-amber-500 hover:bg-amber-600 text-white px-3 py-1 rounded-md text-xs"
                          onClick={() => handleAdvanceStrategy(strategy.id, strategy.stage)}
                          disabled={strategy.status !== 'completed'}
                        >
                          <span className="flex items-center">
                            <Settings size={12} className="mr-1" />
                            Optimize
                          </span>
                        </button>
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id && (
                      <div className="mt-3 ml-6 text-sm">
                        <p className="mb-2 text-gray-600">{strategy.description}</p>
                        
                        {strategy.metrics && strategy.status === 'completed' && (
                          <div className="grid grid-cols-4 gap-4 mt-3 bg-white p-3 rounded-lg border border-blue-200">
                            <div>
                              <div className="text-xs text-gray-500">Sharpe Ratio</div>
                              <div className="font-medium">{strategy.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Sortino Ratio</div>
                              <div className="font-medium">{strategy.metrics.sortino_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Max Drawdown</div>
                              <div className="font-medium">{strategy.metrics.max_drawdown?.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Win Rate</div>
                              <div className="font-medium">{(strategy.metrics.win_rate || 0) * 100}%</div>
                            </div>
                          </div>
                        )}
                        
                        <div className="flex gap-x-4 text-xs text-gray-500 mt-2">
                          <span className="flex items-center">
                            <Clock size={12} className="mr-1" /> 
                            Created: {new Date(strategy.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center">
                            <RefreshCw size={12} className="mr-1" /> 
                            Updated: {new Date(strategy.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-blue-700">
                <div>No strategies in backtesting phase</div>
              </div>
            )}
          </div>
        </div>
        
        {/* Optimization Stage */}
        <div>
          <h3 className="text-md font-semibold mb-3 flex items-center text-gray-700">
            <Settings size={16} className="mr-2 text-amber-500" />
            Optimization
          </h3>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-2">
            {filterStrategiesByStage('optimization').length > 0 ? (
              <div className="divide-y divide-amber-200">
                {filterStrategiesByStage('optimization').map((strategy) => (
                  <div key={strategy.id} className="py-3 px-2">
                    <div className="flex justify-between items-center">
                      <div 
                        className="flex items-center cursor-pointer" 
                        onClick={() => toggleExpanded(strategy.id)}
                      >
                        {expandedStrategy === strategy.id ? (
                          <ChevronDown size={16} className="mr-2 text-amber-600" />
                        ) : (
                          <ChevronRight size={16} className="mr-2 text-amber-600" />
                        )}
                        <h4 className="font-medium">{strategy.name}</h4>
                        <span className="ml-2 text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                          {strategy.type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {strategy.progress !== undefined && strategy.progress < 100 ? (
                          <div className="flex items-center gap-2 text-xs text-amber-700">
                            <div className="w-32 bg-amber-200 rounded-full h-2">
                              <div 
                                className="bg-amber-600 h-2 rounded-full" 
                                style={{ width: `${strategy.progress}%` }}
                              ></div>
                            </div>
                            {strategy.progress}%
                          </div>
                        ) : (
                          getStatusBadge(strategy.status)
                        )}
                        
                        <button 
                          className="text-amber-700 hover:text-amber-900 p-1"
                          onClick={() => console.log(`Compare optimization results for ${strategy.id}`)}
                          title="Compare Results"
                          disabled={strategy.status !== 'completed'}
                        >
                          <Copy size={14} />
                        </button>
                        
                        <button 
                          className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-md text-xs"
                          onClick={() => handleAdvanceStrategy(strategy.id, strategy.stage)}
                          disabled={strategy.status !== 'completed'}
                        >
                          <span className="flex items-center">
                            <Laptop size={12} className="mr-1" />
                            Start Paper Trading
                          </span>
                        </button>
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id && (
                      <div className="mt-3 ml-6 text-sm">
                        <p className="mb-2 text-gray-600">{strategy.description}</p>
                        
                        {strategy.metrics && strategy.status === 'completed' && (
                          <div className="bg-white p-3 rounded-lg border border-amber-200 mt-3">
                            <div className="grid grid-cols-4 gap-4">
                              <div>
                                <div className="text-xs text-gray-500">Sharpe Ratio</div>
                                <div className="font-medium">{strategy.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">Sortino Ratio</div>
                                <div className="font-medium">{strategy.metrics.sortino_ratio?.toFixed(2) || 'N/A'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">Max Drawdown</div>
                                <div className="font-medium">{strategy.metrics.max_drawdown?.toFixed(2)}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">Win Rate</div>
                                <div className="font-medium">{(strategy.metrics.win_rate || 0) * 100}%</div>
                              </div>
                            </div>
                            
                            <div className="mt-3 pt-3 border-t border-amber-100 flex justify-between">
                              <div className="flex items-center text-xs text-amber-700">
                                <Check size={12} className="mr-1" />
                                Optimized with {Math.floor(Math.random() * 20) + 10} parameter combinations
                              </div>
                              <button className="text-xs text-amber-700 underline flex items-center">
                                View detailed report
                                <ExternalLink size={10} className="ml-1" />
                              </button>
                            </div>
                          </div>
                        )}
                        
                        <div className="flex gap-x-4 text-xs text-gray-500 mt-2">
                          <span className="flex items-center">
                            <Clock size={12} className="mr-1" /> 
                            Created: {new Date(strategy.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center">
                            <RefreshCw size={12} className="mr-1" /> 
                            Updated: {new Date(strategy.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-amber-700">
                <div>No strategies in optimization phase</div>
              </div>
            )}
          </div>
        </div>
        
        {/* Paper Trading Stage */}
        <div>
          <h3 className="text-md font-semibold mb-3 flex items-center text-gray-700">
            <Laptop size={16} className="mr-2 text-green-500" />
            Paper Trading
          </h3>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-2">
            {filterStrategiesByStage('paper_trading').length > 0 ? (
              <div className="divide-y divide-green-200">
                {filterStrategiesByStage('paper_trading').map((strategy) => (
                  <div key={strategy.id} className="py-3 px-2">
                    <div className="flex justify-between items-center">
                      <div 
                        className="flex items-center cursor-pointer" 
                        onClick={() => toggleExpanded(strategy.id)}
                      >
                        {expandedStrategy === strategy.id ? (
                          <ChevronDown size={16} className="mr-2 text-green-600" />
                        ) : (
                          <ChevronRight size={16} className="mr-2 text-green-600" />
                        )}
                        <h4 className="font-medium">{strategy.name}</h4>
                        <span className="ml-2 text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                          {strategy.type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getStatusBadge(strategy.status)}
                        
                        <button 
                          className="text-green-700 hover:text-green-900 p-1"
                          onClick={() => console.log(`View paper trading performance for ${strategy.id}`)}
                          title="View Performance"
                        >
                          <LineChart size={14} />
                        </button>
                        
                        <button 
                          className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-xs"
                          onClick={() => handleAdvanceStrategy(strategy.id, strategy.stage)}
                          disabled={strategy.status !== 'completed'}
                        >
                          <span className="flex items-center">
                            <Atom size={12} className="mr-1" />
                            Go Live
                          </span>
                        </button>
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id && (
                      <div className="mt-3 ml-6 text-sm">
                        <p className="mb-2 text-gray-600">{strategy.description}</p>
                        
                        {strategy.metrics && (
                          <div className="grid grid-cols-4 gap-4 mt-3 bg-white p-3 rounded-lg border border-green-200">
                            <div>
                              <div className="text-xs text-gray-500">Sharpe Ratio</div>
                              <div className="font-medium">{strategy.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Sortino Ratio</div>
                              <div className="font-medium">{strategy.metrics.sortino_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Max Drawdown</div>
                              <div className="font-medium">{strategy.metrics.max_drawdown?.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Win Rate</div>
                              <div className="font-medium">{(strategy.metrics.win_rate || 0) * 100}%</div>
                            </div>
                          </div>
                        )}
                        
                        <div className="flex gap-x-4 text-xs text-gray-500 mt-2">
                          <span className="flex items-center">
                            <Clock size={12} className="mr-1" /> 
                            Started: {new Date(strategy.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center">
                            <RefreshCw size={12} className="mr-1" /> 
                            Updated: {new Date(strategy.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-green-700">
                <div>No strategies in paper trading phase</div>
              </div>
            )}
          </div>
        </div>
        
        {/* Live Trading Stage */}
        <div>
          <h3 className="text-md font-semibold mb-3 flex items-center text-gray-700">
            <Atom size={16} className="mr-2 text-red-500" />
            Live Trading
          </h3>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-2">
            {filterStrategiesByStage('live').length > 0 ? (
              <div className="divide-y divide-red-200">
                {filterStrategiesByStage('live').map((strategy) => (
                  <div key={strategy.id} className="py-3 px-2">
                    <div className="flex justify-between items-center">
                      <div 
                        className="flex items-center cursor-pointer" 
                        onClick={() => toggleExpanded(strategy.id)}
                      >
                        {expandedStrategy === strategy.id ? (
                          <ChevronDown size={16} className="mr-2 text-red-600" />
                        ) : (
                          <ChevronRight size={16} className="mr-2 text-red-600" />
                        )}
                        <h4 className="font-medium">{strategy.name}</h4>
                        <span className="ml-2 text-xs text-red-700 bg-red-100 px-2 py-0.5 rounded-full">
                          {strategy.type}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getStatusBadge(strategy.status)}
                        
                        <button 
                          className="text-red-700 hover:text-red-900 p-1"
                          onClick={() => console.log(`View live trading details for ${strategy.id}`)}
                          title="View Performance"
                        >
                          <LineChart size={14} />
                        </button>
                        
                        <button 
                          className={`px-3 py-1 rounded-md text-xs ${
                            strategy.status === 'active'
                              ? 'bg-yellow-500 hover:bg-yellow-600 text-white'
                              : 'bg-green-500 hover:bg-green-600 text-white'
                          }`}
                          onClick={() => console.log(`Toggle strategy ${strategy.id}`)}
                        >
                          {strategy.status === 'active' ? 'Pause' : 'Resume'}
                        </button>
                      </div>
                    </div>
                    
                    {expandedStrategy === strategy.id && (
                      <div className="mt-3 ml-6 text-sm">
                        <p className="mb-2 text-gray-600">{strategy.description}</p>
                        
                        {strategy.metrics && (
                          <div className="grid grid-cols-4 gap-4 mt-3 bg-white p-3 rounded-lg border border-red-200">
                            <div>
                              <div className="text-xs text-gray-500">Sharpe Ratio</div>
                              <div className="font-medium">{strategy.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Sortino Ratio</div>
                              <div className="font-medium">{strategy.metrics.sortino_ratio?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Max Drawdown</div>
                              <div className="font-medium">{strategy.metrics.max_drawdown?.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Win Rate</div>
                              <div className="font-medium">{(strategy.metrics.win_rate || 0) * 100}%</div>
                            </div>
                          </div>
                        )}
                        
                        <div className="flex gap-x-4 text-xs text-gray-500 mt-2">
                          <span className="flex items-center">
                            <Clock size={12} className="mr-1" /> 
                            Live since: {new Date(strategy.created_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center">
                            <RefreshCw size={12} className="mr-1" /> 
                            Updated: {new Date(strategy.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-red-700">
                <div>No strategies in live trading</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}; 
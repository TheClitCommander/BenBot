import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface AIStrategySignal {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  size: number;
  reason: string;
}

interface StrategyStatus {
  id: string;
  name: string;
  type: string;
  status: string;
  instruments: string[];
  timeframe: string;
  priority: number;
  last_sentiment?: number;
  sentiment_threshold?: number;
}

// Custom hook to fetch AI strategies
function useAIStrategies() {
  return useQuery({
    queryKey: ['ai-strategies'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/ai/strategies');
        return data;
      } catch (error) {
        console.error('Error fetching AI strategies:', error);
        throw error;
      }
    },
    refetchInterval: 60000, // Refetch every minute
  });
}

// Custom hook to fetch AI signals
function useAISignals() {
  return useQuery({
    queryKey: ['ai-signals'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/ai/signals');
        return data;
      } catch (error) {
        console.error('Error fetching AI signals:', error);
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export const AiStrategies: React.FC = () => {
  const { data: strategiesData, isLoading: isLoadingStrategies } = useAIStrategies();
  const { data: signalsData, isLoading: isLoadingSignals } = useAISignals();
  const [activeTab, setActiveTab] = useState<'signals' | 'strategies'>('signals');

  // Function to activate a strategy
  const activateStrategy = async (strategyId: string) => {
    try {
      await api.post(`/ai/set-active/${strategyId}`);
      // Refetch data after activation
      await Promise.all([
        useAIStrategies().refetch(),
        useAISignals().refetch()
      ]);
    } catch (error) {
      console.error('Error activating strategy:', error);
      alert('Failed to activate strategy. Please try again.');
    }
  };
  
  // Function to trigger auto-rotation
  const triggerAutoRotation = async () => {
    try {
      const { data } = await api.post('/ai/auto-rotate');
      if (data.rotation_occurred) {
        alert(`Strategy rotated to: ${data.active_strategy}`);
      } else {
        alert('No rotation needed, current strategy is optimal');
      }
      // Refetch data after rotation
      await Promise.all([
        useAIStrategies().refetch(),
        useAISignals().refetch()
      ]);
    } catch (error) {
      console.error('Error during auto-rotation:', error);
      alert('Failed to auto-rotate strategies. Please try again.');
    }
  };

  // Loading states
  if (isLoadingStrategies || isLoadingSignals) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2.5"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2.5"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-6"></div>
        </div>
      </div>
    );
  }

  // Error states
  if (!strategiesData || !signalsData) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="text-red-500">
          Error loading AI strategies data
          <button 
            onClick={() => window.location.reload()}
            className="ml-4 px-3 py-1 bg-blue-100 text-blue-700 rounded-md text-sm font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Helper function for signal confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'bg-green-600 text-white';
    if (confidence > 0.6) return 'bg-green-500 text-white';
    if (confidence > 0.4) return 'bg-yellow-500 text-white';
    if (confidence > 0.2) return 'bg-orange-500 text-white';
    return 'bg-gray-500 text-white';
  };

  // Helper function for action colors
  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return 'bg-green-100 text-green-800';
      case 'sell': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">AI Trading Strategies</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('signals')}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              activeTab === 'signals' 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            Active Signals
          </button>
          <button
            onClick={() => setActiveTab('strategies')}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              activeTab === 'strategies' 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            Strategies
          </button>
          <button
            onClick={triggerAutoRotation}
            className="px-3 py-1 bg-purple-100 text-purple-800 hover:bg-purple-200 rounded-md text-sm font-medium"
          >
            Auto-Rotate
          </button>
        </div>
      </div>
      
      {activeTab === 'signals' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-medium">Active Strategy: {signalsData.strategy_name}</h3>
              <p className="text-sm text-gray-500">{signalsData.strategy_type.replace('_', ' ')} strategy</p>
            </div>
            {signalsData.sentiment !== undefined && (
              <div className="text-right">
                <p className="text-sm text-gray-700">Market Sentiment</p>
                <p className={`text-lg font-bold ${
                  signalsData.sentiment > 0 ? 'text-green-600' : 
                  signalsData.sentiment < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {signalsData.sentiment > 0 ? '+' : ''}{signalsData.sentiment.toFixed(2)}
                </p>
              </div>
            )}
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {signalsData.signals && signalsData.signals.map((signal: AIStrategySignal, index: number) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {signal.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getActionColor(signal.action)}`}>
                        {signal.action.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2.5">
                          <div className={`h-2.5 rounded-full ${getConfidenceColor(signal.confidence)}`} style={{ width: `${signal.confidence * 100}%` }}></div>
                        </div>
                        <span className="ml-2 text-gray-700">{(signal.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {signal.size > 0 ? signal.size.toFixed(2) : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {signal.reason}
                    </td>
                  </tr>
                ))}
                {(!signalsData.signals || signalsData.signals.length === 0) && (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                      No signals available from active strategy
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          {signalsData.market_context && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-2">Market Context</h4>
              <p className="text-gray-700 mb-2">{signalsData.market_context.market_conditions}</p>
              <p className="text-gray-700 italic">Outlook: {signalsData.market_context.outlook}</p>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'strategies' && (
        <div>
          <p className="text-gray-600 mb-4">
            Available AI strategies with performance metrics. Click 'Activate' to manually select a strategy.
          </p>
          
          <div className="grid gap-4 md:grid-cols-2">
            {strategiesData.strategies && Object.entries(strategiesData.strategies).map(([id, strategy]) => {
              const strat = strategy as StrategyStatus;
              const isActive = id === strategiesData.active_strategy;
              
              return (
                <div 
                  key={id}
                  className={`p-4 rounded-lg border ${
                    isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-gray-900">{strat.name}</h3>
                      <p className="text-sm text-gray-500">{strat.type.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        strat.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {strat.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-2 text-sm text-gray-700">
                    <p>Instruments: {strat.instruments.join(', ')}</p>
                    <p>Timeframe: {strat.timeframe}</p>
                    <p>Priority: {strat.priority}</p>
                    {strat.last_sentiment !== undefined && (
                      <p>Last Sentiment: {strat.last_sentiment.toFixed(2)}</p>
                    )}
                  </div>
                  
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={() => activateStrategy(id)}
                      disabled={isActive}
                      className={`px-3 py-1 rounded text-sm font-medium ${
                        isActive
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      }`}
                    >
                      {isActive ? 'Active' : 'Activate'}
                    </button>
                  </div>
                </div>
              );
            })}
            
            {(!strategiesData.strategies || Object.keys(strategiesData.strategies).length === 0) && (
              <div className="col-span-2 p-4 text-center text-gray-500 bg-gray-50 rounded-lg">
                No AI strategies available
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}; 
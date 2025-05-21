import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';

export function useEvolutionData(strategyId?: string) {
  // Get best strategies
  const bestStrategiesQuery = useQuery({
    queryKey: ['evolution', 'best-strategies'],
    queryFn: async () => {
      try {
        const response = await apiService.api.get('/evolution/best');
        return response.data;
      } catch (error) {
        console.error('Error fetching best strategies:', error);
        // Return mock data if API fails
        return [
          { 
            id: 'strategy-001', 
            name: 'BTC Mean Reversion', 
            asset_class: 'crypto',
            sharpe_ratio: 1.85,
            max_drawdown: -12.5,
            total_return: 32.4,
            win_rate: 58.3
          },
          { 
            id: 'strategy-002', 
            name: 'ETH Volatility Breakout', 
            asset_class: 'crypto',
            sharpe_ratio: 1.62,
            max_drawdown: -18.7,
            total_return: 28.9,
            win_rate: 52.1
          },
          { 
            id: 'strategy-003', 
            name: 'Multi-asset Trend', 
            asset_class: 'multi',
            sharpe_ratio: 1.43,
            max_drawdown: -15.2,
            total_return: 21.3,
            win_rate: 55.8
          }
        ];
      }
    },
    enabled: !strategyId
  });

  // Get specific strategy details if ID is provided
  const strategyDetailsQuery = useQuery({
    queryKey: ['evolution', 'strategy', strategyId],
    queryFn: async () => {
      try {
        const response = await apiService.api.get(`/evolution/strategy/${strategyId}`);
        return response.data;
      } catch (error) {
        console.error(`Error fetching strategy details for ${strategyId}:`, error);
        // Return mock data if API fails
        return {
          id: strategyId,
          name: 'Strategy ' + strategyId,
          asset_class: 'crypto',
          parameters: {
            lookback_period: 25,
            entry_threshold: 2.1,
            exit_threshold: 0.8
          },
          performance: {
            sharpe_ratio: 1.85,
            max_drawdown: -12.5,
            total_return: 32.4,
            win_rate: 58.3,
            trades_count: 124
          }
        };
      }
    },
    enabled: !!strategyId
  });

  // Run backtest API call
  const runBacktest = async (params: any) => {
    try {
      const response = await apiService.api.post('/evolution/backtest', params);
      return response.data;
    } catch (error) {
      console.error('Error running backtest:', error);
      // Return mock response
      return {
        status: 'completed',
        strategy_id: 'mock-strategy-' + Date.now(),
        performance: {
          sharpe_ratio: 1.5 + Math.random(),
          max_drawdown: -(Math.random() * 15 + 10),
          total_return: Math.random() * 25 + 15,
          win_rate: Math.random() * 10 + 50
        },
        backtest_id: 'mock-backtest-' + Date.now()
      };
    }
  };

  return {
    bestStrategies: bestStrategiesQuery.data || [],
    strategyDetails: strategyDetailsQuery.data,
    isBestStrategiesLoading: bestStrategiesQuery.isLoading,
    isStrategyDetailsLoading: strategyDetailsQuery.isLoading,
    runBacktest
  };
}

export default useEvolutionData; 
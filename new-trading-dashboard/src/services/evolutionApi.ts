import axios from 'axios';

// Base API URL
const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Strategy interface
export interface Strategy {
  id: string;
  name: string;
  type: string;
  parameters: Record<string, any>;
  performance?: Record<string, number>;
  generation: number;
  parent_ids: string[];
  creation_date: string;
}

// Evolution status interface
export interface EvolutionStatus {
  current_generation: number;
  population_size: number;
  historical_generations: number;
  best_strategies_count: number;
  top_performer: Strategy | null;
  config: Record<string, any>;
}

// Grid result interface
export interface GridResult {
  grid_id: string;
  strategy_type: string;
  param1: {
    name: string;
    values: any[];
  };
  param2: {
    name: string;
    values: any[];
  };
  metric: string;
  grid_data: Array<Array<{
    value: number | null;
    performance?: Record<string, number>;
    error?: string;
  }>>;
  best_params: Record<string, any> | null;
  worst_params: Record<string, any> | null;
  completed_at: string | null;
}

// Parameter space interface for starting evolution
export interface ParameterSpace {
  type: string;
  parameter_space: Record<string, any>;
}

// Grid config interface
export interface GridConfig {
  param1_name: string;
  param1_range: any[];
  param2_name: string;
  param2_range: any[];
  fixed_params?: Record<string, any>;
  strategy_type: string;
  metric?: string;
}

// API response interface
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * API service for the strategy evolution system
 */
const evolutionApi = {
  /**
   * Get current evolution status
   */
  getStatus: async (): Promise<ApiResponse<EvolutionStatus>> => {
    try {
      const response = await axios.get(`${apiBaseUrl}/evolution/status`);
      return response.data;
    } catch (error) {
      console.error('Error fetching evolution status:', error);
      return { success: false, error: 'Failed to fetch evolution status' };
    }
  },

  /**
   * Start a new evolution run
   */
  startEvolution: async (params: ParameterSpace, config?: Record<string, any>): Promise<ApiResponse<{ run_id: string }>> => {
    try {
      const response = await axios.post(`${apiBaseUrl}/evolution/start`, { ...params, config });
      return response.data;
    } catch (error) {
      console.error('Error starting evolution:', error);
      return { success: false, error: 'Failed to start evolution' };
    }
  },

  /**
   * Run backtests for the current generation
   */
  runBacktest: async (): Promise<ApiResponse<null>> => {
    try {
      const response = await axios.post(`${apiBaseUrl}/evolution/backtest`);
      return response.data;
    } catch (error) {
      console.error('Error running backtest:', error);
      return { success: false, error: 'Failed to run backtest' };
    }
  },

  /**
   * Evolve the current generation to create a new one
   */
  evolveGeneration: async (): Promise<ApiResponse<Record<string, any>>> => {
    try {
      const response = await axios.post(`${apiBaseUrl}/evolution/evolve`);
      return response.data;
    } catch (error) {
      console.error('Error evolving generation:', error);
      return { success: false, error: 'Failed to evolve generation' };
    }
  },

  /**
   * Get strategies from current population
   */
  getStrategies: async (generation?: number, limit = 50): Promise<ApiResponse<Strategy[]>> => {
    try {
      const params = new URLSearchParams();
      if (generation !== undefined) params.append('generation', generation.toString());
      if (limit) params.append('limit', limit.toString());

      const response = await axios.get(`${apiBaseUrl}/evolution/strategies?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching strategies:', error);
      return { success: false, error: 'Failed to fetch strategies' };
    }
  },

  /**
   * Get the best strategies found so far
   */
  getBestStrategies: async (limit = 10): Promise<ApiResponse<Strategy[]>> => {
    try {
      const response = await axios.get(`${apiBaseUrl}/evolution/best?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching best strategies:', error);
      return { success: false, error: 'Failed to fetch best strategies' };
    }
  },

  /**
   * Get details of a specific strategy
   */
  getStrategy: async (strategyId: string): Promise<ApiResponse<Strategy>> => {
    try {
      const response = await axios.get(`${apiBaseUrl}/evolution/strategy/${strategyId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching strategy ${strategyId}:`, error);
      return { success: false, error: `Failed to fetch strategy ${strategyId}` };
    }
  },

  /**
   * Auto-promote strategies that meet performance criteria
   */
  autoPromoteStrategies: async (minPerformance?: number): Promise<ApiResponse<Strategy[]>> => {
    try {
      const params = minPerformance !== undefined ? `?min_performance=${minPerformance}` : '';
      const response = await axios.post(`${apiBaseUrl}/evolution/promote${params}`);
      return response.data;
    } catch (error) {
      console.error('Error promoting strategies:', error);
      return { success: false, error: 'Failed to promote strategies' };
    }
  },

  /**
   * Create and run a backtest parameter grid
   */
  createBacktestGrid: async (config: GridConfig): Promise<ApiResponse<{ grid_id: string }>> => {
    try {
      const response = await axios.post(`${apiBaseUrl}/evolution/grid`, config);
      return response.data;
    } catch (error) {
      console.error('Error creating backtest grid:', error);
      return { success: false, error: 'Failed to create backtest grid' };
    }
  },

  /**
   * Get results of a backtest grid
   */
  getGridResults: async (gridId: string): Promise<ApiResponse<GridResult>> => {
    try {
      const response = await axios.get(`${apiBaseUrl}/evolution/grid/${gridId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching grid ${gridId}:`, error);
      return { success: false, error: `Failed to fetch grid ${gridId}` };
    }
  },

  /**
   * List all available backtest grids
   */
  listGrids: async (): Promise<ApiResponse<Record<string, any>[]>> => {
    try {
      const response = await axios.get(`${apiBaseUrl}/evolution/grids`);
      return response.data;
    } catch (error) {
      console.error('Error listing grids:', error);
      return { success: false, error: 'Failed to list grids' };
    }
  }
};

export default evolutionApi; 
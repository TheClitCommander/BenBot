import axios from 'axios';

// Base API URL - ensure this matches your environment configuration
const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// --- TypeScript Interfaces based on Pydantic Models ---

// Utility for optional fields if not using strict null checks extensively
type Optional<T> = T | null | undefined;

export interface EvolutionOverview {
  // Mirror fields from EvoTrader.get_evolution_summary()
  // Example - adjust based on actual EvoTrader output
  current_generation?: number;
  population_size?: number;
  best_fitness?: number;
  // Add other relevant fields from your EvoTrader summary
  [key: string]: any; // For any other dynamic fields
}

export interface ScheduledRunSummary {
  total_scheduled: number;
  active_scheduled_run: Optional<Record<string, any>>;
  // Define structure of active_scheduled_run if known, e.g.:
  // active_scheduled_run?: {
  //   schedule_id: string;
  //   strategy_type: string;
  //   status: string;
  //   next_run_time?: string;
  // };
}

export interface SafetyStatus {
  tradingMode: string;
  emergencyStopActive: boolean;
  circuitBreakers: any; // Define more strictly if CircuitBreakerManager.get_status() is known
  cooldowns: any;       // Define more strictly if CooldownManager.get_status() is known
  tradingAllowed: boolean;
  tradingBlockedReason: Optional<string>;
}

export interface SystemOverviewResponse {
  evolution_overview: EvolutionOverview;
  scheduled_runs_summary: ScheduledRunSummary;
  active_strategies_count: number;
  safety_status: SafetyStatus;
  timestamp: string;
}

export interface StrategyParameter {
  [key: string]: any;
}

export interface StrategyPerformance {
  total_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  trades?: number;
  [key: string]: any;
}

export interface Strategy {
  id: string;
  name: string;
  type: string;
  parameters: StrategyParameter;
  performance?: StrategyPerformance;
  generation?: number;
  parent_ids?: string[];
  creation_date?: string;
  // Add any other fields that active strategies might have from EvoToExecAdapter
  trade_status?: string; // e.g., 'active'
}

export interface OrchestrationApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T; // For single object responses like get_evolution_status
  error?: string;
  // For list responses directly in the root
  strategies?: Strategy[]; // For get_best_strategies, get_active_strategies
  status?: SafetyStatus; // For get_safety_status
}

// For POST /schedule/evolution payload
export interface ScheduleEvolutionPayload {
  strategy_type: string;
  parameter_space: Record<string, any>;
  market_data_id: string;
  schedule_time: string; // ISO format string for time e.g. "22:00:00"
  run_daily: boolean;
  auto_promote: boolean;
  population_size?: number;
  generations?: number;
  mutation_rate?: number;
  crossover_rate?: number;
  elite_size?: number;
}

// Type for the orchestrator API service
interface OrchestratorApiService {
  getSystemOverview: () => Promise<SystemOverviewResponse>;
  scheduleEvolutionRun: (payload: ScheduleEvolutionPayload) => Promise<OrchestrationApiResponse<{schedule_id: string}>>;
  getEvolutionStatus: () => Promise<OrchestrationApiResponse<{evo_trader_status: any, scheduled_runs_summary: any}>>;
  getBestStrategies: (limit?: number) => Promise<OrchestrationApiResponse<Strategy[]>>;
  activateStrategy: (strategyId: string) => Promise<OrchestrationApiResponse<null>>;
  getActiveStrategies: () => Promise<OrchestrationApiResponse<Strategy[]>>;
  getSafetyStatus: () => Promise<OrchestrationApiResponse<SafetyStatus>>;
}

const orchestrationApi: OrchestratorApiService = {
  /**
   * Get a combined overview of the system status.
   */
  getSystemOverview: async (): Promise<SystemOverviewResponse> => {
    try {
      const response = await axios.get<SystemOverviewResponse>(
        `${apiBaseUrl}/orchestration/system/overview`
      );
      return response.data; // Directly returns SystemOverviewResponse structure
    } catch (error) {
      console.error('Error fetching system overview:', error);
      // Provide a default/fallback structure on error to prevent UI crashes
      throw error; // Re-throw to be caught by react-query or component
    }
  },

  /**
   * Schedule a new strategy evolution run.
   */
  scheduleEvolutionRun: async (payload: ScheduleEvolutionPayload): Promise<OrchestrationApiResponse<{schedule_id: string}>> => {
    try {
      const response = await axios.post<OrchestrationApiResponse<{schedule_id: string}>>(
        `${apiBaseUrl}/orchestration/schedule/evolution`,
        payload
      );
      return response.data;
    } catch (error) {
      console.error('Error scheduling evolution run:', error);
      return { success: false, error: 'Failed to schedule evolution run' };
    }
  },

  /**
   * Get the current status of strategy evolution.
   * Note: Backend returns {success: true, data: {success: true, evo_trader_status: ..., scheduled_runs_summary: ...}}
   * We might want to flatten this if UI expects direct data.
   */
  getEvolutionStatus: async (): Promise<OrchestrationApiResponse<{evo_trader_status: any, scheduled_runs_summary: any}>> => {
    try {
      // The backend nests the actual data inside a 'data' field of OrchestrationResponse
      const response = await axios.get<OrchestrationApiResponse<{success: boolean, evo_trader_status: any, scheduled_runs_summary: any}>>(
        `${apiBaseUrl}/orchestration/evolution/status`
      );
      // If response.data.data exists and response.data.data.success is true, return that inner data.
      if (response.data.success && response.data.data) {
        return { 
            success: true, 
            data: {
                evo_trader_status: response.data.data.evo_trader_status,
                scheduled_runs_summary: response.data.data.scheduled_runs_summary
            }
        }; 
      }
      return { success: false, error: response.data.error || 'Failed to parse evolution status' };
    } catch (error) {
      console.error('Error fetching evolution status:', error);
      return { success: false, error: 'Failed to fetch evolution status' };
    }
  },

  /**
   * Get the best performing strategies.
   */
  getBestStrategies: async (limit: number = 10): Promise<OrchestrationApiResponse<Strategy[]>> => {
    try {
      const response = await axios.get<OrchestrationApiResponse<Strategy[]>>(
        `${apiBaseUrl}/orchestration/strategies/best?limit=${limit}`
      );
      return response.data; // Expects {success: boolean, strategies: Strategy[]}
    } catch (error) {
      console.error('Error fetching best strategies:', error);
      return { success: false, strategies: [], error: 'Failed to fetch best strategies' };
    }
  },

  /**
   * Activate a specific strategy for (mock) trading.
   */
  activateStrategy: async (strategyId: string): Promise<OrchestrationApiResponse<null>> => {
    try {
      const response = await axios.post<OrchestrationApiResponse<null>>(
        `${apiBaseUrl}/orchestration/strategies/${strategyId}/activate`
      );
      return response.data;
    } catch (error) {
      console.error(`Error activating strategy ${strategyId}:`, error);
      return { success: false, error: `Failed to activate strategy ${strategyId}` };
    }
  },

  /**
   * Get the list of currently active (mock) strategies.
   */
  getActiveStrategies: async (): Promise<OrchestrationApiResponse<Strategy[]>> => {
    try {
      const response = await axios.get<OrchestrationApiResponse<Strategy[]>>(
        `${apiBaseUrl}/orchestration/strategies/active`
      );
      return response.data; // Expects {success: boolean, strategies: Strategy[]}
    } catch (error) {
      console.error('Error fetching active strategies:', error);
      return { success: false, strategies: [], error: 'Failed to fetch active strategies' };
    }
  },

  /**
   * Get the current safety status.
   */
  getSafetyStatus: async (): Promise<OrchestrationApiResponse<SafetyStatus>> => {
    try {
      const response = await axios.get<OrchestrationApiResponse<SafetyStatus>>(
        `${apiBaseUrl}/orchestration/safety/status`
      );
      // Expects {success: boolean, status: SafetyStatus}
      // If backend wraps status in data field, adjust: response.data.data.status
      return response.data; 
    } catch (error) {
      console.error('Error fetching safety status:', error);
      return { success: false, error: 'Failed to fetch safety status' };
    }
  },
};

export default orchestrationApi; 
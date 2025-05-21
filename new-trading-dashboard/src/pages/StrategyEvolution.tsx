import React, { useState } from 'react';
import StrategyTrainer from '../components/evolution/StrategyTrainer';
import BacktestGrid from '../components/evolution/BacktestGrid';
import BestStrategies from '../components/evolution/BestStrategies';
import MonteCarloResult from '../components/evolution/MonteCarloResult';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`evolution-tabpanel-${index}`}
      aria-labelledby={`evolution-tab-${index}`}
      {...other}
    >
      {value === index && (
        <div className="p-4">
          {children}
        </div>
      )}
    </div>
  );
}

function StrategyEvolution() {
  const [tabValue, setTabValue] = useState(0);
  const [isRunningBacktest, setIsRunningBacktest] = useState(false);
  const [backtestResults, setBacktestResults] = useState<any>(null);

  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRunBacktest = async () => {
    try {
      setIsRunningBacktest(true);
      // Mock API call for now
      setTimeout(() => {
        setBacktestResults({ success: true });
        setIsRunningBacktest(false);
      }, 2000);
    } catch (error) {
      console.error('Error running backtest:', error);
      setIsRunningBacktest(false);
    }
  };

  // Sample data for MonteCarloResult
  const sampleMonteCarloData = {
    strategy_id: "sample-strategy-id",
    strategy_name: "Sample Strategy",
    asset_class: "Crypto",
    monte_carlo_data: {
      consistency_score: 0.75,
      monte_carlo_percentile_5: 10500,
      monte_carlo_percentile_95: 19800,
      monte_carlo_max_dd_percentile_95: 18.5
    },
    initial_capital: 10000
  };

  return (
    <div className="container mx-auto">
      <div className="py-4">
        <h1 className="text-2xl font-bold mb-3">
          Strategy Evolution & Backtesting
        </h1>

        <div className="border-b border-gray-200 mb-3">
          <div className="flex">
            <button 
              className={`py-2 px-4 ${tabValue === 0 ? 'border-b-2 border-blue-500 font-medium' : ''}`}
              onClick={() => setTabValue(0)}
            >
              Strategy Trainer
            </button>
            <button 
              className={`py-2 px-4 ${tabValue === 1 ? 'border-b-2 border-blue-500 font-medium' : ''}`}
              onClick={() => setTabValue(1)}
            >
              Backtest Grid
            </button>
            <button 
              className={`py-2 px-4 ${tabValue === 2 ? 'border-b-2 border-blue-500 font-medium' : ''}`}
              onClick={() => setTabValue(2)}
            >
              Best Strategies
            </button>
            <button 
              className={`py-2 px-4 ${tabValue === 3 ? 'border-b-2 border-blue-500 font-medium' : ''}`}
              onClick={() => setTabValue(3)}
            >
              Monte Carlo Analysis
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <TabPanel value={tabValue} index={0}>
            <div className="mb-3 flex justify-between items-center">
              <h2 className="text-lg font-medium">
                Train and evolve trading strategies
              </h2>
              <button 
                className={`px-4 py-2 bg-blue-500 text-white rounded ${isRunningBacktest ? 'opacity-70' : ''}`}
                onClick={handleRunBacktest}
                disabled={isRunningBacktest}
              >
                {isRunningBacktest ? 'Running Backtest...' : 'Run Backtest'}
              </button>
            </div>
            <StrategyTrainer />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <BacktestGrid />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <BestStrategies />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <MonteCarloResult 
              strategy_id={sampleMonteCarloData.strategy_id}
              strategy_name={sampleMonteCarloData.strategy_name}
              asset_class={sampleMonteCarloData.asset_class}
              monte_carlo_data={sampleMonteCarloData.monte_carlo_data}
              initial_capital={sampleMonteCarloData.initial_capital}
            />
          </TabPanel>
        </div>
      </div>
    </div>
  );
}

export default StrategyEvolution; 
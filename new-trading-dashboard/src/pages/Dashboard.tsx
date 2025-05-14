import React, { useState } from 'react';
import SafetyControls from '../components/trading/SafetyControls';
import SafetyEventHistory from '../components/trading/SafetyEventHistory';
import PerformanceChart from '../components/trading/PerformanceChart';
import PositionTable from '../components/trading/PositionTable';
import SignalLog from '../components/trading/SignalLog';
import StrategyTrainer from '../components/evolution/StrategyTrainer';
import BacktestGrid from '../components/evolution/BacktestGrid';
import BestStrategies from '../components/evolution/BestStrategies';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'safety' | 'performance' | 'evolution'>('overview');
  const [evolutionSubTab, setEvolutionSubTab] = useState<'trainer' | 'grid' | 'best'>('trainer');

  return (
    <div className="container mx-auto p-4">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Trading Dashboard</h1>
        <p className="text-muted-foreground">Monitor and control your trading activities</p>
      </header>

      {/* Dashboard Tabs */}
      <div className="flex border-b mb-6">
        <button
          className={`px-4 py-2 border-b-2 font-medium ${
            activeTab === 'overview' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`px-4 py-2 border-b-2 font-medium ${
            activeTab === 'safety' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('safety')}
        >
          Safety Controls
        </button>
        <button
          className={`px-4 py-2 border-b-2 font-medium ${
            activeTab === 'performance' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button
          className={`px-4 py-2 border-b-2 font-medium ${
            activeTab === 'evolution' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('evolution')}
        >
          Strategy Evolution
        </button>
      </div>

      {/* Dashboard Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            <section>
              <h2 className="text-xl font-medium mb-4">Safety Status</h2>
              <SafetyControls />
            </section>
            
            <section>
              <h2 className="text-xl font-medium mb-4">Performance Overview</h2>
              <PerformanceChart />
            </section>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <section>
                <h2 className="text-xl font-medium mb-4">Current Positions</h2>
                <PositionTable />
              </section>
              
              <section>
                <h2 className="text-xl font-medium mb-4">Recent Signals</h2>
                <SignalLog />
              </section>
            </div>
          </>
        )}
        
        {activeTab === 'safety' && (
          <>
            <section>
              <h2 className="text-xl font-medium mb-4">Safety Controls</h2>
              <SafetyControls />
            </section>
            
            <section className="mt-8">
              <h2 className="text-xl font-medium mb-4">Safety Event History</h2>
              <SafetyEventHistory />
            </section>
          </>
        )}
        
        {activeTab === 'performance' && (
          <>
            <section>
              <h2 className="text-xl font-medium mb-4">Performance Analytics</h2>
              <PerformanceChart />
            </section>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <section>
                <h2 className="text-xl font-medium mb-4">Position Details</h2>
                <PositionTable />
              </section>
              
              <section>
                <h2 className="text-xl font-medium mb-4">Signal Analysis</h2>
                <SignalLog />
              </section>
            </div>
          </>
        )}
        
        {activeTab === 'evolution' && (
          <>
            {/* Evolution subtabs */}
            <div className="flex border-b mb-6">
              <button
                className={`px-4 py-2 border-b-2 font-medium ${
                  evolutionSubTab === 'trainer' 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
                onClick={() => setEvolutionSubTab('trainer')}
              >
                Strategy Trainer
              </button>
              <button
                className={`px-4 py-2 border-b-2 font-medium ${
                  evolutionSubTab === 'grid' 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
                onClick={() => setEvolutionSubTab('grid')}
              >
                Backtest Grid
              </button>
              <button
                className={`px-4 py-2 border-b-2 font-medium ${
                  evolutionSubTab === 'best' 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
                onClick={() => setEvolutionSubTab('best')}
              >
                Best Strategies
              </button>
            </div>
            
            {/* Evolution content */}
            {evolutionSubTab === 'trainer' && <StrategyTrainer />}
            {evolutionSubTab === 'grid' && <BacktestGrid />}
            {evolutionSubTab === 'best' && <BestStrategies />}
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 
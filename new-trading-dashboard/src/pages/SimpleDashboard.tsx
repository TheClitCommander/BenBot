import React from 'react';
import { StatusBanner } from '../components/StatusBanner';
import LiveMarketData from '../components/LiveMarketData';
import LivePortfolio from '../components/LivePortfolio';

const SimpleDashboard: React.FC = () => {
  return (
    <div className="p-4">
      <StatusBanner />
      
      <h1 className="text-2xl font-bold mb-6 mt-4">BenBot Trading Dashboard</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <LivePortfolio />
        <LiveMarketData />
      </div>
      
      <div className="border-t pt-4 text-sm text-gray-500">
        <p>
          WebSocket-powered real-time updates are now active. The data shown above 
          is automatically updated without requiring page refreshes.
        </p>
      </div>
    </div>
  );
};

export default SimpleDashboard; 
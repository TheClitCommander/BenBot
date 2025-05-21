import React from 'react';

interface FooterProps {
  onSwitchToLive: () => void;
  onGoLive: () => void;
  isDemo: boolean;
  isDisabled?: boolean;
}

export const Footer: React.FC<FooterProps> = ({ onSwitchToLive, onGoLive, isDemo, isDisabled = false }) => {
  return (
    <footer className="mt-8 p-4 bg-gray-800 rounded-lg shadow-lg flex justify-between items-center">
      <div>
        <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
          isDemo ? 'bg-yellow-900 text-yellow-300' : 'bg-green-900 text-green-300'
        }`}>
          {isDemo ? 'Using demonstration data' : 'Using LIVE data'}
        </span>
      </div>
      
      <div className="flex gap-3">
        {isDemo && (
          <button
            onClick={onSwitchToLive}
            disabled={isDisabled}
            className="px-4 py-2 border border-gray-600 bg-gray-700 hover:bg-gray-600 text-gray-200 font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Switch to Live Data
          </button>
        )}
        
        {isDemo && (
          <button
            onClick={onGoLive}
            disabled={isDisabled}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Go Live
          </button>
        )}
      </div>
    </footer>
  );
}; 
import React from 'react';

export type TabType = 'strategies' | 'positions' | 'trades' | 'markets' | 'risk' | 'settings' | 'ai';

interface TabItem {
  id: TabType;
  label: string;
}

interface TabNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  tabs?: TabItem[];
}

export const TabNav: React.FC<TabNavProps> = ({ activeTab, onTabChange, tabs }) => {
  const defaultTabs: TabItem[] = [
    { id: 'strategies', label: 'Strategies' },
    { id: 'positions', label: 'Positions' },
    { id: 'trades', label: 'Trades' },
    { id: 'markets', label: 'Markets' },
    { id: 'risk', label: 'Risk' },
    { id: 'settings', label: 'Settings' }
  ];

  const tabItems = tabs || defaultTabs;

  return (
    <div className="mb-6">
      {/* Mobile dropdown for small screens */}
      <div className="sm:hidden">
        <select
          className="block w-full rounded-lg border-gray-700 py-2 px-3 bg-gray-800 text-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
          value={activeTab}
          onChange={(e) => onTabChange(e.target.value as TabType)}
        >
          {tabItems.map((tab) => (
            <option key={tab.id} value={tab.id}>
              {tab.label}
            </option>
          ))}
        </select>
      </div>

      {/* Tabs for larger screens */}
      <div className="hidden sm:block bg-gray-800 rounded-lg">
        <div className="flex flex-wrap">
          {tabItems.map((tab) => (
            <button
              key={tab.id}
              className={`px-4 py-3 font-medium rounded-md transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-900 text-blue-400'
                  : 'text-gray-300 hover:bg-gray-700'
              }`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}; 
import React, { useState, useEffect } from 'react';
import { useActiveStrategies, Strategy } from '../hooks/useActiveStrategies';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { 
  Maximize2, 
  Minimize2, 
  PieChart, 
  BarChart2, 
  Settings, 
  ChevronRight,
  PlayCircle,
  PauseCircle,
  AlertCircle,
  LineChart,
  RefreshCw,
  Clock,
  ArrowUpDown,
  Activity,
  ChevronDown,
  MoreHorizontal,
  Eye,
  Trash2,
  BarChart,
  Play,
  Pause,
  ArrowUpRight,
  ArrowDownRight,
  Layers,
  CheckCircle
} from 'lucide-react';
import { useNavigation } from '../App';

export const StrategyTable: React.FC = () => {
  const { data: strategies = [], isLoading, error } = useActiveStrategies();
  const queryClient = useQueryClient();
  const { navigate } = useNavigation();
  const [expanded, setExpanded] = useState<boolean>(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  
  // Effect to remove the "New Strategy" button from Active Strategies section
  useEffect(() => {
    // Function to remove the "New Strategy" button
    const removeNewStrategyButton = () => {
      // Insert CSS to hide the specific button in the dashboard
      const styleEl = document.createElement('style');
      styleEl.id = 'remove-new-strategy-button-style';
      styleEl.textContent = `
        /* Directly target the button in the Active Strategies section header (from complete_dashboard.html) */
        .section-header:has(h2.section-title:contains("Active Strategies")) button.action-button,
        div.section-header:has(h2:contains("Active Strategies")) button,
        div.section-header:has(.section-title:contains("Active Strategies")) button,
        h2:contains("Active Strategies") + button,
        h2:contains("Active Strategies") ~ button:contains("New Strategy"),
        h2:contains("Active Strategies") ~ .action-button:contains("New Strategy") {
          display: none !important;
          position: absolute !important;
          visibility: hidden !important;
        }
      `;
      
      // Remove any existing style with this ID
      document.getElementById('remove-new-strategy-button-style')?.remove();
      
      // Add the new style
      document.head.appendChild(styleEl);
      
      // Direct DOM manipulation as backup
      document.querySelectorAll('.section-header, [class*="section-header"]').forEach(header => {
        const title = header.querySelector('h2, .section-title');
        if (title && title.textContent && title.textContent.includes('Active Strategies')) {
          const buttons = header.querySelectorAll('button, .action-button');
          buttons.forEach(button => {
            if (button.textContent && button.textContent.includes('New Strategy')) {
              console.log('Found and removing New Strategy button', button);
              (button as HTMLElement).style.display = 'none';
              button.remove();
            }
          });
        }
      });
    };
    
    // Run immediately
    removeNewStrategyButton();
    
    // Run again after a short delay to handle possible delayed rendering
    const timeoutId = setTimeout(removeNewStrategyButton, 500);
    
    // Set up a mutation observer to catch any dynamically added buttons
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) {
          removeNewStrategyButton();
        }
      }
    });
    
    // Start observing the entire document for changes
    observer.observe(document.body, { 
      childList: true, 
      subtree: true 
    });
    
    // Return cleanup function
    return () => {
      observer.disconnect();
      clearTimeout(timeoutId);
      document.getElementById('remove-new-strategy-button-style')?.remove();
    };
  }, []);

  const toggleStrategyMutation = useMutation({
    mutationFn: async ({ strategyId, newStatus }: { strategyId: string; newStatus: 'active' | 'paused' }) => {
      try {
        // In a real app, call the API endpoint to toggle the strategy
        const response = await apiService.activateStrategy({
          id: strategyId,
          status: newStatus
        });
        return response.data;
      } catch (error) {
        console.error('Error toggling strategy:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      // Invalidate and refetch active strategies data
      queryClient.invalidateQueries({ queryKey: ['activeStrategies'] });
    }
  });
  
  const deleteStrategyMutation = useMutation({
    mutationFn: async (strategyId: string) => {
      // In a real app, call the API endpoint to delete the strategy
      await new Promise(resolve => setTimeout(resolve, 500)); 
      console.log(`Deleting strategy ${strategyId}`);
      return { strategyId };
    },
    onSuccess: (data) => {
      setShowDeleteConfirm(null);
      setSelectedStrategy(null);
      queryClient.invalidateQueries({ queryKey: ['activeStrategies'] });
    }
  });

  const saveSettingsMutation = useMutation({
    mutationFn: async (data: { strategyId: string, name: string, riskLevel: string, autoRestart: boolean }) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Saving settings:', data);
      return data;
    },
    onSuccess: (data) => {
      setShowSettings(null);
      setSelectedStrategy(null);
      queryClient.invalidateQueries({ queryKey: ['activeStrategies'] });
    }
  });

  if (isLoading) {
    return (
      <div className="h-full">
        <h2 className="text-md font-semibold mb-3 flex items-center text-gray-700">
          <BarChart size={16} className="mr-2 text-blue-500" />
          Active Strategies
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg p-4 border border-gray-200 h-36">
              <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
              <div className="h-6 bg-gray-200 rounded w-32 mb-2"></div>
              <div className="flex justify-between">
                <div className="h-4 bg-gray-200 rounded w-20"></div>
                <div className="h-6 bg-gray-200 rounded-md w-16"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !strategies) {
    return (
      <div className="p-4">
        <div className="bg-red-50 rounded-lg p-3 border border-red-200">
          <div className="flex items-center text-red-600">
            <AlertCircle size={18} className="mr-2" />
            <span>Error loading strategies</span>
          </div>
        </div>
      </div>
    );
  }

  const toggleDropdown = (strategyId: string) => {
    if (activeDropdown === strategyId) {
      setActiveDropdown(null);
    } else {
      setActiveDropdown(strategyId);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700';
      case 'paused':
        return 'bg-yellow-100 text-yellow-700';
      case 'error':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getPnlColorClass = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="bg-green-100 text-green-700 px-2 py-1 text-xs rounded font-medium">Active</span>;
      case 'paused':
        return <span className="bg-amber-100 text-amber-700 px-2 py-1 text-xs rounded font-medium">Paused</span>;
      case 'backtest':
        return <span className="bg-blue-100 text-blue-700 px-2 py-1 text-xs rounded font-medium">Backtest</span>;
      default:
        return <span className="bg-gray-100 text-gray-700 px-2 py-1 text-xs rounded font-medium">Unknown</span>;
    }
  };

  const toggleStrategy = (id: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    toggleStrategyMutation.mutate({ strategyId: id, newStatus });
  };

  const renderPnl = (value: number) => {
    if (value === 0) return <span className="text-gray-500">0.0%</span>;
    
    return (
      <span className={`flex items-center ${value > 0 ? 'text-green-600' : 'text-red-600'}`}>
        {value > 0 ? (
          <ArrowUpRight className="h-3 w-3 mr-1" />
        ) : (
          <ArrowDownRight className="h-3 w-3 mr-1" />
        )}
        {value > 0 ? '+' : ''}{value}%
      </span>
    );
  };

  const handleEditSettings = (strategyId: string) => {
    const strategy = strategies.find(s => s.id === strategyId) || null;
    setSelectedStrategy(strategy);
    setShowSettings(strategyId);
  };

  const handleDeleteClick = (strategyId: string) => {
    const strategy = strategies.find(s => s.id === strategyId) || null;
    setSelectedStrategy(strategy);
    setShowDeleteConfirm(strategyId);
  };

  const confirmDelete = (strategyId: string) => {
    deleteStrategyMutation.mutate(strategyId);
  };
  
  const handleSaveSettings = (strategyId: string) => {
    const nameInput = document.getElementById('strategy-name') as HTMLInputElement;
    const riskLevelSelect = document.getElementById('risk-level') as HTMLSelectElement;
    const autoRestartCheckbox = document.getElementById('auto-restart') as HTMLInputElement;
    
    if (nameInput && riskLevelSelect && autoRestartCheckbox) {
      saveSettingsMutation.mutate({
        strategyId,
        name: nameInput.value,
        riskLevel: riskLevelSelect.value,
        autoRestart: autoRestartCheckbox.checked
      });
    }
  };

  const navigateToStrategyDetails = (strategyId: string) => {
    navigate(`/strategies/${strategyId}`);
  };

  return (
    <div className="h-full relative">
      <h2 className="text-md font-semibold mb-3 flex items-center text-gray-700">
        <BarChart size={16} className="mr-2 text-blue-500" />
        Active Strategies
      </h2>
      
      <p className="text-xs text-gray-500 mb-3">
        The system will automatically create new strategies based on market conditions and algorithm evolution.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 h-[calc(100%-40px)] overflow-auto">
        {strategies.map((strategy) => (
          <div 
            key={strategy.id} 
            className="bg-white rounded-lg p-4 border border-gray-200 flex flex-col justify-between relative"
          >
            <div>
              <div className="flex justify-between items-start mb-2">
                <h3 
                  className="font-medium text-gray-800 truncate cursor-pointer hover:underline"
                  onClick={() => navigateToStrategyDetails(strategy.id)}
                >
                  {strategy.name}
                </h3>
                {renderStatusBadge(strategy.status)}
              </div>
              
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mb-3">
                <div className="text-xs text-gray-500">Market</div>
                <div className="text-xs text-gray-500">Type</div>
                
                <div className="text-xs font-medium">{strategy.market}</div>
                <div className="text-xs font-medium flex items-center">
                  <Layers className="h-3 w-3 mr-1 text-gray-400" />
                  {strategy.type}
                </div>
                
                <div className="text-xs text-gray-500">Daily P&L</div>
                <div className="text-xs text-gray-500">Total P&L</div>
                
                <div className="text-xs font-medium">{renderPnl(strategy.daily_pnl_pct)}</div>
                <div className="text-xs font-medium">{renderPnl(strategy.total_pnl_pct)}</div>
              </div>
            </div>
            
            <div className="flex justify-between items-center pt-2 border-t border-gray-100">
              <div className="text-xs text-gray-500">Last trade: {strategy.last_trade_time || 'None'}</div>
              <div className="flex gap-1">
                {strategy.status === 'active' ? (
                  <button 
                    onClick={() => toggleStrategy(strategy.id, strategy.status)}
                    className="p-1 bg-amber-50 text-amber-700 rounded hover:bg-amber-100 transition-colors"
                    title="Pause Strategy"
                    disabled={toggleStrategyMutation.isPending}
                  >
                    <Pause size={14} />
                  </button>
                ) : strategy.status === 'paused' && (
                  <button 
                    onClick={() => toggleStrategy(strategy.id, strategy.status)}
                    className="p-1 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                    title="Resume Strategy"
                    disabled={toggleStrategyMutation.isPending}
                  >
                    <Play size={14} />
                  </button>
                )}
                
                <button 
                  className="p-1 bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors"
                  title="Settings"
                  onClick={() => handleEditSettings(strategy.id)}
                >
                  <Settings size={14} />
                </button>
                
                <button 
                  className="p-1 bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors"
                  title="Delete"
                  onClick={() => handleDeleteClick(strategy.id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            {/* Delete confirmation dialog */}
            {showDeleteConfirm === strategy.id && selectedStrategy && (
              <div className="absolute inset-0 bg-white bg-opacity-95 rounded-lg flex flex-col items-center justify-center p-4">
                <p className="text-sm font-medium mb-1">Delete {selectedStrategy.name}?</p>
                <p className="text-xs text-gray-500 mb-4 text-center">This strategy and all its configuration will be permanently removed.</p>
                <div className="flex gap-2">
                  <button 
                    className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                    onClick={() => confirmDelete(strategy.id)}
                    disabled={deleteStrategyMutation.isPending}
                  >
                    {deleteStrategyMutation.isPending ? 'Deleting...' : 'Delete'}
                  </button>
                  <button 
                    className="px-3 py-1 bg-gray-200 rounded text-sm hover:bg-gray-300"
                    onClick={() => {
                      setShowDeleteConfirm(null);
                      setSelectedStrategy(null);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            
            {/* Strategy settings modal */}
            {showSettings === strategy.id && selectedStrategy && (
              <div className="absolute inset-0 bg-white bg-opacity-95 rounded-lg flex flex-col p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium">{selectedStrategy.name} Settings</h4>
                  <button 
                    className="p-1 bg-gray-100 rounded-full hover:bg-gray-200"
                    onClick={() => {
                      setShowSettings(null);
                      setSelectedStrategy(null);
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </button>
                </div>
                
                <div className="flex-1 overflow-auto">
                  <div className="mb-3">
                    <label className="block text-xs font-medium mb-1">Strategy Name</label>
                    <input 
                      id="strategy-name" 
                      type="text" 
                      defaultValue={selectedStrategy.name} 
                      className="w-full px-2 py-1 border rounded text-sm" 
                    />
                  </div>
                  
                  <div className="mb-3">
                    <label className="block text-xs font-medium mb-1">Risk Level</label>
                    <select 
                      id="risk-level"
                      className="w-full px-2 py-1 border rounded text-sm"
                      defaultValue={
                        selectedStrategy.type === 'momentum' ? 'high' :
                        selectedStrategy.market === 'ETHUSDT' ? 'medium' : 'low'
                      }
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  
                  <div className="mb-3">
                    <label className="block text-xs font-medium mb-1">Auto-restart</label>
                    <div className="flex items-center">
                      <input 
                        id="auto-restart"
                        type="checkbox" 
                        defaultChecked 
                        className="mr-2" 
                      />
                      <span className="text-xs">Auto-restart strategy after errors</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-100">
                  <button 
                    className="px-3 py-1 bg-gray-200 rounded text-sm hover:bg-gray-300"
                    onClick={() => {
                      setShowSettings(null);
                      setSelectedStrategy(null);
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                    onClick={() => handleSaveSettings(strategy.id)}
                    disabled={saveSettingsMutation.isPending}
                  >
                    {saveSettingsMutation.isPending ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}; 
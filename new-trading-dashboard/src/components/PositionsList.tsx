import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { useNavigation } from '../App';
import {
  CandlestickChart,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Settings,
  Trash2,
  AlertCircle,
  Eye
} from 'lucide-react';

interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entry_price: number;
  current_price: number;
  pnl_amount: number;
  pnl_percentage: number;
  strategy_id: string;
  strategy_name: string;
  open_time: string;
}

interface PositionsListProps {
  limit?: number;
}

export const PositionsList: React.FC<PositionsListProps> = ({ limit }) => {
  const queryClient = useQueryClient();
  const { navigate } = useNavigation();
  const [showNewPositionModal, setShowNewPositionModal] = useState(false);
  const [showModifyModal, setShowModifyModal] = useState<string | null>(null);
  const [showCloseConfirmation, setShowCloseConfirmation] = useState<string | null>(null);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  const { data: positions, isLoading, error } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: async () => {
      try {
        const response = await apiService.getPositions();
        return limit ? response.data.slice(0, limit) : response.data;
      } catch (err) {
        console.error('Error fetching positions:', err);
        throw err;
      }
    }
  });

  const closePositionMutation = useMutation({
    mutationFn: async (positionId: string) => {
      // In a real app, call the API endpoint to close the position
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log(`Position ${positionId} closed`);
      return { positionId };
    },
    onSuccess: () => {
      setShowCloseConfirmation(null);
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    }
  });

  const modifyPositionMutation = useMutation({
    mutationFn: async ({ positionId, newSize }: { positionId: string; newSize: number }) => {
      // In a real app, call the API endpoint to modify the position
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log(`Position ${positionId} modified to size ${newSize}`);
      return { positionId, newSize };
    },
    onSuccess: () => {
      setShowModifyModal(null);
      setSelectedPosition(null);
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    }
  });

  const handleCloseClick = (positionId: string) => {
    const position = positions?.find(p => p.id === positionId) || null;
    setSelectedPosition(position);
    setShowCloseConfirmation(positionId);
  };

  const confirmClosePosition = (positionId: string) => {
    closePositionMutation.mutate(positionId);
  };

  const handleModifyClick = (positionId: string) => {
    const position = positions?.find(p => p.id === positionId) || null;
    setSelectedPosition(position);
    setShowModifyModal(positionId);
  };

  const handleNewPositionSubmit = (formData: any) => {
    // In a real app, call the API to create a new position
    console.log('Creating new position:', formData);
    setShowNewPositionModal(false);
    // Refresh positions data
    queryClient.invalidateQueries({ queryKey: ['positions'] });
  };
  
  const navigateToPositionDetails = (positionId: string) => {
    navigate(`/positions/${positionId}`);
  };
  
  const navigateToStrategyDetails = (strategyId: string) => {
    navigate(`/strategies/${strategyId}`);
  };

  if (isLoading) {
    return (
      <div className="h-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-md font-semibold flex items-center text-gray-700">
            <CandlestickChart size={16} className="mr-2 text-blue-500" />
            Open Positions
          </h2>
          
          <button className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm flex items-center transition-colors">
            <Plus size={14} className="mr-1" /> New Position
          </button>
        </div>
        
        <div className="animate-pulse space-y-2">
          {[...Array(limit || 5)].map((_, i) => (
            <div key={i} className="bg-white p-3 rounded-lg border border-gray-200">
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="flex justify-between">
                <div className="h-6 bg-gray-200 rounded w-32"></div>
                <div className="h-6 bg-gray-200 rounded w-20"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !positions) {
    return (
      <div className="p-4">
        <div className="bg-red-50 rounded-lg p-3 border border-red-200">
          <div className="flex items-center text-red-600">
            <AlertCircle size={18} className="mr-2" />
            <span>Error loading positions</span>
          </div>
        </div>
      </div>
    );
  }

  const getPnLColorClass = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-md font-semibold flex items-center text-gray-700">
          <CandlestickChart size={16} className="mr-2 text-blue-500" />
          Open Positions
        </h2>
        
        <button 
          className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm flex items-center transition-colors"
          onClick={() => setShowNewPositionModal(true)}
        >
          <Plus size={14} className="mr-1" /> New Position
        </button>
      </div>
      
      {positions.length === 0 ? (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-6 text-center">
          <p className="text-gray-500">No open positions</p>
          <button 
            className="mt-3 px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition-colors"
            onClick={() => setShowNewPositionModal(true)}
          >
            Open a position
          </button>
        </div>
      ) : (
        <div className="overflow-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Symbol</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Side</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Size</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Entry</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Current</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">P&L</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 border-b">Strategy</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-600 border-b">Actions</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(position => (
                <tr key={position.id} className="border-b border-gray-100">
                  <td className="px-3 py-2.5 text-xs font-medium cursor-pointer hover:text-blue-600" onClick={() => navigateToPositionDetails(position.id)}>
                    {position.symbol}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`
                      px-2 py-0.5 rounded text-xs font-medium
                      ${position.side === 'LONG' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
                    `}>
                      {position.side}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs">{position.size}</td>
                  <td className="px-3 py-2.5 text-xs">${position.entry_price.toFixed(2)}</td>
                  <td className="px-3 py-2.5 text-xs">${position.current_price.toFixed(2)}</td>
                  <td className="px-3 py-2.5">
                    <div className={`flex items-center text-xs ${getPnLColorClass(position.pnl_percentage)}`}>
                      {position.pnl_percentage > 0 ? (
                        <ArrowUpRight size={12} className="mr-1" />
                      ) : position.pnl_percentage < 0 ? (
                        <ArrowDownRight size={12} className="mr-1" />
                      ) : null}
                      {position.pnl_percentage.toFixed(2)}% / ${position.pnl_amount.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-xs cursor-pointer hover:text-blue-600" onClick={() => position.strategy_id && navigateToStrategyDetails(position.strategy_id)}>
                    {position.strategy_name}
                  </td>
                  <td className="px-3 py-2.5 text-right space-x-1">
                    <button
                      className="px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs transition-colors"
                      onClick={() => navigateToPositionDetails(position.id)}
                      title="View Position"
                    >
                      <Eye size={12} />
                    </button>
                    <button
                      className="px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs transition-colors"
                      onClick={() => handleModifyClick(position.id)}
                      title="Modify Position"
                    >
                      <Settings size={12} />
                    </button>
                    <button
                      className="px-2 py-1 bg-red-50 hover:bg-red-100 text-red-700 rounded text-xs transition-colors"
                      onClick={() => handleCloseClick(position.id)}
                      title="Close Position"
                    >
                      <Trash2 size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* New Position Modal */}
      {showNewPositionModal && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">New Manual Position</h3>
              <button 
                className="p-1 bg-gray-100 rounded-full hover:bg-gray-200"
                onClick={() => setShowNewPositionModal(false)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <form className="space-y-4">
              <div>
                <label htmlFor="symbol" className="block text-sm font-medium mb-1">Symbol</label>
                <select id="symbol" className="w-full px-3 py-2 border rounded">
                  <option value="BTCUSDT">BTCUSDT</option>
                  <option value="ETHUSDT">ETHUSDT</option>
                  <option value="SOLUSDT">SOLUSDT</option>
                  <option value="BNBUSDT">BNBUSDT</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Side</label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input type="radio" name="side" value="LONG" className="mr-2" defaultChecked />
                    <span>Long</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="side" value="SHORT" className="mr-2" />
                    <span>Short</span>
                  </label>
                </div>
              </div>
              
              <div>
                <label htmlFor="size" className="block text-sm font-medium mb-1">Position Size</label>
                <input id="size" type="number" min="0.001" step="0.001" className="w-full px-3 py-2 border rounded" placeholder="0.1" />
              </div>
              
              <div>
                <label htmlFor="strategy" className="block text-sm font-medium mb-1">Link to Strategy (optional)</label>
                <select id="strategy" className="w-full px-3 py-2 border rounded">
                  <option value="">None (Manual Position)</option>
                  <option value="strat-btc-trend-1">BTC Trend Following</option>
                  <option value="strat-eth-reversion-1">ETH Mean Reversion</option>
                </select>
              </div>
              
              <div className="pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                  onClick={() => setShowNewPositionModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                  onClick={() => {
                    const symbolSelect = document.getElementById('symbol') as HTMLSelectElement;
                    const sideInputs = document.querySelectorAll('input[name="side"]') as NodeListOf<HTMLInputElement>;
                    const sizeInput = document.getElementById('size') as HTMLInputElement;
                    const strategySelect = document.getElementById('strategy') as HTMLSelectElement;
                    
                    const side = Array.from(sideInputs).find(input => input.checked)?.value as 'LONG' | 'SHORT';
                    
                    if (symbolSelect && side && sizeInput.value) {
                      handleNewPositionSubmit({
                        symbol: symbolSelect.value,
                        side,
                        size: parseFloat(sizeInput.value),
                        strategy_id: strategySelect.value || null
                      });
                    }
                  }}
                >
                  Create Position
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Modify Position Modal */}
      {showModifyModal && selectedPosition && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Modify Position</h3>
              <button 
                className="p-1 bg-gray-100 rounded-full hover:bg-gray-200"
                onClick={() => {
                  setShowModifyModal(null);
                  setSelectedPosition(null);
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 bg-gray-50 p-3 rounded border">
                <div>
                  <p className="text-xs text-gray-500">Symbol</p>
                  <p className="font-medium">{selectedPosition.symbol}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Side</p>
                  <p className={`font-medium ${selectedPosition.side === 'LONG' ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedPosition.side}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Entry Price</p>
                  <p className="font-medium">${selectedPosition.entry_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Current Price</p>
                  <p className="font-medium">${selectedPosition.current_price.toFixed(2)}</p>
                </div>
              </div>
              
              <div>
                <label htmlFor="new-size" className="block text-sm font-medium mb-1">New Position Size</label>
                <input 
                  id="new-size" 
                  type="number" 
                  min="0.001" 
                  step="0.001" 
                  defaultValue={selectedPosition.size} 
                  className="w-full px-3 py-2 border rounded" 
                />
              </div>
              
              <div className="pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                  onClick={() => {
                    setShowModifyModal(null);
                    setSelectedPosition(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                  onClick={() => {
                    const sizeInput = document.getElementById('new-size') as HTMLInputElement;
                    if (sizeInput?.value) {
                      modifyPositionMutation.mutate({
                        positionId: selectedPosition.id,
                        newSize: parseFloat(sizeInput.value)
                      });
                    }
                  }}
                  disabled={modifyPositionMutation.isPending}
                >
                  {modifyPositionMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Close Position Confirmation */}
      {showCloseConfirmation && selectedPosition && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="text-center mb-4">
              <h3 className="text-lg font-semibold mb-2">Close Position</h3>
              <p className="text-gray-600">
                Are you sure you want to close your {selectedPosition.side} position in {selectedPosition.symbol}?
              </p>
              
              <div className="mt-3 bg-gray-50 p-3 rounded border text-left">
                <div className="grid grid-cols-2 gap-y-2 text-sm">
                  <p className="text-gray-500">Size:</p>
                  <p className="font-medium">{selectedPosition.size}</p>
                  <p className="text-gray-500">Entry price:</p>
                  <p className="font-medium">${selectedPosition.entry_price.toFixed(2)}</p>
                  <p className="text-gray-500">Current price:</p>
                  <p className="font-medium">${selectedPosition.current_price.toFixed(2)}</p>
                  <p className="text-gray-500">P&L:</p>
                  <p className={`font-medium ${getPnLColorClass(selectedPosition.pnl_percentage)}`}>
                    {selectedPosition.pnl_percentage > 0 ? '+' : ''}{selectedPosition.pnl_percentage.toFixed(2)}% / ${selectedPosition.pnl_amount.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-center gap-3">
              <button
                className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                onClick={() => {
                  setShowCloseConfirmation(null);
                  setSelectedPosition(null);
                }}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                onClick={() => confirmClosePosition(selectedPosition.id)}
                disabled={closePositionMutation.isPending}
              >
                {closePositionMutation.isPending ? 'Closing...' : 'Close Position'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 
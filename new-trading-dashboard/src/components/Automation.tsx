import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { 
  Bot, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Calendar,
  AlertTriangle,
  Info,
  Play,
  Pause,
  RefreshCw,
  Settings as SettingsIcon,
  Save,
  ChevronDown,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

interface AutomationSettings {
  is_active: boolean;
  trading_hours: {
    start_time: string;
    end_time: string;
    days: ('monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday')[];
  };
  risk_limits: {
    max_drawdown_pct: number;
    max_daily_loss_pct: number;
    max_positions: number;
    max_allocation_pct: number;
  };
  notifications: {
    email_alerts: boolean;
    trade_confirmations: boolean;
    risk_warnings: boolean;
    performance_reports: boolean;
    report_frequency: 'daily' | 'weekly' | 'monthly';
  };
}

interface AutomationStatus {
  status: 'online' | 'paused' | 'error' | 'scheduled';
  last_active: string;
  next_action?: string;
  uptime?: string;
  trades_executed: number;
  trades_queued: number;
}

export const Automation: React.FC = () => {
  const queryClient = useQueryClient();
  const [showConfirmation, setShowConfirmation] = useState<'start' | 'stop' | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSettings, setEditedSettings] = useState<AutomationSettings | null>(null);

  const { 
    data: automationStatus, 
    isLoading: statusLoading, 
    error: statusError 
  } = useQuery<AutomationStatus>({
    queryKey: ['automation', 'status'],
    queryFn: async () => {
      try {
        const response = await apiService.getAutomationStatus();
        return response.data;
      } catch (err) {
        console.error('Error fetching automation status:', err);
        throw err;
      }
    }
  });

  const { 
    data: settings, 
    isLoading: settingsLoading, 
    error: settingsError 
  } = useQuery<AutomationSettings>({
    queryKey: ['automation', 'settings'],
    queryFn: async () => {
      try {
        const response = await apiService.getAutomationSettings();
        return response.data;
      } catch (err) {
        console.error('Error fetching automation settings:', err);
        throw err;
      }
    },
    onSuccess: (data) => {
      if (!editedSettings) {
        setEditedSettings(data);
      }
    }
  });

  const startAutomationMutation = useMutation({
    mutationFn: async () => {
      await apiService.startAutomation();
    },
    onSuccess: () => {
      setShowConfirmation(null);
      queryClient.invalidateQueries({ queryKey: ['automation', 'status'] });
    }
  });

  const stopAutomationMutation = useMutation({
    mutationFn: async () => {
      await apiService.stopAutomation();
    },
    onSuccess: () => {
      setShowConfirmation(null);
      queryClient.invalidateQueries({ queryKey: ['automation', 'status'] });
    }
  });

  const saveSettingsMutation = useMutation({
    mutationFn: async (newSettings: AutomationSettings) => {
      await apiService.updateAutomationSettings(newSettings);
    },
    onSuccess: () => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['automation', 'settings'] });
    }
  });

  const isLoading = statusLoading || settingsLoading;
  const error = statusError || settingsError;

  const handleSaveSettings = () => {
    if (editedSettings) {
      saveSettingsMutation.mutate(editedSettings);
    }
  };

  const handleInputChange = (path: string[], value: any) => {
    if (!editedSettings) return;
    
    let newSettings = { ...editedSettings };
    let current: any = newSettings;
    
    // Navigate to the nested property
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    
    // Update the value
    current[path[path.length - 1]] = value;
    setEditedSettings(newSettings);
  };

  const toggleDay = (day: string) => {
    if (!editedSettings) return;
    
    const days = [...editedSettings.trading_hours.days];
    const index = days.indexOf(day as any);
    
    if (index > -1) {
      days.splice(index, 1);
    } else {
      days.push(day as any);
    }
    
    setEditedSettings({
      ...editedSettings,
      trading_hours: {
        ...editedSettings.trading_hours,
        days
      }
    });
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'scheduled': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg p-4 border border-gray-200 h-32">
              <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
              <div className="h-6 bg-gray-200 rounded w-16 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-32"></div>
            </div>
          ))}
        </div>
        <div className="h-64 bg-white rounded-lg border border-gray-200"></div>
      </div>
    );
  }

  if (error || !settings || !automationStatus) {
    return (
      <div className="bg-red-50 rounded-lg p-3 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle size={18} className="mr-2" />
          <span>Error loading automation data</span>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-bold flex items-center text-gray-800 mb-6">
        <Bot size={18} className="mr-2 text-blue-500" />
        Automated Trading Control
      </h2>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="text-sm text-gray-600 font-medium mb-2">Current Status</h3>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${getStatusColor(automationStatus.status)}`}></div>
            <div className="text-lg font-semibold capitalize">{automationStatus.status}</div>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            {automationStatus.status === 'online' && `Active for ${automationStatus.uptime}`}
            {automationStatus.status === 'paused' && `Paused since ${new Date(automationStatus.last_active).toLocaleString()}`}
            {automationStatus.status === 'scheduled' && `Next run: ${automationStatus.next_action}`}
            {automationStatus.status === 'error' && 'Error detected - check logs'}
          </div>
          <div className="flex mt-4 gap-2">
            {automationStatus.status !== 'online' ? (
              <button
                className="px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white rounded text-xs flex items-center"
                onClick={() => setShowConfirmation('start')}
              >
                <Play size={12} className="mr-1" />
                Start
              </button>
            ) : (
              <button
                className="px-3 py-1.5 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs flex items-center"
                onClick={() => setShowConfirmation('stop')}
              >
                <Pause size={12} className="mr-1" />
                Pause
              </button>
            )}
            <button
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs flex items-center"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['automation', 'status'] })}
            >
              <RefreshCw size={12} className="mr-1" />
              Refresh
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="text-sm text-gray-600 font-medium mb-2">Activity</h3>
          <div className="text-lg font-semibold">{automationStatus.trades_executed} trades executed</div>
          <div className="text-xs text-gray-500 mt-2">
            {automationStatus.trades_queued > 0
              ? `${automationStatus.trades_queued} trades queued`
              : 'No trades queued'
            }
          </div>
          <div className="flex mt-4 items-center">
            <Clock size={14} className="mr-1 text-gray-400" />
            <span className="text-xs text-gray-500">Last active: {new Date(automationStatus.last_active).toLocaleString()}</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="text-sm text-gray-600 font-medium mb-2">Schedule</h3>
          <div className="text-base font-semibold">
            {settings.trading_hours.days.length === 0 
              ? 'No scheduled days' 
              : settings.trading_hours.days.length === 7 
                ? 'Every day' 
                : settings.trading_hours.days.map(d => d.slice(0, 3)).join(', ')
            }
          </div>
          <div className="text-xs text-gray-500 mt-2">
            {settings.trading_hours.start_time} - {settings.trading_hours.end_time}
          </div>
          <div className="flex mt-4 items-center">
            <Calendar size={14} className="mr-1 text-gray-400" />
            <span className="text-xs text-gray-500">
              {settings.is_active ? 'Schedule active' : 'Schedule inactive'}
            </span>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="flex justify-between items-center border-b border-gray-200 px-4 py-3">
          <h3 className="font-medium flex items-center">
            <SettingsIcon size={16} className="mr-2 text-blue-500" />
            Automation Settings
          </h3>
          {isEditing ? (
            <div className="flex gap-2">
              <button
                className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm"
                onClick={() => {
                  setIsEditing(false);
                  setEditedSettings(settings);
                }}
              >
                Cancel
              </button>
              <button
                className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm flex items-center"
                onClick={handleSaveSettings}
                disabled={saveSettingsMutation.isPending}
              >
                {saveSettingsMutation.isPending ? (
                  <>
                    <RefreshCw size={14} className="mr-1 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={14} className="mr-1" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          ) : (
            <button
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-sm flex items-center"
              onClick={() => setIsEditing(true)}
            >
              <SettingsIcon size={14} className="mr-1" />
              Edit Settings
            </button>
          )}
        </div>

        <div className="p-4">
          {/* General Settings */}
          <div className="mb-6">
            <h4 className="text-sm font-medium border-b border-gray-100 pb-2 mb-3">General Settings</h4>
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">Enable Automation</div>
                <div className="text-xs text-gray-500">Toggle to enable or disable the automated trading system</div>
              </div>
              {isEditing ? (
                <button
                  className="relative"
                  onClick={() => handleInputChange(['is_active'], !editedSettings?.is_active)}
                >
                  {editedSettings?.is_active ? (
                    <ToggleRight className="text-blue-500 w-10 h-6" />
                  ) : (
                    <ToggleLeft className="text-gray-400 w-10 h-6" />
                  )}
                </button>
              ) : (
                <div className="text-sm font-medium">
                  {settings.is_active ? 'Enabled' : 'Disabled'}
                </div>
              )}
            </div>
          </div>

          {/* Trading Hours */}
          <div className="mb-6">
            <h4 className="text-sm font-medium border-b border-gray-100 pb-2 mb-3">Trading Hours</h4>
            
            {isEditing ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Start Time</label>
                    <input 
                      type="time" 
                      className="w-full p-2 border rounded" 
                      value={editedSettings?.trading_hours.start_time}
                      onChange={(e) => handleInputChange(['trading_hours', 'start_time'], e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">End Time</label>
                    <input 
                      type="time" 
                      className="w-full p-2 border rounded" 
                      value={editedSettings?.trading_hours.end_time}
                      onChange={(e) => handleInputChange(['trading_hours', 'end_time'], e.target.value)}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Trading Days</label>
                  <div className="flex flex-wrap gap-2">
                    {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(day => (
                      <button
                        key={day}
                        className={`px-3 py-1.5 rounded text-sm ${
                          editedSettings?.trading_hours.days.includes(day as any)
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                        onClick={() => toggleDay(day)}
                      >
                        {day.charAt(0).toUpperCase() + day.slice(1, 3)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium">Active Hours</div>
                  <div className="text-sm">{settings.trading_hours.start_time} - {settings.trading_hours.end_time}</div>
                </div>
                <div>
                  <div className="text-sm font-medium">Trading Days</div>
                  <div className="text-sm">
                    {settings.trading_hours.days.length === 0 
                      ? 'None selected' 
                      : settings.trading_hours.days.length === 7 
                        ? 'Every day' 
                        : settings.trading_hours.days.map(d => d.charAt(0).toUpperCase() + d.slice(1, 3)).join(', ')
                    }
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Risk Limits */}
          <div className="mb-6">
            <h4 className="text-sm font-medium border-b border-gray-100 pb-2 mb-3">Risk Limits</h4>
            
            {isEditing ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Max Drawdown (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    step="0.1"
                    className="w-full p-2 border rounded" 
                    value={editedSettings?.risk_limits.max_drawdown_pct}
                    onChange={(e) => handleInputChange(['risk_limits', 'max_drawdown_pct'], parseFloat(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Daily Loss (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    step="0.1"
                    className="w-full p-2 border rounded" 
                    value={editedSettings?.risk_limits.max_daily_loss_pct}
                    onChange={(e) => handleInputChange(['risk_limits', 'max_daily_loss_pct'], parseFloat(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Positions</label>
                  <input 
                    type="number" 
                    min="0" 
                    className="w-full p-2 border rounded" 
                    value={editedSettings?.risk_limits.max_positions}
                    onChange={(e) => handleInputChange(['risk_limits', 'max_positions'], parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Allocation (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    step="0.1"
                    className="w-full p-2 border rounded" 
                    value={editedSettings?.risk_limits.max_allocation_pct}
                    onChange={(e) => handleInputChange(['risk_limits', 'max_allocation_pct'], parseFloat(e.target.value))}
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-500">Max Drawdown</div>
                  <div className="text-sm font-medium">{settings.risk_limits.max_drawdown_pct}%</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Max Daily Loss</div>
                  <div className="text-sm font-medium">{settings.risk_limits.max_daily_loss_pct}%</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Max Positions</div>
                  <div className="text-sm font-medium">{settings.risk_limits.max_positions}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Max Allocation</div>
                  <div className="text-sm font-medium">{settings.risk_limits.max_allocation_pct}%</div>
                </div>
              </div>
            )}
          </div>
          
          {/* Notifications */}
          <div>
            <h4 className="text-sm font-medium border-b border-gray-100 pb-2 mb-3">Notifications</h4>
            
            {isEditing ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm">Email Alerts</div>
                    <div className="text-xs text-gray-500">Receive critical alerts via email</div>
                  </div>
                  <button
                    className="relative"
                    onClick={() => handleInputChange(['notifications', 'email_alerts'], !editedSettings?.notifications.email_alerts)}
                  >
                    {editedSettings?.notifications.email_alerts ? (
                      <ToggleRight className="text-blue-500 w-10 h-6" />
                    ) : (
                      <ToggleLeft className="text-gray-400 w-10 h-6" />
                    )}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm">Trade Confirmations</div>
                    <div className="text-xs text-gray-500">Get notification for each trade</div>
                  </div>
                  <button
                    className="relative"
                    onClick={() => handleInputChange(['notifications', 'trade_confirmations'], !editedSettings?.notifications.trade_confirmations)}
                  >
                    {editedSettings?.notifications.trade_confirmations ? (
                      <ToggleRight className="text-blue-500 w-10 h-6" />
                    ) : (
                      <ToggleLeft className="text-gray-400 w-10 h-6" />
                    )}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm">Risk Warnings</div>
                    <div className="text-xs text-gray-500">Get alerts when risk thresholds are approached</div>
                  </div>
                  <button
                    className="relative"
                    onClick={() => handleInputChange(['notifications', 'risk_warnings'], !editedSettings?.notifications.risk_warnings)}
                  >
                    {editedSettings?.notifications.risk_warnings ? (
                      <ToggleRight className="text-blue-500 w-10 h-6" />
                    ) : (
                      <ToggleLeft className="text-gray-400 w-10 h-6" />
                    )}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm">Performance Reports</div>
                    <div className="text-xs text-gray-500">Receive periodic performance reports</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      className="relative"
                      onClick={() => handleInputChange(['notifications', 'performance_reports'], !editedSettings?.notifications.performance_reports)}
                    >
                      {editedSettings?.notifications.performance_reports ? (
                        <ToggleRight className="text-blue-500 w-10 h-6" />
                      ) : (
                        <ToggleLeft className="text-gray-400 w-10 h-6" />
                      )}
                    </button>
                    
                    {editedSettings?.notifications.performance_reports && (
                      <select
                        className="border p-1 rounded text-sm"
                        value={editedSettings?.notifications.report_frequency}
                        onChange={(e) => handleInputChange(['notifications', 'report_frequency'], e.target.value)}
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </select>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium mb-2">Enabled Notifications</div>
                  <ul className="text-sm space-y-1">
                    {settings.notifications.email_alerts && <li className="flex items-center"><CheckCircle size={14} className="mr-1 text-green-500" /> Email alerts</li>}
                    {settings.notifications.trade_confirmations && <li className="flex items-center"><CheckCircle size={14} className="mr-1 text-green-500" /> Trade confirmations</li>}
                    {settings.notifications.risk_warnings && <li className="flex items-center"><CheckCircle size={14} className="mr-1 text-green-500" /> Risk warnings</li>}
                    {settings.notifications.performance_reports && <li className="flex items-center"><CheckCircle size={14} className="mr-1 text-green-500" /> Performance reports ({settings.notifications.report_frequency})</li>}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Information Panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start">
        <Info size={24} className="text-blue-500 mr-3 mt-0.5 flex-shrink-0" />
        <div>
          <h4 className="text-blue-800 font-medium mb-1">About Automation</h4>
          <p className="text-sm text-blue-700">
            The automated trading system executes trades based on your strategy configurations without manual intervention.
            Make sure to set appropriate risk limits and monitor the system regularly. You can pause the automation at any time.
          </p>
        </div>
      </div>
      
      {/* Start/Stop Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-3">
              {showConfirmation === 'start' ? 'Start Automation' : 'Stop Automation'}
            </h3>
            
            <div className="mb-4">
              {showConfirmation === 'start' ? (
                <div className="flex items-start">
                  <AlertTriangle className="text-yellow-500 mr-2 flex-shrink-0" />
                  <p className="text-sm text-gray-700">
                    You're about to start the automated trading system. It will begin executing trades according to your strategy settings.
                    Make sure your risk parameters are properly configured.
                  </p>
                </div>
              ) : (
                <div className="flex items-start">
                  <AlertTriangle className="text-yellow-500 mr-2 flex-shrink-0" />
                  <p className="text-sm text-gray-700">
                    You're about to stop the automated trading system. No new trades will be executed, but existing positions will remain open.
                    You can restart the system at any time.
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-gray-800"
                onClick={() => setShowConfirmation(null)}
              >
                Cancel
              </button>
              
              <button 
                className={`px-4 py-2 ${
                  showConfirmation === 'start' 
                    ? 'bg-green-500 hover:bg-green-600' 
                    : 'bg-yellow-500 hover:bg-yellow-600'
                } text-white rounded flex items-center`}
                onClick={() => {
                  if (showConfirmation === 'start') {
                    startAutomationMutation.mutate();
                  } else {
                    stopAutomationMutation.mutate();
                  }
                }}
                disabled={startAutomationMutation.isPending || stopAutomationMutation.isPending}
              >
                {(startAutomationMutation.isPending || stopAutomationMutation.isPending) ? (
                  <>
                    <RefreshCw size={16} className="mr-1 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    {showConfirmation === 'start' ? (
                      <>
                        <Play size={16} className="mr-1" />
                        Start Automation
                      </>
                    ) : (
                      <>
                        <Pause size={16} className="mr-1" />
                        Stop Automation
                      </>
                    )}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 
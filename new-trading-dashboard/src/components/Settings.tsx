import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../api/client';
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Zap,
  Palette,
  Save,
  RefreshCw,
  AlertCircle,
  Check,
  Moon,
  Sun
} from 'lucide-react';

interface UserSettings {
  user: {
    name: string;
    email: string;
    profile_image?: string;
  };
  preferences: {
    theme: 'light' | 'dark' | 'system';
    chart_style: 'candles' | 'line' | 'bars';
    default_timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
    show_notifications: boolean;
    sound_alerts: boolean;
    compact_view: boolean;
  };
  security: {
    two_factor_enabled: boolean;
    last_password_change: string;
    active_sessions: number;
  };
  connections: {
    exchanges: {
      id: string;
      name: string;
      connected: boolean;
      last_synced?: string;
    }[];
  };
}

export const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'account' | 'preferences' | 'security' | 'connections'>('account');
  const [editedSettings, setEditedSettings] = useState<UserSettings | null>(null);
  const [showSavedMessage, setShowSavedMessage] = useState(false);

  const { data: settings, isLoading, error } = useQuery<UserSettings>({
    queryKey: ['userSettings'],
    queryFn: async () => {
      try {
        const response = await apiService.getUserSettings();
        return response.data;
      } catch (err) {
        console.error('Error fetching user settings:', err);
        throw err;
      }
    },
    onSuccess: (data) => {
      if (!editedSettings) {
        setEditedSettings(data);
      }
    }
  });

  const updateSettingsMutation = useMutation({
    mutationFn: async (updateData: Partial<UserSettings>) => {
      await apiService.updateUserSettings(updateData);
      return updateData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] });
      setShowSavedMessage(true);
      setTimeout(() => {
        setShowSavedMessage(false);
      }, 3000);
    }
  });

  const handleSave = () => {
    if (editedSettings) {
      updateSettingsMutation.mutate(editedSettings);
    }
  };

  const updateSetting = (path: string[], value: any) => {
    if (!editedSettings) return;
    
    const newSettings = { ...editedSettings };
    let current: any = newSettings;
    
    // Navigate to the nested property
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    
    // Update the value
    current[path[path.length - 1]] = value;
    
    setEditedSettings(newSettings);
  };

  if (isLoading || !editedSettings) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
        <div className="flex gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-10 bg-gray-200 rounded w-32"></div>
          ))}
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="h-6 bg-gray-200 rounded w-24 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle size={18} className="mr-2" />
          <span>Error loading settings</span>
        </div>
        <p className="text-sm text-red-600 mt-2">Please try refreshing the page or contact support if the problem persists.</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Saved message */}
      {showSavedMessage && (
        <div className="absolute top-0 right-0 bg-green-100 text-green-700 px-4 py-2 rounded-md flex items-center">
          <Check size={16} className="mr-2" />
          Settings saved successfully
        </div>
      )}

      <h2 className="text-lg font-bold flex items-center text-gray-800 mb-6">
        <SettingsIcon size={18} className="mr-2 text-blue-500" />
        Account Settings
      </h2>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-6">
          <button
            className={`pb-3 px-1 ${
              activeTab === 'account'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('account')}
          >
            <div className="flex items-center">
              <User size={16} className="mr-2" />
              Account
            </div>
          </button>
          <button
            className={`pb-3 px-1 ${
              activeTab === 'preferences'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('preferences')}
          >
            <div className="flex items-center">
              <Palette size={16} className="mr-2" />
              Preferences
            </div>
          </button>
          <button
            className={`pb-3 px-1 ${
              activeTab === 'security'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('security')}
          >
            <div className="flex items-center">
              <Shield size={16} className="mr-2" />
              Security
            </div>
          </button>
          <button
            className={`pb-3 px-1 ${
              activeTab === 'connections'
                ? 'border-b-2 border-blue-500 text-blue-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('connections')}
          >
            <div className="flex items-center">
              <Zap size={16} className="mr-2" />
              Connections
            </div>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg border border-gray-200">
        {/* Account Settings */}
        {activeTab === 'account' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Personal Information</h3>
            <div className="max-w-md space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input 
                  type="text" 
                  className="w-full p-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500" 
                  value={editedSettings.user.name}
                  onChange={(e) => updateSetting(['user', 'name'], e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Email Address</label>
                <input 
                  type="email" 
                  className="w-full p-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500" 
                  value={editedSettings.user.email}
                  onChange={(e) => updateSetting(['user', 'email'], e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Profile Picture</label>
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gray-200 rounded-full overflow-hidden flex items-center justify-center">
                    {editedSettings.user.profile_image ? (
                      <img 
                        src={editedSettings.user.profile_image} 
                        alt="Profile" 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User size={24} className="text-gray-400" />
                    )}
                  </div>
                  <button className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded text-sm hover:bg-blue-100 transition-colors">
                    Change Picture
                  </button>
                </div>
              </div>
              
              <div className="pt-4">
                <button 
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center transition-colors"
                  onClick={handleSave}
                  disabled={updateSettingsMutation.isPending}
                >
                  {updateSettingsMutation.isPending ? (
                    <>
                      <RefreshCw size={16} className="mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={16} className="mr-2" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Preferences */}
        {activeTab === 'preferences' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Display & Behavior</h3>
            
            <div className="space-y-6">
              <div className="max-w-md">
                <label className="block text-sm font-medium mb-2">Theme</label>
                <div className="flex gap-4">
                  <button
                    className={`flex flex-col items-center p-3 rounded-md border ${
                      editedSettings.preferences.theme === 'light' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => updateSetting(['preferences', 'theme'], 'light')}
                  >
                    <Sun size={24} className="mb-1" />
                    <span className="text-sm">Light</span>
                  </button>
                  
                  <button
                    className={`flex flex-col items-center p-3 rounded-md border ${
                      editedSettings.preferences.theme === 'dark' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => updateSetting(['preferences', 'theme'], 'dark')}
                  >
                    <Moon size={24} className="mb-1" />
                    <span className="text-sm">Dark</span>
                  </button>
                  
                  <button
                    className={`flex flex-col items-center p-3 rounded-md border ${
                      editedSettings.preferences.theme === 'system' 
                        ? 'border-blue-500 bg-blue-50 text-blue-700' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => updateSetting(['preferences', 'theme'], 'system')}
                  >
                    <div className="w-6 h-6 mb-1 flex">
                      <div className="w-1/2 flex items-center justify-center">
                        <Sun size={12} />
                      </div>
                      <div className="w-1/2 bg-gray-700 rounded-r-full flex items-center justify-center">
                        <Moon size={12} className="text-white" />
                      </div>
                    </div>
                    <span className="text-sm">System</span>
                  </button>
                </div>
              </div>
              
              <div className="max-w-md">
                <label className="block text-sm font-medium mb-2">Chart Style</label>
                <select 
                  className="w-full p-2 border rounded" 
                  value={editedSettings.preferences.chart_style}
                  onChange={(e) => updateSetting(['preferences', 'chart_style'], e.target.value)}
                >
                  <option value="candles">Candlestick</option>
                  <option value="line">Line</option>
                  <option value="bars">Bars</option>
                </select>
              </div>
              
              <div className="max-w-md">
                <label className="block text-sm font-medium mb-2">Default Timeframe</label>
                <select 
                  className="w-full p-2 border rounded" 
                  value={editedSettings.preferences.default_timeframe}
                  onChange={(e) => updateSetting(['preferences', 'default_timeframe'], e.target.value)}
                >
                  <option value="1m">1 Minute</option>
                  <option value="5m">5 Minutes</option>
                  <option value="15m">15 Minutes</option>
                  <option value="1h">1 Hour</option>
                  <option value="4h">4 Hours</option>
                  <option value="1d">1 Day</option>
                  <option value="1w">1 Week</option>
                </select>
              </div>
              
              <div className="space-y-3 max-w-md">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Show Notifications</div>
                    <div className="text-xs text-gray-500">Display popup notifications in the app</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only" 
                      checked={editedSettings.preferences.show_notifications}
                      onChange={(e) => updateSetting(['preferences', 'show_notifications'], e.target.checked)}
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${
                      editedSettings.preferences.show_notifications ? 'bg-blue-600' : 'bg-gray-200'
                    }`}>
                      <div className={`w-5 h-5 rounded-full bg-white transition transform ${
                        editedSettings.preferences.show_notifications ? 'translate-x-6' : 'translate-x-1'
                      }`}></div>
                    </div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Sound Alerts</div>
                    <div className="text-xs text-gray-500">Play sound when important events occur</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only" 
                      checked={editedSettings.preferences.sound_alerts}
                      onChange={(e) => updateSetting(['preferences', 'sound_alerts'], e.target.checked)}
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${
                      editedSettings.preferences.sound_alerts ? 'bg-blue-600' : 'bg-gray-200'
                    }`}>
                      <div className={`w-5 h-5 rounded-full bg-white transition transform ${
                        editedSettings.preferences.sound_alerts ? 'translate-x-6' : 'translate-x-1'
                      }`}></div>
                    </div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Compact View</div>
                    <div className="text-xs text-gray-500">Use compact layout to show more information</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only" 
                      checked={editedSettings.preferences.compact_view}
                      onChange={(e) => updateSetting(['preferences', 'compact_view'], e.target.checked)}
                    />
                    <div className={`w-11 h-6 rounded-full transition-colors ${
                      editedSettings.preferences.compact_view ? 'bg-blue-600' : 'bg-gray-200'
                    }`}>
                      <div className={`w-5 h-5 rounded-full bg-white transition transform ${
                        editedSettings.preferences.compact_view ? 'translate-x-6' : 'translate-x-1'
                      }`}></div>
                    </div>
                  </label>
                </div>
              </div>
              
              <div className="pt-4">
                <button 
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center transition-colors"
                  onClick={handleSave}
                  disabled={updateSettingsMutation.isPending}
                >
                  {updateSettingsMutation.isPending ? (
                    <>
                      <RefreshCw size={16} className="mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={16} className="mr-2" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Security */}
        {activeTab === 'security' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Account Security</h3>
            
            <div className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Two-Factor Authentication</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <div className="flex items-center">
                    {editedSettings.security.two_factor_enabled ? (
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium">
                        Enabled
                      </span>
                    ) : (
                      <button className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded text-sm transition-colors">
                        Enable 2FA
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Password</h4>
                <div className="flex items-center justify-between max-w-md bg-gray-50 p-3 rounded-lg border border-gray-200">
                  <div>
                    <div className="text-sm">Last changed</div>
                    <div className="text-xs text-gray-500">
                      {new Date(editedSettings.security.last_password_change).toLocaleDateString()}
                    </div>
                  </div>
                  <button className="bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1.5 rounded text-sm transition-colors">
                    Change Password
                  </button>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Active Sessions</h4>
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="text-sm">
                      You're currently logged in on {editedSettings.security.active_sessions} {editedSettings.security.active_sessions === 1 ? 'device' : 'devices'}
                    </div>
                    <button className="bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1.5 rounded text-sm transition-colors">
                      Logout All Devices
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Connections */}
        {activeTab === 'connections' && (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Exchange Connections</h3>
            
            <div className="space-y-4">
              {editedSettings.connections.exchanges.map((exchange) => (
                <div key={exchange.id} className="bg-gray-50 p-4 rounded-lg border border-gray-200 flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{exchange.name}</h4>
                    <div className="text-sm text-gray-600 mt-1">
                      {exchange.connected ? (
                        <>
                          <span className="text-green-600">Connected</span>
                          {exchange.last_synced && (
                            <span className="text-gray-500"> · Last synced: {new Date(exchange.last_synced).toLocaleString()}</span>
                          )}
                        </>
                      ) : (
                        <span className="text-gray-500">Not connected</span>
                      )}
                    </div>
                  </div>
                  
                  <button
                    className={`px-3 py-1.5 rounded text-sm ${
                      exchange.connected 
                        ? 'bg-red-50 hover:bg-red-100 text-red-700' 
                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                    }`}
                  >
                    {exchange.connected ? 'Disconnect' : 'Connect'}
                  </button>
                </div>
              ))}
              
              <div className="mt-6">
                <button className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded flex items-center transition-colors">
                  <Zap size={16} className="mr-2" />
                  Connect New Exchange
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 
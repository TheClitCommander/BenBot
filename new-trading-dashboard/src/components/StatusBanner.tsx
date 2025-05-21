import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../api/client';
import { systemStatus } from '../api/mockData';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  HardDrive, 
  Clock, 
  ArrowUpDown,
  LucideIcon,
  AlertOctagon,
  Bell,
  ShieldAlert,
  ShieldCheck,
  Unplug
} from 'lucide-react';
import { useSystemStatus } from '../hooks/useSystemStatus';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import WebSocketStatusIndicator from './WebSocketStatusIndicator';

export const StatusBanner: React.FC = () => {
  const { data: status, isLoading } = useSystemStatus();
  const queryClient = useQueryClient();
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [showDetachModal, setShowDetachModal] = useState(false);

  const emergencyOverrideMutation = useMutation({
    mutationFn: async () => {
      // In a production app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Emergency override activated');
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
      setShowEmergencyModal(false);
    }
  });

  const detachExchangeMutation = useMutation({
    mutationFn: async () => {
      // In a production app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Detached from exchanges');
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
      setShowDetachModal(false);
    }
  });

  if (isLoading) {
    return (
      <div className="bg-gray-100 rounded-lg p-4 border border-gray-200 mb-4">
        <div className="flex justify-between items-center animate-pulse">
          <div className="flex items-center">
            <div className="h-6 w-6 bg-gray-200 rounded-full mr-2"></div>
            <div className="h-5 bg-gray-200 rounded w-24"></div>
          </div>
          <div className="flex gap-2">
            <div className="h-8 bg-gray-200 rounded-md w-28"></div>
            <div className="h-8 bg-gray-200 rounded-md w-28"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-red-50 rounded-lg p-4 border border-red-200 mb-4">
        <div className="flex items-center text-red-600">
          <AlertOctagon className="mr-2" size={18} />
          <span>Error loading system status</span>
        </div>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'online':
        return <CheckCircle2 className="mr-2 text-green-500" size={18} />;
      case 'warning':
        return <AlertTriangle className="mr-2 text-amber-500" size={18} />;
      case 'critical':
        return <AlertOctagon className="mr-2 text-red-500" size={18} />;
      default:
        return <Bell className="mr-2 text-gray-500" size={18} />;
    }
  };

  const getStatusClass = () => {
    switch (status.status) {
      case 'online':
        return 'bg-green-100 border-green-200';
      case 'warning':
        return 'bg-amber-100 border-amber-200';
      case 'critical':
        return 'bg-red-100 border-red-200';
      default:
        return 'bg-gray-100 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getUsageBarColor = (percentage: number) => {
    if (percentage > 80) return 'bg-red-500';
    if (percentage > 60) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  type StatusItemProps = {
    icon: LucideIcon;
    label: string;
    value: string | React.ReactNode;
    className?: string;
  };

  const StatusItem = ({ icon: Icon, label, value, className = "" }: StatusItemProps) => (
    <div className={`flex items-center gap-2 ${className}`}>
      <Icon size={14} className="text-gray-500" />
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-gray-600">{label}:</span>
        <span className="text-xs font-medium">{value}</span>
      </div>
    </div>
  );

  return (
    <div className="status-banner bg-gray-800 text-white p-2 flex justify-between items-center">
      <div className="status-item">
        <span className="label">API Status:</span>
        <span className={`status ${status ? 'text-green-400' : 'text-red-400'}`}>
          {status ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      
      <div className="status-item">
        <span className="label">WebSocket:</span>
        <WebSocketStatusIndicator className="inline-flex ml-2" />
      </div>

      <div className={`rounded-lg p-4 border mb-4 ${getStatusClass()}`}>
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            {getStatusIcon()}
            <span className="font-medium">
              {status.status === 'online' && 'System Online'}
              {status.status === 'warning' && 'System Warning'}
              {status.status === 'critical' && 'System Alert'}
            </span>
            {status.message && (
              <span className="ml-2 text-sm text-gray-600">
                - {status.message}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button 
              className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm flex items-center transition-colors"
              onClick={() => setShowEmergencyModal(true)}
            >
              <ShieldAlert className="mr-1" size={14} /> Emergency Override
            </button>
            <button 
              className="px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded text-sm flex items-center transition-colors"
              onClick={() => setShowDetachModal(true)}
            >
              <Unplug className="mr-1" size={14} /> Detach from Exchanges
            </button>
          </div>
        </div>
      </div>

      {/* Emergency Override Modal */}
      {showEmergencyModal && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center text-red-600 mb-4">
              <ShieldAlert className="mr-2" size={20} />
              <h3 className="text-lg font-semibold">Emergency Override</h3>
            </div>
            <p className="mb-4 text-gray-700">
              This will immediately stop all automatic trading activity, close all pending orders, and freeze all strategy execution.
            </p>
            <p className="mb-6 text-sm text-red-600 font-medium">
              This action cannot be easily reversed and may result in losses. Are you sure?
            </p>
            <div className="flex justify-end gap-3">
              <button 
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-gray-800 transition-colors"
                onClick={() => setShowEmergencyModal(false)}
              >
                Cancel
              </button>
              <button 
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded transition-colors flex items-center"
                onClick={() => emergencyOverrideMutation.mutate()}
                disabled={emergencyOverrideMutation.isPending}
              >
                {emergencyOverrideMutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    <ShieldAlert className="mr-1" size={14} /> Confirm Override
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detach from Exchanges Modal */}
      {showDetachModal && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center text-orange-600 mb-4">
              <Unplug className="mr-2" size={20} />
              <h3 className="text-lg font-semibold">Detach from Exchanges</h3>
            </div>
            <p className="mb-4 text-gray-700">
              This will disconnect BenBot from all exchange APIs, preventing it from placing new orders or monitoring existing positions.
            </p>
            <p className="mb-6 text-sm text-orange-600 font-medium">
              Existing positions will remain open on exchanges. You'll need to manually manage them if you proceed. Continue?
            </p>
            <div className="flex justify-end gap-3">
              <button 
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-gray-800 transition-colors"
                onClick={() => setShowDetachModal(false)}
              >
                Cancel
              </button>
              <button 
                className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded transition-colors flex items-center"
                onClick={() => detachExchangeMutation.mutate()}
                disabled={detachExchangeMutation.isPending}
              >
                {detachExchangeMutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    <Unplug className="mr-1" size={14} /> Confirm Detach
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
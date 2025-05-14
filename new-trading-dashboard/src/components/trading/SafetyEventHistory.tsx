import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Clock, AlertCircle, Shield, RefreshCw } from 'lucide-react';
import safetyApi, { SafetyEvent } from '@/services/safetyApi';

const eventTypeIcons: Record<string, React.ReactNode> = {
  emergency_stop: <AlertCircle className="text-bear" size={16} />,
  circuit_breaker: <Shield className="text-highImpact" size={16} />,
  cooldown: <Clock className="text-infoImpact" size={16} />,
  trading_mode: <RefreshCw className="text-primary" size={16} />,
};

const SafetyEventHistory: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['safetyEvents', selectedType],
    queryFn: () => safetyApi.getSafetyEvents(50, selectedType || undefined),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  // Format the timestamp to a readable format
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };
  
  if (isLoading) {
    return (
      <div className="p-4 bg-card border border-border rounded-lg">
        <p className="text-center text-muted-foreground">Loading event history...</p>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="p-4 bg-card border border-border rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Safety Event History</h3>
          <button 
            onClick={() => refetch()}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Refresh
          </button>
        </div>
        <p className="text-center text-bear">Error loading safety events</p>
      </div>
    );
  }
  
  const events = data?.success ? data.data || [] : [];
  
  return (
    <div className="p-4 bg-card border border-border rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium">Safety Event History</h3>
        <div className="flex items-center space-x-2">
          <select
            className="text-xs bg-muted px-2 py-1 rounded-md border border-border"
            value={selectedType || ''}
            onChange={(e) => setSelectedType(e.target.value || null)}
          >
            <option value="">All Events</option>
            <option value="emergency_stop">Emergency Stop</option>
            <option value="circuit_breaker">Circuit Breaker</option>
            <option value="cooldown">Cooldown</option>
            <option value="trading_mode">Trading Mode</option>
          </select>
          <button 
            onClick={() => refetch()}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Refresh
          </button>
        </div>
      </div>
      
      {events.length === 0 ? (
        <p className="text-center text-muted-foreground py-4">No safety events found</p>
      ) : (
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="text-left py-2 px-3">Type</th>
                <th className="text-left py-2 px-3">Action</th>
                <th className="text-left py-2 px-3">Time</th>
                <th className="text-left py-2 px-3">Reason</th>
                <th className="text-left py-2 px-3">Actor</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event: SafetyEvent) => (
                <tr key={event.id} className="border-b border-border hover:bg-muted/50">
                  <td className="py-2 px-3">
                    <div className="flex items-center">
                      {eventTypeIcons[event.type] || <AlertCircle size={16} />}
                      <span className="ml-2">
                        {event.type === 'emergency_stop' ? 'Emergency Stop' :
                         event.type === 'circuit_breaker' ? 'Circuit Breaker' :
                         event.type === 'cooldown' ? 'Cooldown' :
                         event.type === 'trading_mode' ? 'Trading Mode' :
                         event.type}
                      </span>
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <span className={
                      event.action === 'activated' || event.action === 'triggered' 
                        ? 'text-bear'
                        : event.action === 'deactivated' || event.action === 'reset'
                        ? 'text-bull'
                        : ''
                    }>
                      {event.action.charAt(0).toUpperCase() + event.action.slice(1)}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <div className="flex items-center">
                      <Clock size={14} className="mr-1 text-muted-foreground" />
                      {formatTimestamp(event.timestamp)}
                    </div>
                  </td>
                  <td className="py-2 px-3">{event.reason || '-'}</td>
                  <td className="py-2 px-3">{event.actor || 'System'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SafetyEventHistory; 
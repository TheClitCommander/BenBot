import React from 'react';
import { useQuery } from '@tanstack/react-query';
import orchestrationApi, { SystemOverviewResponse } from '@/services/orchestrationApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; // Assuming you have ShadCN UI components
import { Rocket, ShieldCheck, Zap, TrendingUp, ListChecks, AlertTriangle } from 'lucide-react'; // Icons

// Helper to format a generic object or value for display
const formatDetail = (detail: any): string => {
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail, null, 2);
  }
  if (typeof detail === 'boolean') {
    return detail ? 'Yes' : 'No';
  }
  return String(detail !== undefined && detail !== null ? detail : 'N/A');
};

interface DetailCardProps {
  title: string;
  icon: React.ReactNode;
  data: Record<string, any> | null | undefined;
  isLoading?: boolean; // Made optional as it might not always be relevant if parent handles loading state
  error?: Error | null; // Made optional for the same reason
  cardClassName?: string;
  titleClassName?: string;
}

const DetailCard: React.FC<DetailCardProps> = ({ title, icon, data, isLoading, error, cardClassName, titleClassName }) => {
  if (isLoading) return <Card className={cardClassName}><CardHeader><CardTitle className={`flex items-center ${titleClassName}`}>{icon}{title}</CardTitle></CardHeader><CardContent>Loading...</CardContent></Card>;
  if (error) return <Card className={`border-destructive ${cardClassName}`}><CardHeader><CardTitle className={`flex items-center text-destructive ${titleClassName}`}>{icon}{title}</CardTitle></CardHeader><CardContent>Error: {error.message}</CardContent></Card>;
  if (!data) return <Card className={cardClassName}><CardHeader><CardTitle className={`flex items-center ${titleClassName}`}>{icon}{title}</CardTitle></CardHeader><CardContent>No data available.</CardContent></Card>;

  return (
    <Card className={cardClassName}>
      <CardHeader>
        <CardTitle className={`flex items-center ${titleClassName}`}>{icon}<span className="ml-2">{title}</span></CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-1">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}:</span>
            <span className="font-medium text-right">{formatDetail(value)}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const SystemSummary: React.FC = () => {
  const {
    data: overviewData,
    isLoading,
    error,
    refetch
  } = useQuery<SystemOverviewResponse, Error>({
    queryKey: ['systemOverview'],
    queryFn: orchestrationApi.getSystemOverview,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  if (isLoading) return <div className="p-4 text-center text-muted-foreground">Loading system overview...</div>;
  if (error) return <div className="p-4 text-center text-red-500">Error loading system overview: {error.message}</div>;
  if (!overviewData) return <div className="p-4 text-center text-muted-foreground">No system overview data available.</div>;

  const { 
    evolution_overview, 
    scheduled_runs_summary, 
    active_strategies_count, 
    safety_status, 
    timestamp 
  } = overviewData;

  return (
    <div className="space-y-6 p-1">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold">System Overview</h2>
        <div className="text-xs text-muted-foreground">
          Last updated: {new Date(timestamp).toLocaleString()}
          <button onClick={() => refetch()} className="ml-2 p-1 hover:bg-muted rounded text-primary"> (Refresh)</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DetailCard 
          title="Evolution Status" 
          icon={<Rocket size={18} className="mr-2"/>} 
          data={evolution_overview} />
        
        <DetailCard 
          title="Scheduler" 
          icon={<ListChecks size={18} className="mr-2"/>} 
          data={scheduled_runs_summary ? {
            "Total Scheduled": scheduled_runs_summary.total_scheduled,
            "Active Run ID": scheduled_runs_summary.active_scheduled_run?.schedule_id || 'None',
            "Active Run Status": scheduled_runs_summary.active_scheduled_run?.status || 'N/A',
          } : null} />

        <Card>
            <CardHeader>
                <CardTitle className="flex items-center">
                    <Zap size={18} className="mr-2" /> Active Strategies
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-3xl font-bold">{active_strategies_count}</p>
                <p className="text-xs text-muted-foreground">Currently in mock execution</p>
            </CardContent>
        </Card>

        <DetailCard 
          title="Safety Status" 
          icon={<ShieldCheck size={18} className={`mr-2 ${safety_status?.tradingAllowed ? "text-green-500" : "text-red-500"}`} />} 
          data={safety_status ? {
            "Trading Mode": safety_status.tradingMode,
            "Emergency Stop": safety_status.emergencyStopActive,
            "Trading Allowed": safety_status.tradingAllowed,
            "Block Reason": safety_status.tradingBlockedReason || 'N/A',
          }: null}
          titleClassName={safety_status?.tradingAllowed ? "text-green-600" : "text-red-600"}
           />
      </div>
      
      {safety_status && !safety_status.tradingAllowed && (
        <div className="mt-4 p-4 bg-red-50 border border-red-300 text-red-700 rounded-md flex items-center text-sm">
          <AlertTriangle size={20} className="mr-3 flex-shrink-0"/>
          <div>
            <strong className="font-semibold">Trading Blocked:</strong> 
            <span className="ml-1">{safety_status.tradingBlockedReason || 'A safety system is preventing trades.'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemSummary; 
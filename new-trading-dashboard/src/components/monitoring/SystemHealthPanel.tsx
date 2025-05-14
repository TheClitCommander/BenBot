import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import healthMonitorApi from '../../services/healthMonitorApi';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  CheckCircle,
  AlertCircle,
  Timer,
  Cpu,
  Database,
  HardDrive,
  Activity,
  Zap,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

// Helper to format timestamps
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

// Helper to format latency
const formatLatency = (ms: number): string => {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${Math.round(ms)}ms`;
};

// Component for individual status indicator
interface StatusIndicatorProps {
  healthy: boolean;
  name: string;
  value?: string | number;
  icon: React.ReactNode;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ healthy, name, value, icon }) => {
  return (
    <div className="flex items-center space-x-2 p-2">
      <div className={`p-2 rounded-full ${healthy ? 'bg-green-50' : 'bg-red-50'}`}>
        {icon}
      </div>
      <div>
        <div className="font-medium flex items-center">
          {name}
          {healthy ? (
            <CheckCircle className="ml-2 h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="ml-2 h-4 w-4 text-red-500" />
          )}
        </div>
        {value && <div className="text-sm text-muted-foreground">{value}</div>}
      </div>
    </div>
  );
};

// Component for resource usage bar
interface ResourceBarProps {
  label: string;
  value: number;
  max: number;
  warningThreshold?: number;
  criticalThreshold?: number;
}

const ResourceBar: React.FC<ResourceBarProps> = ({ 
  label, 
  value, 
  max, 
  warningThreshold = 70,
  criticalThreshold = 85
}) => {
  const percentage = (value / max) * 100;
  
  let barColor = "bg-green-500";
  if (percentage >= criticalThreshold) {
    barColor = "bg-red-500";
  } else if (percentage >= warningThreshold) {
    barColor = "bg-yellow-500";
  }
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-muted-foreground">{percentage.toFixed(1)}%</span>
      </div>
      <Progress value={percentage} className={barColor} />
    </div>
  );
};

// Main component
const SystemHealthPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  
  const { data: healthStatus, isLoading, error, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthMonitorApi.getCurrentStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  const { data: alerts } = useQuery({
    queryKey: ['healthAlerts'],
    queryFn: () => healthMonitorApi.getAlerts(5),
    refetchInterval: 30000,
  });
  
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Loading health status...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className="border-red-300">
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Error loading health data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center py-4 text-center">
            <AlertTriangle className="h-10 w-10 text-red-500 mb-2" />
            <p className="text-red-500">Failed to load system health data</p>
            <button
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm"
              onClick={() => refetch()}
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (!healthStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>No health data available</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-center py-4 text-muted-foreground">
            Health monitoring data is not available
          </p>
        </CardContent>
      </Card>
    );
  }
  
  // Extract data
  const isSystemHealthy = healthStatus.system_status === 'healthy';
  const dataFeedComponents = Object.entries(healthStatus.components)
    .filter(([name]) => name.startsWith('data_feed_'));
  const resourceComponents = Object.entries(healthStatus.components)
    .filter(([name]) => ['disk_space', 'memory_usage', 'cpu_usage'].includes(name));
  
  // Find any critical components (unhealthy)
  const criticalComponents = Object.entries(healthStatus.components)
    .filter(([_, status]) => !status.healthy);
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>System Health Monitor</CardTitle>
            <CardDescription>
              Last updated: {formatDate(healthStatus.timestamp)}
            </CardDescription>
          </div>
          <Badge className={isSystemHealthy ? "bg-green-500" : "bg-red-500"}>
            {isSystemHealthy ? "Healthy" : "Unhealthy"}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="data-feeds">Data Feeds</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
            <TabsTrigger value="alerts">
              Alerts
              {alerts && alerts.unresolved_count > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {alerts.unresolved_count}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="mt-4">
            {criticalComponents.length > 0 && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <h3 className="text-red-700 font-medium flex items-center">
                  <AlertTriangle className="mr-2 h-5 w-5" />
                  Critical Issues
                </h3>
                <ul className="mt-2 space-y-1">
                  {criticalComponents.map(([name, status]) => (
                    <li key={name} className="text-sm text-red-600">
                      • {name.replace(/_/g, ' ')}: {status.error || 'Unhealthy'}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium mb-2">Data Services</h3>
                {dataFeedComponents.length > 0 ? (
                  <Card>
                    <CardContent className="p-4">
                      {dataFeedComponents.map(([name, status]) => (
                        <StatusIndicator
                          key={name}
                          healthy={status.healthy}
                          name={name.replace('data_feed_', '').replace(/_/g, ' ')}
                          value={status.latency_ms ? formatLatency(status.latency_ms) : undefined}
                          icon={<Timer className={`h-5 w-5 ${status.healthy ? 'text-green-500' : 'text-red-500'}`} />}
                        />
                      ))}
                    </CardContent>
                  </Card>
                ) : (
                  <p className="text-muted-foreground text-sm">No data feed services detected</p>
                )}
              </div>
              
              <div>
                <h3 className="font-medium mb-2">System Resources</h3>
                <Card>
                  <CardContent className="p-4 space-y-4">
                    {healthStatus.components.cpu_usage && (
                      <ResourceBar
                        label="CPU Usage"
                        value={healthStatus.components.cpu_usage.usage_percent || 0}
                        max={100}
                      />
                    )}
                    
                    {healthStatus.components.memory_usage && (
                      <ResourceBar
                        label="Memory Usage"
                        value={healthStatus.components.memory_usage.usage_percent || 0}
                        max={100}
                      />
                    )}
                    
                    {healthStatus.components.disk_space && (
                      <ResourceBar
                        label="Disk Usage"
                        value={healthStatus.components.disk_space.usage_percent || 0}
                        max={100}
                      />
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="data-feeds" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Data Feed Latency</CardTitle>
                <CardDescription>Response time for external data sources</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(healthStatus.data_feed_latency).map(([source, data]) => (
                    <div key={source} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className={`p-2 rounded-full ${data.latency_ms < 1000 ? 'bg-green-50' : 'bg-yellow-50'}`}>
                          <Database className={`h-5 w-5 ${data.latency_ms < 1000 ? 'text-green-500' : 'text-yellow-500'}`} />
                        </div>
                        <div className="ml-3">
                          <div className="font-medium">{source}</div>
                          <div className="text-xs text-muted-foreground">
                            Updated: {formatDate(data.timestamp)}
                          </div>
                        </div>
                      </div>
                      <div>
                        <Badge
                          className={
                            data.latency_ms < 500
                              ? "bg-green-500"
                              : data.latency_ms < 1000
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          }
                        >
                          {formatLatency(data.latency_ms)}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  
                  {Object.keys(healthStatus.data_feed_latency).length === 0 && (
                    <p className="text-center py-4 text-muted-foreground">
                      No data feed latency information available
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="resources" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {resourceComponents.map(([name, status]) => {
                let icon;
                if (name === 'cpu_usage') {
                  icon = <Cpu className="h-6 w-6" />;
                } else if (name === 'memory_usage') {
                  icon = <Activity className="h-6 w-6" />;
                } else {
                  icon = <HardDrive className="h-6 w-6" />;
                }
                
                return (
                  <Card key={name}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center">
                        {icon}
                        <span className="ml-2">{name.replace(/_/g, ' ')}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">
                        {status.usage_percent ? `${status.usage_percent.toFixed(1)}%` : 'N/A'}
                      </div>
                      
                      {status.available_mb && (
                        <div className="text-sm text-muted-foreground">
                          {(status.available_mb / 1024).toFixed(2)} GB available
                        </div>
                      )}
                      
                      {status.free_mb && (
                        <div className="text-sm text-muted-foreground">
                          {(status.free_mb / 1024).toFixed(2)} GB free
                        </div>
                      )}
                    </CardContent>
                    <CardFooter className="pt-0">
                      <Badge className={status.healthy ? "bg-green-500" : "bg-red-500"}>
                        {status.healthy ? "Healthy" : "Warning"}
                      </Badge>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
          
          <TabsContent value="alerts" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Alerts</CardTitle>
                <CardDescription>System health notifications and warnings</CardDescription>
              </CardHeader>
              <CardContent>
                {alerts && alerts.alerts.length > 0 ? (
                  <div className="space-y-4">
                    {alerts.alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`p-3 rounded-md border ${
                          alert.level === 'CRITICAL'
                            ? 'bg-red-50 border-red-200'
                            : alert.level === 'WARNING'
                            ? 'bg-yellow-50 border-yellow-200'
                            : 'bg-blue-50 border-blue-200'
                        }`}
                      >
                        <div className="flex items-center">
                          <AlertTriangle
                            className={`h-5 w-5 mr-2 ${
                              alert.level === 'CRITICAL'
                                ? 'text-red-500'
                                : alert.level === 'WARNING'
                                ? 'text-yellow-500'
                                : 'text-blue-500'
                            }`}
                          />
                          <div className="font-medium">{alert.component}</div>
                          <Badge
                            className={`ml-2 ${
                              alert.level === 'CRITICAL'
                                ? 'bg-red-500'
                                : alert.level === 'WARNING'
                                ? 'bg-yellow-500'
                                : 'bg-blue-500'
                            }`}
                          >
                            {alert.level}
                          </Badge>
                          {alert.resolved && (
                            <Badge className="ml-2 bg-green-500">Resolved</Badge>
                          )}
                        </div>
                        <p className="mt-1 text-sm">{alert.message}</p>
                        <div className="mt-2 text-xs text-muted-foreground">
                          {formatDate(alert.timestamp)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center">
                    <Zap className="mx-auto h-8 w-8 text-muted-foreground" />
                    <p className="mt-2 text-muted-foreground">No alerts to display</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </CardContent>
      
      <CardFooter className="justify-between border-t pt-4">
        <div className="text-xs text-muted-foreground">
          System Health Monitor v1.0
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center text-xs text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className="mr-1 h-3 w-3" />
          Refresh
        </button>
      </CardFooter>
    </Card>
  );
};

export default SystemHealthPanel;
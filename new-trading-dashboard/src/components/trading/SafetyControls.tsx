import React, { useState, useEffect } from 'react';
import { ShieldAlert, Clock, ToggleLeft, ToggleRight, Ban, RefreshCw, AlertTriangle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWebSocketMessage } from '@/services/websocket';
import safetyApi, { SafetyStatus } from '@/services/safetyApi';

const SafetyControls: React.FC = () => {
  const queryClient = useQueryClient();
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatus>({
    tradingMode: 'paper',
    emergencyStopActive: false,
    circuitBreakers: {
      active: false
    },
    cooldowns: {
      active: false
    },
    tradingAllowed: true
  });
  
  // Countdown timer for cooldown
  const [cooldownTimeLeft, setCooldownTimeLeft] = useState<number>(0);
  
  // Get initial safety status
  const { isLoading } = useQuery({
    queryKey: ['safetyStatus'],
    queryFn: () => safetyApi.getSafetyStatus(),
    onSuccess: (response) => {
      if (response.success && response.data) {
        setSafetyStatus(response.data);
        
        if (response.data.cooldowns.active && response.data.cooldowns.remainingSeconds) {
          setCooldownTimeLeft(response.data.cooldowns.remainingSeconds);
        }
      }
    },
    refetchInterval: 10000 // Refresh every 10 seconds
  });
  
  // Mutations
  const toggleTradingMode = useMutation({
    mutationFn: (mode: 'live' | 'paper') => safetyApi.setTradingMode(mode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus'] });
    }
  });
  
  const toggleEmergencyStop = useMutation({
    mutationFn: (active: boolean) => safetyApi.setEmergencyStop(active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus'] });
    }
  });

  const resetCircuitBreaker = useMutation({
    mutationFn: () => safetyApi.resetCircuitBreaker(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus'] });
    }
  });

  const resetCooldown = useMutation({
    mutationFn: () => safetyApi.resetCooldown(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['safetyStatus'] });
    }
  });
  
  // WebSocket updates
  useWebSocketMessage<SafetyStatus>(
    'safety_status_update',
    (message) => {
      setSafetyStatus(message.data);
      
      if (message.data.cooldowns.active && message.data.cooldowns.remainingSeconds) {
        setCooldownTimeLeft(message.data.cooldowns.remainingSeconds);
      } else {
        setCooldownTimeLeft(0);
      }
    },
    []
  );
  
  // Countdown timer effect
  useEffect(() => {
    if (!safetyStatus.cooldowns.active || cooldownTimeLeft <= 0) return;
    
    const timer = setInterval(() => {
      setCooldownTimeLeft(prev => {
        const newValue = prev - 1;
        if (newValue <= 0) {
          clearInterval(timer);
          return 0;
        }
        return newValue;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [safetyStatus.cooldowns.active, cooldownTimeLeft]);
  
  // Format time remaining for cooldown
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds <= 0) return '00:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="p-4 bg-card border border-border rounded-lg">
        <p className="text-center text-muted-foreground">Loading safety controls...</p>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Emergency Stop */}
      <div 
        className={`rounded-lg border p-4 flex flex-col items-center justify-center
          ${safetyStatus.emergencyStopActive 
            ? 'bg-bear/10 border-bear' 
            : 'bg-card border-border'
          }`}
      >
        <div className="flex items-center justify-between w-full mb-2">
          <h3 className="font-medium">Emergency Stop</h3>
          <button
            onClick={() => toggleEmergencyStop.mutate(!safetyStatus.emergencyStopActive)}
            className={`rounded-full p-1 transition-colors
              ${safetyStatus.emergencyStopActive
                ? 'bg-bear/20 text-bear hover:bg-bear/30'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            aria-label={safetyStatus.emergencyStopActive ? "Deactivate emergency stop" : "Activate emergency stop"}
            title={safetyStatus.emergencyStopActive ? "Deactivate emergency stop" : "Activate emergency stop"}
          >
            <Ban size={20} />
          </button>
        </div>
        
        <div className="w-full text-center py-3">
          <span className={`text-lg font-medium
            ${safetyStatus.emergencyStopActive ? 'text-bear' : 'text-success'}`}
          >
            {safetyStatus.emergencyStopActive ? 'ACTIVE' : 'INACTIVE'}
          </span>
          
          <p className="text-xs text-muted-foreground mt-2">
            {safetyStatus.emergencyStopActive 
              ? "Emergency stop is active. All trading is halted."
              : "Activate to immediately halt all trading activity."}
          </p>
        </div>
      </div>
      
      {/* Trading Mode */}
      <div className="rounded-lg border border-border bg-card p-4 flex flex-col">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium">Trading Mode</h3>
          <button
            onClick={() => toggleTradingMode.mutate(safetyStatus.tradingMode === 'live' ? 'paper' : 'live')}
            className="rounded-full p-1 bg-muted text-primary hover:bg-muted/80 transition-colors"
            aria-label="Toggle trading mode"
            title="Toggle trading mode"
          >
            {safetyStatus.tradingMode === 'live' 
              ? <ToggleRight size={20} /> 
              : <ToggleLeft size={20} />}
          </button>
        </div>
        
        <div className="w-full text-center py-3">
          <div className="flex items-center justify-center gap-2">
            <span 
              className={`px-3 py-1 rounded-full text-sm font-medium
                ${safetyStatus.tradingMode === 'paper' 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-muted text-muted-foreground'
                }`}
            >
              Paper
            </span>
            <span 
              className={`px-3 py-1 rounded-full text-sm font-medium
                ${safetyStatus.tradingMode === 'live' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-muted text-muted-foreground'
                }`}
            >
              Live
            </span>
          </div>
          
          <p className="text-xs text-muted-foreground mt-2">
            {safetyStatus.tradingMode === 'live' 
              ? "Live mode: Real trades will be executed with real money."
              : "Paper mode: Simulated trades only, no real money at risk."}
          </p>
        </div>
      </div>
      
      {/* Circuit Breaker */}
      <div 
        className={`rounded-lg border p-4 flex flex-col
          ${safetyStatus.circuitBreakers.active 
            ? 'bg-highImpact/10 border-highImpact' 
            : 'bg-card border-border'
          }`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center">
            <AlertTriangle 
              size={20} 
              className={`mr-2 ${safetyStatus.circuitBreakers.active ? 'text-highImpact' : 'text-muted-foreground'}`} 
            />
            <h3 className="font-medium">Circuit Breaker</h3>
          </div>
          
          {safetyStatus.circuitBreakers.active && (
            <button
              onClick={() => resetCircuitBreaker.mutate()}
              className="rounded-full p-1 bg-muted/70 text-highImpact hover:bg-muted transition-colors"
              aria-label="Reset circuit breaker"
              title="Reset circuit breaker"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>
        
        <div className="w-full">
          <div className="flex items-center justify-between">
            <span className="text-sm">Status:</span>
            <span 
              className={`text-sm font-medium
                ${safetyStatus.circuitBreakers.active 
                  ? 'text-highImpact' 
                  : 'text-success'
                }`}
            >
              {safetyStatus.circuitBreakers.active ? 'TRIGGERED' : 'NORMAL'}
            </span>
          </div>
          
          {safetyStatus.circuitBreakers.active && (
            <>
              <div className="flex items-center justify-between mt-1">
                <span className="text-sm">Reason:</span>
                <span className="text-sm">{safetyStatus.circuitBreakers.reason}</span>
              </div>
              
              {safetyStatus.circuitBreakers.maxDailyLoss && (
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm">Daily Loss:</span>
                  <span className="text-sm">${safetyStatus.circuitBreakers.currentDailyLoss?.toFixed(2)} / ${safetyStatus.circuitBreakers.maxDailyLoss.toFixed(2)}</span>
                </div>
              )}
              
              {safetyStatus.circuitBreakers.maxTradesPerDay && (
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm">Trade Count:</span>
                  <span className="text-sm">{safetyStatus.circuitBreakers.currentTradeCount} / {safetyStatus.circuitBreakers.maxTradesPerDay}</span>
                </div>
              )}
            </>
          )}
          
          {!safetyStatus.circuitBreakers.active && (
            <p className="text-xs text-muted-foreground mt-2">
              Circuit breakers are active and monitoring for excessive losses or trades.
            </p>
          )}
        </div>
      </div>
      
      {/* Cooldown Timer */}
      <div 
        className={`rounded-lg border p-4 flex flex-col
          ${safetyStatus.cooldowns.active 
            ? 'bg-infoImpact/10 border-infoImpact' 
            : 'bg-card border-border'
          }`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center">
            <Clock 
              size={20} 
              className={`mr-2 ${safetyStatus.cooldowns.active ? 'text-infoImpact' : 'text-muted-foreground'}`} 
            />
            <h3 className="font-medium">Trading Cooldown</h3>
          </div>
          
          {safetyStatus.cooldowns.active && (
            <button
              onClick={() => resetCooldown.mutate()}
              className="rounded-full p-1 bg-muted/70 text-infoImpact hover:bg-muted transition-colors"
              aria-label="Reset cooldown"
              title="Reset cooldown"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>
        
        <div className="w-full">
          <div className="flex items-center justify-between">
            <span className="text-sm">Status:</span>
            <span 
              className={`text-sm font-medium
                ${safetyStatus.cooldowns.active 
                  ? 'text-infoImpact' 
                  : 'text-success'
                }`}
            >
              {safetyStatus.cooldowns.active ? 'ACTIVE' : 'READY'}
            </span>
          </div>
          
          {safetyStatus.cooldowns.active && (
            <>
              <div className="flex items-center justify-between mt-1">
                <span className="text-sm">Remaining:</span>
                <span className="text-sm font-mono">{formatTimeRemaining(cooldownTimeLeft)}</span>
              </div>
              
              <div className="flex items-center justify-between mt-1">
                <span className="text-sm">Reason:</span>
                <span className="text-sm">{safetyStatus.cooldowns.reason}</span>
              </div>
            </>
          )}
          
          {!safetyStatus.cooldowns.active && (
            <p className="text-xs text-muted-foreground mt-2">
              No active cooldown. System will enter cooldown after losses to prevent overtrading.
            </p>
          )}
        </div>
      </div>
      
      {/* Trading Status Summary */}
      <div className={`rounded-lg border p-4 lg:col-span-4 flex flex-col
        ${!safetyStatus.tradingAllowed 
          ? 'bg-bear/5 border-bear/20' 
          : 'bg-bull/5 border-bull/20'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ShieldAlert 
              size={20} 
              className={`mr-2 ${!safetyStatus.tradingAllowed ? 'text-bear' : 'text-bull'}`} 
            />
            <h3 className="font-medium">Trading Status</h3>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-2">
          <span 
            className={`text-lg font-medium px-4 py-1 rounded-full 
              ${!safetyStatus.tradingAllowed 
                ? 'bg-bear/10 text-bear' 
                : 'bg-bull/10 text-bull'
              }`}
          >
            {!safetyStatus.tradingAllowed ? 'TRADING HALTED' : 'TRADING ALLOWED'}
          </span>
        </div>
        
        {!safetyStatus.tradingAllowed && safetyStatus.tradingBlockedReason && (
          <p className="text-center text-sm text-muted-foreground mt-1">
            Reason: {
              safetyStatus.tradingBlockedReason === 'emergency_stop_active' ? 'Emergency stop is active' :
              safetyStatus.tradingBlockedReason === 'circuit_breaker_active' ? 'Circuit breaker is triggered' :
              safetyStatus.tradingBlockedReason === 'cooldown_active' ? 'System is in cooldown' :
              safetyStatus.tradingBlockedReason
            }
          </p>
        )}
      </div>
    </div>
  );
};

export default SafetyControls;

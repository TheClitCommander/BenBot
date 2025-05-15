import { useState, useEffect } from 'react';
import { SystemStatus } from './useSystemStatus';

export const useStatusSocket = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    
    const connectWebSocket = () => {
      // Use relative URL to leverage Vite's proxy
      const wsUrl = `${window.location.protocol.replace('http', 'ws')}//${window.location.host}/ws`;
      
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setError(null);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as SystemStatus;
            setStatus(data);
          } catch (e) {
            console.error('Failed to parse WebSocket message', e);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error', error);
          setError(new Error('Failed to connect to status WebSocket'));
          setIsConnected(false);
        };
        
        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          
          // Attempt to reconnect after delay
          setTimeout(() => {
            connectWebSocket();
          }, 5000);
        };
      } catch (err) {
        console.error('Failed to establish WebSocket connection', err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
        setIsConnected(false);
        
        // Attempt to reconnect after delay
        setTimeout(() => {
          connectWebSocket();
        }, 5000);
      }
    };
    
    connectWebSocket();
    
    // Clean up
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);
  
  return { status, isConnected, error };
}; 
import { useState, useEffect, useRef } from 'react';

interface TradeUpdate {
  type: string;
  data: {
    timestamp: string;
    symbol: string;
    price: number;
    volume: number;
    side: 'buy' | 'sell';
  };
}

export const useTradeStream = (enabled = true) => {
  const [isConnected, setIsConnected] = useState(false);
  const [trades, setTrades] = useState<TradeUpdate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Get WebSocket URL from environment or use default
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Function to initialize WebSocket connection
    const connectWebSocket = () => {
      try {
        // Close existing connection if it exists
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.close();
        }

        // Create new WebSocket connection
        wsRef.current = new WebSocket(wsUrl);

        // Connection opened
        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setError(null);
        };

        // Listen for messages
        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            // Only handle trade updates
            if (message.type === 'trade_update') {
              setTrades((prev) => {
                // Keep only latest 100 trades
                const updatedTrades = [message, ...prev];
                return updatedTrades.slice(0, 100);
              });
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e);
          }
        };

        // Connection closed
        wsRef.current.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setIsConnected(false);
          
          // Try to reconnect after a delay unless closed deliberately (code 1000)
          if (event.code !== 1000) {
            setTimeout(() => {
              connectWebSocket();
            }, 5000); // Reconnect after 5 seconds
          }
        };

        // Error handling
        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setError('Connection error, will retry...');
        };
      } catch (e) {
        console.error('Failed to initialize WebSocket:', e);
        setError('Failed to initialize connection, will retry...');
        
        // Try to reconnect after delay
        setTimeout(() => {
          connectWebSocket();
        }, 5000);
      }
    };

    // Initialize connection
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        // Use code 1000 for normal closure
        wsRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [enabled, wsUrl]);

  // Function to manually reconnect
  const reconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setError('Reconnecting...');
    setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
        wsRef.current = new WebSocket(wsUrl);
      }
    }, 1000);
  };

  return {
    isConnected,
    trades,
    error,
    reconnect
  };
};

export default useTradeStream; 
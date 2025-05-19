import { useState, useEffect, useRef, useCallback } from 'react';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface UseWebSocketOptions {
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  reconnectInterval?: number;
  reconnectAttempts?: number;
  automaticOpen?: boolean;
}

interface UseWebSocketResult {
  status: WebSocketStatus;
  sendMessage: (data: any) => void;
  reconnect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for WebSocket connections with auto-reconnect capabilities
 */
export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const {
    onOpen,
    onMessage,
    onClose,
    onError,
    reconnectInterval = 2000,
    reconnectAttempts = 10,
    automaticOpen = true,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const webSocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const attemptRef = useRef(0);

  // Clean up function to reset WebSocket
  const cleanUp = useCallback(() => {
    if (webSocketRef.current) {
      webSocketRef.current.onopen = null;
      webSocketRef.current.onmessage = null;
      webSocketRef.current.onclose = null;
      webSocketRef.current.onerror = null;
      
      if (webSocketRef.current.readyState === WebSocket.OPEN) {
        webSocketRef.current.close();
      }
      
      webSocketRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Connect function to establish WebSocket connection
  const connect = useCallback(() => {
    cleanUp();
    
    try {
      setStatus('connecting');
      webSocketRef.current = new WebSocket(url);

      webSocketRef.current.onopen = (event) => {
        setStatus('connected');
        attemptRef.current = 0;
        
        if (onOpen) {
          onOpen(event);
        }
      };

      webSocketRef.current.onmessage = (event) => {
        if (onMessage) {
          onMessage(event);
        }
      };

      webSocketRef.current.onclose = (event) => {
        setStatus('disconnected');
        
        if (onClose) {
          onClose(event);
        }

        // Attempt to reconnect if not closed cleanly and we haven't exceeded max attempts
        if (!event.wasClean && attemptRef.current < reconnectAttempts) {
          attemptRef.current += 1;
          setStatus('reconnecting');
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, reconnectInterval * Math.pow(1.5, attemptRef.current - 1)); // Exponential backoff
        }
      };

      webSocketRef.current.onerror = (event) => {
        if (onError) {
          onError(event);
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setStatus('disconnected');
    }
  }, [url, onOpen, onMessage, onClose, onError, reconnectInterval, reconnectAttempts, cleanUp]);

  // Reconnect manually
  const reconnect = useCallback(() => {
    attemptRef.current = 0;
    connect();
  }, [connect]);

  // Disconnect manually
  const disconnect = useCallback(() => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      webSocketRef.current.close();
    }
  }, []);

  // Send message function
  const sendMessage = useCallback((data: any) => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      webSocketRef.current.send(message);
      return true;
    }
    return false;
  }, []);

  // Initialize WebSocket connection on mount
  useEffect(() => {
    if (automaticOpen) {
      connect();
    }

    return () => {
      cleanUp();
    };
  }, [url, connect, cleanUp, automaticOpen]);

  return {
    status,
    sendMessage,
    reconnect,
    disconnect
  };
}

export default useWebSocket; 
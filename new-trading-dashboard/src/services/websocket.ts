import { useEffect, useRef } from 'react';

// WebSocket connection URL
const WS_URL = import.meta.env.VITE_API_URL?.replace('http', 'ws') || 'ws://localhost:8000/ws';

// Message types
export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
}

// Singleton WebSocket instance
let socket: WebSocket | null = null;
let isConnecting = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

// Listeners by message type
const listeners: Record<string, Set<(message: WebSocketMessage) => void>> = {};

// Initialize WebSocket connection
const initializeWebSocket = () => {
  if (socket || isConnecting) return;
  
  isConnecting = true;
  
  socket = new WebSocket(WS_URL);
  
  socket.onopen = () => {
    console.log('WebSocket connection established');
    isConnecting = false;
    reconnectAttempts = 0;
  };
  
  socket.onmessage = (event) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Notify all listeners for this message type
      if (message.type && listeners[message.type]) {
        listeners[message.type].forEach(callback => {
          callback(message);
        });
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };
  
  socket.onclose = () => {
    console.log('WebSocket connection closed');
    socket = null;
    isConnecting = false;
    
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      setTimeout(initializeWebSocket, RECONNECT_DELAY);
    }
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    socket?.close();
  };
};

// Send a message through the WebSocket
export const sendMessage = (type: string, data: any = {}) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    initializeWebSocket();
    console.warn('WebSocket not connected, message not sent');
    return false;
  }
  
  socket.send(JSON.stringify({ type, data }));
  return true;
};

// Use WebSocket to listen for specific message types
export const useWebSocketMessage = <T>(
  messageType: string, 
  callback: (message: WebSocketMessage<T>) => void,
  deps: any[] = []
) => {
  const callbackRef = useRef(callback);
  
  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);
  
  useEffect(() => {
    // Initialize WebSocket if not already done
    initializeWebSocket();
    
    // Create a listener function
    const listener = (message: WebSocketMessage) => {
      callbackRef.current(message);
    };
    
    // Initialize listener set if needed
    if (!listeners[messageType]) {
      listeners[messageType] = new Set();
    }
    
    // Add the listener
    listeners[messageType].add(listener);
    
    // Cleanup on unmount
    return () => {
      if (listeners[messageType]) {
        listeners[messageType].delete(listener);
        
        // Remove the message type if no listeners remain
        if (listeners[messageType].size === 0) {
          delete listeners[messageType];
        }
      }
    };
  }, [messageType, ...deps]);
};

// Hook to maintain an active WebSocket connection
export const useWebSocket = () => {
  useEffect(() => {
    initializeWebSocket();
    
    // Cleanup on unmount
    return () => {
      // Don't close the WebSocket as other components might be using it
      // It will be managed by the singleton pattern
    };
  }, []);
  
  return {
    sendMessage,
    isConnected: socket !== null && socket.readyState === WebSocket.OPEN
  };
};

export default {
  sendMessage,
  useWebSocketMessage,
  useWebSocket
}; 
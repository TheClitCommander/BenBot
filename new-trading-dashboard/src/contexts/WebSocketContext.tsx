import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import useWebSocket, { WebSocketStatus } from '../hooks/useWebSocket';

interface MarketData {
  timestamp: number;
  market_data: {
    [symbol: string]: {
      price: number;
      volume: number;
    };
  };
}

interface PortfolioData {
  timestamp: number;
  portfolio: {
    total_value: number;
    cash: number;
    positions_value: number;
    day_pnl: number;
    day_pnl_percent: number;
  };
}

interface WebSocketContextType {
  status: WebSocketStatus;
  marketData: MarketData | null;
  portfolioData: PortfolioData | null;
  reconnect: () => void;
  disconnect: () => void;
  sendMessage: (data: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  
  // Get the WebSocket URL from environment variables
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws';

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.market_data) {
        setMarketData(data as MarketData);
      } else if (data.portfolio) {
        setPortfolioData(data as PortfolioData);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, []);

  // Initialize WebSocket
  const { status, sendMessage, reconnect, disconnect } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    reconnectInterval: 3000,
    reconnectAttempts: 20,
  });

  return (
    <WebSocketContext.Provider
      value={{
        status,
        marketData,
        portfolioData,
        reconnect,
        disconnect,
        sendMessage,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

export default WebSocketContext; 
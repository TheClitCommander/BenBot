import React from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

interface WebSocketStatusIndicatorProps {
  className?: string;
}

const WebSocketStatusIndicator: React.FC<WebSocketStatusIndicatorProps> = ({ className = '' }) => {
  const { status, reconnect } = useWebSocketContext();
  
  // Determine the color and text based on the connection status
  let statusColor = '';
  let statusText = '';
  
  switch (status) {
    case 'connected':
      statusColor = 'bg-green-500';
      statusText = 'Connected';
      break;
    case 'connecting':
      statusColor = 'bg-yellow-500';
      statusText = 'Connecting...';
      break;
    case 'reconnecting':
      statusColor = 'bg-yellow-500';
      statusText = 'Reconnecting...';
      break;
    case 'disconnected':
      statusColor = 'bg-red-500';
      statusText = 'Disconnected';
      break;
    default:
      statusColor = 'bg-gray-500';
      statusText = 'Unknown';
  }
  
  return (
    <div className={`flex items-center ${className}`}>
      <div className={`w-3 h-3 rounded-full ${statusColor} mr-2`} />
      <span className="text-sm">{statusText}</span>
      
      {status === 'disconnected' && (
        <button
          onClick={reconnect}
          className="ml-2 text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Reconnect
        </button>
      )}
    </div>
  );
};

export default WebSocketStatusIndicator; 
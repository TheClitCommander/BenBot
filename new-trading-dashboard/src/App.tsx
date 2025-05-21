import React, { useState, useEffect } from 'react';
import LiveTradesPanel from './components/LiveTradesPanel';
import DebugPanel from './components/DebugPanel';
import { apiService } from './api/client';
import { WebSocketProvider } from './contexts/WebSocketContext';
import WebSocketStatusIndicator from './components/WebSocketStatusIndicator';

// Simple error boundary component
class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: 'red', border: '1px solid red' }}>
          <h2>Something went wrong!</h2>
          <details>
            <summary>View error details</summary>
            <pre>{this.state.error?.toString()}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  console.log('App component rendering');
  
  // Debug info for connection status
  useEffect(() => {
    // Log the API base URL and mock data status
    console.log('API URL:', import.meta.env.VITE_API_URL || 'Not set');
    console.log('WebSocket URL:', import.meta.env.VITE_WS_URL || 'Not set');
    console.log('Force Mock Data:', import.meta.env.VITE_FORCE_MOCK_DATA || 'Not set');
    console.log('Using Mock Data:', (apiService as any).useMockData);
    
    // Try a health check
    apiService.health()
      .then(response => console.log('Health check response:', response))
      .catch(error => console.error('Health check error:', error));
  }, []);
  
  // State for active tab
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Mock data
  const portfolioValue = '$10,245.80';
  const portfolioChange = '+2.3% today';
  const activeStrategies = '7';
  const strategiesStats = '3 profitable, 4 in development';
  const openPositions = '12';
  const positionsStats = '8 long, 4 short';
  const cpuUsage = '25%';
  const memoryUsage = '42%';
  const uptime = '4d 7h';
  const lastTradeTime = '15m ago';
  
  // Sample strategies
  const strategies = [
    { name: 'Mean Reversion Alpha', type: 'Mean Reversion', return: '+18.2%', status: 'Active' },
    { name: 'Trend Follower', type: 'Trend Following', return: '+12.5%', status: 'Active' },
    { name: 'Volatility Breakout', type: 'Breakout', return: '-3.2%', status: 'Optimizing' }
  ];
  
  // Handle tab click
  const handleTabClick = (tab: string) => {
    setActiveTab(tab);
  };
  
  return (
    <WebSocketProvider>
      <ErrorBoundary>
        <div style={{ 
          fontFamily: 'Arial, sans-serif',
          margin: 0,
          padding: 0,
          backgroundColor: '#f2f2f2',
          color: '#333',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden'
        }}>
          {/* Main container */}
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            width: '100%'
          }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '10px 20px',
              backgroundColor: 'white',
              boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)',
              zIndex: 100
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center'
              }}>
                <h2 style={{ margin: 0, marginRight: '10px' }}>BensBot</h2>
                <span style={{ fontSize: '14px', color: '#666' }}>Trading Dashboard</span>
              </div>
              
              {/* Status indicators */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '15px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                  <span>▪️</span>
                  <span>CPU <span>{cpuUsage}</span></span>
                  <div style={{ 
                    width: '50px', 
                    height: '6px', 
                    backgroundColor: '#eee', 
                    marginLeft: '5px',
                    borderRadius: '3px'
                  }}>
                    <div style={{ 
                      width: cpuUsage, 
                      height: '100%', 
                      backgroundColor: '#4CAF50',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                  <span>▪️</span>
                  <span>Mem <span>{memoryUsage}</span></span>
                  <div style={{ 
                    width: '50px', 
                    height: '6px', 
                    backgroundColor: '#eee', 
                    marginLeft: '5px',
                    borderRadius: '3px'
                  }}>
                    <div style={{ 
                      width: memoryUsage, 
                      height: '100%', 
                      backgroundColor: '#4CAF50',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                  <span>▪️</span>
                  <span>Uptime <span>{uptime}</span></span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                  <span>▪️</span>
                  <span>Last trade <span>{lastTradeTime}</span></span>
                </div>
                
                <div style={{ 
                  backgroundColor: (apiService as any).useMockData ? '#FFD700' : '#4CAF50',
                  color: '#333', 
                  padding: '3px 8px', 
                  borderRadius: '3px', 
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  {(apiService as any).useMockData ? 'Mock Data' : 'Live Data'}
                </div>
              </div>
            </div>
            
            {/* Content */}
            <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
              {/* Tab Navigation */}
              <div style={{
                display: 'flex',
                borderBottom: '1px solid #ddd',
                marginBottom: '20px'
              }}>
                {['dashboard', 'strategies', 'pipeline', 'positions', 'trades', 'markets', 'risk', 'automation', 'settings'].map(tab => (
                  <button 
                    key={tab}
                    onClick={() => handleTabClick(tab)}
                    style={{
                      padding: '10px 15px',
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      fontWeight: activeTab === tab ? 'bold' : 'normal',
                      borderBottom: activeTab === tab ? '3px solid #0066cc' : 'none',
                      color: activeTab === tab ? '#0066cc' : '#333',
                      textTransform: 'capitalize'
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              
              {/* Dashboard Tab Content */}
              {activeTab === 'dashboard' && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gridTemplateRows: 'auto',
                  gap: '20px',
                  marginBottom: '20px'
                }}>
                  {/* First row */}
                  <div style={{
                    gridColumn: '1 / 2',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>Portfolio Value</h3>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{portfolioValue}</div>
                    <div style={{ fontSize: '14px', color: 'green' }}>{portfolioChange}</div>
                  </div>
                  
                  <div style={{
                    gridColumn: '2 / 3',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>Active Strategies</h3>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{activeStrategies}</div>
                    <div style={{ fontSize: '14px', color: '#666' }}>{strategiesStats}</div>
                  </div>
                  
                  <div style={{
                    gridColumn: '3 / 4',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>Open Positions</h3>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{openPositions}</div>
                    <div style={{ fontSize: '14px', color: '#666' }}>{positionsStats}</div>
                  </div>
                  
                  <div style={{
                    gridColumn: '4 / 5',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>Risk Score</h3>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>Medium</div>
                    <div style={{ fontSize: '14px', color: '#ff9800' }}>Risk Checker Active</div>
                  </div>
                  
                  {/* Second row */}
                  <div style={{
                    gridColumn: '1 / 3',
                    gridRow: '2 / 4',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', color: '#666' }}>Portfolio Performance</h3>
                    <div style={{ 
                      border: '1px dashed #ccc', 
                      borderRadius: '5px', 
                      padding: '40px',
                      height: '250px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      Chart Placeholder
                    </div>
                  </div>
                  
                  <div style={{
                    gridColumn: '3 / 5',
                    gridRow: '2 / 3',
                    backgroundColor: 'white',
                    borderRadius: '5px',
                    padding: '20px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', color: '#666' }}>Top Strategies</h3>
                    <table style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      fontSize: '14px'
                    }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: 'left', padding: '8px 5px', borderBottom: '1px solid #ddd' }}>Strategy</th>
                          <th style={{ textAlign: 'left', padding: '8px 5px', borderBottom: '1px solid #ddd' }}>Type</th>
                          <th style={{ textAlign: 'right', padding: '8px 5px', borderBottom: '1px solid #ddd' }}>Return</th>
                          <th style={{ textAlign: 'right', padding: '8px 5px', borderBottom: '1px solid #ddd' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {strategies.map((strategy, index) => (
                          <tr key={index}>
                            <td style={{ padding: '8px 5px', borderBottom: '1px solid #eee' }}>{strategy.name}</td>
                            <td style={{ padding: '8px 5px', borderBottom: '1px solid #eee' }}>{strategy.type}</td>
                            <td style={{ 
                              padding: '8px 5px', 
                              borderBottom: '1px solid #eee',
                              textAlign: 'right',
                              color: strategy.return.startsWith('+') ? 'green' : 'red'
                            }}>{strategy.return}</td>
                            <td style={{ 
                              padding: '8px 5px', 
                              borderBottom: '1px solid #eee',
                              textAlign: 'right'
                            }}>
                              <span style={{
                                display: 'inline-block',
                                padding: '2px 6px',
                                borderRadius: '3px',
                                fontSize: '12px',
                                backgroundColor: strategy.status === 'Active' ? '#e6f7e6' : '#fff3e0',
                                color: strategy.status === 'Active' ? '#388e3c' : '#ff9800'
                              }}>
                                {strategy.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  <div style={{
                    gridColumn: '3 / 5',
                    gridRow: '3 / 4',
                    height: '300px'
                  }}>
                    <LiveTradesPanel />
                  </div>
                </div>
              )}
              
              {/* Strategies Tab Content */}
              {activeTab === 'strategies' && (
                <div>
                  <h2>Strategies</h2>
                  <p>Your trading strategies will be displayed here.</p>
                </div>
              )}
              
              {/* Positions Tab Content */}
              {activeTab === 'positions' && (
                <div>
                  <h2>Positions</h2>
                  <p>Your open positions will be displayed here.</p>
                </div>
              )}
              
              {/* Trades Tab Content */}
              {activeTab === 'trades' && (
                <div style={{ height: 'calc(100vh - 200px)' }}>
                  <h2>Trades</h2>
                  <LiveTradesPanel />
                </div>
              )}
              
              {/* Debug Tab */}
              {activeTab === 'debug' && (
                <div style={{ height: 'calc(100vh - 200px)' }}>
                  <h2>Debug Information</h2>
                  <p>Use this panel to debug API and WebSocket connections.</p>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '15px', 
                    borderRadius: '5px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify({
                      apiUrl: import.meta.env.VITE_API_URL || 'Not set',
                      wsUrl: import.meta.env.VITE_WS_URL || 'Not set',
                      forceMockData: import.meta.env.VITE_FORCE_MOCK_DATA || 'Not set',
                      usingMockData: (apiService as any).useMockData
                    }, null, 2)}
                  </pre>
                </div>
              )}
              
              {/* Other tabs */}
              {activeTab !== 'dashboard' && 
               activeTab !== 'strategies' && 
               activeTab !== 'positions' && 
               activeTab !== 'trades' &&
               activeTab !== 'debug' && (
                <div>
                  <h2 style={{ textTransform: 'capitalize' }}>{activeTab}</h2>
                  <p>This feature is currently in development.</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Debug Panel */}
          <DebugPanel />
        </div>
      </ErrorBoundary>
    </WebSocketProvider>
  );
}

export default App; 
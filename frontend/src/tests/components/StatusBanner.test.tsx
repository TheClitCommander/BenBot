import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import StatusBanner from '../../components/StatusBanner';

// Mock the custom hook
jest.mock('../../hooks/useSystemStatus', () => ({
  useSystemStatus: jest.fn(() => ({
    data: {
      status: 'online',
      connection: 'production',
      cpu_usage: 25,
      memory_usage: 42,
      uptime: '4d 7h',
      last_trade_time: '15m ago',
    },
    isLoading: false,
    error: null,
  })),
}));

// Create a fresh QueryClient for each test
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
  },
});

describe('StatusBanner', () => {
  it('renders correctly when data is loaded', () => {
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <StatusBanner />
      </QueryClientProvider>
    );
    
    // Check that status items are displayed
    expect(screen.getByText(/Online/i)).toBeInTheDocument();
    expect(screen.getByText(/Production/i)).toBeInTheDocument();
    expect(screen.getByText(/25%/i)).toBeInTheDocument();
    expect(screen.getByText(/42%/i)).toBeInTheDocument();
    expect(screen.getByText(/4d 7h/i)).toBeInTheDocument();
    expect(screen.getByText(/15m ago/i)).toBeInTheDocument();
  });
  
  it('displays loading state', () => {
    // Override the mock to return loading state
    require('../../hooks/useSystemStatus').useSystemStatus.mockReturnValueOnce({
      data: null,
      isLoading: true,
      error: null,
    });
    
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <StatusBanner />
      </QueryClientProvider>
    );
    
    // Check that loading indicator is displayed
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });
  
  it('displays error state', () => {
    // Override the mock to return error state
    require('../../hooks/useSystemStatus').useSystemStatus.mockReturnValueOnce({
      data: null,
      isLoading: false,
      error: new Error('Failed to fetch system status'),
    });
    
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <StatusBanner />
      </QueryClientProvider>
    );
    
    // Check that error message is displayed
    expect(screen.getByText(/Error/i)).toBeInTheDocument();
  });
}); 
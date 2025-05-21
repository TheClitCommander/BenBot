import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import App from './App'
import './index.css'

console.log('Initializing application...');

// Create QueryClient with proper configuration for React Query v5
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 10 * 1000,
      gcTime: 60 * 1000 // Add gcTime (formerly cacheTime)
    },
  },
})

// Add more specific error boundary for debugging
const rootElement = document.getElementById('root')
if (!rootElement) {
  console.error('Root element not found')
} else {
  try {
    console.log('Rendering application...');
    
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </React.StrictMode>,
    )
    
    console.log('Application rendering complete');
  } catch (error) {
    console.error('Failed to render app:', error)
    rootElement.innerHTML = '<div style="padding: 20px; color: red;">Error rendering application. Check console for details.</div>'
  }
} 
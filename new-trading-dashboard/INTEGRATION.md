# Frontend-Backend Integration Guide

This document describes how the React frontend connects to the BensBot backend API and provides troubleshooting steps for connectivity issues.

## Architecture Overview

- **Backend**: FastAPI server exposing REST/WebSocket endpoints (port 8001)
- **Frontend**: React application with Vite (port 5173-5178)

## API Configuration

### Environment Variables

The frontend uses environment variables to configure the API:

```
# .env.local
VITE_API_BASE_URL=http://localhost:8001
```

This can also be overridden by the Vite proxy settings in `vite.config.ts`.

### Vite Proxy Configuration

The `vite.config.ts` contains proxy settings to handle API requests and WebSockets:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    },
    '/ws': {
      target: 'ws://localhost:8001',
      ws: true
    }
  }
}
```

This enables the frontend to make requests to `/api/*` which get proxied to the backend.

## API Client

The frontend uses Axios for API requests, configured in `src/api/client.ts`:

```typescript
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: 5000,
});
```

## Key API Endpoints

| Frontend Path | Backend Path | Description |
|---------------|-------------|-------------|
| `/api/health` | `/health` | Health check endpoint |
| `/api/status` | `/status` | System status |
| `/api/system/status` | `/system/status` | Detailed system status |
| `/api/strategies` | `/strategies` | Trading strategies |
| `/api/positions` | `/positions` | Open positions |
| `/api/trades` | `/trades` | Recent trades |
| `/api/markets/data` | `/markets/data` | Market data |
| `/api/metrics/risk` | `/metrics/risk` | Risk metrics |
| `/api/system/settings` | `/system/settings` | System settings |
| `/ws` | `/ws` | WebSocket endpoint |

## Data Flow

1. React components use custom hooks (in `src/hooks/`) to fetch data
2. Hooks use the API client to make requests
3. The Vite dev server proxies requests to the backend
4. Backend processes the request and returns data
5. React Query manages caching and state

## WebSocket Integration

The frontend connects to WebSockets for real-time updates using the `useStatusSocket` hook.

## Troubleshooting

1. **API Connection Issues**:
   - Verify backend is running: `curl http://localhost:8001/health`
   - Check `.env.local` has the correct API URL
   - Review browser console for CORS errors

2. **CORS Errors**:
   - Ensure backend has correct CORS configuration
   - Check the hostname/port in the frontend matches allowed origins in backend

3. **Proxy Issues**:
   - Verify proxy settings in `vite.config.ts`
   - Restart Vite dev server after changing proxy config

4. **WebSocket Connection Failures**:
   - Check WebSocket URL in hooks
   - Verify WebSocket proxy configuration
   - Inspect browser network tab for WebSocket handshake errors

5. **Endpoint Mismatches**:
   - Compare API paths used in frontend hooks with backend routes
   - Look for typos or inconsistent naming conventions

## Running the Stack

1. Start backend:
   ```
   python3 mock_api.py  # For development
   ```

2. Start frontend:
   ```
   cd new-trading-dashboard && npm run dev
   ```

3. Open browser:
   ```
   http://localhost:5173  # Or whatever port Vite is using
   ``` 
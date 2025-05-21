# Troubleshooting Guide for Trading Dashboard

This document provides a step-by-step guide to diagnosing and fixing issues with the BensBot Trading Dashboard, particularly around API connections and live data.

## Table of Contents
1. [Quick Start with Debug Mode](#quick-start-with-debug-mode)
2. [Checking if the Backend is Running](#checking-if-the-backend-is-running)
3. [Verifying API Connectivity](#verifying-api-connectivity)
4. [Environment Variables](#environment-variables)
5. [WebSocket Connection Issues](#websocket-connection-issues)
6. [Debug Console](#debug-console)
7. [Common Issues](#common-issues)
8. [Advanced Debugging](#advanced-debugging)

## Quick Start with Debug Mode

The easiest way to debug connection issues is to use the debug launch script:

```bash
# Run with real API and debug tools enabled
./launch_debug.sh

# Force using mock data 
./launch_debug.sh --mock-data

# Use a different port (for mock API)
./launch_debug.sh --api-port 8001

# Only start the frontend (if backend is already running)
./launch_debug.sh --frontend-only
```

## Checking if the Backend is Running

1. Check running processes:
   ```bash
   ps aux | grep uvicorn
   ```

2. If nothing shows up, the API server isn't running. Start it with:
   ```bash
   python3 -m uvicorn trading_bot.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. If you see permission errors, try:
   ```bash
   sudo python3 -m uvicorn trading_bot.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

## Verifying API Connectivity

1. Test the API health endpoint with curl:
   ```bash
   curl http://localhost:8000/health
   ```

2. If you get a response like `{"status":"healthy",...}`, the API is running correctly.

3. Test other endpoints:
   ```bash
   curl http://localhost:8000/metrics/overview
   curl http://localhost:8000/execution/positions
   ```

4. If you see errors or no response, the API may be running but have internal issues.

## Environment Variables

The dashboard needs the correct environment variables to connect to the API:

1. Check `.env.local` in the `new-trading-dashboard` directory:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000/ws
   VITE_FORCE_MOCK_DATA=false
   ```

2. After changing environment variables, restart the frontend:
   ```bash
   cd new-trading-dashboard && npm run dev
   ```

3. You can temporarily override environment variables when running:
   ```bash
   cd new-trading-dashboard && VITE_FORCE_MOCK_DATA=true npm run dev
   ```

## WebSocket Connection Issues

1. Check if your WebSocket server is running by testing with a tool like wscat:
   ```bash
   npm install -g wscat
   wscat -c ws://localhost:8000/ws
   ```

2. If you see a successful connection, the WebSocket server is working.

3. If it fails, check that your backend has WebSocket support enabled.

4. In the browser, open the Debug Panel and check the WebSocket status.

## Debug Console

The dashboard includes a built-in debug panel:

1. Click "Show Debug Panel" button at the bottom right of the dashboard
2. Check the environment variables section to confirm API URLs
3. Test endpoints directly from the panel
4. Toggle between mock and real data

## Common Issues

### Dashboard shows mock data but API is running

1. Check if `VITE_FORCE_MOCK_DATA` is set to `true` in `.env.local`
2. Open browser console and look for connection errors
3. Use the Debug Panel to test API endpoints
4. Try setting mock data mode off using the Debug Panel toggle

### CORS Errors in Browser Console

If you see errors like:
```
Access to XMLHttpRequest at 'http://localhost:8000/health' from origin 'http://localhost:5173' has been blocked by CORS policy
```

1. Ensure your API server has CORS headers set correctly:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. Restart the API server after making changes.

### Connection Refused / Network Error

1. Verify the API is running on the expected port
2. Check firewall settings that might block connections
3. Verify the ports aren't being used by other applications

## Advanced Debugging

For more advanced debugging:

1. Start the mock API on a different port to confirm the frontend works:
   ```bash
   python3 mock_api.py --port 8001
   ```

2. Then connect the frontend to it:
   ```bash
   cd new-trading-dashboard && VITE_API_URL=http://localhost:8001 npm run dev
   ```

3. Check browser network requests:
   - Open DevTools (F12)
   - Go to the Network tab
   - Filter by "XHR" or "WS" to see API requests
   - Look for errors or unexpected status codes

4. Enable verbose logging:
   - Open the browser console
   - Type `localStorage.debug = '*'` and press Enter
   - Reload the page to see more detailed logs

---

If you continue to experience issues after trying these steps, please open an issue with the full error details and steps to reproduce. 
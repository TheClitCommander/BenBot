# Quick Start Guide for Dashboard Debugging

This guide provides a summary of all the debugging tools and commands available for the BensBot Trading Dashboard.

## Launch Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `./launch_real_dashboard.sh` | Launches the real trading API with the React frontend | `./launch_real_dashboard.sh` |
| `./launch_dashboard.sh` | Launches the mock API with the React frontend | `./launch_dashboard.sh` |
| `./launch_debug.sh` | Advanced debugging script with options | See below |

## Debug Launch Script Options

The debug launch script provides several options for troubleshooting:

```bash
# Run with default settings (real API)
./launch_debug.sh

# Force using mock data
./launch_debug.sh --mock-data

# Run on a different API port
./launch_debug.sh --api-port 8001

# Start only the frontend (assuming API is running)
./launch_debug.sh --frontend-only

# Start only the backend
./launch_debug.sh --backend-only

# Show help
./launch_debug.sh --help
```

## Debug Panel

Once the dashboard is running, you can use the built-in Debug Panel:

1. Click the "Show Debug Panel" button in the bottom right corner
2. Use the panel to:
   - View environment variables
   - Check WebSocket connection status
   - Toggle between mock and real data
   - Test API endpoints directly

## Browser Developer Tools

Use your browser's developer tools (F12) for additional debugging:

1. Console tab:
   - Look for error messages
   - View console logs for API/WebSocket status

2. Network tab:
   - Filter by XHR to see API requests
   - Filter by WS to see WebSocket connections
   - Check response status and content

## Common Commands

```bash
# Check if API is running
ps aux | grep uvicorn

# Test API health endpoint
curl http://localhost:8000/health

# Test other API endpoints
curl http://localhost:8000/metrics/overview
curl http://localhost:8000/execution/positions

# Test WebSocket connection
npx wscat -c ws://localhost:8000/ws

# Start dashboard with forced mock data
cd new-trading-dashboard && VITE_FORCE_MOCK_DATA=true npm run dev

# Start dashboard with real data connection
cd new-trading-dashboard && VITE_FORCE_MOCK_DATA=false npm run dev

# Check the .env.local file
cat new-trading-dashboard/.env.local
```

## Debugging CORS Issues

If you're seeing CORS errors in the console, update your API server:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## For More Help

See the following documents for detailed information:

- `TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `INTEGRATION.md` - Details about API/frontend integration
- `new-trading-dashboard/README.md` - React dashboard documentation 
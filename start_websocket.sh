#!/bin/bash
set -e

# Configure colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting BenBot WebSocket Server and Frontend${NC}"
echo "========================================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source venv/bin/activate

# Install required Python packages if not already installed
if ! python -c "import flask_socketio" &> /dev/null; then
    echo "Installing required Python packages..."
    pip install flask flask-socketio flask-cors
fi

# Create .env.local for frontend if it doesn't exist
if [ ! -f "new-trading-dashboard/.env.local" ]; then
    echo "Creating .env.local for frontend..."
    cat > new-trading-dashboard/.env.local << EOL
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8001/ws
EOL
fi

# Start WebSocket server in the background
echo -e "${GREEN}Starting WebSocket server on http://localhost:8001${NC}"
python websocket_server.py &
WS_PID=$!

# Wait for WebSocket server to start
echo "Waiting for WebSocket server to start..."
sleep 2

# Change to frontend directory and start dev server
echo -e "${GREEN}Starting frontend dev server...${NC}"
cd new-trading-dashboard
npm run dev &
FRONTEND_PID=$!

# Setup trap to kill both processes on script exit
trap "echo 'Shutting down servers...'; kill $WS_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for user to press Ctrl+C
echo -e "${GREEN}✓ Both servers are running!${NC}"
echo "WebSocket server: http://localhost:8001"
echo "Frontend server: Check the URL above in the vite output"
echo ""
echo "Press Ctrl+C to stop both servers"
wait 
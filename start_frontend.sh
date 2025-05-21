#!/bin/bash

# Create static directory if it doesn't exist
mkdir -p static

# Check if port 5173 is in use
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 5173 is already in use. Attempting to kill the process..."
    kill $(lsof -t -i:5173)
    sleep 2
fi

# Start the server with proper error handling
echo "Starting frontend server on port 5173..."
python3 -m http.server 5173 --directory . --bind 0.0.0.0

# If the server fails to start, show error message
if [ $? -ne 0 ]; then
    echo "Failed to start frontend server. Please check the error message above."
    exit 1
fi 
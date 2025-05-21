#!/bin/bash

# Check if Python virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Python virtual environment is not activated"
    echo "Please activate your virtual environment first"
    exit 1
fi

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import requests, fastapi, uvicorn, websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install "requests" "fastapi" "uvicorn[standard]" "websockets" "python-dotenv"
fi

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if port 8001 is in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 8001 is already in use. Attempting to kill the process..."
    kill $(lsof -t -i:8001)
    sleep 2
fi

# Start the FastAPI server
echo "Starting backend server on port 8001..."
uvicorn trading_bot.api.app:app --host 0.0.0.0 --port 8001 --reload

# If the server fails to start, show error message
if [ $? -ne 0 ]; then
    echo "Failed to start backend server. Please check the error message above."
    exit 1
fi 
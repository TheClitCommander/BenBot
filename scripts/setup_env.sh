#!/bin/bash
set -e

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if the frontend directory exists
if [ -d "new-trading-dashboard" ]; then
    echo "Setting up frontend dependencies..."
    cd new-trading-dashboard
    
    # Install Node.js dependencies
    npm install
    
    # Install specific packages that might be missing
    npm install @tanstack/react-query-devtools @mui/icons-material
    
    cd ..
fi

# Create .env.example file
echo "Creating .env.example file..."
cat > .env.example << EOL
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/trading_bot

# Alpaca API Configuration
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_api_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Tradier API Configuration
TRADIER_API_KEY=your_tradier_api_key
TRADIER_ACCOUNT_ID=your_tradier_account_id
TRADIER_BASE_URL=https://sandbox.tradier.com/v1

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your actual configuration values."
fi

# Create frontend .env.local
if [ -d "new-trading-dashboard" ]; then
    echo "Creating frontend .env.local file..."
    cat > new-trading-dashboard/.env.local << EOL
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
EOL
fi

echo "Environment setup complete!"
echo "Activate the virtual environment with: source venv/bin/activate"
echo "Start the backend with: python demo_backend.py"
echo "Start the frontend with: cd new-trading-dashboard && npm run dev" 
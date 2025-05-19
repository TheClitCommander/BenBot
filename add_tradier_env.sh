#!/bin/bash

# Color codes for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Tradier API Integration${NC}"
echo "==============================================="

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f $ENV_FILE ]; then
    echo -e "${YELLOW}Creating new .env file${NC}"
    touch $ENV_FILE
else
    echo -e "${YELLOW}Updating existing .env file${NC}"
fi

# Ask for Tradier token if not provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Enter your Tradier Bearer Token:${NC}"
    read -s TRADIER_TOKEN
    echo ""
else
    TRADIER_TOKEN="$1"
fi

# Check if the token is already in the file to avoid duplication
if grep -q "TRADIER_TOKEN" $ENV_FILE; then
    # Update existing token
    sed -i.bak "s/TRADIER_TOKEN=.*/TRADIER_TOKEN=$TRADIER_TOKEN/" $ENV_FILE
    echo -e "${GREEN}Updated existing Tradier token${NC}"
else
    # Add new token
    echo "TRADIER_TOKEN=$TRADIER_TOKEN" >> $ENV_FILE
    echo -e "${GREEN}Added Tradier token${NC}"
fi

# Add or update base URL
if grep -q "TRADIER_BASE_URL" $ENV_FILE; then
    sed -i.bak "s#TRADIER_BASE_URL=.*#TRADIER_BASE_URL=https://api.tradier.com/v1#" $ENV_FILE
    echo -e "${GREEN}Updated Tradier base URL${NC}"
else
    echo "TRADIER_BASE_URL=https://api.tradier.com/v1" >> $ENV_FILE
    echo -e "${GREEN}Added Tradier base URL${NC}"
fi

# Create frontend .env.local if it doesn't exist
FE_ENV_FILE="new-trading-dashboard/.env.local"
if [ ! -f $FE_ENV_FILE ]; then
    echo -e "${YELLOW}Creating frontend .env.local file${NC}"
    cat > $FE_ENV_FILE << EOL
# API Configuration
VITE_API_URL=http://localhost:8000

# Mock Data Configuration (set to 'true' to use mock data if API is unavailable)
VITE_USE_MOCK=true

# Broker Selection ('alpaca' or 'tradier')
VITE_BROKER=tradier

# UI Configuration
VITE_APP_TITLE=BensBot - Trading Dashboard
VITE_DEFAULT_THEME=light
EOL
    echo -e "${GREEN}Created frontend configuration file${NC}"
else
    # Update broker in existing file
    if grep -q "VITE_BROKER" $FE_ENV_FILE; then
        sed -i.bak "s/VITE_BROKER=.*/VITE_BROKER=tradier/" $FE_ENV_FILE
        echo -e "${GREEN}Updated broker to Tradier in frontend config${NC}"
    else
        echo "VITE_BROKER=tradier" >> $FE_ENV_FILE
        echo -e "${GREEN}Added broker setting to frontend config${NC}"
    fi
fi

# Clean up backup files
rm -f $ENV_FILE.bak $FE_ENV_FILE.bak 2>/dev/null

echo ""
echo -e "${GREEN}Tradier integration setup complete!${NC}"
echo "-----------------------------------------------"
echo -e "To test the integration, try these commands:"
echo -e "1. ${YELLOW}curl http://localhost:8000/tradier/quote/AAPL${NC}"
echo -e "2. ${YELLOW}curl http://localhost:8000/tradier/chains/AAPL${NC}"
echo ""
echo -e "Frontend will use Tradier APIs when VITE_BROKER=tradier in .env.local"
echo "===============================================" 
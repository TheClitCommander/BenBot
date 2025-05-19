# Tradier API Integration for BensBot

This guide explains how to set up and use the Tradier API integration in the BensBot trading dashboard.

## Setup Instructions

### 1. Prerequisites

- A Tradier account with API access
- Your Tradier Bearer Token
- BensBot trading system up and running

### 2. Configuration

Run the setup script to configure your environment:

```bash
chmod +x add_tradier_env.sh
./add_tradier_env.sh YOUR_TRADIER_TOKEN
```

Or run it without arguments to be prompted for your token:

```bash
./add_tradier_env.sh
```

This will:
- Add the Tradier token and base URL to your backend `.env` file
- Create or update the frontend `.env.local` file to use Tradier as the broker

### 3. Restart Services

Restart your backend and frontend services to apply the changes:

```bash
# Restart backend
cd trading_bot
python -m uvicorn api.app:app --reload

# Restart frontend
cd new-trading-dashboard
npm run dev
```

## Using Tradier in the Dashboard

The integration adds several new features:

### Market Data

- Real-time quotes from Tradier for stocks and ETFs
- Options chains with expiration date selection
- Integration with the existing market data panels

### Trading

- Place orders directly through Tradier
- View account information and positions
- Toggle between Alpaca and Tradier as your broker

### Components

The following components are available for use:

- `TradierQuoteDisplay`: Shows real-time quotes for a symbol
- `TradierOptionsChain`: Displays options chains with expiration selection
- `TradierOrderForm`: Form to submit market orders to Tradier

## Backend API Endpoints

### Quotes

```
GET /tradier/quote/{symbol}
```

Returns the current quote for the specified symbol.

### Options Chains

```
GET /tradier/chains/{symbol}?expiration={expiration}
```

Returns options chains for the symbol, optionally filtered by expiration date.

### Order Submission

```
POST /tradier/order
```

Submits an order to Tradier. Requires the following body:

```json
{
  "account_id": "YOUR_TRADIER_ACCOUNT_ID",
  "symbol": "AAPL",
  "qty": 1,
  "side": "buy"
}
```

## Switching Between Brokers

You can toggle between Alpaca and Tradier by changing the `VITE_BROKER` environment variable in the frontend:

```
# In new-trading-dashboard/.env.local
VITE_BROKER=tradier  # or "alpaca"
```

The system includes a unified broker API that will automatically route requests to the appropriate service based on this setting.

## Troubleshooting

If you encounter issues:

1. Verify your Tradier token is correct and has the necessary permissions
2. Check that the environment variables are set correctly
3. Look for errors in the browser console and server logs
4. Ensure your account has the proper access level for the API features you're using

For more information on the Tradier API, visit [Tradier's API Documentation](https://documentation.tradier.com/). 
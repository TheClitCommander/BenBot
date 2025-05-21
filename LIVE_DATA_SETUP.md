# BensBot: Live Data Integration with Alpaca

This document explains how to set up and use the live market data integration with Alpaca API in BensBot.

## Overview

We've integrated Alpaca Trading API to provide real-time market data and trading capabilities to your BensBot dashboard. This integration includes:

1. A Python service wrapper for Alpaca API
2. FastAPI endpoints exposing Alpaca functionality
3. React hooks for consuming the live data
4. Example components showing how to display the data

## Prerequisites

1. An Alpaca account with API keys
2. Python 3.8+ and Node.js 16+

## Setup Steps

### 1. Configure Alpaca API Keys

Create a `.env` file at the root of your project with your Alpaca API keys:

```
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use paper for testing
```

### 2. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv ~/trading_venv
source ~/trading_venv/bin/activate

# Install required packages
pip install alpaca_trade_api flask fastapi uvicorn
```

### 3. Configure React Dashboard

Create a `.env.local` file in the `new-trading-dashboard` directory:

```
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK=false
```

Alternatively, you can run the provided script:

```bash
./setup_live_dashboard.sh
```

### 4. Start the Backend

Run the backend server with the Alpaca integration:

```bash
./start_live_trading.sh
```

This script will:
- Load your Alpaca API keys from the `.env` file
- Activate the virtual environment
- Install required packages if needed
- Start the FastAPI application

### 5. Start the Frontend

```bash
cd new-trading-dashboard
npm run dev
```

## Using Live Data in React Components

### 1. Fetching Live Prices

```tsx
import { useLivePrice } from '../hooks/useLiveData';

function StockPrice({ symbol }) {
  const { price, loading, error } = useLivePrice(symbol);
  
  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;
  
  return <p>{symbol}: ${price}</p>;
}
```

### 2. Getting Account Information

```tsx
import { useLiveAccount } from '../hooks/useLiveData';

function AccountSummary() {
  const { account, loading, error } = useLiveAccount();
  
  if (loading) return <p>Loading account data...</p>;
  if (error) return <p>Error: {error}</p>;
  
  return (
    <div>
      <p>Cash: ${account.cash}</p>
      <p>Portfolio Value: ${account.portfolio_value}</p>
    </div>
  );
}
```

### 3. Placing Orders

```tsx
import { useOrderSubmission } from '../hooks/useLiveData';

function OrderForm() {
  const { submitOrder, loading, error } = useOrderSubmission();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await submitOrder({
        symbol: 'AAPL',
        side: 'buy',
        qty: 1
      });
      alert('Order placed successfully!');
    } catch (err) {
      console.error(err);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button type="submit" disabled={loading}>
        {loading ? 'Placing Order...' : 'Buy'}
      </button>
      {error && <p>{error}</p>}
    </form>
  );
}
```

## Available API Endpoints

- `GET /live/price/{symbol}` - Get live price for a symbol
- `GET /live/account` - Get account information
- `GET /live/positions` - Get current positions
- `GET /live/orders` - Get open orders
- `POST /live/order` - Place a new order

## Troubleshooting

1. **API Connection Issues**: Ensure your Alpaca API keys are correctly set in the `.env` file.
2. **CORS Errors**: The FastAPI server is configured to accept requests from localhost. If you're running on a different domain, update the CORS settings in `app.py`.
3. **Mock Data Still Showing**: Make sure `VITE_USE_MOCK=false` is set in your `.env.local` file. 
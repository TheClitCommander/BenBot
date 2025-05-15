from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import json
import asyncio
from datetime import datetime, timedelta
import time

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# System status endpoint
@app.get("/system/status")
async def system_status():
    return {
        "status": "online",
        "connection": "demo",
        "cpu_usage": random.randint(10, 40),
        "memory_usage": random.randint(20, 60),
        "uptime": f"{random.randint(1, 10)}d {random.randint(1, 23)}h",
        "last_trade_time": f"{random.randint(1, 59)}m ago"
    }

# Metrics overview
@app.get("/metrics/overview")
async def metrics_overview():
    return {
        "portfolio_value": round(10000 + random.uniform(-500, 500), 2),
        "portfolio_change_percent": round(random.uniform(-3, 5), 2),
        "portfolio_change_value": round(random.uniform(-300, 500), 2),
        "position_count": random.randint(1, 5),
        "position_summary": ["BTC (long)", "ETH (short)"],
        "strategy_count": random.randint(2, 5),
        "strategy_status": "All strategies running normally",
        "todays_pnl": round(random.uniform(-200, 300), 2),
        "pnl_percent": round(random.uniform(-2, 3), 2)
    }

# Strategies list
@app.get("/orchestration/strategies")
async def get_strategies():
    strategies = [
        {
            "id": "strat-btc-trend-1",
            "name": "BTC Trend Following",
            "market": "BTCUSDT",
            "status": "active",
            "pnl_today": round(random.uniform(-2, 4), 2),
            "pnl_total": round(random.uniform(5, 20), 2)
        },
        {
            "id": "strat-eth-reversion-1",
            "name": "ETH Mean Reversion",
            "market": "ETHUSDT",
            "status": "active",
            "pnl_today": round(random.uniform(-2, 2), 2),
            "pnl_total": round(random.uniform(3, 10), 2)
        },
        {
            "id": "strat-alt-momentum-1",
            "name": "Altcoin Momentum",
            "market": "Multi",
            "status": "paused",
            "pnl_today": 0,
            "pnl_total": round(random.uniform(4, 12), 2)
        }
    ]
    return {"strategies": strategies}

# Positions list
@app.get("/execution/positions")
async def get_positions():
    positions = [
        {
            "id": "pos-1",
            "symbol": "BTCUSDT",
            "side": "long",
            "size": 0.1,
            "entry_price": 44350.50,
            "current_price": round(44350.50 * (1 + random.uniform(-0.02, 0.05)), 2),
            "pnl_percent": round(random.uniform(-2, 5), 2),
            "pnl_value": round(random.uniform(-100, 200), 2)
        },
        {
            "id": "pos-2",
            "symbol": "ETHUSDT",
            "side": "short",
            "size": 1.25,
            "entry_price": 2570.00,
            "current_price": round(2570.00 * (1 + random.uniform(-0.05, 0.02)), 2),
            "pnl_percent": round(random.uniform(-2, 5), 2),
            "pnl_value": round(random.uniform(-100, 200), 2)
        }
    ]
    return {"positions": positions}

# Recent trades
@app.get("/execution/trades")
async def get_trades():
    trades = [
        {
            "id": "trade-1",
            "time": (datetime.now() - timedelta(minutes=random.randint(10, 500))).strftime("%b %d, %I:%M %p"),
            "symbol": "BTCUSDT",
            "side": "buy",
            "size": 0.1,
            "price": 44350.50,
            "total": 4435.05,
            "strategy": "BTC Trend Following"
        },
        {
            "id": "trade-2",
            "time": (datetime.now() - timedelta(minutes=random.randint(10, 500))).strftime("%b %d, %I:%M %p"),
            "symbol": "ETHUSDT",
            "side": "sell",
            "size": 1.25,
            "price": 2570.00,
            "total": 3212.50,
            "strategy": "ETH Mean Reversion"
        },
        {
            "id": "trade-3",
            "time": (datetime.now() - timedelta(minutes=random.randint(10, 500))).strftime("%b %d, %I:%M %p"),
            "symbol": "SOLUSDT",
            "side": "buy",
            "size": 10,
            "price": 121.50,
            "total": 1215.00,
            "strategy": "Altcoin Momentum"
        }
    ]
    return {"trades": trades}

# Market data
@app.get("/markets/data")
async def get_market_data():
    markets = [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "price": round(45000 + random.uniform(-1000, 1000), 2),
            "change_24h": round(random.uniform(-3, 5), 2),
            "volume": f"${random.randint(20, 40)}.{random.randint(1, 9)}B"
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "price": round(2500 + random.uniform(-100, 100), 2),
            "change_24h": round(random.uniform(-3, 5), 2),
            "volume": f"${random.randint(10, 25)}.{random.randint(1, 9)}B"
        },
        {
            "symbol": "SOL",
            "name": "Solana",
            "price": round(120 + random.uniform(-10, 10), 2),
            "change_24h": round(random.uniform(-5, 8), 2),
            "volume": f"${random.randint(2, 8)}.{random.randint(1, 9)}B"
        },
        {
            "symbol": "BNB",
            "name": "BNB",
            "price": round(600 + random.uniform(-20, 20), 2),
            "change_24h": round(random.uniform(-2, 3), 2),
            "volume": f"${random.randint(1, 4)}.{random.randint(1, 9)}B"
        }
    ]
    return {"markets": markets}

# Risk metrics
@app.get("/metrics/risk")
async def get_risk_metrics():
    return {
        "sharpe_ratio": round(random.uniform(1.5, 3.0), 2),
        "max_drawdown": round(random.uniform(-15, -5), 2),
        "win_rate": round(random.uniform(55, 75), 2),
        "profit_loss_ratio": round(random.uniform(1.5, 2.5), 2),
        "equity_data": [10000 + i * random.uniform(-50, 100) for i in range(30)],
        "returns_data": [round(random.uniform(-1.5, 2.0), 2) for _ in range(14)]
    }

# Settings
@app.get("/system/settings")
async def get_settings():
    return {
        "trading_mode": "DEMO",
        "quote_currency": "USDT",
        "max_positions": 5,
        "auto_rebalance": True,
        "max_position_size": "15% of Portfolio",
        "stop_loss_type": "Trailing (5%)",
        "take_profit": "Variable (Strategy-based)",
        "auto_evolution": True,
        "evolution_frequency": "Weekly",
        "sampling_method": "Weighted Historical",
        "optimization_target": "Sharpe Ratio"
    }

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Send market updates every 2 seconds
            mock_data = {
                "type": "market_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "markets": [
                        {
                            "symbol": "BTC/USD",
                            "price": round(45000 + random.uniform(-100, 100), 2),
                            "change": round(random.uniform(-0.5, 0.5), 3)
                        },
                        {
                            "symbol": "ETH/USD",
                            "price": round(2500 + random.uniform(-20, 20), 2),
                            "change": round(random.uniform(-0.3, 0.3), 3)
                        }
                    ]
                }
            }
            await websocket.send_text(json.dumps(mock_data))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 
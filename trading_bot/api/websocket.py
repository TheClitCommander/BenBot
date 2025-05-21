from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import psutil
from trading_bot.core.portfolio import Portfolio
from trading_bot.core.market_data import MarketData
from trading_bot.core.trading_engine import TradingEngine

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.portfolio = Portfolio()
        self.market_data = MarketData()
        self.trading_engine = TradingEngine()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial data
        await self.send_initial_data(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_initial_data(self, websocket: WebSocket):
        # Send system status
        await self.send_system_status(websocket)
        # Send portfolio data
        await self.send_portfolio_update(websocket)
        # Send trade history
        await self.send_trade_history(websocket)
        # Send portfolio allocation
        await self.send_portfolio_allocation(websocket)
        # Send risk metrics
        await self.send_risk_metrics(websocket)

    async def send_system_status(self, websocket: WebSocket):
        status = {
            "type": "system_status",
            "data": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "api_status": self.trading_engine.is_api_connected()
            }
        }
        await websocket.send_json(status)

    async def send_portfolio_update(self, websocket: WebSocket):
        portfolio_data = {
            "type": "portfolio_update",
            "data": {
                "total_value": self.portfolio.get_total_value(),
                "daily_pnl": self.portfolio.get_daily_pnl(),
                "win_rate": self.portfolio.get_win_rate(),
                "active_trades": len(self.portfolio.get_active_trades()),
                "cash_balance": self.portfolio.get_cash_balance(),
                "invested_amount": self.portfolio.get_invested_amount(),
                "unrealized_pnl": self.portfolio.get_unrealized_pnl()
            }
        }
        await websocket.send_json(portfolio_data)

    async def send_portfolio_allocation(self, websocket: WebSocket):
        allocation = self.portfolio.get_allocation()
        allocation_data = {
            "type": "portfolio_allocation",
            "data": {
                "allocations": [
                    {
                        "symbol": symbol,
                        "percentage": percentage,
                        "value": value
                    }
                    for symbol, (percentage, value) in allocation.items()
                ]
            }
        }
        await websocket.send_json(allocation_data)

    async def send_risk_metrics(self, websocket: WebSocket):
        risk_data = {
            "type": "risk_metrics",
            "data": {
                "sharpe_ratio": self.portfolio.get_sharpe_ratio(),
                "max_drawdown": self.portfolio.get_max_drawdown(),
                "volatility": self.portfolio.get_volatility(),
                "beta": self.portfolio.get_beta(),
                "correlation_matrix": self.portfolio.get_correlation_matrix()
            }
        }
        await websocket.send_json(risk_data)

    async def send_trade_history(self, websocket: WebSocket):
        trades = self.portfolio.get_recent_trades()
        trade_data = {
            "type": "trade_update",
            "data": {
                "trades": [
                    {
                        "symbol": trade.symbol,
                        "side": trade.side,
                        "quantity": trade.quantity,
                        "price": trade.price,
                        "total": trade.total,
                        "timestamp": trade.timestamp.isoformat()
                    }
                    for trade in trades
                ]
            }
        }
        await websocket.send_json(trade_data)

    async def send_price_update(self, websocket: WebSocket):
        price_data = self.market_data.get_latest_prices()
        update = {
            "type": "price_update",
            "data": {
                "timestamps": [p.timestamp.isoformat() for p in price_data],
                "prices": [p.price for p in price_data],
                "volumes": [p.volume for p in price_data]
            }
        }
        await websocket.send_json(update)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)

    async def start_data_stream(self):
        while True:
            for connection in self.active_connections:
                try:
                    await self.send_system_status(connection)
                    await self.send_portfolio_update(connection)
                    await self.send_portfolio_allocation(connection)
                    await self.send_risk_metrics(connection)
                    await self.send_price_update(connection)
                except Exception as e:
                    print(f"Error sending data: {e}")
                    self.disconnect(connection)
            await asyncio.sleep(1)  # Update every second

# Create a global instance
websocket_manager = WebSocketManager() 
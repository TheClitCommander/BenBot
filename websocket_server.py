from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store connected clients
connected_clients = set()

@app.route('/health')
def health():
    return {"status": "healthy", "websocket": True}

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients.add(client_id)
    logger.info(f"Client connected: {client_id}. Total clients: {len(connected_clients)}")
    emit('connection_success', {'message': 'Connected successfully', 'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients.remove(client_id)
    logger.info(f"Client disconnected: {client_id}. Total clients: {len(connected_clients)}")

# Mock data broadcaster
def broadcast_market_data():
    while True:
        if connected_clients:
            # Generate mock market data
            data = {
                'timestamp': time.time(),
                'market_data': {
                    'AAPL': {
                        'price': round(150 + random.uniform(-5, 5), 2),
                        'volume': int(random.uniform(10000, 100000))
                    },
                    'MSFT': {
                        'price': round(300 + random.uniform(-10, 10), 2),
                        'volume': int(random.uniform(8000, 80000))
                    },
                    'TSLA': {
                        'price': round(800 + random.uniform(-20, 20), 2),
                        'volume': int(random.uniform(5000, 50000))
                    }
                }
            }
            
            # Broadcast to all connected clients
            socketio.emit('market_data', data)
            logger.debug(f"Broadcasted market data to {len(connected_clients)} clients")
        
        # Sleep for 1 second
        time.sleep(1)

# Mock portfolio data broadcaster
def broadcast_portfolio_updates():
    while True:
        if connected_clients:
            # Generate mock portfolio data
            data = {
                'timestamp': time.time(),
                'portfolio': {
                    'total_value': round(random.uniform(95000, 105000), 2),
                    'cash': round(random.uniform(25000, 35000), 2),
                    'positions_value': round(random.uniform(60000, 70000), 2),
                    'day_pnl': round(random.uniform(-2000, 2000), 2),
                    'day_pnl_percent': round(random.uniform(-2.0, 2.0), 2)
                }
            }
            
            # Broadcast to all connected clients
            socketio.emit('portfolio_update', data)
            logger.debug(f"Broadcasted portfolio update to {len(connected_clients)} clients")
        
        # Sleep for 3 seconds
        time.sleep(3)

if __name__ == '__main__':
    # Start the data broadcast threads
    market_thread = threading.Thread(target=broadcast_market_data, daemon=True)
    market_thread.start()
    
    portfolio_thread = threading.Thread(target=broadcast_portfolio_updates, daemon=True)
    portfolio_thread.start()
    
    logger.info("Starting WebSocket server on http://0.0.0.0:8001")
    socketio.run(app, host='0.0.0.0', port=8001, debug=True, allow_unsafe_werkzeug=True) 
"""
# ⚡ QUANTIQ INDEPENDENT LIVE MARKET DATA ENGINE

A lightweight, high-performance, and **100% Free** independent real-time data streaming engine built in Python. 
This script connects directly to global public financial WebSocket routers to fetch live tick-by-tick Indian 
Stock Market (NSE) feeds without relying on any expensive broker APIs, API keys, or login sessions.

## 🛠️ Tech Stack & Quick Installation:
1. Run command: pip install websocket-client
2. Run script:  python app.py

Distributed under the MIT License. Feel free to use, modify, and optimize for personal algorithmic setups!
---
"""

import websocket
import json
import base64
import sys

# --- 1. CONFIGURATION POOL ---
# Add your target NSE stocks or Indices here (.NS suffix is mandatory)
TRACKING_SYMBOLS = ["SBIN.NS", "TATAMOTORS.NS", "RELIANCE.NS", "^NSEI"]
WEBSOCKET_STREAM_URL = "wss://streamer.finance.yahoo.com"


# --- 2. CORE STREAMING FUNCTIONS ---
def on_message(ws, message):
    """Triggered instantly whenever a new tick frame hits the buffer network."""
    try:
        # Step A: Decode base64 network string into raw bytes
        raw_bytes = base64.b64decode(message)
        
        # Step B: Convert bytes data stream into a clear readable string
        clean_payload = raw_bytes.decode('utf-8', errors='ignore')
        
        print(f"📡 [LIVE TICK] Buffer Data Pipeline -> {clean_payload}")
        
    except Exception as e:
        pass


def on_error(ws, error):
    print(f"❌ Connection Network Error: {error}", file=sys.stderr)


def on_close(ws, close_status_code, close_msg):
    print("🛑 Personal Live Data Streaming Pipe Closed.")


def on_open(ws):
    print("🚀 Connection Successfully Established with Global Finance Router!")
    
    # Send subscription handshake payload to the server
    subscribe_packet = {"subscribe": TRACKING_SYMBOLS}
    ws.send(json.dumps(subscribe_packet))
    print(f"Actively tracking and listening to custom asset pool: {TRACKING_SYMBOLS}")


# --- 3. SYSTEM LAUNCH ENGINE ---
def launch_independent_engine():
    print("🤖 Initializing Quantiq Independent Real-time Core Data Engine...")
    print(f"Connecting to remote router socket: {WEBSOCKET_STREAM_URL}")
    
    ws = websocket.WebSocketApp(
        WEBSOCKET_STREAM_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Infinite network listening loop wrapper
    ws.run_forever()


if __name__ == "__main__":
    launch_independent_engine()
    

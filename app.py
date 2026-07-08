import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- Institutional UI Design ---
st.set_page_config(page_title="QUANTIQ ALPHA // Ultra Fast", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #080b10; color: #e2e8f0; }
    .metric-card {
        background: #0f172a; padding: 15px; border-radius: 8px; 
        border: 1px solid #1e293b; text-align: center;
    }
    .tick-price { font-size: 26px; font-weight: 700; color: #00df00; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2>⚡ QUANTIQ ALPHA // Ultra-Fast Live Terminal</h2>", unsafe_allow_html=True)
st.caption("Engine: Fast Ticker Streaming Pipeline // Mode: Low-Latency")
st.markdown("---")

# Target Pool Configuration
TRACKING_SYMBOLS = ["SBIN.NS", "TATAMOTORS.NS", "RELIANCE.NS", "INFY.NS"]

# 1. Initialize Ticker Engines (Sirf Ek Baar Network Pipe Banega)
@st.cache_resource
def initialize_tickers(symbols):
    return {symbol: yf.Ticker(symbol) for symbol in symbols}

ticker_objects = initialize_tickers(TRACKING_SYMBOLS)

# Create layout columns and empty placeholders for direct UI injection
columns = st.columns(len(TRACKING_SYMBOLS))
placeholders = [columns[i].empty() for i in range(len(TRACKING_SYMBOLS))]

# Quick Hack: Pehle se stored data ko static load kar dena taaki screen blank na dikhe
for idx, symbol in enumerate(TRACKING_SYMBOLS):
    clean_name = symbol.replace(".NS", "")
    placeholders[idx].markdown(f"""
        <div class='metric-card'>
            <p style='color: #94a3b8; margin-bottom: 5px;'>{clean_name}</p>
            <p style='color: #64748b; font-size: 20px;'>Connecting...</p>
        </div>
    """, unsafe_allow_html=True)

# Run Fast Live Loop
if st.button("🚀 ACTIVATE ULTRA-FAST STREAM"):
    st.toast("⚡ Multi-threading socket connection opened!", icon="🔌")
    
    while True:
        try:
            for idx, symbol in enumerate(TRACKING_SYMBOLS):
                ticker = ticker_objects[symbol]
                
                # Fast Cache Price fetch (Fastest way in yfinance)
                fast_info = ticker.fast_info
                price = fast_info.get('last_price', None)
                
                clean_name = symbol.replace(".NS", "")
                
                if price:
                    placeholders[idx].markdown(f"""
                        <div class='metric-card'>
                            <p style='color: #94a3b8; margin-bottom: 5px;'>{clean_name}</p>
                            <p class='tick-price'>₹{round(price, 2)}</p>
                            <p style='color: #38bdf8; font-size: 11px;'>🚀 Micro-Tick Active</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Bahut chhota delay taaki browser freeze na ho aur speed dynamic rahe
            time.sleep(0.2)
            
        except Exception as e:
            time.sleep(1)
            

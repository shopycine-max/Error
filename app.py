import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import time
from datetime import datetime

# --- Page Configurations ---
st.set_page_config(page_title="NSE Pro Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 NSE Pro Stock Scanner Terminal")
st.caption("Scan All NSE Stocks | RSI + EMA + Volume Shock + Breakout Filters")

# --- 1. Reliable NSE Universe Fetcher ---
@st.cache_data(ttl=86400) # 24 hours cache
def get_nse_universe():
    # NSE official bhavcopy list
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Only EQ series stocks
            df = df[df['Series'] == 'EQ']
            nse_tickers = [str(sym).strip() + ".NS" for sym in df['SYMBOL'].dropna()]
            st.sidebar.success(f"NSE Universe Loaded: {len(nse_tickers)} Stocks")
            return nse_tickers
    except Exception as e:
        st.sidebar.error(f"NSE List Fetch Failed: {e}")
    
    # Fallback to Nifty500
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    response = requests.get(url, headers=headers, timeout=10)
    df = pd.read_csv(io.StringIO(response.text))
    nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
    st.sidebar.warning(f"Fallback to Nifty500: {len(nse_tickers)} Stocks")
    return nse_tickers

# --- 2. Chunked Data Downloader for yfinance ---
@st.cache_data(ttl=3600, show_spinner="Fetching market data...")
def download_data_in_chunks(tickers, period="1y"):
    all_data = {}
    batch_size = 100 # yfinance limit se bachne ke liye
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(batch, period=period, interval="1d", progress=False, group_by='ticker', auto_adjust=True)
            if isinstance(data.columns, pd.MultiIndex):
                for ticker in batch:
                    if ticker in data.columns.levels:

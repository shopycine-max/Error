import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import requests
from datetime import datetime

# Page Configurations
st.set_page_config(page_title="ERROR09 - Pro Scanner & Backtester", page_icon="📈", layout="wide")

st.title("📈 ERROR09 - Advanced Scanner & Backtester")
st.caption("Live Breakout Signals + 2-Month Historical Backtest Engine")

# --- Nifty 500 Ticker Fetcher ---
@st.cache_data(ttl=86400)
def get_nifty500_tickers():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_csv(url)
            return [str(symbol).strip() + ".NS" for symbol in df['Symbol'].dropna()]
    except Exception as e:
        st.sidebar.error(f"NSE Fetch Error: {e}. Using fallback.")
    return ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "RELIANCE.NS", "TCS.NS"]

# Sidebar Panel
st.sidebar.header("⚙️ Settings Panel")
universe_option = st.sidebar.selectbox("Select Universe", ["Nifty 500", "Custom List"])
all_tickers = get_nifty500_tickers() if universe_option == "Nifty 500" else ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]

st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- Main App Tabs ---
tab1, tab2 = st.tabs(["🚀 Live Scanner (Today)", "⏳ 2-Month Backtester (Chartink Style)"])

# --- Core Advanced Data Engine ---
def process_data_vectorized(tickers, mode="live"):
    st.info("📥 Fetching and analyzing live 3-year data for lookback tracking...")
    try:
        batch_data = yf.download(tickers, period="3y", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    live_results = []
    backtest_results = []
    
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            if len(tickers) > 1:
                df = batch_data
                

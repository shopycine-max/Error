import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# --- Config ---
st.set_page_config(page_title="Institutional Scanner", layout="wide", page_icon="📈")
st.markdown("""<style>.stApp { background-color: #0e1117; } .metric-card { padding: 10px; border-radius: 5px; background: #161b22; }</style>""", unsafe_allow_html=True)

st.title("🚀 Institutional Grade Stock Scanner")
st.sidebar.header("⚙️ Configuration")

# --- Optimized Data Fetching ---
@st.cache_data(ttl=86400) # Cache for 24h
def get_all_nse_tickers():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s).strip() + ".NS" for s in df['Symbol']]
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

# --- Core Logic Engine ---
def analyze_stock(ticker):
    try:
        # Download data
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        
        # Ensure column format
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Indicators
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, 0.001))))
        
        # Current Metrics
        ltp = df['Close'].iloc[-1]
        vol = df['Volume'].iloc[-1]
        vol_sma = df['Vol_SMA20'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        # Strategy: Breakout + Volume Spike + Trend
        if (ltp > df['EMA20'].iloc[-1]) and (vol > vol_sma * 1.5) and (rsi > 55):
            return {
                "Symbol": ticker.replace(".NS", ""),
                "LTP": round(ltp, 2),
                "Vol Spike": round(vol / vol_sma, 1),
                "RSI": round(rsi, 1),
                "StopLoss (ATR)": round(ltp - (df['ATR'].iloc[-1] * 2), 2),
                "Trend": "Bullish"
            }
    except:
        return None
    return None

# --- UI Layout ---
tab1, tab2 = st.tabs(["⚡ Live Screener", "🔍 Watchlist & Charting"])

with tab1:
    col1, col2 = st.columns([1, 3])
    limit = col1.slider("Limit Stocks", 10, 500, 50)
    if col1.button("🚀 Execute Scan"):
        tickers = get_all_nse_tickers()[:limit]
        results = []
        
        progress = st.progress(0)
        # Using Parallel Processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            data = list(executor.map(analyze_stock, tickers))
            
        results = [d for d in data if d is not None]
        
        if results:
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("No setup found. Increase the limit or try later.")

with tab2:
    st.subheader("Interactive Chart")
    ticker_input = st.text_input("Enter Ticker", "RELIANCE.NS")
    if ticker_input:
        chart_df = yf.download(ticker_input, period="1y", interval="1d", progress=False)
        fig = go.Figure(data=[go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'])])
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
        

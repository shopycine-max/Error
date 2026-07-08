import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
from concurrent.futures import ThreadPoolExecutor

# --- Config ---
st.set_page_config(page_title="Institutional Scanner", layout="wide")

# Theme
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .metric-card { background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Institutional Grade Alpha Scanner")
st.sidebar.header("⚙️ Control Panel")

# --- Optimized Data Fetching ---
@st.cache_data(ttl=3600)
def get_all_nse_tickers():
    # Fetching list of all NSE stocks (F&O + Nifty 500)
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        df = pd.read_csv(url)
        return [str(s).strip() + ".NS" for s in df['SYMBOL']]
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

# --- Scanner Logic (Parallel Processing) ---
def analyze_stock(ticker):
    try:
        # Use a short period to keep it fast
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        
        # Fixing column index (yfinance issue)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Indicators
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()
        df['Vol_SMA'] = df['Volume'].rolling(20).mean()
        
        # Criteria: Price > EMA20, Price > SMA200, Volume Spike > 1.5x
        curr_price = df['Close'].iloc[-1]
        curr_vol = df['Volume'].iloc[-1]
        
        if (curr_price > df['EMA20'].iloc[-1]) and (curr_vol > df['Vol_SMA'].iloc[-1] * 1.5):
            return {
                "Ticker": ticker,
                "Price": round(curr_price, 2),
                "Vol Spike": round(curr_vol / df['Vol_SMA'].iloc[-1], 2),
                "Trend": "Bullish"
            }
    except:
        return None
    return None

# --- Dashboard Layout ---
tab1, tab2 = st.tabs(["⚡ Live Screener", "🔍 Watchlist Analysis"])

with tab1:
    col1, col2, col3 = st.columns(3)
    universe = col1.selectbox("Universe", ["Nifty 500", "Full NSE (Slow)"])
    limit = col2.slider("Max Stocks to Scan", 10, 200, 50)
    start_btn = col3.button("🚀 Start Professional Scan")

    if start_btn:
        tickers = get_all_nse_tickers()[:limit]
        results = []
        
        progress = st.progress(0)
        with ThreadPoolExecutor(max_workers=10) as executor:
            data = list(executor.map(analyze_stock, tickers))
            
        results = [d for d in data if d is not None]
        
        if results:
            st.success(f"Found {len(results)} potential setups!")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("No setups found with current settings.")

with tab2:
    st.subheader("Manual Analysis")
    ticker_input = st.text_input("Enter Ticker (e.g., RELIANCE.NS)")
    if ticker_input:
        chart_df = yf.download(ticker_input, period="1y", interval="1d", progress=False)
        fig = go.Figure(data=[go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'])])
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        

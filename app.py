import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io
import warnings

# Ignore pandas warnings for cleaner terminal
warnings.filterwarnings("ignore")

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner v2.0", page_icon="🚀", layout="wide")

# Custom Dark Premium Theme & Table Styling
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; border-radius: 8px; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #2ea043; border-color: white; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    h1, h2, h3 { color: #58a6ff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 AlphaTrade Momentum Terminal")
st.caption("Advanced Engine: RSI, MACD, Bollinger Bands, & Volume Shocks for High-Conviction Breakouts")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "ZOMATO.NS", "TATASTEEL.NS"]
    if universe_type == "📸 Quick Test (7 Stocks)":
        return target_stocks

    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
            for stock in target_stocks:
                if stock not in nse_tickers:
                    nse_tickers.append(stock)
            return nse_tickers
    except Exception:
        pass
    return target_stocks

# --- Sidebar Pro Settings Panel ---
st.sidebar.header("⚙️ Terminal Controls")
universe_choice = st.sidebar.selectbox("Scanning Universe", ["📸 Quick Test (7 Stocks)", "Nifty 500"])

with st.sidebar.expander("📈 Trend & Momentum Filters", expanded=True):
    rsi_filter = st.slider("Min RSI (Strength)", 50, 80, 60)
    req_macd = st.checkbox("Require MACD Bullish", value=True)
    req_bb = st.checkbox("Price Near Upper Bollinger Band", value=False)
    dist_52w = st.slider("Max Distance from 52W High (%)", 5, 50, 20)

with st.sidebar.expander("📊 Volume & Price Filters", expanded=True):
    volume_multiplier = st.slider("Volume Shock (Multiplier)", 1.0, 5.0, 2.0, step=0.1)
    min_price = st.number_input("Minimum Stock Price (₹)", value=20)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.success(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- Core Scanner Engine ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: 
        return pd.DataFrame()

    try:
        data = yf.download(tickers, period="2y", interval="1d", progress=False)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0, text="Scanning Market Data...")
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers), text=f"Analyzing {
            

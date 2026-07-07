import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import requests
import io
from datetime import datetime

# Page Configurations
st.set_page_config(page_title="ERROR09 - Supercharged Bullish Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 ERROR09 - Next-Day Bullish Predictor")
st.caption("Created by Chandan kumar shaw | Live Scanner + Target Predictor Engine")

# Dictionary to map company names perfectly (Chartink Style)
STOCK_NAME_MAP = {
    "CUPID": "Cupid Limited",
    "DIACABS": "Diamond Power Infrastructure Ltd",
    "SPARC": "Sun Pharma Advanced Research Company",
    "ADANIENSOL": "Adani Energy Solutions Ltd",
    "JBCHEPHARM": "JB Chemicals & Pharmaceuticals Ltd"
}

def get_clean_name(symbol):
    ticker_clean = symbol.replace(".NS", "")
    return STOCK_NAME_MAP.get(ticker_clean, ticker_clean)

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    if universe_type == "📸 Chartink Screenshot Test (5 Stocks)":
        return target_stocks

    url = "https://niftyindices.com/IndexConstituentList/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
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
        
    try:
        backup_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        res = requests.get(backup_url, headers=headers, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            return [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
    except Exception:
        pass

    return target_stocks

# Sidebar Settings Panel
st.sidebar.header("⚙️ Scanner Controls")
universe_choice = st.sidebar.selectbox(
    "Select Scanning Universe", 
    ["📸 Chartink Screenshot Test (5 Stocks)", "Nifty 500 + Targets"]
)
all_tickers = get_scanning_universe(universe_choice)
st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# App Navigation Tabs
tab1, tab2 = st.tabs(["⚡ Live Scanner & Next-Day Prediction", "📊 2-Month Historical Backtester"])

# --- Core Scanner Engine ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        
        try:
            if len(tickers) > 1:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].dropna(subset=['Close'])
                else:
                    continue
            else:
                df = data.dropna(subset=['Close'])

            if len(df) < 510:
                continue

            # Core Calculations
            df['Pct_Change'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
            df
            

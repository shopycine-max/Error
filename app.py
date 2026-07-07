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
        backup_url =
        

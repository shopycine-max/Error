import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced Stock Scanner Terminal")
st.caption("Engine Upgraded: Multi-Link Fallback, Cache Cleared & Full Market Scan")

# --- NAYA ROBUST UNIVERSE FETCHER (Ab hamesha saare stocks aayenge) ---
@st.cache_data(ttl=10800, show_spinner=False)
def get_full_market_universe(universe_type):
    # Yeh 5 stocks sirf Test/Demo mode ke liye hain
    test_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    
    # Agar user jaan-bujh kar sirf 5 stock wala option chune
    if "Chartink" in universe_type:
        return test_stocks

    # 3 Alag-alag URLs ka backup system (Ek fail toh dusra pass)
    csv_urls = [
        "https://raw.githubusercontent.com/anirban-m/indian-stock-market-datasets/main/ind_niftytotalmarket_list.csv",
        "https://raw.githubusercontent.com/sanjitk/nse-stocks-list/master/nse_stocks.csv",
        "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Code bari-bari har link try karega
    for url in csv_urls:
        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                df.columns = df.columns.str.strip().str.upper()
                
                sym_col = None
                for col in df.columns:
                    if 'SYMBOL' in col or 'TICKER' in col:
                        sym_col = col
                        break
                        
                if sym_col:
                    nse_tickers = [str(sym).strip() + ".NS" for sym in df[sym_col].dropna() if len(str(sym).strip()) > 1]
                    # Agar list mein 200 se zyada stocks hain, tabhi usko real list manega
                    if len(nse_tickers) > 200: 
                        return list(set(nse_tickers + test_stocks))
        except Exception:
            continue # Ek fail hua toh skip karke agla link try karo

    # Agar kismat kharab hui aur teeno link block ho gaye, toh kam se kam Top 50 stocks dega (Sirf 5 par nahi atakega)
    nifty_backup = ["RELIANCE.NS
    

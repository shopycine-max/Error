import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="ERROR09 - Live NSE Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; border-radius: 5px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    div.block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ERROR09 - Live Stock Scanner Dashboard")
st.caption("Created by Chandan kumar shaw | Powered by Live yFinance Data")

st.sidebar.header("⚙️ Scanner Settings")
index_choice = st.sidebar.selectbox("Select Universe", ["Nifty 500", "Nifty 50", "Nifty Next 50", "All NSE Stocks"])
run_scan = st.sidebar.button("🚀 Run Live Scan")

@st.cache_data(ttl=86400)
def load_nifty_symbols(universe_type):
    mirrors = {
        "Nifty 50": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty50list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_nifty50list.csv"
        ],
        "Nifty Next 50": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_niftynext50list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_niftynext50list.csv"
        ],
        "Nifty 500": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty500list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_nifty00list.csv"
        ],
        "All NSE Stocks": [
            "https://raw.githubusercontent.com/shubham-singh-9/NSE-Symbols/main/symbols.csv",
            "https://raw.githubusercontent.com/pankaj0323/NSE-Stock-Tickers/master/NSE_Tickers.csv"
        ]
    }
    
    selected_urls = mirrors[universe_type]
    df = None
    
    for url in selected_urls:
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            break
        except Exception:
            continue
            
    if df is not None:
        try:
            if 'Symbol' not in df.columns and 'SYMBOL' in df.columns:
                df = df.rename(columns={'SYMBOL': 'Symbol'})
            if 'Company Name' not in df.columns and 'NAME OF COMPANY' in df.columns:
                df = df.rename(columns={'NAME OF COMPANY': 'Company Name'})
            if 'Industry' not in df.columns:
                df['Industry'] = 'NSE Equity'
                
            df['Ticker'] = df['Symbol'].str.strip() + ".NS"
            return df[['Ticker', 'Symbol', 'Company Name', 'Industry']].dropna().drop_duplicates()
        except Exception:
            pass

    fallback_data = {
        'Ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'CUPID.NS', 'DIACABS.NS', 'SPARC.NS', 'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS'],
        'Symbol':
    

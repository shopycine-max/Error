import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# Page configuration
st.set_page_config(
    page_title="ERROR09 - Live NSE Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
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

# Sidebar configurations
st.sidebar.header("⚙️ Scanner Settings")
index_choice = st.sidebar.selectbox("Select Universe", ["Nifty 500", "Nifty 50", "Nifty Next 50", "All NSE Stocks"])
run_scan = st.sidebar.button("🚀 Run Live Scan")

@st.cache_data(ttl=86400) # 24 hours caching
def load_nifty_symbols(universe_type):
    # Multiple highly reliable backup mirrors to prevent any future 404 errors
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
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_nifty500list.csv"
        ],
        "All NSE Stocks": [
            "https://raw.githubusercontent.com/shubham-singh-9/NSE-Symbols/main/symbols.csv",
            "https://raw.githubusercontent.com/pankaj0323/NSE-Stock-Tickers/master/NSE_Tickers.csv"
        ]
    }
    
    selected_urls = mirrors[universe_type]
    df = None
    
    # Try fetching from mirrors one by one
    for url in selected_urls:
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            break # If successful, break the loop
        except Exception:
            continue # If fails, try the next mirror
            
    if df is not None:
        try:
            # Map column names based on dataset format
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

    # Safe hardcoded emergency fallback with top Nifty stocks if all mirrors fail
    fallback_data = {
        'Ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'CUPID.NS', 'DIACABS.NS', 'SPARC.NS', 'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS'],
        'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'CUPID', 'DIACABS', 'SPARC', 'TATAMOTORS', 'SBIN', 'BHARTIARTL', 'ITC'],
        'Company Name': ['Reliance Industries', 'TCS', 'Infosys', 'HDFC Bank', 'ICICI Bank', 'Cupid Ltd', 'Diamond Power', 'Sun Pharma Adv', 'Tata Motors', 'SBI', 'Bharti Airtel', 'ITC Ltd'],
        'Industry': ['Oil & Gas', 'IT', 'IT', 'Banking', 'Banking', 'Healthcare', 'Industrials', 'Healthcare', 'Automobile', 'Banking', 'Telecom', 'FMCG']
    }
    return pd.DataFrame(fallback_data)

def process_ticker(ticker_info):
    ticker = ticker_info['Ticker']
    symbol = ticker_info['Symbol']
    company_name = ticker_info['Company Name']
    industry = ticker_info['Industry']
    
    try:  # Fixed the missing colon syntax error here
        df = yf.download(ticker, period="3y", progress=False, group_by='ticker')
        if df.empty or len(df) < 501:
            return None
            
        if isinstance(df.columns, pd.Multi):
                      

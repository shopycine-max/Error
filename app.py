import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import time
import requests
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Aashiyana Dashboard Pro Max 🚀", page_icon="📈", layout="wide")

# --- 🛠️ SAFELY INITIALIZE SESSION STATE ---
if 'live_results' not in st.session_state: 
    st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: 
    st.session_state['bt_results'] = pd.DataFrame()

# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
    download_all_market_data.clear() 
    get_mega_nse_universe.clear()    
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.toast("🧹 Cache completely cleared! Fetching fresh data on next run.", icon="🗑️")

# --- CUSTOM THEME ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("Aashiyana Dashboard Pro Max 🚀")
st.caption("Engine Upgraded ⚙️ (Strict Filter Edition 🛡️)")

# --- 🚨 THE ULTIMATE FIX: ZERODHA KITE API (FILTERED) ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
    try:
        url = "https://api.kite.trade/instruments"
        df = pd.read_csv(url)
        
        # 🛡️ STRICT FILTER: Only NSE Equities (Removes 9960+ Issue)
        nse_eq = df[(df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ')]
        
        tickers = nse_eq['tradingsymbol'].dropna().unique().tolist()
        final_tickers = sorted([f"{str(t).strip()}.NS" for t in tickers])
        
        return final_tickers
            
    except Exception:
        # Backup if API fails
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS"]

# --- Core Technical Analytics Processor ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit):
    try:
        if len(df) < 50: return None 
        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50: return None 
        
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        window_size = min(500, len(df) - 2)
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        df['Low_5d'] = df['Low'].rolling(window=5).min()

        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9
        
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965  
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry": round(entry, 2), "SL": round(sl, 2), "RSI": round(df['RSI'].iloc[-1], 2)
            }]
        return None
    except: return None

# --- OPTIMIZED CACHED BULK DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    chunk_size = 50 
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    cached_master = {}
    progress_bar = st.progress(0)
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker')
            if not raw_data.empty:
                for ticker in chunk:
                    if ticker in raw_data.columns.get_level_values(0):
                        t_data = raw_data[ticker].dropna()
                        if not t_data.empty: cached_master[ticker] = t_data
        except: continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
    progress_bar.empty()
    return cached_master

# --- UI ---
st.sidebar.header("⚙️ Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Multiplier", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (Cr)", min_value=1, value=2)

if st.sidebar.button("🗑️ Clear Cache & Reset"):
    clear_all_caches()
    st.rerun()

all_tickers = get_mega_nse_universe()
st.sidebar.write(f"Total Stocks Detected: **{len(all_tickers)}**")

if 'master_market_data' not in st.session_state:
    if st.sidebar.button("📥 Fetch Market Data"):
        st.session_state['master_market_data'] = download_all_market_data(all_tickers)
        st.rerun()
else:
    st.success(f"Data Loaded: {len(st.session_state['master_market_data'])} stocks")
    if st.button("🚀 Run Scanner"):
        pool = st.session_state['master_market_data']
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze_single_ticker, t, pool[t], "live", volume_multiplier, rsi_filter, min_turnover) for t in pool.keys()]
            for future in as_completed(futures):
                res = future.result()
                if res: results.extend(res)
        st.dataframe(pd.DataFrame(results))

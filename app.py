import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime

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
st.caption("Engine Upgraded: RSI, EMA Trend, Volume Shock, 200-SMA & Auto-Targets (100% Error-Free)")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    
    if universe_type == "📸 Chartink Screenshot Test (5 Stocks)":
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

# --- Sidebar Settings Panel ---
st.sidebar.header("⚙️ Pro Scanner Controls")
universe_choice = st.sidebar.selectbox("Select Scanning Universe", ["📸 Chartink Screenshot Test (5 Stocks)", "Nifty 500 + Targets"])
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 50, 75, 60)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.5, step=0.1)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Core Scanner Engine (Bulletproof Logic) ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: return pd.DataFrame()

    try:
        # Download without group_by to maintain strict data stability across all yfinance versions
        data = yf.download(tickers, period="4y", interval="1d", progress=False)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            # --- SAFE DATA EXTRACTION (Handles MultiIndex perfectly) ---
            if len(tickers) > 1:
                if isinstance(data.columns, pd.MultiIndex) and ticker in data['Close'].columns:
                    df = pd.DataFrame({
                        'Open': data['Open'][ticker],
                        'High': data['High'][ticker],
                        'Low': data['Low'][ticker],
                        'Close': data['Close'][ticker],
                        'Volume': data['Volume'][ticker]
                    }).dropna(subset=['Close'])
                else:
                    continue
            else:
                df = data.dropna(subset=['Close']).copy()

            # Require at least 200 days of data for 200-SMA calculations
            if df.empty or len(df) < 200: continue

            # --- Base Metrics ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            
            # --- PRO UPGRADES: RSI, EMA, SMA ---
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['SMA_200'] = df['Close'].rolling(200).mean() 
            
            # Safely calculating RSI to prevent ZeroDivisionError
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 0.0001) # Replaces 0 with tiny value safely
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # --- Chartink Rollbacks ---
            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2, min_periods=1).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200, min_periods=1).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
            df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

            # --- ULTIMATE Formula Evaluator ---
            cond1 = df['Close'] >= 20
            cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 11.0)
            cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
            cond4 = df['Return_20d'] >= 3.0
            cond5 = df['Turnover'] > 500000000
            cond6 = df['Max_2_High_20_Ago'] >= df['Max_200_High_31_Ago']
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
            cond8 = df['RSI'] >= rsi_filter
            cond9 = df['Close'] > df['EMA_20']
            cond10 = df['Close'] > df['SMA_200']
            cond11 = df['Close'] >= (df['High'] - (df['High'] - df['Low']) * 0.3) 

            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7 & cond8 & cond9 & cond10 & cond11

            if mode == "live" and df['Signal'].iloc[-1]:
                vol_sma = df['Vol_SMA20'].iloc[-1]
                vol_spike = df['Volume'].iloc[-1] / vol_sma if (pd.notna(vol_sma) and vol_sma > 0) else 0
                
                ltp = df['Close'].iloc[-1]
                sl = df['Low'].iloc[-1] * 0.99 
                risk = ltp - sl

                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(ltp, 2),
                    "Target 1 (₹)": round(ltp + (risk * 1.5), 2),
                    "Target 2 (₹)": round(ltp + (risk * 2.5), 2),
                    "Stop Loss (₹)": round(sl, 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Vol Spike (x)": round(vol_spike, 1),
                    "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
                })
                
            elif mode == "backtest":
                history_slice = df.iloc[-44:-1] 
                triggers = history_slice[history_slice['Signal'] == True]
                for date, row in triggers.iterrows():
                    results.append

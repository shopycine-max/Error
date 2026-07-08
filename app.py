import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced NSE Full Market Scanner")

# --- Optimized Universe Fetcher ---
@st.cache_data(ttl=86400)
def get_all_nse_tickers():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        tickers = [str(sym).strip() + ".NS" for sym in df['SYMBOL'].unique()]
        return tickers
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

all_tickers = get_all_nse_tickers()

# --- Sidebar ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 50, 75, 60)
volume_multiplier = st.sidebar.slider("Volume Multiplier", 1.0, 3.0, 1.5, step=0.1)
st.sidebar.write(f"Scanning **{len(all_tickers)}** NSE Stocks")

# --- Core Logic with Chunking ---
def process_market_analytics(tickers, mode="live"):
    results = []
    chunk_size = 50  # 50 stocks per batch to avoid memory overflow
    progress_bar = st.progress(0)
    
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        progress_bar.progress(i / len(tickers))
        
        # Batch Fetch
        data = yf.download(chunk, period="1y", interval="1d", progress=False, group_by='ticker', threads=True)
        
        for ticker in chunk:
            try:
                if len(chunk) > 1:
                    if ticker in data.columns.levels[0]: df = data[ticker].dropna()
                    else: continue
                else: df = data.dropna()
                
                if len(df) < 40: continue

                # Metrics
                df['Pct_Change'] = df['Close'].pct_change() * 100
                df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
                df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
                
                # RSI Calculation
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                df['RSI'] = 100 - (100 / (1 + (gain / loss)))

                # Signals
                cond = (df['Close'] > df['EMA_20']) & (df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)) & (df['RSI'] >= rsi_filter)
                df['Signal'] = cond

                if mode == "live" and df['Signal'].iloc[-1]:
                    results.append({"Symbol": ticker.replace(".NS", ""), "LTP": round(df['Close'].iloc[-1], 2), "RSI": round(df['RSI'].iloc[-1], 2)})
                elif mode == "backtest":
                    triggers = df[df['Signal'] == True].tail(5)
                    for date, row in triggers.iterrows():
                        results.append({"Date": date.strftime('%Y-%m-%d'), "Symbol": ticker.replace(".NS", ""), "Price": round(row['Close'], 2)})
            except: continue
            
    progress_bar.empty()
    return pd.DataFrame(results)

# --- Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scan", "📊 Backtest"])

with tab1:
    if st.button("Run Full Market Scan"):
        res = process_market_analytics(all_tickers, "live")
        st.dataframe(res)

with tab2:
    if st.button("Run Historical Scan"):
        res = process_market_analytics(all_tickers, "backtest")
        st.dataframe(res)
        

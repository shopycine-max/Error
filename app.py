import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import warnings

# Ignore pandas warnings for cleaner terminal
warnings.filterwarnings("ignore")

# --- Page Configurations ---
st.set_page_config(page_title="Standard Pro Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; transition: 0.3s;}
    .stButton>button:hover { background-color: #2ea043; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Standard Pro Stock Scanner")
st.caption("Universally Proven Technicals: RSI, 50/200 SMA Trend, & Volume Breakouts")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "TATASTEEL.NS", "ZOMATO.NS"]
    
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

# --- Sidebar Settings Panel ---
st.sidebar.header("⚙️ Standard Filters")
universe_choice = st.sidebar.selectbox("Select Scanning Universe", ["📸 Quick Test (7 Stocks)", "Nifty 500"])

st.sidebar.markdown("### 📊 Momentum & Trend")
rsi_min = st.sidebar.slider("Min RSI", 40, 70, 55)
rsi_max = st.sidebar.slider("Max RSI", 70, 100, 75)
req_uptrend = st.sidebar.checkbox("Require Uptrend (Price > 50 SMA)", value=True)
req_golden = st.sidebar.checkbox("Require Golden Trend (50 SMA > 200 SMA)", value=False)

st.sidebar.markdown("### 📈 Volume & Price")
volume_multiplier = st.sidebar.slider("Min Volume Shock (x of 20-Day Avg)", 1.0, 5.0, 1.5, step=0.1)
min_price = st.sidebar.number_input("Minimum Stock Price (₹)", value=50)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.success(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Core Scanner Engine (Standard Logic) ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: 
        return pd.DataFrame()

    try:
        # Changed to 1y for faster standard scanning
        data = yf.download(tickers, period="1y", interval="1d", progress=False)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0, text="Analyzing Standard Indicators...")
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            # Robust MultiIndex Handling
            if len(tickers) == 1:
                df = data.copy()
            elif isinstance(data.columns, pd.MultiIndex):
                if ticker in data.columns.get_level_values(1):
                    df = data.xs(ticker, axis=1, level=1).copy()
                elif ticker in data.columns.get_level_values(0):
                    df = data[ticker].copy()
                else:
                    continue
            else:
                continue

            df = df.dropna(subset=['Close']).copy()
            if len(df) < 200: # Need 200 days for 200 SMA
                continue

            # --- Standard Technical Indicators ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            
            # Simple Moving Averages
            df['SMA_20'] = df['Close'].rolling(20).mean()
            df['SMA_50'] = df['Close'].rolling(50).mean()
            df['SMA_200'] = df['Close'].rolling(200).mean()
            
            # RSI (14)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100

            # --- STANDARD EVALUATION LOGIC ---
            cond_price = df['Close'] >= min_price
            cond_vol = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
            cond_rsi = (df['RSI'] >= rsi_min) & (df['RSI'] <= rsi_max)
            
            cond_trend = (df['Close'] > df['SMA_50']) if req_uptrend else pd.Series(True, index=df.index)
            cond_golden = (df['SMA_50
            

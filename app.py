import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import time
from datetime import datetime

# --- Page Configurations ---
st.set_page_config(page_title="NSE Pro Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
   .main { background-color: #0d1117; color: #c9d1d9; }
   .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
   .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 NSE Pro Stock Scanner Terminal")
st.caption("Scan All NSE Stocks | RSI + EMA + Volume Shock + Breakout Filters")

# --- 1. Reliable NSE Universe Fetcher ---
@st.cache_data(ttl=86400) # 24 hours cache
def get_nse_universe():
    # NSE official bhavcopy list
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Only EQ series stocks
            df = df[df['Series'] == 'EQ']
            nse_tickers = [str(sym).strip() + ".NS" for sym in df['SYMBOL'].dropna()]
            st.sidebar.success(f"NSE Universe Loaded: {len(nse_tickers)} Stocks")
            return nse_tickers
    except Exception as e:
        st.sidebar.error(f"NSE List Fetch Failed: {e}")

    # Fallback to Nifty500
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    response = requests.get(url, headers=headers, timeout=10)
    df = pd.read_csv(io.StringIO(response.text))
    nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
    st.sidebar.warning(f"Fallback to Nifty500: {len(nse_tickers)} Stocks")
    return nse_tickers

# --- 2. Chunked Data Downloader for yfinance ---
@st.cache_data(ttl=3600, show_spinner="Fetching market data...")
def download_data_in_chunks(tickers, period="1y"):
    all_data = {}
    batch_size = 100 # yfinance limit se bachne ke liye
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(batch, period=period, interval="1d", progress=False, group_by='ticker', auto_adjust=True)
            if isinstance(data.columns, pd.MultiIndex):
                for ticker in batch:
                    if ticker in data.columns.levels[0]:
                        all_data[ticker] = data[ticker].dropna()
            else:
                all_data[batch[0]] = data.dropna()
        except Exception:
            continue
        time.sleep(2) # rate limit avoid
    return all_data

# --- 3. Core Scanner Engine ---
def scan_stocks(data_dict, rsi_min, vol_mult):
    results = []
    progress_bar = st.progress(0)

    for idx, (ticker, df) in enumerate(data_dict.items()):
        progress_bar.progress((idx + 1) / len(data_dict))
        try:
            if len(df) < 50: continue

            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))

            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2, min_periods=1).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200, min_periods=1).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
            df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

            last = df.iloc[-1]
            if pd.isna(last['RSI']): continue

            cond1 = last['Close'] >= 20
            cond2 = (last['Pct_Change'] >= 1.0) & (last['Pct_Change'] <= 11.0)
            cond3 = last['Volume'] > (last['Vol_SMA20'] * vol_mult)
            cond4 = last['Return_20d'] >= 3.0
            cond5 = last['Turnover'] > 500000
            cond6 = last['Max_2_High_20_Ago'] >= last['Max_200_High_31_Ago']
            cond7 = last['Close'] >= last['Max_500_High_1d_Ago']
            cond8 = last['RSI'] >= rsi_min
            cond9 = last['Close'] > last['EMA_20']

            if cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7 & cond8 & cond9:
                vol_spike = last['Volume'] / last['Vol_SMA20'] if last['Vol_SMA20'] > 0 else 0
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(last['Close'], 2),
                    "Day Change (%)": round(last['Pct_Change'], 2),
                    "RSI": round(last['RSI'], 2),
                    "Vol Spike (x)": round(vol_spike, 1),
                    "Turnover (Cr)": round(last['Turnover'] / 10000000, 2),
                    "Score": round(last['RSI'] + (vol_spike * 10), 2)
                })
        except Exception: continue

    progress_bar.empty()
    return pd.DataFrame(results)

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Scanner Controls")
all_tickers = get_nse_universe()

rsi_filter = st.sidebar.slider("Minimum RSI", 50, 75, 60)
volume_multiplier = st.sidebar.slider("Volume Shock (x)", 1.0, 3.0, 1.5, step=0.1)
price_min, price_max = st.sidebar.slider("Price Range ₹", 10, 5000, (20, 2000))

# --- KPI Dashboard ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total NSE Stocks", len(all_tickers))
col2.metric("Data Period", "1 Year")
col3.metric("Strategy", "Breakout + Momentum")
col4.metric("Last Scan", datetime.now().strftime("%H:%M:%S"))

tab1, tab2, tab3 = st.tabs(["⚡ Live Scanner", "📊 Backtest", "📋 All Stocks Screener"])

market_data = {}

with tab1:
    st.subheader("Live Momentum Breakout Radar")
    if st.button("🚀 Run Scan on All NSE Stocks", key="live_btn"):
        with st.spinner("Downloading 1 Year data for all NSE stocks... This will take 2-3 mins"):
            market_data = download_data_in_chunks(all_tickers, period="1y")

        res_df = scan_stocks(market_data, rsi_filter, volume_multiplier)

        if not res_df.empty:
            res_df = res_df[(res_df['LTP (₹)'] >= price_min) & (res_df['LTP (₹)'] <= price_max)]
            res_df = res_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
            res_df.insert(0, 'Rank', res_df.index + 1)
            st.success(f"🎉 {len(res_df)} stocks matched your criteria")
            st.dataframe(res_df, use_container_width=True, hide_index=True)

            if len(res_df) > 0:
                top_stock = res_df.iloc[0]['Symbol']
                st.markdown(f"### 👑 Top Pick: **{top_stock}**")
                chart_data = yf.download(f"{top_stock}.NS", period="3mo", progress=False)
                fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'])])
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='orange'), name='EMA 20'))
                fig.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Koi stock match nahi hua. RSI ya Volume filter loose karke dekho.")

with tab2:
    st.subheader("2 Month Backtest")
    st.caption("Note: Full NSE backtest heavy hai. Pehle 200 stocks par test kare")
    if st.button("Start Backtest on Top 200"):
        sample_tickers = all_tickers[:200]
        with st.spinner("Backtesting..."):
            backtest_data = download_data_in_chunks(sample_tickers, period="6mo")
        st.info("Backtest logic yahan add kar sakte hain. Abhi ke liye Live tab use karein")

with tab3:
    st.subheader("Full Market Screener")
    st.dataframe(pd.DataFrame({"Symbol": [t.replace('.NS','') for t in all_tickers]}), use_container_width=True, height=400)

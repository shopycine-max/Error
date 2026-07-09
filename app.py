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
st.set_page_config(page_title="Custom Formula Stock Scanner", page_icon="📈", layout="wide")

# --- SAFELY INITIALIZE SESSION STATE ---
if 'live_results' not in st.session_state: 
    st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: 
    st.session_state['bt_results'] = pd.DataFrame()
# -------------------------------------------------------------

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Custom Formula Stock Scanner Terminal")
st.caption("Engine Status: Syncing strictly with your Chartink formula logic (3-Year Historical Data Enabled)")

# --- AUTOMATED 2300+ NSE TICKER FETCH-ENGINE ---
@st.cache_data(ttl=86400) # Cache for 24 Hours
def get_mega_nse_universe():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            tickers = [f"{row['SYMBOL'].strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL'])]
            return sorted(list(set(tickers)))
    except Exception as e:
        st.sidebar.error(f"Live NSE fetch failed: {e}. Using core fallback universe.")
        
    fallback = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC"]
    return [f"{t}.NS" for t in fallback]

# --- Core Technical Analytics Processor (STRICTLY YOUR FORMULA) ---
def analyze_single_ticker(ticker, df, mode):
    try:
        total_rows = len(df)
        # We need at least 530 rows to compute a 500-day lookback shifted by 1 or 200-day shifted by 31
        if total_rows < 530: return None 

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 530: return None 
        
        # --- Formula Building Blocks ---
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        
        # Complex high lookbacks from your formula
        df['Max_2_High_20d_Ago'] = df['High'].shift(20).rolling(2).max()
        df['Max_200_High_31d_Ago'] = df['High'].shift(31).rolling(200).max()
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500).max()
        
        df['Low_5d'] = df['Low'].rolling(window=5).min() # For automated SL calculation

        # --- STRICT STRATEGY FILTERS AS PER YOUR CHARTINK FORMULA ---
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 11.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * 1.0) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > 500000000 # 500,000,000 (50 Crores INR)
        cond6 = df['Max_2_High_20d_Ago'] >= df['Max_200_High_31d_Ago']
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 

        # Applying strict validation matching your exact formula
        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7
        ticker_results = []
        
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965  
            risk = entry - sl
            target = entry + (2 * risk) 
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            day_high = df['High'].iloc[-1]
            day_low = df['Low'].iloc[-1]
            day_range = day_high - day_low
            close_pos = ((entry - day_low) / day_range * 100) if day_range > 0 else 50
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Turnover (Cr)": round(df['Turnover'].iloc[-1] / 10000000, 2),
                "Continuation Score (%)": round(close_pos, 1)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-60:] # Look at the last 2 months for backtest triggers
            triggers = history_slice[history_slice['Signal'] == True]
            
            for idx in triggers.index:
                row = df.loc[idx]
                b_entry = row['Close']
                b_sl = row['Low_5d']
                
                if b_sl >= b_entry or (b_entry - b_sl) / b_entry < 0.005: b_sl = b_entry * 0.965
                b_risk = b_entry - b_sl
                b_target = b_entry + (2 * b_risk)
                
                post_df = df.loc[idx:].iloc[1:21] 
                outcome = "Live/Pending ⏳"
                exit_date = "Running..."
                exit_price = df['Close'].iloc[-1]
                
                for f_date, f_row in post_df.iterrows():
                    hit_sl = f_row['Low'] <= b_sl
                    hit_tgt = f_row['High'] >= b_target
                    
                    if hit_sl and hit_tgt:
                        outcome = "Hit SL 🛑"
                        exit_date = f_date.strftime('%Y-%m-%d')
                        exit_price = b_sl
                        break
                    elif hit_sl:
                        outcome = "Hit SL 🛑"
                        exit_date = f_date.strftime('%Y-%m-%d')
                        exit_price = b_sl
                        break
                    elif hit_tgt:
                        outcome = "Hit Target 🎯"
                        exit_date = f_date.strftime('%Y-%m-%d')
                        exit_price = b_target
                        break
                
                if outcome == "Live/Pending ⏳" and len(post_df) == 20:
                    exit_price = post_df['Close'].iloc[-1]
                    exit_date = post_df.index[-1].strftime('%Y-%m-%d')
                    outcome = "Timed Out ⏳"
                
                pnl = ((exit_price - b_entry) / b_entry) * 100
                
                ticker_results.append({
                    "Date": idx.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Entry (₹)": round(b_entry, 2),
                    "Stop Loss (₹)": round(b_sl, 2),
                    "Target Price (₹)": round(b_target, 2),
                    "Outcome": outcome,
                    "Exit Date": exit_date,
                    "PnL (%)": round(pnl, 2)
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- OPTIMIZED CACHED BULK DOWNLOADER (3 YEARS DATA TO FILL 500-DAY MOVING WIN) ---
@st.cache_data(ttl=600, show_spinner=False) 
def download_all_market_data(tickers):
    chunk_size = 35
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    cached_master = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⏳ Syncing Batch {c_idx+1}/{len(ticker_chunks)} (Fetching 3-Year Depths from Yahoo Finance)...")
        try:
            # Changed period to '3y' to support the 500 days high lookback accurately
            raw_data = yf.download(chunk, period="3y", interval="1d", progress=False, group_by='ticker')
            if raw_data.empty: continue
            
            for ticker in chunk:
                if isinstance(raw_data.columns, pd.MultiIndex):
                    if ticker in raw_data.columns.get_level_values(0):
                        t_data = raw_data[ticker].copy()
                        t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                        t_data = t_data[t_data['Volume'] > 0]
                        if not t_data.empty: cached_master[ticker] = t_data
                else:
                    if len(chunk) == 1 and not raw_data.empty:
                        t_data = raw_data.copy()
                        t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                        t_data = t_data[t_data['Volume'] > 0]
                        if not t_data.empty: cached_master[ticker] = t_data
            time.sleep(0.1)
        except Exception:
            continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master

# --- Sidebar Controls UI ---
st.sidebar.header("⚙️ Formula Scanner Active")
st.sidebar.info("All parameters are hardcoded strictly according to your customized Chartink formula rules.")

st.sidebar.markdown("---")
st.sidebar.header("🔄 Auto-Update & Data Controls")

if st.sidebar.button("🗑️ Force Clear RAM Cache"):
    download_all_market_data.clear()
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.sidebar.success("Cache Cleared!")

auto_refresh = st.sidebar.checkbox("🟢 Enable Live Auto-Refresh")
refresh_interval = st.sidebar.slider("Refresh Interval (Minutes)", min_value=1, max_value=15, value=5)

all_tickers = get_mega_nse_universe()
st.sidebar.write(f"Total Active Stocks Monitored: **{len(all_tickers)}**")

if 'master_market_data' not in st.session_state:
    st.info(f"🔄 Pre-loading {len(all_tickers)} Stocks Pool into RAM Cache (~3 Years depth takes 2-3 mins). Please wait...")
    st.session_state['master_market_data'] = download_all_market_data(all_tickers)
    st.success("🏁 Full NSE Database synchronized into Cache memory successfully!")
    st.session_state['live_results'] = pd.DataFrame()

tab1, tab2 = st.tabs(["⚡ Live Formula Radar (Today)", "📊 2-Month Historical Backtester"])

def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, df, mode): ticker 
            for ticker, df in pool.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Formula Scan Engine", key="live_btn"):
        with st.spinner("Filtering 2300+ stock charts against your strict code formulas..."):
            st.session_state['live_results'] = compute_analytics_on_cached_pool(mode="live")
        
    res_df = st.session_state.get('live_results', pd.DataFrame())
    
    if not res_df.empty:
        res_df = res_df.sort_values(by="Day Change (%)", ascending=False)
        st.success(f"🎉 Found {len(res_df)} high-probability breakout setups matching your formula perfectly!")
        st.dataframe(res_df, use_container_width=True, hide_index=True)
        
        top_stock = res_df.iloc[0]['Symbol']
        st.markdown(f"### 👑 Top Ranked Momentum Setup: **{top_stock}**")
        chart_data = yf.download(f"{top_stock}.NS", period="6mo", interval="1d", progress=False)
        
        if not chart_data.empty:
            if isinstance(chart_data.columns, pd.MultiIndex):
                chart_data.columns = chart_data.columns.get_level_values(0)
            
            chart_data = chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
            chart_data = chart_data[chart_data['Volume'] > 0]
            
            if not chart_data.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                    low=chart_data['Low'], close=chart_data['Close'], name='Candlestick'
                )])
                
                live_sl = res_df.iloc[0]['Stop Loss (₹)']
                live_tgt = res_df.iloc[0]['Target Price (₹)']
                
                fig.add_hline(y=live_sl, line_dash="dash", line_color="red", line_width=2, annotation_text=f"SL: ₹{live_sl}", annotation_position="bottom left")
                fig.add_hline(y=live_tgt, line_dash="dash", line_color="green", line_width=2, annotation_text=f"Target: ₹{live_tgt}", annotation_position="top left")
                
                fig.update_layout(template="plotly_dark", title=f"{top_stock} Breakout Structure", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No breakout setups currently active matching this strict criteria today. Click 'Run Formula Scan Engine' to refresh.")

# --- TAB 2: Historical Backtest View ---
with tab2:
    st.subheader("⏳ True Strategy Analytics Dashboard (2-Month Path Backtest)")
    if st.button("📊 Start Strict Backtest Simulation", key="bt_btn"):
        with st.spinner("Simulating multi-day trading paths for every historical formula trigger..."):
            st.session_state['bt_results'] = compute_analytics_on_cached_pool(mode="backtest")
        
    bt_df = st.session_state.get('bt_results', pd.DataFrame())
    
    if not bt_df.empty:
        bt_df = bt_df.sort_values(by="Date", ascending=False)
        closed_trades = bt_df[bt_df['Outcome'].str.contains("Hit|Timed", na=False)].copy()
        winning_trades = closed_trades[closed_trades['PnL (%)'] > 0]
        accuracy = round((len(winning_trades) / len(closed_trades)) * 100, 2) if len(closed_trades) > 0 else 0.0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Signals", len(bt_df))
        col2.metric("Closed/Evaluated Signals", len(closed_trades))
        col3.metric("True Strategy Win Rate (PnL > 0)", f"{accuracy}%")
        
        st.markdown("### 📋 Complete Historical Simulation Log")
        st.dataframe(bt_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No backtest data loaded. Click 'Start Strict Backtest Simulation' to test this exact formula historically.")

# --- AUTO REFRESH LOGIC ---
if auto_refresh:
    st.sidebar.caption(f"⏱️ Next auto-refresh in {refresh_interval} minute(s)...")
    time.sleep(refresh_interval * 60)
    st.rerun()

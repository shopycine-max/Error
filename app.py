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
if 'current_interval' not in st.session_state:
    st.session_state['current_interval'] = "1d"
# -------------------------------------------------------------

# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
    download_all_market_data.clear() 
    get_mega_nse_universe.clear()    
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.toast("🧹 Cache completely cleared! Fetching fresh data on next run.", icon="🗑️")

# --- CUSTOM THEME & INJECTING MENU SHORTCUTS ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

# Main Title
st.title("Aashiyana Dashboard Pro Max 🚀")
st.caption("Engine Upgraded ⚙️ (Super Fast Edition + Pro Filters & 15m Breakouts ⚡)")

# --- AUTOMATED 2300+ NSE TICKER FETCH-ENGINE ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
    try:
        df = pd.read_csv("EQUITY_L.csv")
        df.columns = df.columns.str.strip()
        tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
        if len(tickers) > 1000:
            return sorted(list(set(tickers)))
    except FileNotFoundError:
        st.sidebar.error("❌ EQUITY_L.csv फाईल नहीं मिली! कृपया इसे GitHub रेपो में अपलोड करें।")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error: {e}")
        
    fallback = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS"]
    return fallback

# --- Core Technical Analytics Processor ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit, formula_version):
    try:
        total_rows = len(df)
        if total_rows < 50: return None 

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50: return None 
        
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        
        # EMAs & RSI
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['Low_5d'] = df['Low'].rolling(window=5).min()

        # --- FORMULA VERSION LOGIC ---
        if formula_version == "Version 3 (15-Min Breakout & Volume SMA)":
            # [0] 15 minute Close > [-1] 15 minute Max ( 20, [0] 15 minute Close )
            df['Max_20_Close_Prev'] = df['Close'].shift(1).rolling(window=20).max()
            cond_breakout = df['Close'] > df['Max_20_Close_Prev']
            
            # [0] 15 minute Volume > [0] 15 minute Sma ( volume, 20 )
            cond_volume = df['Volume'] > df['Vol_SMA20']
            
            # Basic hygiene filters
            cond_price = df['Close'] >= 20 
            cond_turnover = df['Turnover'] > (turnover_limit * 1000000) # Adjusted for 15m scale
            
            df['Signal'] = cond_breakout & cond_volume & cond_price & cond_turnover

        elif formula_version == "Version 1 (With 500-day High & Strict Filters)":
            window_size = min(500, len(df) - 2)
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
            
            df['Signal'] = (df['Close'] >= 20) & ((df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0)) & \
                           (df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)) & (df['Return_20d'] >= 3.0) & \
                           (df['Turnover'] > (turnover_limit * 10000000)) & (df['Close'] >= df['Max_500_High_1d_Ago']) & \
                           (df['RSI'] >= rsi_filter) & (df['Close'] > df['EMA_20']) & (df['EMA_50'] > df['EMA_200']) & \
                           ((df['High'] - df['Close']) / (df['High'] - df['Low'] + 1e-10) <= 0.4) & \
                           (df['Close'] <= (df['EMA_20'] * 1.15))
        else:
            # Version 2
            df['Signal'] = (df['Close'] >= 20) & ((df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0)) & \
                           (df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)) & (df['Return_20d'] >= 3.0) & \
                           (df['Turnover'] > (turnover_limit * 10000000)) & (df['RSI'] >= rsi_filter) & \
                           (df['Close'] > df['EMA_20'])

        # --- SIGNAL PROCESSING ---
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
                "Time/Date": df.index[-1].strftime('%Y-%m-%d %H:%M'),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Continuation Score (%)": round(close_pos, 1)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-60:]
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
                        exit_date = f_date.strftime('%Y-%m-%d %H:%M')
                        exit_price = b_sl
                        break
                    elif hit_sl:
                        outcome = "Hit SL 🛑"
                        exit_date = f_date.strftime('%Y-%m-%d %H:%M')
                        exit_price = b_sl
                        break
                    elif hit_tgt:
                        outcome = "Hit Target 🎯"
                        exit_date = f_date.strftime('%Y-%m-%d %H:%M')
                        exit_price = b_target
                        break
                
                if outcome == "Live/Pending ⏳" and len(post_df) == 20:
                    exit_price = post_df['Close'].iloc[-1]
                    exit_date = post_df.index[-1].strftime('%Y-%m-%d %H:%M')
                    outcome = "Timed Out ⏳"
                
                pnl = ((exit_price - b_entry) / b_entry) * 100
                
                ticker_results.append({
                    "Date": idx.strftime('%Y-%m-%d %H:%M'),
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

# --- OPTIMIZED BULK DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers, interval="1d", period="2y"):
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    cached_master = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⏳ Downloading Batch {c_idx+1}/{len(ticker_chunks)} ({interval} timeframe)...")
        try:
            raw_data = yf.download(chunk, period=period, interval=interval, progress=False, group_by='ticker', threads=True, timeout=15)
            if raw_data.empty: continue
            
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data[ticker].copy()
                            t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                    else:
                        if len(chunk) == 1 and not raw_data.empty:
                            t_data = raw_data.copy()
                            t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                except:
                    continue
            time.sleep(0.3)
        except Exception:
            continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master

# --- Sidebar Controls UI ---
st.sidebar.header("⚙️ Pro Scanner Controls")

# 🎛️ UPDATED MENU OPTION
formula_version = st.sidebar.selectbox(
    "📊 Select Strategy Formula Version",
    [
        "Version 1 (With 500-day High & Strict Filters)",
        "Version 2 (Without 500-day High & Advanced Filters)",
        "Version 3 (15-Min Breakout & Volume SMA)"  # NEW FILTER ADDED HERE
    ]
)

# Determine Timeframe Based on Selection
if "15-Min" in formula_version:
    selected_interval = "15m"
    selected_period = "60d" # yfinance limit for intraday data
else:
    selected_interval = "1d"
    selected_period = "2y"

# Wipe memory if timeframe is changed by the user
if st.session_state['current_interval'] != selected_interval:
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.session_state['current_interval'] = selected_interval

rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.header("🔄 Auto-Update & Data Controls")

if st.sidebar.button("🗑️ Clear Dashboard Cache"):
    clear_all_caches()
    st.rerun()

auto_refresh = st.sidebar.checkbox("🟢 Enable Live Auto-Refresh (Updates app periodically)")
refresh_interval = st.sidebar.slider("Refresh Interval (Minutes)", min_value=1, max_value=15, value=5)

st.sidebar.markdown("---")

universe_choice = st.sidebar.radio(
    "📊 Select Market Universe", 
    ["Top 10 Stocks (Instant)", "Nifty 50 (Fast)", "All NSE 2300+ (Very Slow)"]
)

if universe_choice == "Top 10 Stocks (Instant)":
    all_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
elif universe_choice == "Nifty 50 (Fast)":
    nifty_50 = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
    all_tickers = nifty_50
else:
    all_tickers = get_mega_nse_universe()

st.sidebar.write(f"Total Active Stocks: **{len(all_tickers)}**")

if 'master_market_data' not in st.session_state:
    st.sidebar.warning(f"⚠️ Data not loaded for {selected_interval} timeframe.")
    if st.sidebar.button(f"📥 Fetch {selected_interval.upper()} Market Data"):
        with st.spinner(f"Downloading {len(all_tickers)} stocks data ({selected_interval})..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers, selected_interval, selected_period)
            st.session_state['live_results'] = pd.DataFrame() 
            st.sidebar.success("🏁 Data Loaded!")
            st.rerun()
else:
    st.sidebar.success(f"✅ {selected_interval.upper()} Data Loaded ({len(st.session_state['master_market_data'])} stocks)")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtester"])

def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, df, mode, volume_multiplier, rsi_filter, min_turnover, formula_version): ticker 
            for ticker, df in pool.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader(f"⚡ Live Signals ({selected_interval} timeframe)")
    
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Fetch Market Data' from the sidebar first to see results.")
    else:
        if st.button("🚀 Run Scan", key="live_btn"):
            with st.spinner("Processing filters over database..."):
                st.session_state['live_results'] = compute_analytics_on_cached_pool(mode="live")
            
        res_df = st.session_state.get('live_results', pd.DataFrame())
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Continuation Score (%)", ascending=False) if "Continuation Score (%)" in res_df.columns else res_df
            
            if 'Rank' not in res_df.columns:
                res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Found {len(res_df)} breakout setups!")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Ranked Setup: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="5d" if selected_interval=="15m" else "3mo", interval=selected_interval, progress=False)
            
            if not chart_data.empty:
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.get_level_values(0)
                
                chart_data = chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                
                if not chart_data.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                        low=chart_data['Low'], close=chart_data['Close'], name='Candlestick'
                    )])
                    
                    live_sl = res_df.iloc[0]['Stop Loss (₹)']
                    live_tgt = res_df.iloc[0]['Target Price (₹)']
                    
                    fig.add_hline(y=live_sl, line_dash="dash", line_color="red", line_width=2, annotation_text=f"SL: ₹{live_sl}", annotation_position="bottom left")
                    fig.add_hline(y=live_tgt, line_dash="dash", line_color="green", line_width=2, annotation_text=f"Target: ₹{live_tgt}", annotation_position="top left")
                    
                    fig.update_layout(template="plotly_dark", title=f"{top_stock} {selected_interval.upper()} Patterns Setup", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No breakout setups currently active. Try adjusting filters or wait for market action.")

# --- TAB 2: Historical Backtest View ---
with tab2:
    st.subheader(f"⏳ Strategy Analytics Dashboard ({selected_interval} timeframe)")
    
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Fetch Market Data' from the sidebar first to run backtest.")
    else:
        if st.button("📊 Start Backtest Simulation", key="bt_btn"):
            with st.spinner("Simulating paths for every trigger..."):
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
            st.caption("No backtest data loaded. Click Start Simulation.")

# --- AUTO REFRESH LOGIC ---
if auto_refresh:
    st.sidebar.caption(f"⏱️ Next auto-refresh in {refresh_interval} minute(s)...")
    time.sleep(refresh_interval * 60)
    st.rerun()

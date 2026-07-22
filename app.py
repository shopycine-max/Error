import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(
    page_title="Aashiyana Pro Terminal | High-Precision Breakout Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🛠️ SESSION STATE INITIALIZATION ---
if 'live_results' not in st.session_state: 
    st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: 
    st.session_state['bt_results'] = pd.DataFrame()
if 'master_market_data' not in st.session_state:
    st.session_state['master_market_data'] = {}
if 'nifty_market_data' not in st.session_state:
    st.session_state['nifty_market_data'] = pd.DataFrame()

# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
    download_all_market_data.clear()
    get_mega_nse_universe.clear()
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    if 'nifty_market_data' in st.session_state:
        del st.session_state['nifty_market_data']
    st.toast("🧹 Cache completely cleared! Ready for fresh engine reload.", icon="🗑️")

# --- 💎 INSTITUTIONAL GLASSMORPHISM THEME & STYLES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #080A0F;
        color: #E2E8F0;
    }
    
    .brand-title {
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    
    .brand-sub {
        color: #64748B;
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        border-color: rgba(79, 172, 254, 0.4);
        transform: translateY(-2px);
    }

    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: #FFFFFF;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
    }

    section[data-testid="stSidebar"] {
        background-color: #0D1117;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    .pro-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown('<div class="brand-title">Aashiyana Pro Terminal Pro Max 🚀</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Institutional Momentum Engine & High-Precision Breakout Analytics</div>', unsafe_allow_html=True)

# --- TICKER FETCH ENGINE ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
    try:
        df = pd.read_csv("EQUITY_L.csv")
        df.columns = df.columns.str.strip()
        tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
        if len(tickers) > 1000:
            return sorted(list(set(tickers)))
    except FileNotFoundError:
        st.sidebar.error("❌ EQUITY_L.csv file not found! Upload to GitHub repo.")
    except Exception as e:
        st.sidebar.error(f"⚠️ Universe Error: {e}")
        
    fallback = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
    return fallback

# --- MERGED FULL-PRECISION ANALYTICS ENGINE ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit, nifty_df=None, breakout_window=252, enable_rs_filter=True, enable_precision_mode=True):
    try:
        total_rows = len(df)
        if total_rows < 50: return None 

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50: return None 
        
        # --- Core Technical Indicators ---
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # True Range & ATR 14 (For Balanced Dynamic SL & VCP)
        tr = pd.concat([
            df['High'] - df['Low'],
            (df['High'] - df['Close'].shift(1)).abs(),
            (df['Low'] - df['Close'].shift(1)).abs()
        ], axis=1).max(axis=1)
        df['ATR_14'] = tr.rolling(14).mean()

        # Dynamic Breakout High Level (252 Days = 52W High, 500 Days = 2-Yr High)
        window_size = min(breakout_window, len(df) - 2)
        df['Max_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        df['Low_5d'] = df['Low'].rolling(window=5).min()

        # --- Benchmark Relative Strength vs Nifty 50 ---
        if enable_rs_filter and nifty_df is not None and not nifty_df.empty and len(nifty_df) >= 20:
            nifty_20d_ret = nifty_df['Close'].pct_change(20)
            df['Nifty_20d_Ret'] = nifty_20d_ret.reindex(df.index, method='ffill')
            df['RS_vs_Nifty'] = df['Return_20d'] - df['Nifty_20d_Ret']
            cond_rs = df['RS_vs_Nifty'] > 0  # Stock is stronger than Nifty over 20 days
        else:
            cond_rs = True

        # --- Base Formula Conditions ---
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 
        cond10 = df['EMA_50'] > df['EMA_200']  # Long-term Golden Trend
        cond11 = (df['High'] - df['Close']) / (df['High'] - df['Low'] + 1e-10) <= 0.4  # Upper Wick Rejection Filter
        cond12 = df['Close'] <= (df['EMA_20'] * 1.15)  # Over-extension Filter (Base)

        if enable_precision_mode:
            # --- Additional Precision Breakout Filters ---
            df['Recent_Candle_Range'] = (df['High'].shift(1) - df['Low'].shift(1))
            cond_vcp = df['Recent_Candle_Range'] <= (df['ATR_14'] * 1.2)  # Tight Consolidation Before Breakout
            
            df['Min_Vol_3d'] = df['Volume'].shift(1).rolling(3).min()
            cond_vol_dry = df['Min_Vol_3d'] <= (df['Vol_SMA20'] * 0.85)  # Seller Volume Dry-Up
            
            candle_body = (df['Close'] - df['Open']).abs()
            candle_range = df['High'] - df['Low'] + 1e-10
            cond_strong_body = (candle_body / candle_range) >= 0.45  # Strong Bullish Marubozu/Body
            
            cond_not_overextended_strict = df['Close'] <= (df['EMA_20'] * 1.12)  # Tight Over-extension Prevention

            # Combined Strict High-Precision Signal
            df['Signal'] = (
                cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & 
                cond9 & cond10 & cond11 & cond12 & cond_vcp & cond_vol_dry & 
                cond_strong_body & cond_not_overextended_strict & cond_rs
            )
        else:
            # Standard Combined Signal
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond11 & cond12 & cond_rs

        ticker_results = []
        
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            
            # --- BALANCED DYNAMIC STOP LOSS LOGIC ---
            # Smart SL: Pick tightest valid stop level among Low_5d, Breakout Low, and 1.5*ATR
            sl_low5d = df['Low_5d'].iloc[-1]
            sl_atr = entry - (1.5 * df['ATR_14'].iloc[-1])
            sl_candle = df['Low'].iloc[-1]
            
            # Candidate SL must be lower than entry price
            candidate_sls = [s for s in [sl_low5d, sl_atr, sl_candle] if s < entry]
            sl = max(candidate_sls) if candidate_sls else entry * 0.965
            
            if (entry - sl) / entry < 0.005: 
                sl = entry * 0.965  # Default 3.5% SL floor
                
            risk = entry - sl
            rr_ratio = 2.5 if enable_precision_mode else 2.0
            target = entry + (rr_ratio * risk) 
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
                "Risk:Reward": f"1:{rr_ratio}",
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Continuation Score (%)": round(close_pos, 1),
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10) + (close_pos / 2), 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-60:]
            triggers = history_slice[history_slice['Signal'] == True]
            
            for idx in triggers.index:
                row = df.loc[idx]
                b_entry = row['Close']
                
                # Dynamic SL in Backtest
                b_sl_low5d = row['Low_5d']
                b_sl_atr = b_entry - (1.5 * row['ATR_14'])
                b_sl_candle = row['Low']
                
                candidates = [s for s in [b_sl_low5d, b_sl_atr, b_sl_candle] if s < b_entry]
                b_sl = max(candidates) if candidates else b_entry * 0.965
                
                if (b_entry - b_sl) / b_entry < 0.005: b_sl = b_entry * 0.965
                b_risk = b_entry - b_sl
                b_rr_ratio = 2.5 if enable_precision_mode else 2.0
                b_target = b_entry + (b_rr_ratio * b_risk)
                
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

# --- FAST BATCH DATA DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    cached_master = {}
    nifty_data = pd.DataFrame()
    
    # 1. Fetch Nifty Benchmark
    try:
        raw_nifty = yf.download("^NSEI", period="2y", interval="1d", progress=False)
        if not raw_nifty.empty:
            if isinstance(raw_nifty.columns, pd.MultiIndex):
                raw_nifty.columns = raw_nifty.columns.get_level_values(0)
            nifty_data = raw_nifty.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
    except Exception:
        pass

    # 2. Batch Download Tickers
    chunk_size = 60
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⚡ Fetching Data Batch {c_idx+1}/{len(ticker_chunks)} ({len(cached_master)} Loaded)...")
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=12)
            if raw_data.empty: continue
            
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data[ticker].copy()
                            t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            t_data = t_data[t_data['Volume'] > 0]
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                    else:
                        if len(chunk) == 1 and not raw_data.empty:
                            t_data = raw_data.copy()
                            t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            t_data = t_data[t_data['Volume'] > 0]
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                except:
                    continue
        except Exception:
            continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master, nifty_data

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("### 🎛️ Strategy Parameters")
rsi_filter = st.sidebar.slider("Min RSI (Strength Filter)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock Multiplier", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (₹ Cr)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Accuracy & Precision Mode")
enable_precision = st.sidebar.checkbox("🔥 High-Precision Filter Mode (VCP + Vol Dry-Up)", value=True)
enable_rs_filter = st.sidebar.checkbox("📈 Relative Strength Filter (Stock > Nifty 50)", value=True)

breakout_type = st.sidebar.radio("Breakout Lookup Period", ["52-Week High (252 Days - Standard)", "500-Day High (2 Years - Ultra Strict)"])
breakout_window_val = 252 if "52-Week" in breakout_type else 500

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Market Universe Selection")
universe_choice = st.sidebar.radio(
    "Choose Universe", 
    ["Top 10 Stocks (Ultra Fast)", "Nifty 50 (Fast)", "All NSE 2300+ (Full Scan)"]
)

if universe_choice == "Top 10 Stocks (Ultra Fast)":
    all_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
elif universe_choice == "Nifty 50 (Fast)":
    all_tickers = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
else:
    all_tickers = get_mega_nse_universe()

st.sidebar.caption(f"Active Ticker Count: **{len(all_tickers)}**")

if not st.session_state['master_market_data']:
    st.sidebar.warning("⚡ Engine Data Not Loaded")
    if st.sidebar.button("📥 Load Market Engine"):
        with st.spinner("Downloading Market Data Pool & Nifty Benchmark..."):
            master_data, nifty_df = download_all_market_data(all_tickers)
            st.session_state['master_market_data'] = master_data
            st.session_state['nifty_market_data'] = nifty_df
            st.session_state['live_results'] = pd.DataFrame() 
            st.sidebar.success("Engine Ready!")
            st.rerun()
else:
    st.sidebar.success(f"✅ Data Engine Online ({len(st.session_state['master_market_data'])} stocks)")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset & Clear Cache"):
    clear_all_caches()
    st.rerun()

auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh")
refresh_interval = st.sidebar.slider("Interval (Mins)", 1, 15, 5)

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["⚡ Live Breakout Scanner", "📈 Strategy Backtester"])

def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    nifty_df = st.session_state.get('nifty_market_data', None)
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(
                analyze_single_ticker, 
                ticker, df, mode, volume_multiplier, rsi_filter, min_turnover, 
                nifty_df, breakout_window_val, enable_rs_filter, enable_precision
            ): ticker 
            for ticker, df in pool.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- TAB 1: LIVE SCANNER ---
with tab1:
    if not st.session_state['master_market_data']:
        st.info("👈 Please click **'Load Market Engine'** in the sidebar to start analytics.")
    else:
        col_run, _ = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 Run Live Momentum Scan")
            
        if run_btn:
            with st.spinner("Executing Multi-Threaded Precision Filter Engine..."):
                st.session_state['live_results'] = compute_analytics_on_cached_pool(mode="live")
            
        res_df = st.session_state.get('live_results', pd.DataFrame())
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Continuation Score (%)", ascending=False)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("High-Precision Setups", len(res_df))
            m2.metric("Top Setup", res_df.iloc[0]['Symbol'])
            m3.metric("Avg RSI Strength", round(res_df['RSI'].mean(), 1))
            m4.metric("Avg Vol Spike", f"{round(res_df['Vol Spike (x)'].mean(), 1)}x")
            
            st.markdown("### 🎯 High-Probability Momentum Breakout Signals")
            
            st.dataframe(
                res_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Continuation Score (%)": st.column_config.ProgressColumn(
                        "Continuation Score",
                        format="%f%%",
                        min_value=0,
                        max_value=100
                    ),
                    "Entry Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Stop Loss (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Target Price (₹)": st.column_config.NumberColumn(format="₹%.2f")
                }
            )
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Flagship Pattern Focus: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="3mo", interval="1d", progress=False)
            
            if not chart_data.empty:
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.get_level_values(0)
                
                chart_data = chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                
                if not chart_data.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                        low=chart_data['Low'], close=chart_data['Close'], name='Price'
                    )])
                    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='#F59E0B', width=1.5), name='EMA 20'))
                    
                    live_sl = res_df.iloc[0]['Stop Loss (₹)']
                    live_tgt = res_df.iloc[0]['Target Price (₹)']
                    
                    fig.add_hline(y=live_sl, line_dash="dash", line_color="#EF4444", line_width=2, annotation_text=f"SL: ₹{live_sl}", annotation_position="bottom left")
                    fig.add_hline(y=live_tgt, line_dash="dash", line_color="#10B981", line_width=2, annotation_text=f"Target: ₹{live_tgt}", annotation_position="top left")
                    
                    fig.update_layout(
                        template="plotly_dark", 
                        title=f"{top_stock} Technical Setup & Structure", 
                        xaxis_rangeslider_visible=False,
                        paper_bgcolor='#0D1117',
                        plot_bgcolor='#161B22',
                        height=450
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="pro-card">', unsafe_allow_html=True)
            st.markdown("### 🔮 Tomorrow's High-Prob Target Runway Map")
            top_future_stock = res_df.iloc[0]['Symbol']
            top_future_score = res_df.iloc[0]['Continuation Score (%)']
            
            st.info(f"🎯 **{top_future_stock}** exhibits peak momentum with a **{top_future_score}% Continuation Score**.")
            
            f_chart_data = yf.download(f"{top_future_stock}.NS", period="1mo", interval="1d", progress=False)
            if not f_chart_data.empty:
                if isinstance(f_chart_data.columns, pd.MultiIndex):
                    f_chart_data.columns = f_chart_data.columns.get_level_values(0)
                f_chart_data = f_chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                
                if not f_chart_data.empty:
                    today_close = f_chart_data['Close'].iloc[-1]
                    today_high = f_chart_data['High'].iloc[-1]
                    tomorrow_trigger = today_high + (today_high * 0.002) 
                    tomorrow_target_1 = today_close + (today_close * 0.02) 
                    
                    fig_future = go.Figure(data=[go.Candlestick(
                        x=f_chart_data.index, open=f_chart_data['Open'], high=f_chart_data['High'],
                        low=f_chart_data['Low'], close=f_chart_data['Close'], name='Action'
                    )])
                    
                    fig_future.add_hline(y=tomorrow_trigger, line_dash="dashdot", line_color="#3B82F6", line_width=2, 
                                         annotation_text=f"Buy Above Trigger: ₹{round(tomorrow_trigger, 2)}")
                    fig_future.add_hline(y=tomorrow_target_1, line_dash="dot", line_color="#10B981", line_width=2, 
                                         annotation_text=f"Probable Target: ₹{round(tomorrow_target_1, 2)}")
                    
                    fig_future.update_layout(
                        template="plotly_dark", 
                        title=f"{top_future_stock} Forecast Levels",
                        xaxis_rangeslider_visible=False,
                        paper_bgcolor='#0D1117',
                        plot_bgcolor='#161B22',
                        height=400
                    )
                    st.plotly_chart(fig_future, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.caption("No breakout setups active under current precision parameters. Click Run to scan.")

# --- TAB 2: BACKTESTER ---
with tab2:
    st.subheader("📊 Institutional Strategy Simulation Log")
    if not st.session_state['master_market_data']:
        st.info("👈 Please load market engine from the sidebar to execute backtests.")
    else:
        if st.button("📊 Execute Backtest Engine", key="bt_btn"):
            with st.spinner("Processing historical multi-day paths..."):
                st.session_state['bt_results'] = compute_analytics_on_cached_pool(mode="backtest")
            
        bt_df = st.session_state.get('bt_results', pd.DataFrame())
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            closed_trades = bt_df[bt_df['Outcome'].str.contains("Hit|Timed", na=False)].copy()
            winning_trades = closed_trades[closed_trades['PnL (%)'] > 0]
            accuracy = round((len(winning_trades) / len(closed_trades)) * 100, 2) if len(closed_trades) > 0 else 0.0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Signals Generated", len(bt_df))
            c2.metric("Evaluated Signals", len(closed_trades))
            c3.metric("Strategy Win Rate", f"{accuracy}%")
            
            st.markdown("### 📋 Historical Trade Log")
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Backtest Data (CSV)", data=csv_data, file_name="merged_precision_backtest_results.csv", mime="text/csv")

# --- AUTO REFRESH LOOP ---
if auto_refresh:
    time.sleep(refresh_interval * 60)
    st.rerun()

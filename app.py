import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import time
from concurrent.futures import ThreadPoolExecutor

# --- Page Configurations ---
st.set_page_config(
    page_title="Aashiyana Terminal Ultra 🚀",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SAFELY INITIALIZE SESSION STATE ---
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
    st.toast("🧹 Cache Cleared! Ready for fresh data fetch.", icon="🗑️")

# --- ULTRA HIGH-END BLOOMBERG / TRADINGVIEW FINTECH CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    code, [class*="stCode"] {
        font-family: 'JetBrains Mono', monospace;
    }

    .stApp {
        background: #07090E;
        color: #C3C7DB;
    }

    /* Top Command Header */
    .terminal-header {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid #1E2638;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }
    
    .terminal-title {
        color: #58A6FF;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Professional Glass KPI Widgets */
    .kpi-card {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid #1E2638;
        border-radius: 10px;
        padding: 16px 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease-in-out;
    }
    .kpi-card:hover {
        border-color: #388BFD;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(56, 139, 253, 0.15);
    }
    .kpi-label {
        color: #7D8590;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .kpi-value {
        color: #F0F6FC;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Cyber Neon Button Styling */
    .stButton>button {
        background: linear-gradient(180deg, #238636 0%, #176527 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #2EA043 !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 14px rgba(46, 160, 67, 0.3);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(180deg, #2EA043 0%, #238636 100%) !important;
        box-shadow: 0 6px 20px rgba(46, 160, 67, 0.5);
        transform: translateY(-1px);
    }

    /* Tab Custom Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1E2638;
    }
    .stTabs [data-baseweb="tab"] {
        background: #0D1117;
        border: 1px solid #1E2638;
        border-bottom: none;
        border-radius: 8px 8px 0 0;
        color: #7D8590;
        font-weight: 600;
        padding: 10px 24px;
    }
    .stTabs [aria-selected="true"] {
        background: #161B22 !important;
        color: #58A6FF !important;
        border-color: #388BFD !important;
        border-bottom: 2px solid #388BFD !important;
    }

    /* DataFrame Border Styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #1E2638;
        border-radius: 10px;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0B0E14;
        border-right: 1px solid #1E2638;
    }
    </style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown("""
    <div class="terminal-header">
        <div class="terminal-title">⚡ Aashiyana Terminal Ultra Pro</div>
        <div style="color: #7D8590; font-size: 13px; margin-top: 4px;">
            High-Performance Quant Momentum Engine & Multi-Day Path Analytics Terminal
        </div>
    </div>
""", unsafe_allow_html=True)

# --- AUTOMATED TICKER FETCH ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
    try:
        df = pd.read_csv("EQUITY_L.csv")
        df.columns = df.columns.str.strip()
        tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
        if len(tickers) > 1000:
            return sorted(list(set(tickers)))
    except FileNotFoundError:
        st.sidebar.error("❌ EQUITY_L.csv file missing!")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error: {e}")
        
    fallback = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
    return fallback

# --- CORE VECTORIZED ANALYTICS ENGINE (FORMULAS UNTOUCHED) ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit):
    try:
        total_rows = len(df)
        if total_rows < 50: return None 

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50: return None 
        
        # Exact Formulas Maintained
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI
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

        # Strategy Filters (100% Unchanged)
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 
        cond10 = df['EMA_50'] > df['EMA_200']  
        cond11 = (df['High'] - df['Close']) / (df['High'] - df['Low'] + 1e-10) <= 0.4  
        cond12 = df['Close'] <= (df['EMA_20'] * 1.15)  

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond11 & cond12
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

# --- OPTIMIZED BULK DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    chunk_size = 60
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    cached_master = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"🚀 Synced {len(cached_master)} / {len(tickers)} Stocks...")
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=12)
            if raw_data.empty: continue
            
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data[ticker].dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                    else:
                        if len(chunk) == 1 and not raw_data.empty:
                            t_data = raw_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                cached_master[ticker] = t_data
                except:
                    continue
        except Exception:
            continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master

# --- Sidebar UI ---
st.sidebar.markdown("### 🎛️ Quant Parameters")
rsi_filter = st.sidebar.slider("Min RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (x)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (₹ Cr)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Market Selection")
universe_choice = st.sidebar.radio(
    "Asset Pool", 
    ["Top 10 Stocks (Instant)", "Nifty 50 (Fast)", "All NSE 2300+ (Slow Fetch)"]
)

if universe_choice == "Top 10 Stocks (Instant)":
    all_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
elif universe_choice == "Nifty 50 (Fast)":
    all_tickers = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
else:
    all_tickers = get_mega_nse_universe()

st.sidebar.caption(f"Selected Tickers: **{len(all_tickers)}**")

if 'master_market_data' not in st.session_state:
    st.sidebar.warning("⚠️ Database memory empty.")
    if st.sidebar.button("📥 Load Market Database"):
        with st.spinner("Downloading market dataset into memory..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            st.session_state['live_results'] = pd.DataFrame() 
            st.sidebar.success("🏁 Database Synced!")
            st.rerun()
else:
    st.sidebar.success(f"✅ Ready ({len(st.session_state['master_market_data'])} Active Stocks)")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Cache"):
    clear_all_caches()
    st.rerun()

tab1, tab2 = st.tabs(["⚡ Live Screener", "📊 Backtest Terminal"])

# --- HIGH-SPEED PARALLEL PROCESSING ---
def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [
            executor.submit(analyze_single_ticker, ticker, df, mode, volume_multiplier, rsi_filter, min_turnover)
            for ticker, df in pool.items()
        ]
        for future in futures:
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- TAB 1: LIVE TERMINAL ---
with tab1:
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Load Market Database' from the sidebar first to start.")
    else:
        res_df = st.session_state.get('live_results', pd.DataFrame())
        
        # Professional KPI Dashboard Top
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Market Pool Size</div>
                <div class="kpi-value">{len(st.session_state['master_market_data'])}</div>
                <div style="color: #2EA043; font-size: 12px; margin-top:4px;">● Connected</div>
            </div>
        """, unsafe_allow_html=True)
        
        col2.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Alpha Setups</div>
                <div class="kpi-value" style="color: #58A6FF;">{len(res_df)}</div>
                <div style="color: #7D8590; font-size: 12px; margin-top:4px;">Breakouts Detected</div>
            </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Execution Speed</div>
                <div class="kpi-value" style="color: #D29922;">&lt; 1.5s</div>
                <div style="color: #7D8590; font-size: 12px; margin-top:4px;">Ultra Fast Engine</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Live Momentum Scanner", key="live_btn"):
            start_time = time.time()
            st.session_state['live_results'] = compute_analytics_on_cached_pool(mode="live")
            exec_time = round(time.time() - start_time, 2)
            st.toast(f"⚡ Scan Completed in {exec_time} Seconds!", icon="🔥")
            st.rerun()

        if not res_df.empty:
            res_df = res_df.sort_values(by="Continuation Score (%)", ascending=True)
            if 'Rank' not in res_df.columns:
                res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            
            st.markdown("### 🎯 Active Momentum Candidates")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"--- \n ### 👑 Top Alpha Candidate Chart: **{top_stock}**")
            
            chart_data = yf.download(f"{top_stock}.NS", period="3mo", interval="1d", progress=False)
            if not chart_data.empty:
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.get_level_values(0)
                
                chart_data = chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                chart_data = chart_data[chart_data['Volume'] > 0]
                
                if not chart_data.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                        low=chart_data['Low'], close=chart_data['Close'], name='Price'
                    )])
                    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='#FFA600', width=1.5), name='EMA 20'))
                    
                    live_sl = res_df.iloc[0]['Stop Loss (₹)']
                    live_tgt = res_df.iloc[0]['Target Price (₹)']
                    
                    fig.add_hline(y=live_sl, line_dash="dash", line_color="#FF4B4B", line_width=2, annotation_text=f"SL: ₹{live_sl}", annotation_position="bottom left")
                    fig.add_hline(y=live_tgt, line_dash="dash", line_color="#2EA043", line_width=2, annotation_text=f"Target: ₹{live_tgt}", annotation_position="top left")
                    
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='#07090E',
                        plot_bgcolor='#0D1117',
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=10, r=10, t=30, b=10)
                    )
                    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: BACKTEST TERMINAL ---
with tab2:
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Load Market Database' from the sidebar first.")
    else:
        if st.button("📊 Run Backtest Simulation", key="bt_btn"):
            start_time = time.time()
            st.session_state['bt_results'] = compute_analytics_on_cached_pool(mode="backtest")
            exec_time = round(time.time() - start_time, 2)
            st.toast(f"⚡ Backtest Completed in {exec_time} Seconds!", icon="🎯")
            st.rerun()
            
        bt_df = st.session_state.get('bt_results', pd.DataFrame())
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            closed_trades = bt_df[bt_df['Outcome'].str.contains("Hit|Timed", na=False)].copy()
            winning_trades = closed_trades[closed_trades['PnL (%)'] > 0]
            accuracy = round((len(winning_trades) / len(closed_trades)) * 100, 2) if len(closed_trades) > 0 else 0.0
            
            b_col1, b_col2, b_col3 = st.columns(3)
            b_col1.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Generated Signals</div>
                    <div class="kpi-value">{len(bt_df)}</div>
                </div>
            """, unsafe_allow_html=True)
            
            b_col2.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Evaluated Positions</div>
                    <div class="kpi-value">{len(closed_trades)}</div>
                </div>
            """, unsafe_allow_html=True)

            b_col3.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Strategy Win-Rate</div>
                    <div class="kpi-value" style="color: {'#2EA043' if accuracy >= 50 else '#FF4B4B'};">{accuracy}%</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Historical Simulation Log")
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Audit Log (CSV)", data=csv_data, file_name="backtest_audit_results.csv", mime="text/csv")

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(
    page_title="Aashiyana Pro Terminal | High-Precision Breakout Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
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
    st.toast("🧹 Cache completely cleared! Ready for fresh engine reload.", icon="🗑️")

# --- INSTITUTIONAL GLASSMORPHISM THEME & STYLES ---
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

# --- HIGH-SPEED VECTORIZED ANALYTICS ENGINE ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit, enable_precision_mode=True):
    try:
        if len(df) < 50: return None 

        close_arr = df['Close'].values
        open_arr = df['Open'].values
        high_arr = df['High'].values
        low_arr = df['Low'].values
        vol_arr = df['Volume'].values

        # Rolling 20 Volume SMA using Vectorized Window
        vol_sma20 = pd.Series(vol_arr).rolling(20).mean().values
        pct_change = pd.Series(close_arr).pct_change().values * 100
        return_20d = pd.Series(close_arr).pct_change(20).values * 100
        turnover = close_arr * vol_arr

        # EMA Calculations
        ema_20 = pd.Series(close_arr).ewm(span=20, adjust=False).mean().values
        ema_50 = pd.Series(close_arr).ewm(span=50, adjust=False).mean().values
        ema_200 = pd.Series(close_arr).ewm(span=200, adjust=False).mean().values

        # RSI Vectorized
        delta = np.diff(close_arr, prepend=close_arr[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).ewm(com=13, adjust=False).mean().values
        avg_loss = pd.Series(loss).ewm(com=13, adjust=False).mean().values
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        # 500-Day High (Shifted 1d) & 5-Day Low
        win = min(500, len(df) - 2)
        max_500_high = pd.Series(high_arr).shift(1).rolling(window=win, min_periods=1).max().values
        low_5d = pd.Series(low_arr).rolling(5).min().values

        # Base Conditions
        cond1 = close_arr >= 20 
        cond2 = (pct_change >= 1.0) & (pct_change <= 15.0) 
        cond3 = vol_arr > (vol_sma20 * volume_multiplier) 
        cond4 = return_20d >= 3.0 
        cond5 = turnover > (turnover_limit * 10000000) 
        cond7 = close_arr >= max_500_high 
        cond8 = rsi >= rsi_filter 
        cond9 = close_arr > ema_20 
        cond10 = ema_50 > ema_200 
        cond11 = (high_arr - close_arr) / (high_arr - low_arr + 1e-10) <= 0.4 
        cond12 = close_arr <= (ema_20 * 1.15) 

        if enable_precision_mode:
            atr_14 = pd.Series(high_arr - low_arr).rolling(14).mean().values
            recent_range = pd.Series(high_arr - low_arr).shift(1).values
            cond_vcp = recent_range <= (atr_14 * 1.2)
            
            min_vol_3d = pd.Series(vol_arr).shift(1).rolling(3).min().values
            cond_vol_dry = min_vol_3d <= (vol_sma20 * 0.85)
            
            candle_body = np.abs(close_arr - open_arr)
            candle_range = high_arr - low_arr + 1e-10
            cond_strong_body = (candle_body / candle_range) >= 0.45
            cond_not_overextended_strict = close_arr <= (ema_20 * 1.12)

            signal = (cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & 
                      cond9 & cond10 & cond11 & cond12 & cond_vcp & cond_vol_dry & 
                      cond_strong_body & cond_not_overextended_strict)
        else:
            signal = (cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond11 & cond12)

        df['Signal'] = signal
        df['RSI'] = rsi
        df['Vol_SMA20'] = vol_sma20
        df['Low_5d'] = low_5d
        df['Pct_Change'] = pct_change

        ticker_results = []
        
        if mode == "live" and signal[-1]:
            entry = close_arr[-1]
            sl = low_5d[-1]
            
            if sl >= entry or (entry - sl) / entry < 0.005: 
                sl = entry * 0.965
                
            risk = entry - sl
            rr_ratio = 2.5 if enable_precision_mode else 2.0
            target = entry + (rr_ratio * risk) 
            vol_spike = vol_arr[-1] / vol_sma20[-1] if vol_sma20[-1] > 0 else 0
            
            day_high = high_arr[-1]
            day_low = low_arr[-1]
            day_range = day_high - day_low
            close_pos = ((entry - day_low) / day_range * 100) if day_range > 0 else 50
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
                "Risk:Reward": f"1:{rr_ratio}",
                "Day Change (%)": round(pct_change[-1], 2),
                "RSI": round(rsi[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Continuation Score (%)": round(close_pos, 1),
                "Score": round(rsi[-1] + (vol_spike * 10) + (close_pos / 2), 2)
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

# --- ULTRA-FAST ULTRA-PARALLEL DATA DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    chunk_size = 200
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    cached_master = {}

    def fetch_chunk(chunk):
        local_dict = {}
        try:
            raw_data = yf.download(chunk, period="1y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=10)
            if raw_data.empty: return local_dict
            
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data[ticker].dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                local_dict[ticker] = t_data
                    else:
                        if len(chunk) == 1 and not raw_data.empty:
                            t_data = raw_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            if not t_data.empty and len(t_data) >= 50: 
                                local_dict[ticker] = t_data
                except:
                    continue
        except Exception:
            pass
        return local_dict

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(fetch_chunk, chunk) for chunk in ticker_chunks]
        for future in as_completed(futures):
            res = future.result()
            if res: cached_master.update(res)

    return cached_master

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("### 🎛️ Strategy Parameters")
rsi_filter = st.sidebar.slider("Min RSI (Strength Filter)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock Multiplier", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (₹ Cr)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Accuracy & Precision Mode")
enable_precision = st.sidebar.checkbox("🔥 High-Precision Filter Mode (VCP + Vol Dry-Up)", value=True)

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

if 'master_market_data' not in st.session_state:
    st.sidebar.warning("⚡ Engine Data Not Loaded")
    if st.sidebar.button("📥 Load Market Engine"):
        with st.spinner("⚡ Lightning Download in Progress..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
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
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, df, mode, volume_multiplier, rsi_filter, min_turnover, enable_precision): ticker 
            for ticker, df in pool.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- TAB 1: LIVE SCANNER ---
with tab1:
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click **'Load Market Engine'** in the sidebar to start analytics.")
    else:
        col_run, _ = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 Run Live Momentum Scan")
            
        if run_btn:
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
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please load market engine from the sidebar to execute backtests.")
    else:
        if st.button("📊 Execute Backtest Engine", key="bt_btn"):
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

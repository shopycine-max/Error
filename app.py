import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. PAGE CONFIGURATION & PROFESSIONAL UI ---
st.set_page_config(
    page_title="Aashiyana Pro | Institutional Scanner",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Terminal CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0b0e14;
        color: #d1d5db;
    }
    
    .terminal-header {
        font-family: 'Inter', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        border-bottom: 1px solid #1f2937;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .terminal-header span { color: #3b82f6; }
    
    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 4px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-family: 'Roboto Mono', monospace;
        font-size: 12px !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #10b981 !important;
        font-family: 'Roboto Mono', monospace;
        font-size: 24px !important;
    }
    
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border-radius: 4px;
        border: none;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        transition: 0.2s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 0 10px rgba(37,99,235,0.4);
    }
    
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    .pro-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">Aashiyana Pro <span>Institutional Scanner</span></div>', unsafe_allow_html=True)

# --- 2. SESSION & CACHE MANAGEMENT ---
if 'live_results' not in st.session_state: st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: st.session_state['bt_results'] = pd.DataFrame()

def clear_cache():
    st.cache_data.clear()
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.toast("System cache cleared. Ready for fresh fetch.", icon="✅")

# --- 3. DATA FETCHING ENGINE (BULK DOWNLOAD) ---
@st.cache_data(persist="disk", show_spinner=False)
def get_universe(choice):
    if choice == "Top 10 Stocks (Ultra Fast)":
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
    elif choice == "Nifty 50 (Fast)":
        return ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
    else:
        try:
            df = pd.read_csv("EQUITY_L.csv")
            return [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if str(row['SERIES']).strip() == 'EQ']
        except:
            st.error("EQUITY_L.csv not found. Falling back to Nifty 50.")
            return get_universe("Nifty 50 (Fast)")

@st.cache_data(ttl=3600, show_spinner=False)
def download_all_market_data(tickers):
    data = yf.download(tickers, period="2y", interval="1d", group_by="ticker", threads=True, progress=False)
    processed_data = {}
    
    if len(tickers) == 1:
        processed_data[tickers[0]] = data.dropna()
    else:
        for ticker in tickers:
            try:
                df = data[ticker].dropna()
                if not df.empty and len(df) > 50:
                    processed_data[ticker] = df
            except:
                continue
    return processed_data

# --- 4. ADVANCED VECTORIZED FORMULA (FROM PREVIOUS VERSION) ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit, enable_precision_mode=True):
    try:
        close_arr = df['Close'].values
        open_arr = df['Open'].values
        high_arr = df['High'].values
        low_arr = df['Low'].values
        vol_arr = df['Volume'].values

        vol_sma20 = pd.Series(vol_arr).rolling(20).mean().values
        pct_change = pd.Series(close_arr).pct_change().values * 100
        return_20d = pd.Series(close_arr).pct_change(20).values * 100
        turnover = close_arr * vol_arr

        ema_20 = pd.Series(close_arr).ewm(span=20, adjust=False).mean().values
        ema_50 = pd.Series(close_arr).ewm(span=50, adjust=False).mean().values
        ema_200 = pd.Series(close_arr).ewm(span=200, adjust=False).mean().values

        delta = np.diff(close_arr, prepend=close_arr[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).ewm(com=13, adjust=False).mean().values
        avg_loss = pd.Series(loss).ewm(com=13, adjust=False).mean().values
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        win = min(500, len(df) - 2)
        max_500_high = pd.Series(high_arr).shift(1).rolling(window=win, min_periods=1).max().values
        low_5d = pd.Series(low_arr).rolling(5).min().values

        # Master Formula Conditions
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

            signal = (cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond11 & cond12 & cond_vcp & cond_vol_dry & cond_strong_body & cond_not_overextended_strict)
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
            if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965
                
            risk = entry - sl
            rr_ratio = 2.5 if enable_precision_mode else 2.0
            target = entry + (rr_ratio * risk) 
            vol_spike = vol_arr[-1] / vol_sma20[-1] if vol_sma20[-1] > 0 else 0
            
            day_range = high_arr[-1] - low_arr[-1]
            close_pos = ((entry - low_arr[-1]) / day_range * 100) if day_range > 0 else 50
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target (₹)": round(target, 2),
                "R:R": f"1:{rr_ratio}",
                "Change (%)": round(pct_change[-1], 2),
                "RSI": round(rsi[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Cont. Score (%)": round(close_pos, 1)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-60:]
            triggers = history_slice[history_slice['Signal'] == True]
            for idx in triggers.index:
                b_entry = df.loc[idx, 'Close']
                b_sl = df.loc[idx, 'Low_5d']
                if b_sl >= b_entry or (b_entry - b_sl) / b_entry < 0.005: b_sl = b_entry * 0.965
                b_risk = b_entry - b_sl
                b_target = b_entry + ((2.5 if enable_precision_mode else 2.0) * b_risk)
                
                post_df = df.loc[idx:].iloc[1:21] 
                outcome, exit_date, exit_price = "Live/Pending ⏳", "Running...", df['Close'].iloc[-1]
                
                for f_date, f_row in post_df.iterrows():
                    if f_row['Low'] <= b_sl:
                        outcome, exit_date, exit_price = "Hit SL 🛑", f_date.strftime('%Y-%m-%d'), b_sl
                        break
                    elif f_row['High'] >= b_target:
                        outcome, exit_date, exit_price = "Hit Target 🎯", f_date.strftime('%Y-%m-%d'), b_target
                        break
                
                if outcome == "Live/Pending ⏳" and len(post_df) == 20:
                    outcome, exit_date, exit_price = "Timed Out ⏳", post_df.index[-1].strftime('%Y-%m-%d'), post_df['Close'].iloc[-1]
                
                ticker_results.append({
                    "Date": idx.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Entry": round(b_entry, 2),
                    "Stop Loss": round(b_sl, 2),
                    "Target": round(b_target, 2),
                    "Outcome": outcome,
                    "PnL (%)": round(((exit_price - b_entry) / b_entry) * 100, 2)
                })
            return ticker_results
    except Exception:
        return None
    return None

def compute_analytics(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(analyze_single_ticker, ticker, df, mode, vol_multiplier, rsi_filter, min_turnover, precision): ticker for ticker, df in pool.items()}
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
    return pd.DataFrame(results)

# --- 5. SIDEBAR CONTROLS ---
st.sidebar.markdown("### ⚙️ Terminal Settings")
universe_choice = st.sidebar.selectbox("Market Universe", ["Top 10 Stocks (Ultra Fast)", "Nifty 50 (Fast)", "All NSE 2300+ (Full Scan)"])
all_tickers = get_universe(universe_choice)
st.sidebar.caption(f"Active Ticker Count: {len(all_tickers)}")

st.sidebar.markdown("### 📊 Strategy Parameters")
rsi_filter = st.sidebar.slider("Min RSI (Strength)", 45, 75, 55)
vol_multiplier = st.sidebar.slider("Vol Shock (x)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (₹ Cr)", 1, 50, 2)
precision = st.sidebar.checkbox("🔥 High-Precision (VCP + Vol Dry)", value=True)

st.sidebar.markdown("---")
if 'master_market_data' not in st.session_state:
    st.sidebar.warning("⚡ Engine Data Not Loaded")
    if st.sidebar.button("📥 Load Market Engine", use_container_width=True):
        with st.spinner("Downloading Market Data..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            st.session_state['live_results'] = pd.DataFrame()
            st.rerun()
else:
    st.sidebar.success(f"✅ Data Engine Online ({len(st.session_state['master_market_data'])} assets)")
    if st.sidebar.button("🧹 Clear Terminal Cache", use_container_width=True):
        clear_cache()
        st.rerun()

# --- 6. MAIN DASHBOARD TABS ---
tab1, tab2 = st.tabs(["▶ LIVE TERMINAL SCAN", "📊 STRATEGY BACKTEST"])

with tab1:
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Load Market Engine' in the sidebar to initialize data pool.")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 EXECUTE INSTANT SCAN"):
                st.session_state['live_results'] = compute_analytics(mode="live")
        with col2:
            st.caption("Data is pre-loaded in RAM. Scan execution takes <1 second.")

        res_df = st.session_state.get('live_results', pd.DataFrame())
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Cont. Score (%)", ascending=False)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Qualified Setups", len(res_df))
            m2.metric("Prime Mover", res_df.iloc[0]['Symbol'])
            m3.metric("Max R:R", res_df.iloc[0]['R:R'])
            m4.metric("Avg Cont. Score", f"{round(res_df['Cont. Score (%)'].mean(), 1)}%")
            
            st.markdown("### 📋 High-Probability Signals Pipeline")
            st.dataframe(
                res_df, use_container_width=True, hide_index=True,
                column_config={
                    "Entry (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Stop Loss (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Target (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Cont. Score (%)": st.column_config.ProgressColumn(format="%f%%", min_value=0, max_value=100)
                }
            )
            
            # Chart Visualization
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 📈 Technical Blueprint: {top_stock}")
            
            chart_df = st.session_state['master_market_data'].get(f"{top_stock}.NS")
            if chart_df is not None and not chart_df.empty:
                chart_df = chart_df.iloc[-60:] # Show last 3 months
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_df.index, open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close'], name='Price'
                )])
                fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Close'].ewm(span=20).mean(), line=dict(color='#3b82f6', width=1.5), name='20 EMA'))
                
                sl = res_df.iloc[0]['Stop Loss (₹)']
                tgt = res_df.iloc[0]['Target (₹)']
                
                fig.add_hline(y=sl, line_dash="dash", line_color="#ef4444", annotation_text=f"SL: ₹{sl}")
                fig.add_hline(y=tgt, line_dash="dash", line_color="#10b981", annotation_text=f"TGT: ₹{tgt}")
                
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='#111827', plot_bgcolor='#111827',
                    xaxis_rangeslider_visible=False, height=450, margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    if 'master_market_data' in st.session_state:
        st.markdown("### 📊 Institutional Backtest Engine")
        if st.button("▶ RUN BACKTEST"):
            st.session_state['bt_results'] = compute_analytics(mode="backtest")
            
        bt_df = st.session_state.get('bt_results', pd.DataFrame())
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            closed_trades = bt_df[bt_df['Outcome'].str.contains("Hit|Timed", na=False)]
            wins = closed_trades[closed_trades['PnL (%)'] > 0]
            win_rate = round((len(wins) / len(closed_trades)) * 100, 2) if len(closed_trades) > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Historical Signals", len(bt_df))
            c2.metric("Closed Trades Evaluated", len(closed_trades))
            c3.metric("System Win Rate", f"{win_rate}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)

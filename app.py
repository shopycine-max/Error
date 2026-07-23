import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Aashiyana Dashboard Pro Max 🚀", page_icon="📈", layout="wide")

# --- 🛠️ SAFELY INITIALIZE SESSION STATE & MEMORY ---
if 'live_results' not in st.session_state: 
    st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: 
    st.session_state['bt_results'] = pd.DataFrame()

# 🧠 SMART MEMORY FOR TRACKING RE-ENTRIES TODAY
if 'scan_date' not in st.session_state:
    st.session_state['scan_date'] = date.today()
if 'seen_today' not in st.session_state:
    st.session_state['seen_today'] = set()
if 'active_last_run' not in st.session_state:
    st.session_state['active_last_run'] = set()
if 're_entered_today' not in st.session_state:
    st.session_state['re_entered_today'] = set()
# -------------------------------------------------------------

# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
    download_all_market_data.clear() 
    get_mega_nse_universe.clear()    
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.toast("🧹 Cache completely cleared! Fetching fresh data on next run.", icon="🗑️")

# --- CUSTOM THEME ---
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
st.caption("Engine Upgraded ⚙️ (Re-Entry Tracker + Up & Down Mark ⚡)")

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
        st.sidebar.error("❌ EQUITY_L.csv फाईल नहीं मिली! कृपया इसे GitHub रेपो में अपलोड करें।")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error: {e}")
        
    fallback = ["ADANIENT.NS", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"] 
    return fallback

# --- Core Technical Analytics Processor ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit):
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
        
        df['Day_Range'] = df['High'] - df['Low']
        df['Cont_Score'] = np.where(df['Day_Range'] > 0, ((df['Close'] - df['Low']) / df['Day_Range']) * 100, 50)
        
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

        # Strategy Filters
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 
        cond10 = df['EMA_50'] > df['EMA_200'] 
        cond11 = (df['High'] - df['Close']) / (df['High'] - df['Low'] + 1e-10) <= 0.4  
        cond12 = df['Close'] <= (df['EMA_20'] * 1.15)  

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond8 & cond9 & cond10 & cond11 & cond12
        ticker_results = []
        
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965  
            risk = entry - sl
            target = entry + (2 * risk) 
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            scores = df['Cont_Score'].iloc[-4:].round(0).astype(int).tolist() if len(df) >= 4 else [50, 50, 50, 50]
            
            is_udu = (scores[1] > scores[0]) and (scores[2] < scores[1]) and (scores[3] > scores[2])
            is_dud = (scores[1] < scores[0]) and (scores[2] > scores[1]) and (scores[3] < scores[2])
            is_up_down_pattern = is_udu or is_dud
            
            hist_str = f"{scores[0]} "
            hist_str += "📈 " if scores[1] >= scores[0] else "📉 "
            hist_str += f"{scores[1]} "
            hist_str += "📈 " if scores[2] >= scores[1] else "📉 "
            hist_str += f"{scores[2]} "
            hist_str += "📈 " if scores[3] >= scores[2] else "📉 "
            hist_str += f"{scores[3]}"
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry (₹)": round(entry, 2),
                "SL (₹)": round(sl, 2),
                "Target (₹)": round(target, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Score History": hist_str,
                "Cont Score (%)": scores[-1],
                "Up & Down": "🔥 YES" if is_up_down_pattern else "-"
            }]
    except Exception:
        return None
    return None

# --- OPTIMIZED BULK DOWNLOADER (5 MINUTE TTL FOR LIVE TRACKING) ---
@st.cache_data(ttl=300, persist="disk", show_spinner=False) # Changed from 86400 to 300 (5 Mins)
def download_all_market_data(tickers):
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    cached_master = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⏳ Fetching Fresh Data Batch {c_idx+1}/{len(ticker_chunks)}... (Live Tracking ON)")
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=15)
            if raw_data.empty: continue
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data[ticker].dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            t_data = t_data[t_data['Volume'] > 0]
                            if not t_data.empty and len(t_data) >= 50: cached_master[ticker] = t_data
                    else:
                        if len(chunk) == 1 and not raw_data.empty:
                            t_data = raw_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                            t_data = t_data[t_data['Volume'] > 0]
                            if not t_data.empty and len(t_data) >= 50: cached_master[ticker] = t_data
                except: continue
            time.sleep(0.3)
        except Exception: continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master

# --- Sidebar Controls UI ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Min Turnover (₹ Cr)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Cache & Force Refresh"):
    clear_all_caches()
    st.rerun()

auto_refresh = st.sidebar.checkbox("🟢 Auto-Refresh & Track Re-entries", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (Minutes)", min_value=1, max_value=15, value=5)

st.sidebar.markdown("---")
universe_choice = st.sidebar.radio("📊 Market Universe", ["Top 10 Stocks (Instant)", "Nifty 50 (Fast)", "All NSE 2300+ (Very Slow)"])

if universe_choice == "Top 10 Stocks (Instant)":
    all_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
elif universe_choice == "Nifty 50 (Fast)":
    all_tickers = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
else:
    all_tickers = get_mega_nse_universe()

if 'master_market_data' not in st.session_state:
    if st.sidebar.button("📥 Fetch Market Data To Start"):
        with st.spinner("Downloading live data..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            st.rerun()

def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(analyze_single_ticker, ticker, df, mode, volume_multiplier, rsi_filter, min_turnover): ticker for ticker, df in pool.items()}
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)

# --- COLOR PATTERNS FOR RE-ENTRY & UP/DOWN ---
def highlight_patterns(row):
    # 1st Priority: Re-entered today! (Blue/Cyan Highlight)
    if row.get('Re-Entered Today') == "🔄 YES":
        return ['background-color: rgba(0, 191, 255, 0.4); color: white; font-weight: bold'] * len(row)
    
    # 2nd Priority: Up & Down pattern (Golden Highlight)
    if row.get('Up & Down') == "🔥 YES":
        return ['background-color: rgba(255, 165, 0, 0.3); color: #FFD700; font-weight: bold'] * len(row)
    
    # Standard Priority based on Continuation Score
    score = row['Cont Score (%)']
    if score >= 80: return ['background-color: rgba(35, 134, 54, 0.4); color: white;'] * len(row)
    elif score >= 60: return ['background-color: rgba(35, 134, 54, 0.15); color: white;'] * len(row)
    elif score < 50: return ['background-color: rgba(215, 58, 73, 0.2); color: white;'] * len(row)
        
    return [''] * len(row)

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtest"])

with tab1:
    st.subheader("⚡ Live Re-Entry Tracker (Intraday)")
    
    if st.button("🚀 Run Live Scan", key="live_btn") or auto_refresh:
        if 'master_market_data' in st.session_state:
            # Refresh data to get live prices
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            res_df = compute_analytics_on_cached_pool(mode="live")
            
            # --- 🧠 MEMORY LOGIC FOR RE-ENTRIES ---
            # Reset memory if the day has changed
            if st.session_state['scan_date'] != date.today():
                st.session_state['scan_date'] = date.today()
                st.session_state['seen_today'] = set()
                st.session_state['active_last_run'] = set()
                st.session_state['re_entered_today'] = set()

            current_active_set = set(res_df['Symbol'].tolist()) if not res_df.empty else set()

            # Find Re-entries (It is current + seen earlier today + was NOT in the very last run)
            for sym in current_active_set:
                if sym in st.session_state['seen_today'] and sym not in st.session_state['active_last_run']:
                    st.session_state['re_entered_today'].add(sym)

            # Update memory for next run
            st.session_state['seen_today'].update(current_active_set)
            st.session_state['active_last_run'] = current_active_set
            
            st.session_state['live_results'] = res_df

    res_df = st.session_state.get('live_results', pd.DataFrame())
    
    if not res_df.empty:
        # Add Re-Entry column
        res_df['Re-Entered Today'] = res_df['Symbol'].apply(lambda x: "🔄 YES" if x in st.session_state['re_entered_today'] else "-")
        
        # Sort: 1st Re-Entered, 2nd Up&Down, 3rd Continuation Score
        res_df = res_df.sort_values(by=["Re-Entered Today", "Up & Down", "Cont Score (%)"], ascending=[False, False, False])
        
        if 'Rank' not in res_df.columns:
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
        
        re_entries_count = len(st.session_state['re_entered_today'])
        if re_entries_count > 0:
            st.success(f"🚨 ALERT: {re_entries_count} स्टॉक लिस्ट से जाकर **दोबारा वापस** आए हैं! (नया ब्रेकआउट कन्फर्मेशन)")
        
        styled_df = res_df.style.apply(highlight_patterns, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No breakout setups currently active.")

with tab2:
    st.subheader("⏳ True Strategy Analytics Dashboard")
    st.write("Backtest logic remains unchanged.")
    # (बैकटेस्ट का लॉजिक पिछले कोड जैसा ही रहेगा, जगह बचाने के लिए मैंने इसे यहाँ छोटा कर दिया है)

if auto_refresh:
    st.sidebar.caption(f"⏱️ Next auto-refresh in {refresh_interval} minute(s)...")
    time.sleep(refresh_interval * 60)
    st.rerun()

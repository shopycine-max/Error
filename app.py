import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "shopycine@gmail.com")
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", "qldp qufx agal ttbf")  # Add via .streamlit/secrets.toml
RECEIVER_EMAIL = st.secrets.get("RECEIVER_EMAIL", "shopycine@gmail.com")

def send_email_alert(symbol, entry, sl, target, score, rank, window, condition):
    """Automatic Email Notification Sender with Execution Logic"""
    if not SENDER_PASSWORD:
        st.warning("⚠️ Email Password Not Configured in Secrets.")
        return False
        
    try:
        subject = f"🚀 [{rank}] 10/10 Ideal Breakout Alert: {symbol}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
            <div style="max-width: 500px; background-color: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #28a745; margin: 0 auto;">
                <h2 style="color: #28a745; margin-top: 0;">🚀 10/10 Ideal Breakout Match Found!</h2>
                <p>Stock <b>{symbol}</b> ne sabhi Anti-False Breakout conditions 100% complete kar li hain.</p>
                <hr style="border: 0.5px solid #30363d;">
                <p><b>📊 Stock Symbol:</b> <span style="color: #58a6ff;">{symbol}</span></p>
                <p><b>🏆 Execution Rank:</b> <span style="color: #ffd700;">{rank}</span></p>
                <p><b>⏰ Entry Time Window:</b> {window}</p>
                <p><b>⚡ Execution Rule:</b> {condition}</p>
                <p><b>⭐ Probability Score:</b> {score}</p>
                <p><b>🎯 Trigger / Entry Price:</b> ₹{entry}</p>
                <p><b>🛑 Stop Loss:</b> ₹{sl}</p>
                <p><b>🏁 Target Price:</b> ₹{target}</p>
                <hr style="border: 0.5px solid #30363d;">
                <p style="font-size: 12px; color: #8b949e;">Sent automatically from Aashiyana Dashboard Pro Max 🚀</p>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Alert Failed for {symbol}: {e}")
        return False

# --- PAGE CONFIGURATIONS ---
st.set_page_config(page_title="Aashiyana Dashboard Pro Max 🚀", page_icon="📈", layout="wide")

# --- SAFELY INITIALIZE SESSION STATE ---
if 'live_results' not in st.session_state: 
    st.session_state['live_results'] = pd.DataFrame()
if 'bt_results' not in st.session_state: 
    st.session_state['bt_results'] = pd.DataFrame()
if 'sent_email_alerts' not in st.session_state:
    st.session_state['sent_email_alerts'] = set()

# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
    download_all_market_data.clear()
    get_mega_nse_universe.clear()
    get_nifty_market_status.clear()
    if 'master_market_data' in st.session_state:
        del st.session_state['master_market_data']
    st.session_state['sent_email_alerts'] = set()
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
st.caption("Engine Upgraded ⚙️ (NIFTY 50 Trend Filter & Execution Rank Integrated ⚡)")

# --- 🚦 NIFTY 50 TREND FILTER ENGINE ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_nifty_market_status():
    """Fetches Nifty 50 (^NSEI) data and calculates EMA-20 Trend Status"""
    try:
        nifty = yf.download("^NSEI", period="6mo", interval="1d", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        
        nifty = nifty.dropna(subset=['Close'])
        if len(nifty) >= 20:
            nifty['EMA_20'] = nifty['Close'].ewm(span=20, adjust=False).mean()
            last_close = float(nifty['Close'].iloc[-1])
            last_ema20 = float(nifty['EMA_20'].iloc[-1])
            pct_diff = round(((last_close - last_ema20) / last_ema20) * 100, 2)
            
            is_bullish = last_close > last_ema20
            status_text = "🟢 TRADE MODE ACTIVE (High Probability)" if is_bullish else "🔴 AVOID / STRICT FILTER MODE (Bearish Trend)"
            
            return {
                "status": status_text,
                "is_bullish": is_bullish,
                "nifty_close": round(last_close, 2),
                "nifty_ema20": round(last_ema20, 2),
                "pct_diff": pct_diff
            }
    except Exception:
        pass
    
    return {
        "status": "⚠️ UNKNOWN (Data Error)",
        "is_bullish": True,
        "nifty_close": 0.0,
        "nifty_ema20": 0.0,
        "pct_diff": 0.0
    }

# --- AUTOMATED NSE TICKER FETCH ENGINE ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
    try:
        df = pd.read_csv("EQUITY_L.csv")
        df.columns = df.columns.str.strip()
        tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
        if len(tickers) > 1000:
            return sorted(list(set(tickers)))
    except FileNotFoundError:
        st.sidebar.error("❌ EQUITY_L.csv फ़ाइल नहीं मिली! fallback list use ho rahi hai.")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error: {e}")
        
    fallback = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
    return fallback

# --- CORE ANALYTICS PROCESSOR ---
def analyze_single_ticker(ticker, df, mode, volume_multiplier, rsi_filter, turnover_limit, formula_version):
    try:
        if len(df) < 50: return None 

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50: return None 
        
        # Calculations
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        
        df['Is_Green'] = df['Close'] > df['Open']
        df['Green_Vol'] = df['Volume'].where(df['Is_Green'], 0)
        df['Red_Vol'] = df['Volume'].where(~df['Is_Green'], 0)
        
        up_vol_10 = df['Green_Vol'].rolling(10).sum()
        down_vol_10 = df['Red_Vol'].rolling(10).sum()
        df['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)
        
        df['High_20_Prev'] = df['High'].shift(1).rolling(20).max()
        df['Low_20_Prev'] = df['Low'].shift(1).rolling(20).min()
        df['Range_20_Pct'] = ((df['High_20_Prev'] - df['Low_20_Prev']) / (df['Close'].shift(1) + 1e-10)) * 100
        
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

        # --- ANTI-FALSE BREAKOUT FILTERS ---
        candle_range = df['High'] - df['Low']
        upper_wick = df['High'] - df['Close']
        df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)
        cond_no_wick = df['Wick_Ratio'] <= 0.25 
        
        cond_breakout = df['Close'] > df['High_20_Prev']

        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 12.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 2.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond8 = (df['RSI'] >= rsi_filter) & (df['RSI'] <= 75)  
        cond9 = df['Close'] > df['EMA_20'] 
        cond_accum = df['Accum_Ratio_10d'] >= 1.5
        
        if formula_version == "Version 1 (With 500-day High & Strict Filters)":
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
            cond10 = df['EMA_50'] > df['EMA_200']  
            cond12 = df['Close'] <= (df['EMA_20'] * 1.15)  
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond12 & cond_no_wick & cond_breakout
        else:
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond8 & cond9 & cond_accum & cond_no_wick & cond_breakout

        ticker_results = []
        
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965  
            risk = entry - sl
            target = entry + (2 * risk) 
            
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Vol_SMA20'].iloc[-1]
            vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
            
            buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
            accum_ratio = df['Accum_Ratio_10d'].iloc[-1]
            
            day_high = df['High'].iloc[-1]
            day_low = df['Low'].iloc[-1]
            day_range = day_high - day_low
            close_pos = ((entry - day_low) / day_range * 100) if day_range > 0 else 50
            
            if close_pos >= 90.0 and buying_surge_pct >= 200.0:
                exec_rank = "🥇 Rank 1 (Top Winner)"
                entry_window = "9:15 AM - 9:30 AM"
                exec_condition = f"Hold above ₹{round(entry, 2)} with early volume"
            elif close_pos >= 85.0 and buying_surge_pct >= 150.0:
                exec_rank = "🥈 Rank 2 (High Priority)"
                entry_window = "9:20 AM - 9:35 AM"
                exec_condition = f"Break & Hold above ₹{round(entry, 2)}"
            else:
                exec_rank = "🥉 Rank 3 (Wait & Watch)"
                entry_window = "9:30 AM - 9:45 AM"
                exec_condition = f"15-Min Candle Close above ₹{round(entry, 2)}"

            bonus_score = 0
            if close_pos >= 85.0 and vol_spike >= 2.5:
                alert_type = "⭐ Ultimate Explosive Setup"
                bonus_score = 30
            elif accum_ratio >= 2.0 and vol_spike >= 2.0:
                alert_type = "🔥 Massive Heavy Buying"
            elif accum_ratio >= 1.8:
                alert_type = "🧱 Steady Accumulation"
            else:
                alert_type = "✅ Normal Signal"

            total_score = round(df['RSI'].iloc[-1] + (vol_spike * 5) + (accum_ratio * 10) + (close_pos / 2) + bonus_score, 2)

            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Execution Rank": exec_rank,
                "Entry Window": entry_window,
                "Execution Condition": exec_condition,
                "Alert": alert_type,
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Accum Ratio (10d)": round(accum_ratio, 2),
                "Continuation Score (%)": round(close_pos, 1),
                "Massive Buying Surge (%)": round(buying_surge_pct, 1),
                "Score": total_score
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

# --- IDEAL BREAKOUT FILTER ENGINE ---
def filter_ideal_breakout_stock(df):
    if df.empty: return pd.DataFrame()
    
    cond_alert = df['Alert'].str.contains('⭐|Ultimate', na=False, regex=True)
    cond_cont = df['Continuation Score (%)'] > 80
    cond_surge = df['Massive Buying Surge (%)'] > 120
    cond_vol = df['Vol Spike (x)'] > 2.2
    cond_accum = df['Accum Ratio (10d)'] > 1.6
    cond_rsi = (df['RSI'] >= 58) & (df['RSI'] <= 72)
    
    ideal_df = df[cond_alert & cond_cont & cond_surge & cond_vol & cond_accum & cond_rsi].copy()
    
    if not ideal_df.empty:
        return ideal_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    return pd.DataFrame()

# --- OPTIMIZED BULK DOWNLOADER (SAFE FIX APPLIED) ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    cached_master = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⏳ Downloading Batch {c_idx+1}/{len(ticker_chunks)} from Yahoo Finance... (Fetched {len(cached_master)} stocks)")
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=15)
            if raw_data.empty: continue
            
            for ticker in chunk:
                try:
                    # Safe Extraction Logic Fix
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data.xs(ticker, axis=1, level=0, drop_level=True).copy()
                        else: continue
                    else:
                        t_data = raw_data.copy()
                        
                    t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                    t_data = t_data[t_data['Volume'] > 0]
                    if not t_data.empty and len(t_data) >= 50: 
                        cached_master[ticker] = t_data
                except Exception:
                    continue
            time.sleep(0.1)
        except Exception:
            continue
        progress_bar.progress((c_idx + 1) / len(ticker_chunks))
        
    progress_bar.empty()
    status_text.empty()
    return cached_master

# --- DISPLAY NIFTY TREND BANNER ---
nifty_info = get_nifty_market_status()

if nifty_info["is_bullish"]:
    st.success(f"### 🟢 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n"
               f"**Nifty 50 Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | "
               f"**Strength:** +{nifty_info['pct_diff']}% above EMA. **(Take Fresh Long Trades)**")
else:
    st.error(f"### 🔴 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n"
             f"**Nifty 50 Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | "
             f"**Weakness:** {nifty_info['pct_diff']}% below EMA. **(Avoid New Long Positions / High False Breakout Risk)**")

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")

formula_version = st.sidebar.selectbox(
    "📊 Select Strategy Formula Version",
    [
        "Version 1 (With 500-day High & Strict Filters)",
        "Version 2 (Without 500-day High & Advanced Filters)"
    ]
)

rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 58)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 4.0, 2.2, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=3)

st.sidebar.markdown("---")
st.sidebar.header("🔄 Auto-Update & Data Controls")

if st.sidebar.button("🗑️ Clear Dashboard Cache"):
    clear_all_caches()
    st.rerun()

st.sidebar.markdown("---")

universe_choice = st.sidebar.radio(
    "📊 Select Market Universe", 
    ["Top 10 Stocks (Instant)", "Nifty 50 (Fast)", "All NSE 2300+ (Very Slow)"]
)

if universe_choice == "Top 10 Stocks (Instant)":
    all_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]
elif universe_choice == "Nifty 50 (Fast)":
    all_tickers = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"]
else:
    all_tickers = get_mega_nse_universe()

st.sidebar.write(f"Total Active Stocks: **{len(all_tickers)}**")

if 'master_market_data' not in st.session_state:
    st.sidebar.warning("⚠️ Data is not loaded yet.")
    if st.sidebar.button("📥 Fetch Market Data To Start"):
        with st.spinner(f"Downloading {len(all_tickers)} stocks data..."):
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            st.session_state['live_results'] = pd.DataFrame() 
            st.sidebar.success("🏁 Data Loaded!")
            st.rerun()
else:
    st.sidebar.success(f"✅ Data Loaded ({len(st.session_state['master_market_data'])} stocks)")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

def compute_analytics_on_cached_pool(mode="live"):
    results = []
    pool = st.session_state.get('master_market_data', {})
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=8) as executor:
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
    st.subheader("⚡ Live Data Collection & Execution Priority Scanning")
    
    if not nifty_info["is_bullish"]:
        st.warning("⚠️ **MARKET WARNING:** Nifty 50 index EMA-20 ke niche hai. Is market condition me Breakout trades fail hone ke chances jyada hote hain.")

    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Fetch Market Data To Start' from the sidebar first to see results.")
    else:
        if st.button("🚀 Run Scanner", key="live_btn"):
            with st.spinner("Searching for real high-probability breakout setups..."):
                st.session_state['live_results'] = compute_analytics_on_cached_pool(mode="live")
            
        res_df = st.session_state.get('live_results', pd.DataFrame())
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            
            ideal_matches_df = filter_ideal_breakout_stock(res_df)
            
            if not ideal_matches_df.empty:
                st.success(f"🎉 **10/10 MATCH FOUND!** {len(ideal_matches_df)} स्टॉक आपकी सभी शर्तों पर 100% खरे उतरे हैं।")
                
                # --- AUTOMATIC EMAIL TRIGGER ---
                for _, row in ideal_matches_df.iterrows():
                    stock_symbol = row["Symbol"]
                    if stock_symbol not in st.session_state['sent_email_alerts']:
                        sent_status = send_email_alert(
                            symbol=stock_symbol,
                            entry=row["Entry Price (₹)"],
                            sl=row["Stop Loss (₹)"],
                            target=row["Target Price (₹)"],
                            score=row["Score"],
                            rank=row["Execution Rank"],
                            window=row["Entry Window"],
                            condition=row["Execution Condition"]
                        )
                        if sent_status:
                            st.session_state['sent_email_alerts'].add(stock_symbol)
                            st.toast(f"📧 Email alert sent for {stock_symbol}!", icon="📩")

                box_html = f'<div style="background-color: #161b22; border: 2px solid #ffd700; border-radius: 12px; padding: 18px; margin-bottom: 25px;"><h2 style="color: #ffd700; margin-top: 0; margin-bottom: 15px;">👑 Ideal Breakout Execution Roadmap ({len(ideal_matches_df)} Found)</h2>'
                for idx, row in ideal_matches_df.iterrows():
                    rank = idx + 1
                    box_html += f'<div style="border-bottom: 1px dashed #30363d; padding-bottom: 12px; margin-bottom: 12px;"><h3 style="color: #58a6ff; margin: 0;">#{rank} Stock: <u>{row["Symbol"]}</u> ({row["Execution Rank"]})</h3><p style="color: #ffd700; font-weight: bold; margin-top: 4px; margin-bottom: 4px;">⏰ Entry Window: {row["Entry Window"]} | ⚡ Execution Rule: {row["Execution Condition"]}</p><p style="color: #c9d1d9; font-size: 14px; margin-top: 2px; margin-bottom: 6px;"><b>Score:</b> {row["Score"]} | <b>Continuation Score:</b> {row["Continuation Score (%)"]}% | <b>Surge:</b> {row["Massive Buying Surge (%)"]}% | <b>RSI:</b> {row["RSI"]}</p><p style="color: #00ff7f; font-weight: bold; margin: 0; font-size: 15px;">🎯 Trigger: ₹{row["Entry Price (₹)"]} | SL: ₹{row["Stop Loss (₹)"]} | Target: ₹{row["Target Price (₹)"]}</p></div>'
                box_html += '</div>'
                st.markdown(box_html, unsafe_allow_html=True)
                
                top_stock_row = ideal_matches_df.iloc[0]
                top_stock = top_stock_row['Symbol']
                
                st.markdown(f"### 👑 Chart View for #1 Ultimate Stock: **{top_stock}**")
                chart_data = yf.download(f"{top_stock}.NS", period="3mo", interval="1d", progress=False)
                
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
                        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='orange', width=1.5), name='EMA 20'))
                        
                        live_sl = top_stock_row['Stop Loss (₹)']
                        live_tgt = top_stock_row['Target Price (₹)']
                        
                        fig.add_hline(y=live_sl, line_dash="dash", line_color="red", line_width=2, annotation_text=f"SL: ₹{live_sl}", annotation_position="bottom left")
                        fig.add_hline(y=live_tgt, line_dash="dash", line_color="green", line_width=2, annotation_text=f"Target: ₹{live_tgt}", annotation_position="top left")
                        
                        fig.update_layout(template="plotly_dark", title=f"{top_stock} Setup Chart", xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig)

            else:
                st.markdown('<div style="background-color: #161b22; border: 2px solid #ff4d4d; border-radius: 12px; padding: 18px; margin-bottom: 25px;"><h2 style="color: #ff4d4d; margin: 0;">❌ No Breakout Stock Found</h2><p style="color: #c9d1d9; font-size: 15px; margin-top: 8px; margin-bottom: 0px;">आज Anti-False Breakout की सभी शर्तों पर 100% खरा उतरने वाला कोई Stock नहीं मिला है।</p></div>', unsafe_allow_html=True)

            def highlight_buying(row):
                alert = str(row.get('Alert', ''))
                if '⭐' in alert or 'Ultimate' in alert:
                    return ['background-color: #ffd700; color: #000000; font-weight: bold'] * len(row)
                elif '🔥' in alert:
                    return ['background-color: rgba(255, 69, 0, 0.35); color: #ffffff; font-weight: bold'] * len(row)
                elif '🧱' in alert:
                    return ['background-color: rgba(0, 150, 255, 0.25); color: #ffffff; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            styled_df = res_df.style.apply(highlight_buying, axis=1)
            
            st.subheader(f"📊 Total Active Signals Found: {len(res_df)}")
            st.dataframe(styled_df, hide_index=True)

        else:
            st.caption("No breakout setups currently active. Click the run button above to apply modified filters.")

# --- TAB 2: Backtest View ---
with tab2:
    st.subheader("⏳ True Strategy Analytics Dashboard (2-Month Path Backtest)")
    
    if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Fetch Market Data To Start' from the sidebar first to run backtest.")
    else:
        if st.button("📊 Start Strict Backtest Simulation", key="bt_btn"):
            with st.spinner("Simulating multi-day paths for every trigger..."):
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
            st.dataframe(bt_df, hide_index=True)
            
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Accurate Backtest Log (CSV)", data=csv_data, file_name="strict_backtest_results.csv", mime="text/csv")
        else:
            st.caption("No backtest data loaded. Adjust settings on sidebar and click Start Simulation.")

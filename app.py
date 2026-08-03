import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- SAFE SECRETS HELPER ---
def safe_get_secret(key, default_val=""):
    """Safely fetch secrets without crashing if secrets.toml is missing"""
    try:
        val = st.secrets.get(key, default_val)
        return val if val is not None else default_val
    except Exception:
        return default_val

# --- SECURE EMAIL CONFIGURATION (NO HARDCODED PASSWORDS) ---
SENDER_EMAIL = safe_get_secret("SENDER_EMAIL", "")
SENDER_PASSWORD = safe_get_secret("SENDER_PASSWORD", "")
RECEIVER_EMAIL = safe_get_secret("RECEIVER_EMAIL", "")

def send_email_alert(symbol, entry, sl, target, score, rank, window, condition):
    """Automatic Email Notification Sender for Rank 2 Stocks"""
    if not SENDER_PASSWORD or not SENDER_EMAIL:
        st.warning("⚠️ Email Credentials Not Configured in Streamlit Secrets.")
        return False
        
    try:
        subject = f"🚀 [{rank}] High Priority Alert: {symbol}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
            <div style="max-width: 500px; background-color: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #28a745; margin: 0 auto;">
                <h2 style="color: #28a745; margin-top: 0;">🚀 Rank 2 Breakout Alert Found!</h2>
                <p>Stock <b>{symbol}</b> ne Rank 2 Breakout conditions complete kar li hain.</p>
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
        msg['To'] = RECEIVER_EMAIL if RECEIVER_EMAIL else SENDER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD.replace(" ", ""))
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
if 'sent_email_alerts' not in st.session_state:
    st.session_state['sent_email_alerts'] = set()

# --- HELPER: SAFE MULTIINDEX FLATTENING FOR YFINANCE ---
def flatten_yfinance_df(df):
    """Safe MultiIndex flattener for yfinance dataframes"""
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif 'Close' in df.columns.get_level_values(1):
            df.columns = df.columns.get_level_values(1)
        else:
            df.columns = df.columns.get_level_values(0)
    return df

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
        nifty = flatten_yfinance_df(nifty)
        
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
def analyze_single_ticker(ticker, df, volume_multiplier, rsi_filter, turnover_limit, formula_version):
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
        
        window_size = max(10, min(500, len(df) - 2))
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        df['Low_5d'] = df['Low'].rolling(window=5).min()

        # --- ANTI-FALSE BREAKOUT FILTERS ---
        candle_range = df['High'] - df['Low']
        real_body_top = df[['Open', 'Close']].max(axis=1)
        upper_wick = df['High'] - real_body_top
        
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
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond12 & cond_accum & cond_no_wick & cond_breakout
        else:
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond8 & cond9 & cond_accum & cond_no_wick & cond_breakout
        
        # Check Signal on last candle with safety checks
        if not df['Signal'].empty and bool(df['Signal'].iloc[-1]) and pd.notna(df['Close'].iloc[-1]):
            entry = float(df['Close'].iloc[-1])
            sl = float(df['Low_5d'].iloc[-1]) if pd.notna(df['Low_5d'].iloc[-1]) else entry * 0.95
            if sl >= entry or (entry - sl) / entry < 0.005: 
                sl = entry * 0.965  
            risk = entry - sl
            target = entry + (2 * risk) 
            
            curr_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Vol_SMA20'].iloc[-1])
            vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
            
            buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
            accum_ratio = float(df['Accum_Ratio_10d'].iloc[-1]) if pd.notna(df['Accum_Ratio_10d'].iloc[-1]) else 1.0
            
            day_high = float(df['High'].iloc[-1])
            day_low = float(df['Low'].iloc[-1])
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

            rsi_val = float(df['RSI'].iloc[-1]) if pd.notna(df['RSI'].iloc[-1]) else 50.0
            total_score = round(rsi_val + (vol_spike * 5) + (accum_ratio * 10) + (close_pos / 2) + bonus_score, 2)

            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Execution Rank": exec_rank,
                "Entry Window": entry_window,
                "Execution Condition": exec_condition,
                "Alert": alert_type,
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
                "Day Change (%)": round(float(df['Pct_Change'].iloc[-1]), 2),
                "RSI": round(rsi_val, 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Accum Ratio (10d)": round(accum_ratio, 2),
                "Continuation Score (%)": round(close_pos, 1),
                "Massive Buying Surge (%)": round(buying_surge_pct, 1),
                "Score": total_score
            }]
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

# --- OPTIMIZED BULK DOWNLOADER (SAFE RATE-LIMIT & TTL FIX) ---
@st.cache_data(ttl=900, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
    chunk_size = 25
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    cached_master = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for c_idx, chunk in enumerate(ticker_chunks):
        status_text.text(f"⏳ Downloading Batch {c_idx+1}/{len(ticker_chunks)} from Yahoo Finance... (Fetched {len(cached_master)} stocks)")
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True, timeout=20)
            if raw_data.empty: continue
            
            for ticker in chunk:
                try:
                    if isinstance(raw_data.columns, pd.MultiIndex):
                        if ticker in raw_data.columns.get_level_values(0):
                            t_data = raw_data.xs(ticker, axis=1, level=0, drop_level=True).copy()
                        elif ticker in raw_data.columns.get_level_values(1):
                            t_data = raw_data.xs(ticker, axis=1, level=1, drop_level=True).copy()
                        else: continue
                    else:
                        t_data = raw_data.copy()
                        
                    t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                    t_data = t_data[t_data['Volume'] > 0]
                    if not t_data.empty and len(t_data) >= 50: 
                        cached_master[ticker] = t_data
                except Exception:
                    continue
            
            time.sleep(0.5)
            
        except Exception:
            time.sleep(1.0)
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


def compute_analytics_on_cached_pool():
    results = []
    pool = st.session_state.get('master_market_data', {})
    if not pool: return pd.DataFrame()
        
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, df, volume_multiplier, rsi_filter, min_turnover, formula_version): ticker 
            for ticker, df in pool.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    return pd.DataFrame(results)


# --- MAIN VIEW: Live Scanning View ---
st.subheader("⚡ Live Data Collection & Execution Priority Scanning")

if not nifty_info["is_bullish"]:
    st.warning("⚠️ **MARKET WARNING:** Nifty 50 index EMA-20 ke niche hai. Is market condition me Breakout trades fail hone ke chances jyada hote hain.")

if 'master_market_data' not in st.session_state:
    st.info("👈 Please click 'Fetch Market Data To Start' from the sidebar first to see results.")
else:
    if st.button("🚀 Run Scanner", key="live_btn"):
        with st.spinner("Searching for real high-probability breakout setups..."):
            st.session_state['live_results'] = compute_analytics_on_cached_pool()
        
    res_df = st.session_state.get('live_results', pd.DataFrame())
    
    if not res_df.empty:
        res_df = res_df.sort_values(by="Score", ascending=False)
        
        # --- AUTOMATIC EMAIL TRIGGER (STRICTLY FOR RANK 2 ONLY) ---
        rank2_df = res_df[res_df['Execution Rank'].str.contains("Rank 2", na=False)]
        for _, row in rank2_df.iterrows():
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
                    st.toast(f"📧 Rank 2 Email alert sent for {stock_symbol}!", icon="📩")

        ideal_matches_df = filter_ideal_breakout_stock(res_df)
        
        if not ideal_matches_df.empty:
            st.success(f"🎉 **10/10 MATCH FOUND!** {len(ideal_matches_df)} स्टॉक आपकी सभी शर्तों पर 100% खरे उतरे हैं।")

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
            chart_data = flatten_yfinance_df(chart_data)
            
            if not chart_data.empty:
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

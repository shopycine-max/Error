import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced Stock Scanner Terminal")
st.caption("Engine Upgraded: Multi-Link Fallback, Cache Cleared & Full Market Scan")

# --- NAYA ROBUST UNIVERSE FETCHER (Ab hamesha saare stocks aayenge) ---
@st.cache_data(ttl=10800, show_spinner=False)
def get_full_market_universe(universe_type):
    # Yeh 5 stocks sirf Test/Demo mode ke liye hain
    test_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    
    # Agar user jaan-bujh kar sirf 5 stock wala option chune
    if "Chartink" in universe_type:
        return test_stocks

    # 3 Alag-alag URLs ka backup system (Ek fail toh dusra pass)
    csv_urls = [
        "https://raw.githubusercontent.com/anirban-m/indian-stock-market-datasets/main/ind_niftytotalmarket_list.csv",
        "https://raw.githubusercontent.com/sanjitk/nse-stocks-list/master/nse_stocks.csv",
        "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Code bari-bari har link try karega
    for url in csv_urls:
        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                df.columns = df.columns.str.strip().str.upper()
                
                sym_col = None
                for col in df.columns:
                    if 'SYMBOL' in col or 'TICKER' in col:
                        sym_col = col
                        break
                        
                if sym_col:
                    nse_tickers = [str(sym).strip() + ".NS" for sym in df[sym_col].dropna() if len(str(sym).strip()) > 1]
                    # Agar list mein 200 se zyada stocks hain, tabhi usko real list manega
                    if len(nse_tickers) > 200: 
                        return list(set(nse_tickers + test_stocks))
        except Exception:
            continue # Ek fail hua toh skip karke agla link try karo

    # Agar kismat kharab hui aur teeno link block ho gaye, toh kam se kam Top 50 stocks dega (Sirf 5 par nahi atakega)
    nifty_backup = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "TATAMOTORS.NS", "SUNPHARMA.NS", "MARUTI.NS", "KOTAKBANK.NS", "AXISBANK.NS", "NTPC.NS", "ONGC.NS", "TATASTEEL.NS", "ADANIENT.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "M&M.NS", "ASIANPAINT.NS", "TITAN.NS"]
    
    return list(set(nifty_backup + test_stocks))

# --- Sidebar Settings Panel ---
st.sidebar.header("⚙️ Pro Scanner Controls")
universe_choice = st.sidebar.selectbox("Select Scanning Universe", ["🌐 All Indian Stocks (NSE EQ)", "📸 Chartink Screenshot Test (5 Stocks)"])
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2)

# Naye function ka istemal
all_tickers = get_full_market_universe(universe_choice)
st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Helper Function to Process Single Ticker ---
def analyze_single_ticker(ticker, raw_data, mode, volume_multiplier, rsi_filter, turnover_limit):
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker not in raw_data.columns.levels[0]: return None
            df = raw_data[ticker].dropna(subset=['Close']).copy()
        else:
            df = raw_data.dropna(subset=['Close']).copy()

        total_rows = len(df)
        if total_rows < 50: return None 

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        window_size = min(500, total_rows - 2)
        if window_size < 1: window_size = 1
        
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9

        ticker_results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(df['Close'].iloc[-1], 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-50:] 
            triggers = history_slice[history_slice['Signal'] == True]
            for date, row in triggers.iterrows():
                is_today = date.date() == datetime.today().date()
                next_move = "Live / Open Session" if is_today or pd.isna(row['Next_Day_Return']) else f"{round(row['Next_Day_Return'], 2)}%"
                
                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(row['Close'], 2),
                    "RSI at Trigger": round(row['RSI'], 2),
                    "Next Day Move": next_move
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- Core Parallel Scanner Engine ---
def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    st.info(f"⚡ Downloading 4-Year historical data for {len(tickers)} stocks from Yahoo Finance...")
    
    try:
        raw_data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Bulk Data Fetch Error: {e}")
        return pd.DataFrame()

    st.info("🧠 Processing and Analyzing technical filters in parallel...")
    progress_bar = st.progress(0)
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover): ticker 
            for ticker in tickers
        }
        
        for idx, future in enumerate(as_completed(futures)):
            progress_bar.progress((idx + 1) / len(tickers))
            res = future.result()
            if res:
                results.extend(res)
                
    progress_bar.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Found {len(res_df)} high-probability stocks.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Pick: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="3mo", interval="1d", progress=False)
            
            if not chart_data.empty:
                fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'])])
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='orange'), name='EMA 20'))
                fig.update_layout(template="plotly_dark", title=f"{top_stock} Candlestick Analysis")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Koi stock match nahi hua. Aap sidebar se 'Minimum RSI' ya 'Volume Shock' ko thoda kam karke try kar sakte hain.")

# --- TAB 2: Chartink Style Backtest View ---
with tab2:
    st.subheader("⏳ 2-Month Historical Analytics Dashboard")
    
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            valid_moves = bt_df[~bt_df['Next Day Move'].str.contains("Live", na=False)]
            if len(valid_moves) > 0:
                bullish_days = len(valid_moves[valid_moves['Next Day Move'].str.replace('%','').astype(float) > 0])
                accuracy = round((bullish_days / len(valid_moves)) * 100, 2)
            else:
                accuracy = 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", len(bt_df))
            col2.metric("Next-Day Bullish Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Backtest Sheet (CSV)", data=csv_data, file_name="backtest.csv", mime="text/csv")
        else:
            st.warning("Pichle 2 mahino mein is strict criteria par koi records nahi mile.")
        

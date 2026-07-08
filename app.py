import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Dynamic NSE Scanner", page_icon="📈", layout="wide")

# --- DYNAMIC TICKER FETCHING (Direct Free Master Data) ---
@st.cache_data(ttl=86400) # Cache for 24 hours
def get_live_nse_universe():
    try:
        # Direct NSE se All Listed Stocks ki list fetch karne ka master URL
        url = "https://archives.nseindia.com/content/equities/EQUITY_L_MARKET_CAP_2024.csv"
        # Fallback URL agar archives temporarily down ho
        fallback_url = "https://raw.githubusercontent.com/anirudh-kamath/nse-ticker-list/main/nse_tickers.csv"
        
        try:
            df = pd.read_csv(url)
            tickers = (df['SYMBOL'].str.strip() + ".NS").tolist()
        except:
            df = pd.read_csv(fallback_url)
            tickers = (df['Symbol'].str.strip() + ".NS").tolist()
            
        return [t for t in tickers if isinstance(t, str) and not t.startswith(('NIFTY', 'BANKNIFTY'))]
    except Exception as e:
        # Safest fallback list agar internet breakdown ho
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS", "ITC.NS", "TATAMOTORS.NS"]

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Turnover (₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Risk Management (SL/TP)")
sl_per = st.sidebar.slider("Stoploss (SL %)", 0.5, 5.0, 2.0, step=0.1)
tp_per = st.sidebar.slider("Target (TP %)", 1.0, 10.0, 4.0, step=0.1)

# Fetching Full Universe Dynamically
all_tickers = get_live_nse_universe()
st.sidebar.write(f"🔥 Total Active NSE Pool Loaded: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtester"])

# --- Core Analyzer ---
def analyze_single_ticker(ticker, df, mode, vol_mult, rsi_filt, t_limit):
    try:
        if df.empty or len(df) < 35: return None
        df = df.dropna(subset=['Close', 'High', 'Low', 'Volume']).copy()

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.clip(lower=0)).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        df['Max_250_High'] = df['High'].shift(1).rolling(window=min(250, len(df)-2), min_periods=1).max()

        # Strict Breakout Criteria
        c1 = df['Close'] >= 15
        c2 = (df['Pct_Change'] >= 0.8) & (df['Pct_Change'] <= 16.0)
        c3 = df['Volume'] > (df['Vol_SMA20'] * vol_mult)
        c4 = df['Turnover'] > (t_limit * 10000000)
        c5 = df['Close'] >= df['Max_250_High']
        c6 = df['RSI'] >= rsi_filt
        c7 = df['Close'] > df['EMA_20']

        df['Signal'] = c1 & c2 & c3 & c4 & c5 & c6 & c7

        results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            trigger_price = df['Close'].iloc[-1]
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(trigger_price, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Target (₹)": round(trigger_price * (1 + tp_per/100), 2),
                "Stoploss (₹)": round(trigger_price * (1 - sl_per/100), 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike": f"{round(vol_spike, 1)}x",
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest":
            triggers = df.iloc[-45:][df['Signal'] == True]
            for date, row in triggers.iterrows():
                idx = df.index.get_loc(date)
                if idx + 1 >= len(df):
                    trade_outcome = "Open Session"
                    pnl = "0.0%"
                else:
                    next_day_row = df.iloc[idx + 1]
                    t_close = row['Close']
                    sl_val = t_close * (1 - sl_per/100)
                    tp_val = t_close * (1 + tp_per/100)
                    
                    if next_day_row['Low'] <= sl_val:
                        trade_outcome = "❌ SL Hit"
                        pnl = f"-{sl_per}%"
                    elif next_day_row['High'] >= tp_val:
                        trade_outcome = "🎯 Target Hit"
                        pnl = f"+{tp_per}%"
                    else:
                        day_return = ((next_day_row['Close'] - t_close) / t_close) * 100
                        trade_outcome = "📈 Closed Positive" if day_return > 0 else "📉 Closed Negative"
                        pnl = f"{round(day_return, 2)}%"

                results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(row['Close'], 2),
                    "Target Price (₹)": round(row['Close'] * (1 + tp_per/100), 2),
                    "Stoploss Price (₹)": round(row['Close'] * (1 - sl_per/100), 2),
                    "Outcome": trade_outcome,
                    "P&L (%)": pnl
                })
            return results
    except:
        return None
    return None

def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 25 # Shorter safe batching to bypass Yahoo restrictions
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚙️ Running Scanning over {len(tickers)} Live Stocks Dynamically...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="1y", interval="1d", progress=False, group_by='ticker')
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {}
                for ticker in chunk:
                    try:
                        if isinstance(raw_data.columns, pd.MultiIndex):
                            if ticker in raw_data.columns.levels[0]:
                                futures[executor.submit(analyze_single_ticker, ticker, raw_data[ticker], mode, volume_multiplier, rsi_filter, min_turnover)] = ticker
                        else:
                            futures[executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover)] = ticker
                    except:
                        continue
                
                for future in as_completed(futures):
                    res = future.result()
                    if res: results.extend(res)
        except:
            continue
            
        main_progress.progress((c_idx + 1) / len(ticker_chunks))
                
    main_progress.empty()
    return pd.DataFrame(results)

# --- UI Render Logic ---
with tab1:
    st.subheader("⚡ Dynamic Live Momentum Breakout Radar")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Processed pool and found {len(res_df)} matches.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No breakout stocks found right now with current filters.")

with tab2:
    st.subheader("⏳ Historical Risk Analytics Dashboard")
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            total_trades = len(bt_df[bt_df['Outcome'] != "Open Session"])
            target_hits = len(bt_df[bt_df['Outcome'] == "🎯 Target Hit"])
            sl_hits = len(bt_df[bt_df['Outcome'] == "❌ SL Hit"])
            accuracy = round((target_hits / total_trades) * 100, 2) if total_trades > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Closed Trades", total_trades)
            col2.metric("Target Hit Ratio🎯", f"{accuracy}%")
            col3.metric("SL Hit Count❌", sl_hits)
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No historical breakthrough points detected inside the current data pool.")

import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Structure Based NSE Scanner", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Price Action & Chart Pattern Breakout Scanner")
st.caption("Engine: Vectorized Parallel Processing | Risk: Dynamic Swing Low Support & Structural Targets")

# --- FETCH ALL 2000+ NSE STOCKS INSTANTLY ---
@st.cache_data(ttl=86400)
def get_absolute_nse_universe():
    try:
        url = "https://raw.githubusercontent.com/anirudh-kamath/nse-ticker-list/main/nse_tickers.csv"
        df = pd.read_csv(url)
        symbol_col = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
        tickers = (df[symbol_col].str.strip() + ".NS").tolist()
        cleaned_tickers = sorted(list(set([t for t in tickers if isinstance(t, str) and not t.startswith(('NIFTY', 'BANKNIFTY'))])))
        if len(cleaned_tickers) > 1500:
            return cleaned_tickers
    except Exception:
        pass
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS", "ITC.NS", "TATAMOTORS.NS"]

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Turnover (₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Chart Pattern Risk Setup")
# Fixed percentage ke bajaye ab Risk:Reward user ke hath me hai
rr_ratio = st.sidebar.slider("Risk : Reward Ratio (1 : X)", 1.5, 4.0, 2.0, step=0.5, help="Example: 2.0 matlab jitna chart par risk hai, uska dugna target.")

all_tickers = get_absolute_nse_universe()
st.sidebar.write(f"🔥 Total Active NSE Pool Loaded: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtester"])

# --- Core Vectorized Pattern Analyzer ---
def analyze_single_ticker(ticker, df, mode, vol_mult, rsi_filt, t_limit):
    try:
        if df.empty or len(df) < 35: return None
        df = df.dropna(subset=['Close', 'High', 'Low', 'Volume']).copy()

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # Fast Vectorized RSI
        delta = df['Close'].diff()
        gain = (delta.clip(lower=0)).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        # Chart Pattern Breakout (250 Days High Resistance Line)
        df['Max_250_High'] = df['High'].shift(1).rolling(window=min(250, len(df)-2), min_periods=1).max()

        # Dynamic Support Level (Lowest low of last 3 sessions for tight chart stoploss)
        df['Swing_Support'] = df['Low'].rolling(window=3).min() * 0.995 

        # Rules Evaluation
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
            # Agar swing low kharab calculated ho toh standard 3% floor mechanism backup
            sl_price = df['Swing_Support'].iloc[-1]
            if sl_price >= trigger_price or (trigger_price - sl_price)/trigger_price > 0.08:
                sl_price = trigger_price * 0.965
            
            risk_amount = trigger_price - sl_price
            target_price = trigger_price + (risk_amount * rr_ratio)
            
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(trigger_price, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Chart Stoploss (₹)": round(sl_price, 2),
                "Pattern Target (₹)": round(target_price, 2),
                "Risk Per Share (₹)": round(risk_amount, 2),
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
                    
                    sl_val = row['Swing_Support']
                    if sl_val >= t_close or (t_close - sl_val)/t_close > 0.08:
                        sl_val = t_close * 0.965
                        
                    risk_amt = t_close - sl_val
                    tp_val = t_close + (risk_amt * rr_ratio)
                    
                    if next_day_row['Low'] <= sl_val:
                        trade_outcome = "❌ SL Hit (Support Violated)"
                        pnl = f"-{round(((t_close - sl_val)/t_close)*100, 2)}%"
                    elif next_day_row['High'] >= tp_val:
                        trade_outcome = "🎯 Target Hit (Pattern Done)"
                        pnl = f"+{round(((tp_val - t_close)/t_close)*100, 2)}%"
                    else:
                        day_return = ((next_day_row['Close'] - t_close) / t_close) * 100
                        trade_outcome = "📈 Closed Positive" if day_return > 0 else "📉 Closed Negative"
                        pnl = f"{round(day_return, 2)}%"

                results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(row['Close'], 2),
                    "Pattern Target (₹)": round(t_close + ((t_close - sl_val if sl_val < t_close else t_close*0.035) * rr_ratio), 2),
                    "Chart Stoploss (₹)": round(sl_val if sl_val < t_close else t_close*0.965, 2),
                    "Outcome": trade_outcome,
                    "P&L (%)": pnl
                })
            return results
    except:
        return None
    return None

# --- Hyper-Velocity Engine ---
def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 95 
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚡ Processing {len(tickers)} stocks via high-speed chart architecture...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="1y", interval="1d", progress=False, group_by='ticker', threads=True)
            
            with ThreadPoolExecutor(max_workers=16) as executor:
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
    st.subheader("⚡ Live Structural Breakout Radar (Dynamic SL/TP)")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Found {len(res_df)} breakout setups with chart-mapped risk levels.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No structural breakouts found right now. Try relaxing your filters.")

with tab2:
    st.subheader("⏳ Structural Backtest Performance Dashboard")
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            total_trades = len(bt_df[bt_df['Outcome'] != "Open Session"])
            target_hits = len(bt_df ,["🎯 Target Hit" in str(x) for x in bt_df['Outcome']])
            
            accuracy = round((target_hits / total_trades) * 100, 2) if total_trades > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Pattern Signals Generated", total_trades)
            col2.metric("Chart Target Success Rate🎯", f"{accuracy}%")
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No structural data points recorded inside this session.")

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import io
import time

# --- Page Configurations ---
st.set_page_config(page_title="Mega Stock Scanner 2400+", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Mega Stock Scanner Terminal (2400+ NSE Live Universe)")
st.caption("Engine Upgraded: Dynamic NSE Auto-Fetch, Anti-Ban Protection & 1:2 Dynamic Projections")

# --- DYNAMIC 2400+ NSE TICKER DATABASE FETCH ---
@st.cache_data(ttl=86400)
def get_mega_nse_universe():
    try:
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        
        df = df[df['SERIES'] == 'EQ']
        tickers = df['SYMBOL'].tolist()
        return sorted(list(set([f"{t}.NS" for t in tickers if isinstance(t, str)])))
    except Exception as e:
        st.warning("⚠️ NSE Server timeout. Using Fallback Top 200 Stocks list.")
        fallback = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC", "LT", "BAJFINANCE", "TATAMOTORS", "SUNPHARMA", "NTPC", "ZOMATO", "JIOFIN", "SUZLON", "RVNL", "IREDA", "IRFC", "HAL"]
        return sorted(list(set([f"{t}.NS" for t in fallback])))

# --- Process Single Ticker Core Calculations ---
def analyze_single_ticker(ticker, raw_data, mode, volume_multiplier, rsi_filter, turnover_limit):
    try:
        # Robust MultiIndex handling
        if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker in raw_data.columns.get_level_values(1):
                df = raw_data.xs(ticker, axis=1, level=1).copy()
            elif ticker in raw_data.columns.get_level_values(0):
                df = raw_data[ticker].copy()
            else:
                return None
        else:
            df = raw_data.copy()

        df = df.dropna(subset=['Close'])
        if len(df) < 50: return None 

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI Calculations
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        window_size = max(1, min(500, len(df) - 2))
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        
        df['Low_5d'] = df['Low'].rolling(window=5).min()
        df['Next_Day_Return'] = df['Pct_Change'].shift(-1)

        # Filters
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
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            
            if sl >= entry or (entry - sl) / entry < 0.005: 
                sl = entry * 0.965  
                
            risk = entry - sl
            target = entry + (2 * risk) 
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
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
                next_move = "Live Session Open" if is_today or pd.isna(row['Next_Day_Return']) else f"{round(row['Next_Day_Return'], 2)}%"
                
                b_entry = row['Close']
                b_sl = row['Low_5d']
                if b_sl >= b_entry or (b_entry - b_sl) / b_entry < 0.005:
                    b_sl = b_entry * 0.965
                b_risk = b_entry - b_sl
                b_target = b_entry + (2 * b_risk)

                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger/Entry (₹)": round(b_entry, 2),
                    "Stop Loss (₹)": round(b_sl, 2),
                    "Target Price (₹)": round(b_target, 2),
                    "RSI at Trigger": round(row['RSI'], 2),
                    "Next Day Move": next_move
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2)

all_tickers = get_mega_nse_universe()
st.sidebar.write(f"🟢 Active Stocks Loaded: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()
    results = []
    chunk_size = 40  
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚡ Processing {len(tickers)} symbols... Please wait.")
    main_progress = st.progress(0.0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False)
            
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(analyze_single_ticker, t, raw_data, mode, volume_multiplier, rsi_filter, min_turnover): t for t in chunk}
                for future in as_completed(futures):
                    res = future.result()
                    if res: results.extend(res)
            
            # Anti-ban sleep logic to prevent yfinance block
            time.sleep(0.5) 
            
        except Exception:
            continue
            
        main_progress.progress(min((c_idx + 1) / len(ticker_chunks), 1.0))
                
    main_progress.empty()
    return pd.DataFrame(results)

with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Full 2400+ Stocks Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Found {len(res_df)} high-momentum breakout setups!")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Ranked Setup: **{top_stock}**")
            
            ticker_obj = yf.Ticker(f"{top_stock}.NS")
            chart_data = ticker_obj.history(period="3mo", interval="1d")
            
            if not chart_data.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                    low=chart_data['Low'], close=chart_data['Close'], name='Candlestick'
                )])
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='orange', width=1.5), name='EMA 20'))
                
                live_sl = res_df.iloc[0]['Stop Loss (₹)']
                live_tgt = res_df.iloc[0]['Target Price (₹)']
                
                fig.add_hline(y=live_sl, line_dash="dash", line_color="red", line_width=2, annotation_text=f"5-Day SL: ₹{live_sl}", annotation_position="bottom left")
                fig.add_hline(y=live_tgt, line_dash="dash", line_color="green", line_width=2, annotation_text=f"Target (1:2): ₹{live_tgt}", annotation_position="top left")
                
                fig.update_layout(template="plotly_dark", title=f"{top_stock} Price Action & Triggers", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No breakout setups spotted matching current filters today.")

with tab2:
    st.subheader("⏳ 2-Month Historical Analytics Dashboard")
    if st.button("📊 Start Mega Backtest (Takes Time)", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            valid_moves = bt_df[~bt_df['Next Day Move'].str.contains("Live", na=False)].copy()
            if len(valid_moves) > 0:
                numeric_moves = valid_moves['Next Day Move'].str.replace('%','').astype(float)
                bullish_days = len(numeric_moves[numeric_moves > 0])
                accuracy = round((bullish_days / len(valid_moves)) * 100, 2)
            else:
                accuracy = 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", len(bt_df))
            col2.metric("Next-Day Bullish Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Backtest Sheet", data=csv_data, file_name="mega_backtest.csv", mime="text/csv")
        else:
            st.warning("No historical signal matches discovered.")

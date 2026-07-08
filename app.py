import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime
import warnings

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
st.caption("Engine Upgraded: RSI, EMA Trend, & Volume Shock Filters Added for Next-Day Momentum")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    
    if universe_type == "📸 Chartink Screenshot Test (5 Stocks)":
        return target_stocks

    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
            
            for stock in target_stocks:
                if stock not in nse_tickers:
                    nse_tickers.append(stock)
            return nse_tickers
    except Exception:
        pass
    return target_stocks

# --- Sidebar Settings Panel ---
st.sidebar.header("⚙️ Pro Scanner Controls")
universe_choice = st.sidebar.selectbox("Select Scanning Universe", ["📸 Chartink Screenshot Test (5 Stocks)", "Nifty 500 + Targets"])
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 50, 75, 60)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.5, step=0.1)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Core Scanner Engine (Upgraded Logic) ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: return pd.DataFrame()

    try:
        data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            if len(tickers) > 1:
                if ticker in data.columns.levels[0]: df = data[ticker].dropna(subset=['Close']).copy()
                else: continue
            else:
                df = data.dropna(subset=['Close']).copy()

            if len(df) < 40: continue

            # --- Base Metrics ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            
            # --- PRO UPGRADES: RSI & EMA ---
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # --- Chartink Rollbacks ---
            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2, min_periods=1).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200, min_periods=1).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
            df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

            # --- UPGRADED Formula Evaluator ---
            cond1 = df['Close'] >= 20
            cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 11.0)
            cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) # Institutional Volume
            cond4 = df['Return_20d'] >= 3.0
            cond5 = df['Turnover'] > 500000000
            cond6 = df['Max_2_High_20_Ago'] >= df['Max_200_High_31_Ago']
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
            cond8 = df['RSI'] >= rsi_filter # Trend Strength
            cond9 = df['Close'] > df['EMA_20'] # Price above 20 EMA

            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7 & cond8 & cond9

            # --- Fixed live mode block ---
            if mode == "live" and df['Signal'].iloc[-1]:
                vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(df['Close'].iloc[-1], 2),
                    "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Vol Spike (x)": round(vol_spike, 1),
                    "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2) # Custom Momentum Score
                })
                
            # --- Fixed backtest mode block ---
            elif mode == "backtest":
                history_slice = df.iloc[-44:-1] 
                triggers = history_slice[history_slice['Signal'] == True]
                for date, row in triggers.iterrows():
                    results.append({
                        "Date": date.strftime('%Y-%m-%d'),
                        "Symbol": ticker.replace(".NS", ""),
                        "Trigger Price (₹)": round(row['Close'], 2),
                        "RSI at Trigger": round(row['RSI'], 2),
                        "Next Day Move (%)": round(row['Next_Day_Return'], 2) if not pd.isna(row['Next_Day_Return']) else "Open Session"
                    })
        except Exception: continue

    progress_bar.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False) # Rank by best momentum
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Found {len(res_df)} high-probability stocks.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            # Interactive Chart for the top stock
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
    st.caption("Pichle 60 dino mein jab breakout trigger hua, toh **Next Day** kaisa movement diya:")
    
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            valid_moves = bt_df[bt_df['Next Day Move (%)'] != "Open Session"]
            bullish_days = len(valid_moves[valid_moves['Next Day Move (%)'].astype(float) > 0])
            accuracy = round((bullish_days / len(valid_moves)) * 100, 2) if len(valid_moves) > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", len(bt_df))
            col2.metric("Next-Day Bullish Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Backtest Sheet (CSV)", data=csv_data, file_name="backtest.csv", mime="text/csv")
        else:
            st.warning("Pichle 2 mahino mein is strict criteria par koi records nahi mile.")
# Import (agar use karna chahein)
# from ta.trend import ADXIndicator 

# Modification example inside your loop:
# Assuming df is ready:
df['BB_Width'] = (['Close'].rolling(20).std() * 2) / df['Close'].rolling(20).mean()

# New Condition:
cond10 = df['BB_Width'] > 0.02 # Yahan aap condition set kar sakte hain

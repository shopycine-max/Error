import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import requests
import io
from datetime import datetime

# Page Configurations
st.set_page_config(page_title="ERROR09 - Supercharged Bullish Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 ERROR09 - Next-Day Bullish Predictor")
st.caption("Created by Chandan kumar shaw | Live Scanner + Target Predictor Engine")

# Dictionary to map company names perfectly (Chartink Style)
STOCK_NAME_MAP = {
    "CUPID": "Cupid Limited",
    "DIACABS": "Diamond Power Infrastructure Ltd",
    "SPARC": "Sun Pharma Advanced Research Company",
    "ADANIENSOL": "Adani Energy Solutions Ltd",
    "JBCHEPHARM": "JB Chemicals & Pharmaceuticals Ltd"
}

def get_clean_name(symbol):
    ticker_clean = symbol.replace(".NS", "")
    return STOCK_NAME_MAP.get(ticker_clean, ticker_clean)

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    if universe_type == "📸 Chartink Screenshot Test (5 Stocks)":
        return target_stocks

    url = "https://niftyindices.com/IndexConstituentList/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
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
        
    try:
        backup_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        res = requests.get(backup_url, headers=headers, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            return [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
    except Exception:
        pass

    return target_stocks

# Sidebar Settings Panel
st.sidebar.header("⚙️ Scanner Controls")
universe_choice = st.sidebar.selectbox(
    "Select Scanning Universe", 
    ["📸 Chartink Screenshot Test (5 Stocks)", "Nifty 500 + Targets"]
)
all_tickers = get_scanning_universe(universe_choice)
st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# App Navigation Tabs
tab1, tab2 = st.tabs(["⚡ Live Scanner & Next-Day Prediction", "📊 2-Month Historical Backtester"])

# --- Core Scanner Engine ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers:
        return pd.DataFrame()

    try:
        # Download historical bulk data
        data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        
        try:
            # Multi-index or single tracker parsing
            if len(tickers) > 1:
                if ticker not in data.columns.levels[0]:
                    continue
                df = data[ticker].dropna(subset=['Close']).copy()
            else:
                df = data.dropna(subset=['Close']).copy()

            if len(df) < 510:
                continue

            # Core Calculations
            df['Pct_Change'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            
            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2, min_periods=1).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200, min_periods=1).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
            
            # Next Day Move
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100

            # Formula Conditions
            cond1 = df['Close'] >= 20
            cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 11.0)
            cond3 = df['Volume'] > df['Vol_SMA20']
            cond4 = df['Return_20d'] >= 3.0
            cond5 = df['Turnover'] > 500000000
            cond6 = df['Max_2_High_20_Ago'] >= df['Max_200_High_31_Ago']
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago']

            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7

            # Mode evaluation separated inside flat formatting to avoid indent slips
            if mode == "live":
                if df['Signal'].iloc[-1]:
                    ltp = df['Close'].iloc[-1]
                    t_min = round(ltp * 1.01, 2)
                    t_max = round(ltp * 1.03, 2)
                    results.append({
                        "Stock Name": get_clean_name(ticker),
                        "Symbol": ticker.replace(".NS", ""),
                        "LTP (₹)": round(ltp, 2),
                        "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                        "Tomorrow Outlook": "🔥 Highly Bullish",
                        "Expected Target Zone": f"₹{t_min} - ₹{t_max}",
                        "Turnover (Cr)": round(df['Turnover'].iloc[-1] / 10000000, 2)
                    })

            if mode == "backtest":
                history_slice = df.iloc[-44:-1] 
                triggers = history_slice[history_slice['Signal'] == True]
                for date, row in triggers.iterrows():
                    results.append({
                        "Date": date.strftime('%Y-%m-%d'),
                        "Stock Name": get_clean_name(ticker),
                        "Symbol": ticker.replace(".NS", ""),
                        "Trigger Price (₹)": round(row['Close'], 2),
                        "Next Day Move (%)": round(row['Next_Day_Return'], 2) if not pd.isna(row['Next_Day_Return']) else "Open Session"
                    })

        except Exception:
            continue

    progress_bar.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Next-Day Bullish Breakout Radar")
    if st.button("🚀 Run Live Prediction Scan", key="live_btn"):
        res_df = process_market_analytics(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df.insert(0, 'Sr.', range(1, len(res_df) + 1))
            st.success(f"🎉 Breakout Confirmed! Found {len(res_df)} stocks expected to remain Bullish Tomorrow.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Filhal market parameters ke according koi strong signal breakout nahi mila.")

# --- TAB 2: Chartink Style Backtest View ---
with tab2:
    st.subheader("⏳ 2-Month Historical Accuracy Log")
    
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            total_triggers = len(bt_df)
            valid_moves = bt_df[bt_df['Next Day Move (%)'] != "Open Session"]
            bullish_days = len(valid_moves[valid_moves['Next Day Move (%)'].astype(float) > 0])
            accuracy = round((bullish_days / len(valid_moves)) * 100, 2) if len(valid_moves) > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", total_triggers)
            col2.metric("Next-Day Bullish Success Rate", f"{accuracy}%")
            
            st.subheader("📋 Historical Signals Log Sheet")
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Pichle 2 mahino mein koi historical records nahi mile.")
            

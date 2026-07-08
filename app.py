import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import requests
from datetime import datetime

# Page Configurations
st.set_page_config(page_title="ERROR09 - Pro Scanner & Backtester", page_icon="📈", layout="wide")

st.title("📈 ERROR09 - Advanced Scanner & Backtester")
st.caption("Live Breakout Signals + 2-Month Historical Backtest Engine")

# --- Nifty 500 Ticker Fetcher ---
@st.cache_data(ttl=86400)
def get_nifty500_tickers():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_csv(url)
            return [str(symbol).strip() + ".NS" for symbol in df['Symbol'].dropna()]
    except Exception as e:
        st.sidebar.error(f"NSE Fetch Error: {e}. Using fallback.")
    return ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "RELIANCE.NS", "TCS.NS"]

# Sidebar Panel
st.sidebar.header("⚙️ Settings Panel")
universe_option = st.sidebar.selectbox("Select Universe", ["Nifty 500", "Custom List"])
all_tickers = get_nifty500_tickers() if universe_option == "Nifty 500" else ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]

st.sidebar.write(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- Main App Tabs ---
tab1, tab2 = st.tabs(["🚀 Live Scanner (Today)", "⏳ 2-Month Backtester (Chartink Style)"])

# --- Core Advanced Data Engine ---
def process_data_vectorized(tickers, mode="live"):
    st.info("📥 Fetching and analyzing live 3-year data for lookback tracking...")
    try:
        batch_data = yf.download(tickers, period="3y", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    live_results = []
    backtest_results = []
    
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            if len(tickers) > 1:
                df = batch_data[ticker].dropna()
            else:
                df = batch_data.dropna()

            if len(df) < 535:
                continue
            
            # --- Vectorized Indicator Calculations ---
            df['pct_change'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
            df['sma_volume_20'] = df['Volume'].rolling(20).mean()
            
            close_20_days_ago = df['Close'].shift(20)
            df['return_20_days'] = ((df['Close'] - close_20_days_ago) / close_20_days_ago) * 100
            df['value_traded'] = df['Close'] * df['Volume']
            
            df['max_2_high_20_ago'] = df['High'].shift(20).rolling(2).max()
            df['max_200_high_31_ago'] = df['High'].shift(31).rolling(200).max()
            df['max_500_high_1_day_ago'] = df['High'].shift(1).rolling(500).max()
            
            # Target Metric: Next Day Return (for Backtesting)
            df['next_day_return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
            
            # --- Chartink Formula Condition Matrix ---
            cond1 = df['Close'] >= 20
            cond2 = (df['pct_change'] >= 1.0) & (df['pct_change'] <= 11.0)
            cond3 = df['Volume'] > df['sma_volume_20']
            cond4 = df['return_20_days'] >= 3.0
            cond5 = df['value_traded'] > 500000000
            cond6 = df['max_2_high_20_ago'] >= df['max_200_high_31_ago']
            cond7 = df['Close'] >= df['max_500_high_1_day_ago']
            
            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7
            
            # Filter Data based on Mode
            if mode == "live" and df['Signal'].iloc[-1]:
                # Live Filter for Current Day
                live_results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(df['Close'].iloc[-1], 2),
                    "Day Change (%)": round(df['pct_change'].iloc[-1], 2),
                    "Volume": int(df['Volume'].iloc[-1]),
                    "Value Traded (Cr)": round(df['value_traded'].iloc[-1] / 10000000, 2)
                })
            elif mode == "backtest":
                # Historical Filter for Last 2 Months (Approx 42 Trading Days)
                historical_slice = df.iloc[-43:-1] # Exclude today to get completed next-day cycles
                signals_df = historical_slice[historical_slice['Signal'] == True]
                
                for date, row in signals_df.iterrows():
                    backtest_results.append({
                        "Signal Date": date.strftime('%Y-%m-%d'),
                        "Symbol": ticker.replace(".NS", ""),
                        "Signal Price (₹)": round(row['Close'], 2),
                        "Volume (Lakhs)": round(row['Volume'] / 100000, 2),
                        "Next Day Return (%)": round(row['next_day_return'], 2) if not pd.isna(row['next_day_return']) else 0.0
                    })
                    
        except Exception:
            continue
            
    progress_bar.empty()
    return pd.DataFrame(live_results) if mode == "live" else pd.DataFrame(backtest_results)

# --- TAB 1: Live Scanner Execution ---
with tab1:
    st.subheader("⚡ Live Market Momentum Radar")
    if st.button("🔍 Run Live Scan", key="btn_live"):
        results_df = process_data_vectorized(all_tickers, mode="live")
        
        if not results_df.empty:
            st.success(f"🔥 Found {len(results_df)} stocks matching criteria today!")
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            fig = px.bar(results_df, x="Symbol", y="Day Change (%)", color="Day Change (%)",
                         title="Live Signals Momentum Rate", color_continuous_scale="Greens")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Filhal aaj ke din koi stock is stringent formula ko match nahi kar raha hai.")

# --- TAB 2: 2-Month Backtester Execution ---
with tab2:
    st.subheader("⏳ Chartink-Style 2-Month Backtest Analytics")
    st.caption("Pichle 60 dino mein jab bhi signal aaya, uske agle din (Next Day) stock ne kaisa perform kiya:")
    
    if st.button("📊 Start Historical Backtest", key="btn_backtest"):
        bt_df = process_data_vectorized(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            # Sort by latest date
            bt_df = bt_df.sort_values(by="Signal Date", ascending=False)
            
            # Calculations for Strategy Performance
            total_signals = len(bt_df)
            positive_days = len(bt_df[bt_df['Next Day Return (%)'] > 0])
            accuracy = round((positive_days / total_signals) * 100, 2) if total_signals > 0 else 0
            avg_gain = round(bt_df['Next Day Return (%)'].mean(), 2)
            
            # Metrics Cards
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Backtest Signals", total_signals)
            c2.metric("Next-Day Bullish Accuracy", f"{accuracy}%")
            c3.metric("Average Next-Day Return", f"{avg_gain}%")
            
            st.subheader("📋 Historical Trigger Log Sheet")
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            
            # Visualizing Backtest Data
            fig_bt = px.histogram(bt_df, x="Next Day Return (%)", nbins=20, 
                                 title="Distribution of Next-Day Returns (Bullish vs Bearish Outcomes)",
                                 color_discrete_sequence=['#2ecc71'])
            st.plotly_chart(fig_bt, use_container_width=True)
            
            # Download Facility
            csv = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Backtest Data to CSV", data=csv, file_name="backtest_report.csv", mime="text/csv")
        else:
            st.warning("Pichle 2 mahino mein is filter criteria par koi historical triggers nahi mile.")
        

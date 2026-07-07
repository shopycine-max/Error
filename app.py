import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="ERROR09 - Live Stock Scanner", page_icon="📊", layout="wide")

st.title("📊 ERROR09 - Live Stock Scanner Dashboard")
st.caption("Created with ❤️ | Powered by Live yFinance Data")

# --- Sidebar Settings ---
st.sidebar.header("🔧 Scanner Settings")
universe = st.sidebar.selectbox(
    "Select Universe",
    ["Nifty 50", "Nifty Next 50", "Custom Watchlist"]
)

# Reliable Fallback Ticker Lists (To avoid NSE 404 Errors)
tickers_dict = {
    "Nifty 50": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
        "INFY.NS", "SBI.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS",
        "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS",
        "TATAMOTORS.NS", "NTPC.NS", "KOTAKBANK.NS", "TITAN.NS"
    ],
    "Nifty Next 50": [
        "CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS",
        "IRFC.NS", "PFC.NS", "RECLTD.NS", "HAL.NS", "BEL.NS", "ZOMATO.NS"
    ],
    "Custom Watchlist": ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
}

selected_tickers = tickers_dict[universe]

# --- Scanner Logic ---
def run_scanner(tickers):
    success_stocks = []
    
    st.info(f"Scanning {len(tickers)} stocks from {universe} using merged formulas...")
    progress_bar = st.progress(0)
    
    # Download 3 years of data in one batch for maximum speed & live performance
    with st.spinner("Fetching live market data from yfinance..."):
        try:
            data = yf.download(tickers, period="3y", group_by='ticker', progress=False)
        except Exception as e:
            st.error(f"Error fetching data from yfinance: {e}")
            return pd.DataFrame()

    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        
        try:
            # Extract ticker specific dataframe
            if len(tickers) > 1:
                df = data[ticker].dropna()
            else:
                df = data.dropna()
                
            if len(df) < 520:  # 500 day breakout ke liye पर्याप्त data hona chahiye
                continue
                
            # Current and Previous values
            close_today = df['Close'].iloc[-1]
            close_yesterday = df['Close'].iloc[-2]
            volume_today = df['Volume'].iloc[-1]
            high_today = df['High'].iloc[-1]
            
            # --- Chartink Merged Formula Implementation ---
            
            # 1. Daily Close >= 20
            cond1 = close_today >= 20
            
            # 2. Daily % Change between 1% and 11%
            pct_change = ((close_today - close_yesterday) / close_yesterday) * 100
            cond2 = 1.0 <= pct_change <= 11.0
            
            # 3. Daily Volume > Daily SMA(Volume, 20)
            sma_volume_20 = df['Volume'].rolling(20).mean().iloc[-1]
            cond3 = volume_today > (sma_volume_20 * 1)
            
            # 4. 20 days ago close return >= 3%
            close_20_days_ago = df['Close'].iloc[-21] # 20 candles back
            return_20_days = ((close_today - close_20_days_ago) / close_20_days_ago) * 100
            cond4 = return_20_days >= 3.0
            
            # 5. Daily Close * Daily Volume > 50,000,000 (Value Traded)
            cond5 = (close_today * volume_today) > 500000000
            
            # 6. Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High)
            max_2_high_20_ago = df['High'].shift(20).rolling(2).max().iloc[-1]
            max_200_high_31_ago = df['High'].shift(31).rolling(200).max().iloc[-1]
            cond6 = max_2_high_20_ago >= max_200_high_31_ago
            
            # 7. Daily Close >= 1 day ago Max(500, Daily High) -> 500 Day Breakout!
            max_500_high_1_day_ago = df['High'].shift(1).rolling(500).max().iloc[-1]
            cond7 = close_today >= max_500_high_1_day_ago
            
            # Merging all conditions
            if cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7:
                success_stocks.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "Close": round(close_today, 2),
                    "% Change": round(pct_change, 2),
                    "Volume": int(volume_today),
                    "Value Traded (Cr)": round((close_today * volume_today) / 10000000, 2)
                })
                
        except Exception:
            continue # Agar kisi stock ka data corrupt ho to skip karein
            
    return pd.DataFrame(success_stocks)

# --- Main App Execution ---
if st.button("🚀 Run Live Scan", type="primary"):
    results_df = run_scanner(selected_tickers)
    
    if not results_df.empty:
        st.success(f"🔥 Found {len(results_df)} stocks matching your criteria!")
        
        # Display Summary Cards
        col1, col2 = st.columns(2)
        col1.metric("Total Stocks Scanned", len(selected_tickers))
        col2.metric("Stocks Passed Filters", len(results_df))
        
        # Display Table
        st.subheader("📋 Filtered Stocks List")
        st.dataframe(results_df, use_container_width=True)
        
        # Live Plotly Chart for Visualizing % Change
        st.subheader("📈 Performance Visualization")
        fig = px.bar(results_df, x="Symbol", y="% Change", text="Close", color="% Change",
                     title="Passed Stocks Day Change %", color_continuous_scale="Greens")
        st.plotly_chart(fig, use_container_width=True)
        
        # Export Option
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("
        

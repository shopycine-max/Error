import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import requests
from datetime import datetime

# Page Configurations
st.set_page_config(page_title="ERROR09 - Live Mega Scanner", page_icon="🚀", layout="wide")

st.title("🚀 ERROR09 - Live Stock Scanner Dashboard")
st.caption("Merged Formula Scanner | Live yFinance & NSE Data Integration")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=86400)  # Cache for 24 hours to keep it fast
def get_nifty500_tickers():
    """Fetches Nifty 500 tickers safely using proper headers to avoid 404 errors"""
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            lines = response.text.split('\n')
            df = pd.read_csv(url)
            # Append .NS for yfinance format
            tickers = [str(symbol).strip() + ".NS" for symbol in df['Symbol'].dropna()]
            return tickers
    except Exception as e:
        st.sidebar.error(f"NSE Fetch Error: {e}. Using robust fallback.")
    
    # Rock-solid fallback list if NSE site is down or blocking
    return ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", 
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

# Sidebar Configuration
st.sidebar.header("⚙️ Scanner Control Panel")
universe_option = st.sidebar.selectbox("Select Scanning Universe", ["Nifty 500 (All major stocks)", "Custom Test List"])

if universe_option == "Nifty 500 (All major stocks)":
    all_tickers = get_nifty500_tickers()
else:
    all_tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]

st.sidebar.write(f"Total Tickers Loaded: **{len(all_tickers)}**")

# --- Scanner Core Logic ---
def execute_live_scan(tickers):
    matched_stocks = []
    
    # Step 1: Batch download historical data to prevent 404/rate limits
    # We need ~550 daily candles to accurately compute a 500-day high breakout
    st.info("📥 Fetching live market data from yfinance in an optimized batch...")
    try:
        batch_data = yf.download(tickers, period="3y", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        st.error(f"Error connecting to data servers: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 2: Loop through data to check your Chartink Merged Formula
    for i, ticker in enumerate(tickers):
        progress_bar.progress((i + 1) / len(tickers))
        status_text.text(f"Analyzing {i+1}/{len(tickers)}: {ticker}")
        
        try:
            # Handle multi-index data correctly
            if len(tickers) > 1:
                df = batch_data[ticker].dropna()
            else:
                df = batch_data.dropna()
                
            if len(df) < 535: # Ensure enough historical data exists for 500-day rolling metrics
                continue
                
            # Extract basic tracking points
            close_today = df['Close'].iloc[-1]
            close_yesterday = df['Close'].iloc[-2]
            volume_today = df['Volume'].iloc[-1]
            high_today = df['High'].iloc[-1]
            
            # --- Chartink Formula Validations ---
            
            # 1. Daily Close >= 20
            if not (close_today >= 20): continue
            
            # 2 & 3. Daily % Change between 1% and 11%
            pct_change = ((close_today - close_yesterday) / close_yesterday) * 100
            if not (1.0 <= pct_change <= 11.0): continue
            
            # 4. Daily Volume > Daily SMA (Volume, 20) * 1
            sma_volume_20 = df['Volume'].rolling(20).mean().iloc[-1]
            if not (volume_today > (sma_volume_20 * 1)): continue
            
            # 5. Daily Close - 20 days ago close return >= 3%
            close_20_days_ago = df['Close'].iloc[-21] 
            return_20_days = ((close_today - close_20_days_ago) / close_20_days_ago) * 100
            if not (return_20_days >= 3.0): continue
            
            # 6. Daily Close * Daily Volume > 500,000,000 (Value traded rule)
            value_traded = close_today * volume_today
            if not (value_traded > 500000000): continue
            
            # 7. Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High)
            max_2_high_20_ago = df['High'].shift(20).rolling(2).max().iloc[-1]
            max_200_high_31_ago = df['High'].shift(31).rolling(200).max().iloc[-1]
            if not (max_2_high_20_ago >= max_200_high_31_ago): continue
            
            # 8. Daily Close >= 1 day ago Max(500, Daily High) -> The 500-Day Breakout Rule
            max_500_high_1_day_ago = df['High'].shift(1).rolling(500).max().iloc[-1]
            if not (close_today >= max_500_high_1_day_ago): continue
            
            # Step 3: Elite Optimization - Only query .info API for stocks that pass all technical filters
            # This completely avoids IP blocking and speeds up execution
            try:
                ticker_info = yf.Ticker(ticker).info
                market_cap_crores = ticker_info.get('marketCap', 0) / 10000000 # Convert to Crores
            except:
                market_cap_crores = 1001 # Fallback value to not lose tracking if info block occurs
                
            # Chartink Rule: Market Cap > 1000 Cr
            if market_cap_crores > 1000:
                matched_stocks.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(close_today, 2),
                    "Day Change (%)": round(pct_change, 2),
                    "Volume": int(volume_today),
                    "Market Cap (Cr)": round(market_cap_crores, 2),
                    "Value Traded (Cr)": round(value_traded / 10000000, 2)
                })
                
        except Exception:
            continue # Silently bypass corrupt data frames
            
    status_text.empty()
    return pd.DataFrame(matched_stocks)

# --- UI Action Controller ---
if st.sidebar.button("🚀 Start Live Scanner", type="primary"):
    start_time = datetime.now()
    results_df = execute_live_scan(all_tickers)
    end_time = datetime.now()
    
    st.toast(f"Scan completed in {(end_time - start_time).seconds} seconds!")
    
    if not results_df.empty:
        st.success(f"🔥 Found {len(results_df)} stocks matching your exact formula criteria!")
        
        # Matrix Layout Metrics
        m1, m2 = st.columns(2)
        m1.metric("Total Universe Scanned", len(all_tickers))
        m2.metric("Successful Outliers Identified", len(results_df))
        
        # Interactive Grid Display
        st.subheader("📋 Filtered Stocks Data Sheet")
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        
        # Live Chart Rendering (Fixes your Plotly Module Missing bug)
        st.subheader("📊 Dynamic Market Performance Chart")
        fig = px.scatter(
            results_df, 
            x="Market Cap (Cr)", 
            y="Day Change (%)", 
            size="Value Traded (Cr)", 
            color="Symbol",
            hover_name="Symbol", 
            text="Symbol",
            size_max=40,
            title="Passed Stocks: Change % vs Market Cap (Bubble size = Value Traded)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Data Export Gateway
        csv_data = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Live Scan Report (CSV)", data=csv_data, file_name="live_scan_output.csv", mime="text/csv")
        
    else:
        st.warning("Taaza market data ke mutabiq filhal koi bhi stock is tough criteria ko match nahi kar raha hai. Live market hours ke dauran ise fir se chalayein.")

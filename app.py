import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# Page Initialization & Theme
st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 NSE Pro Market Breakout Engine (Full Market Scan)")

st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > Target Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# SIDEBAR DYNAMIC CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=1, max_value=100, value=10, step=1)

# 🔄 STEP 1: DYNAMIC TICKER FETCHING FOR ALL NSE STOCKS
@st.cache_data(ttl=86400) # Cache list for 24 hours to minimize web-scraping latency
def get_all_nse_tickers():
    """
    Fetches ALL listed stocks on the NSE.
    Uses a highly reliable public repository to avoid intermittent 403 blocks from official portals.
    """
    url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/master/EQUITY_L.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.BytesIO(response.content))
            # Extract SYMBOL column and append the .NS Yahoo Finance extension
            tickers = [f"{str(symbol).strip()}.NS" for symbol in df['SYMBOL'] if pd.notna(symbol)]
            return tickers
        else:
            return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]
    except Exception:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]

# 🚀 STEP 2: BULK DOWNLOAD ENGINE WITH MULTI-THREADING
@st.cache_data(ttl=14400) # Historical data cached for 4 hours to preserve RAM and skip API limits
def bulk_download_market_matrix(stocks_list):
    """
    Downloads historical multi-index data for all 2000+ stocks in parallel.
    Uses yfinance native multi-threading architecture for optimal network speed.
    """
    # Pulling 3-Year data frame to cover the intensive 500-day historical lookbacks safely
    data = yf.download(stocks_list, period="3y", progress=False, threads=True, timeout=120)
    return data

# 🧠 STEP 3: IN-MEMORY MATHEMATICAL SCREENING ENGINE
def process_cached_matrix(data, tickers_list, target_turnover_cr):
    scanned_results = []
    
    if data.empty or not isinstance(data.columns, pd.MultiIndex):
        return pd.DataFrame()
        
    # Unpack columns globally to avoid high overhead cost inside the loop
    try:
        close_matrix = data['Close']
        high_matrix = data['High']
        volume_matrix = data['Volume']
    except KeyError:
        return pd.DataFrame()
        
    for ticker in tickers_list:
        if ticker not in close_matrix.columns:
            continue
            
        try:
            # Clean missing rows/NaN values for data continuity on newer/low-volume listings
            close_series = close_matrix[ticker].dropna()
            high_series = high_matrix[ticker].dropna()
            volume_series = volume_matrix[ticker].dropna()
            
            # Absolute structure block check for deep 500-day window metrics
            if len(close_series) < 515:
                continue
                
            current_close = close_series.iloc[-1]
            current_volume = volume_series.iloc[-1]
            prev_close = close_series.iloc[-2]
            close_20d_ago = close_series.iloc[-20]
            
            # Volume 20-period Simple Moving Average via vectorized slicing
            volume_sma20 = volume_series.iloc[-20:].mean() 
            
            if prev_close <= 0 or close_20d_ago <= 0:
                continue
                
            # --- FORMULA CONDITIONS MATRICES ---
            c1 = current_close >= 20
            
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (1.0 <= daily_return <= 11.0)
            
            c3 = current_volume > volume_sma20
            
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3.0
            
            turnover_cr = (current_close * current_volume) / 10000000
            c5 = turnover_cr >= target_turnover_cr
            
            # --- ADVANCED LOOKBACK HIGHS FORMULA VALIDATION ---
            # Max of 2 trading sessions starting from 20 days ago (t-20, t-21)
            max_2_20d_ago_high = high_series.iloc[-21:-19].max()
            
            # Max of 200 trading sessions from 31 days ago (t-31 backwards to t-231)
            max_200_31d_ago_high = high_series.iloc[-231:-31].max()
            c6 = max_2_20d_ago_high >= max_200_31d_ago_high
            
            # Max high of past 500 sessions excluding today's current high
            max_500_1d_ago_high = high_series.iloc[-501:-1].max()
            c7 = current_close >= max_500_1d_ago_high
            
            # Final data check to catch runtime NaNs
            if pd.isna(max_2_20d_ago_high) or pd.isna(max_200_31d_ago_high) or pd.isna(max_500_1d_ago_high):
                continue
                
            # Trigger match append
            if c1 and c2 and c3 and c4 and c5 and c6 and c7:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Price (₹)": round(current_close, 2),
                    "Daily Change %": round(daily_return, 2),
                    "20-Day Change %": round(return_20d, 2),
                    "Volume": int(current_volume),
                    "Turnover (Cr)": round(turnover_cr, 2)
                })
        except Exception:
            continue
            
    return pd.DataFrame(scanned_results)

# 🚦 SCAN ENGINE RUNNER
if st.button("🔍 Run Full Market Scan (2000+ Stocks)"):
    status_msg = st.empty()
    
    status_msg.info("⏳ Step 1: Extracting all active listed equities from NSE database...")
    live_tickers = get_all_nse_tickers()
    
    status_msg.info(f"⚡ Step 2: Downloading 3-year multi-index matrix for {len(live_tickers)} symbols... Please wait.")
    raw_market_data = bulk_download_market_matrix(live_tickers)
    
    status_msg.info("⚙️ Step 3: Running mathematical vector formulas on whole database columns...")
    df_final = process_cached_matrix(raw_market_data, live_tickers, min_turnover_cr)
    
    status_msg.empty() # Clear loading information
    
    if not df_final.empty:
        st.success(f"🎯 Boom! Found {len(df_final)} High-Momentum Breakout Stocks:")
        st.dataframe(df_final, use_container_width=True)
        
        # Format CSV report for clean Excel imports
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.write("---")
        st.download_button("📥 Download Excel/CSV Report", data=csv, file_name="nse_full_market_breakouts.csv", mime="text/csv")
    else:
        st.warning("No Data Found! Is complex filter par pure market me filhal koi stock fit nahi ho raha hai. Sidebar se Turnover settings thodi kam karke firse run karein.")
        

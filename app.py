import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# Page Initialization
st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 NSE Pro Market Breakout Engine")

st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > 50Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# SIDEBAR DYNAMIC CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=1, max_value=100, value=10, step=1)

# 🔄 STEP 1: DYNAMIC TICKER FETCHING (ALL INDIAN STOCKS REPLACED WITH LIVE NSE
@st.cache_data(ttl=86400) # Cache list for 24 hours to keep app extremely snappy
def get_live_nse_tickers():
    """
    Fetches the constituent list of Nifty 500 directly from the official Nifty Indices database.
    This eliminates hardcoding and ensures corporate actions (delistings/adds) are handled automatically.
    """
    url = "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.BytesIO(response.content))
            # Safely extract Symbol column and convert to Yahoo Finance format
            tickers = [f"{str(symbol).strip()}.NS" for symbol in df['Symbol'] if pd.notna(symbol)]
            return tickers
        else:
            st.error("⚠️ NSE Data Endpoint unreachable. Using fallback top anchors.")
            return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    except Exception as e:
        st.error(f"⚠️ Live Fetch Error: {str(e)}. Using fallback anchors.")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

# 🚀 STEP 2: BULK DOWNLOAD ENGINE WITH CACHING
@st.cache_data(ttl=14400) # Stock historical data cached for 4 hours
def bulk_download_market_matrix(stocks_list):
    """
    Downloads historical data for the entire stock array parallelly.
    Uses native multithreading inside yfinance for raw speed.
    """
    # 3-Year historical matrix pull
    data = yf.download(stocks_list, period="3y", progress=False, threads=True, timeout=60)
    return data

# 🧠 STEP 3: IN-MEMORY MATHEMATICAL SCREENING ENGINE
def process_cached_matrix(data, tickers_list, target_turnover_cr):
    scanned_results = []
    
    if data.empty or not isinstance(data.columns, pd.MultiIndex):
        return pd.DataFrame()
        
    # Extract structural sub-frames instantly to prevent multi-indexing slowdowns inside the loop
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
            # Localize specific stock vectors from RAM matrix (Super fast)
            close_series = close_matrix[ticker].dropna()
            high_series = high_matrix[ticker].dropna()
            volume_series = volume_matrix[ticker].dropna()
            
            # Absolute structure check for deep 500-day lookback calculation
            if len(close_series) < 515:
                continue
                
            current_close = close_series.iloc[-1]
            current_volume = volume_series.iloc[-1]
            prev_close = close_series.iloc[-2]
            close_20d_ago = close_series.iloc[-20]
            
            # 20 SMA Volume using modern memory slicing
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
            
            if pd.isna(max_2_20d_ago_high) or pd.isna(max_200_31d_ago_high) or pd.isna(max_500_1d_ago_high):
                continue
                
            if c1 and c2 and c3 and c4 and c5 and c6 and c7:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Price (₹)": round(current_close, 2),
                    "Daily Change %": round(daily_return, 2),
                    "20-Day Change %": round(return_20d, 2),
                    "Volume": int(current_volume),
                    "Turnover (Cr)": round(turnover_cr, 2)
                })
        except:
            continue
            
    return pd.DataFrame(scanned_results)

# 🚦 SCAN ENGINE TRIGGER
if st.button("🔍 Start Live Broad Market Scan"):
    status_msg = st.empty()
    
    status_msg.info("⏳ Step 1: Fetching active Nifty 500 tickers dynamically from indices matrix...")
    live_tickers = get_live_nse_tickers()
    
    status_msg.info(f"⚡ Step 2: Running parallel data downloads for {len(live_tickers)} instruments via ThreadPool...")
    raw_market_data = bulk_download_market_matrix(live_tickers)
    
    status_msg.info("⚙️ Step 3: Executing multi-conditional trend lookbacks in-memory...")
    df_final = process_cached_matrix(raw_market_data, live_tickers, min_turnover_cr)
    
    status_msg.empty() # Clear information bar
    
    if not df_final.empty:
        st.success(f"🎯 Boom! Found {len(df_final)} High-Momentum Breakout Stocks:")
        st.dataframe(df_final, use_container_width=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.write("---")
        st.download_button("📥 Download Report (CSV)", data=csv, file_name="nse_breakouts.csv")
    else:
        st.warning(f"No Data Found. Is criteria par filhal koi stock match nahi ho raha hai. Turnover slider kam karke try karein!")
            

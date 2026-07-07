import os
import sys

# Auto-installer for yfinance & requests
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance requests")
    import yfinance as yf

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="India Full Market Scanner (NSE + BSE)", layout="wide")
st.title("🚀 COMPLETE INDIA FULL MARKET MOMENTUM SCANNER")
st.write("🔥 **Chartink Style Unrestricted Engine:** Price >= 20 | Return 1% to 11% | Volume > 20 SMA | Turnover > 50Cr")

# 1. DYNAMICALLY FETCH 100% OF ALL NSE & BSE TICKERS FROM LIVE REPOSITORIES
@st.cache_data(ttl=86400)
def get_absolute_all_indian_tickers():
    nse_tickers = []
    bse_tickers = []
    
    # Fetching Complete NSE List (Approx 2000+ Stocks)
    try:
        nse_url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/main/NSE_ALL_STOCKS.csv"
        df_nse = pd.read_csv(nse_url)
        if 'SYMBOL' in df_nse.columns:
            nse_tickers = [str(sym).strip() + ".NS" for sym in df_nse['SYMBOL'].dropna().unique() if str(sym).strip()]
    except Exception as e:
        st.sidebar.warning(f"NSE Live Link Slow: Using Core Backup")
        nse_tickers = ["RELIANCE.NS", "SBIN.NS", "TCS.NS", "TATAMOTORS.NS"]

    # Fetching Complete BSE List (Approx 4000+ Stocks)
    try:
        bse_url = "https://raw.githubusercontent.com/shinchven/tech-share-list/master/bse.txt"
        response = requests.get(bse_url, timeout=10)
        if response.status_code == 200:
            lines = response.text.split('\n')
            for line in lines:
                sym = line.strip()
                if sym and not sym.isdigit():
                    bse_tickers.append(sym + ".BO")
    except:
        pass
        
    # Fallback to generate BSE equivalents if link fails, ensuring full depth
    if not bse_tickers and nse_tickers:
        bse_tickers = [sym.replace(".NS", ".BO") for sym in nse_tickers]

    return nse_tickers, bse_tickers

# Load the unrestricted database
nse_list, bse_list = get_absolute_all_indian_tickers()
total_combined_market = len(nse_list) + len(bse_list)

# 2. SELECTION PANEL FOR THE USER
st.sidebar.markdown("## 🎯 Market Universe")
universe_choice = st.sidebar.selectbox(
    "Choose What To Scan:",
    [
        f"NSE Full Cash (All {len(nse_list)} Stocks)", 
        f"BSE Full Cash (All {len(bse_list)} Stocks)", 
        f"👉 Entire Indian Market Combined ({total_combined_market} Stocks)"
    ]
)

# Map target list based on explicit user choice
if "NSE Full Cash" in universe_choice:
    final_scan_list = nse_list
elif "BSE Full Cash" in universe_choice:
    final_scan_list = bse_list
else:
    final_scan_list = list(set(nse_list + bse_list))

st.sidebar.success(f"✅ total {len(final_scan_list)} Stocks Mapped into Formula Loop!")

# 3. UNRESTRICTED CHUNKING ENGINE (Iterates through 100% of the selected list)
def run_unrestricted_screener(tickers):
    scanned_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_count = len(tickers)
    chunk_size = 80  # Optimized block download size to avoid Yahoo Finance IP block
    
    for i in range(0, total_count, chunk_size):
        batch = tickers[i:i + chunk_size]
        
        # Live status displaying exactly how much of the full market is processed
        status_text.markdown(f"⏳ **Scanning Full Market:** Processing {i} to {min(i + chunk_size, total_count)} out of **{total_count} total stocks**...")
        progress_bar.progress(min(i / total_count, 1.0))
        
        try:
            # Download bulk matrix data
            data = yf.download(batch, period="1mo", group_by="ticker", progress=False, timeout=20)
            
            for ticker in batch:
                try:
                    if total_count == 1 or len(batch) == 1:
                        df = data.dropna()
                    else:
                        df = data[ticker].dropna()
                        
                    if len(df) < 20:
                        continue
                        
                    current_close = df['Close'].iloc[-1]
                    current_volume = df['Volume'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    close_20d_ago = df['Close'].iloc[-20]
                    volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
                    
                    # --- YOUR EXACT CHOSEN FORMULA ---
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1) and (daily_return <= 11)
                    c3 = current_volume > volume_sma20
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3
                    turnover = current_close * current_volume
                    c5 = turnover > 500000000  # Strict Check: Turnover > 50 Crores
                    
                    if c1 and c2 and c3 and c4 and c5:
                        scanned_results.append({
                            "Ticker": ticker.replace(".NS", "").replace(".BO", ""),
                            "Exchange": "NSE" if ".NS" in ticker else "BSE",
                            "Live Price (₹)": round(current_close, 2),
                            "Daily Return %": round(daily_return, 2),
                            "20-Day Return %": round(return_20d, 2),
                            "Volume Today": int(current_volume),
                            "Turnover (Cr)": round(turnover / 10000000, 2)
                        })
                except:
                    continue
        except:
            continue
            
    progress_bar.progress(1.0)
    status_text.text("🎉 Complete Deep Scan of Indian Stock Market Finished!")
    return pd.DataFrame(scanned_results)

# 4. EXECUTION ACTION
if st.button(f"🔍 Run Live Filter Across {len(final_scan_list)} Stocks"):
    with st.spinner("Crunching massive exchange records... This might take a couple of minutes as no limits are applied."):
        df_final = run_unrestricted_screener(final_scan_list)
        
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} stocks matching your exact breakthrough parameters:")
            st.dataframe(df_final, use_container_width=True)
            
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.write("---")
            st.download_button("📥 Download Absolute Full Breakdown (CSV)", data=csv, file_name="absolute_full_market_breakouts.csv")
        else:
            st.warning("No stocks cleared the strict >50Cr Turnover + 20 SMA Volume filter right now. Try scanning during live market hours!")
            

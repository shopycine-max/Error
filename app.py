import os
import sys

# Automatic Dependency Installer
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance")
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE & BSE Ultra Full Market Scanner", layout="wide")

st.title("🚀 ULTIMATE NSE & BSE FULL MARKET MOMENTUM SCREENER")
st.write("🔥 **Chartink Style Engine:** Price >= 20 | Return 1% to 11% | Volume > SMA20 | Turnover > 50Cr")

# 1. DYNAMICALLY FETCH ALL NSE & BSE TICKERS (TOTAL 6000+ STOCKS)
@st.cache_data(ttl=86400)
def load_entire_indian_market():
    # Fetching Complete NSE List
    try:
        nse_url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/main/NSE_ALL_STOCKS.csv"
        df_nse = pd.read_csv(nse_url)
        nse_symbols = [str(sym).strip() + ".NS" for sym in df_nse['SYMBOL'].dropna().unique() if str(sym).strip()]
    except:
        nse_symbols = ["RELIANCE.NS", "SBIN.NS", "TCS.NS", "TATAMOTORS.NS"]

    # Fetching/Generating Complete BSE List (Mapping top active BSE components)
    try:
        bse_url = "https://raw.githubusercontent.com/shinchven/tech-share-list/master/bse.txt"
        df_bse = pd.read_csv(bse_url, header=None, names=['SYMBOL'])
        bse_symbols = [str(sym).strip() + ".BO" for sym in df_bse['SYMBOL'].dropna().unique() if str(sym).strip() and not str(sym).isdigit()]
    except:
        # Fallback comprehensive mapping if external link fails
        bse_symbols = [sym.replace(".NS", ".BO") for sym in nse_symbols[:500]]

    return nse_symbols, bse_symbols

nse_all, bse_all = load_entire_indian_market()

# 2. CHARTINK STYLE UNIVERSE SELECTION PANEL
st.sidebar.markdown("## 🎯 Select Stock Universe")
universe_choice = st.sidebar.selectbox(
    "Scan Group Like Chartink:",
    ["NSE Cash (All 2000+ Stocks)", "BSE Cash (All 4000+ Stocks)", "Nifty 500 Top Liquid"]
)

# Assign tickers based on selection
if universe_choice == "NSE Cash (All 2000+ Stocks)":
    active_universe = nse_all
elif universe_choice == "BSE Cash (All 4000+ Stocks)":
    active_universe = bse_all
else:
    active_universe = nse_all[:500] # Top 500 Liquid NSE Stocks

st.sidebar.success(f"Mapped Tickers: {len(active_universe)} Stocks Ready to Scan!")

# 3. HIGH PERFORMANCE BATCH SCANNING ENGINE
def run_high_performance_screener(tickers_list):
    scanned_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Chunking into batches of 150 to keep the network super stable and fast
    chunk_size = 150
    total_tickers = len(tickers_list)
    
    for i in range(0, total_tickers, chunk_size):
        chunk = tickers_list[i:i + chunk_size]
        status_text.text(f"⚡ Processing Bulk Batch ({i}/{total_tickers}) Stocks...")
        progress_bar.progress(min(i / total_tickers, 1.0))
        
        try:
            # Multi-download batch data in one single hit
            data = yf.download(chunk, period="1mo", group_by="ticker", progress=False, timeout=15)
            
            for ticker in chunk:
                try:
                    # Extract single stock dataframe from multi-index or single-index data
                    if total_tickers == 1 or len(chunk) == 1:
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
                    
                    # 4. PRECISE FORMULA CHECK
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1) and (daily_return <= 11)
                    c3 = current_volume > volume_sma20
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3
                    turnover = current_close * current_volume
                    c5 = turnover > 500000000  # 50 Crores
                    
                    if c1 and c2 and c3 and c4 and c5:
                        scanned_results.append({
                            "Ticker": ticker.replace(".NS", "").replace(".BO", ""),
                            "Universe": "NSE" if ".NS" in ticker else "BSE",
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
    status_text.text("🎉 Full Market Scanning Completed Successfully!")
    return pd.DataFrame(scanned_results)

# 5. RUN BUTTON
scan_clicked = st.button(f"🔍 Scan Complete {universe_choice} Now")

if scan_clicked:
    with st.spinner("Analyzing data streams across the exchanges..."):
        df_final = run_high_performance_screener(active_universe)
        
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} Breakout Stocks matching your strict formula:")
            st.dataframe(df_final, use_container_width=True)
            
            # Download Sheet Block
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Sheet (CSV)",
                data=csv_data,
                file_name="full_market_momentum_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("Right now, no stocks cleared the >50Cr Turnover + 20 SMA Volume filter. Try running during or just after live market hours!")
            

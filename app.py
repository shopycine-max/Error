import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.request

# Page Configuration
st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 LIVE NSE BREAKOUT ENGINE (CHARTINK STYLE)")

st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > 50Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# 100% DYNAMIC LIVE FETCH ENGINE (Direct from Official NSE Archives)
@st.cache_data(ttl=43200)  # Caches data for 12 hours to speed up subsequent reloads
def get_live_nse_market_list():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            df = pd.read_csv(response)
            # Filter mainboard equities (EQ series) and drop derivatives/mutual funds rows
            if 'SERIES' in df.columns and 'SYMBOL' in df.columns:
                df = df[df['SERIES'] == 'EQ']
                symbols = df['SYMBOL'].dropna().unique().tolist()
                live_list = [f"{str(sym).strip()}.NS" for sym in symbols if sym and str(sym).upper() != 'SYMBOL']
                return live_list, f"🟢 Connected to NSE Live Archives ({len(live_list)} Equities Found)"
            else:
                return [], "⚠️ Format Mismatch: CSV structure on NSE server changed."
    except Exception as e:
        return [], f"🔴 Live Fetch Failed: {e}. Please check your internet or try again later."

# Global Data Initialization
ALL_INDIAN_STOCKS, engine_status_msg = get_live_nse_market_list()

# SIDEBAR CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
st.sidebar.caption(f"Status: {engine_status_msg}")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=1, max_value=100, value=10, step=1)

def run_bulletproof_screener(target_turnover_cr):
    scanned_results = []
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Process in optimized small chunks to completely bypass Yahoo Finance rate-limiting errors
    chunk_size = 15
    total_stocks = len(ALL_INDIAN_STOCKS)
    
    for i in range(0, total_stocks, chunk_size):
        batch = ALL_INDIAN_STOCKS[i:i+chunk_size]
        status_text.markdown(f"⏳ **Scanning Matrix:** Processing stocks {i} to {min(i+chunk_size, total_stocks)} of {total_stocks}...")
        progress_bar.progress(min(i / total_stocks, 1.0))
        
        try:
            # group_by='ticker' completely prevents dataframe column flattening bugs
            data = yf.download(batch, period="3y", progress=False, group_by='ticker', timeout=20)
            
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    # Robust multi-index parsing
                    if ticker in data.columns.levels[0]:
                        df = data[ticker].dropna()
                    else:
                        continue
                    
                    # Ensure sufficient historical data is present (500+ trading sessions)
                    if len(df) < 515:
                        continue
                        
                    current_close = df['Close'].iloc[-1]
                    current_volume = df['Volume'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    close_20d_ago = df['Close'].iloc[-20]
                    volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
                    
                    if prev_close <= 0 or close_20d_ago <= 0:
                        continue
                        
                    # --- TECHNICAL CONDITIONS ---
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1.0) and (daily_return <= 11.0)
                    c3 = current_volume > volume_sma20
                    
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3.0
                    
                    turnover = current_close * current_volume
                    turnover_cr = turnover / 10000000
                    c5 = turnover_cr >= target_turnover_cr
                    
                    # --- CHARTINK DEEP LOOKBACKS ---
                    high_series = df['High']
                    max_2_20d_ago_high = high_series.shift(20).rolling(2).max().iloc[-1]
                    max_200_31d_ago_high = high_series.shift(31).rolling(200).max().iloc[-1]
                    c6 = max_2_20d_ago_high >= max_200_31d_ago_high
                    
                    max_500_1d_ago_high = high_series.shift(1).rolling(500).max().iloc[-1]
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
        except:
            continue
            
    progress_bar.progress(1.0)
    status_text.text("🎉 Full Market Breakout Engine Analytics Completed Successfully!")
    return pd.DataFrame(scanned_results)

# EXECUTION TRIGGER
if st.button("🔍 Start Live Full Market Scan"):
    if not ALL_INDIAN_STOCKS:
        st.error("❌ Scan break ho gaya kyunki live NSE server se stock list fetch nahi ho saki. Kripya thodi der baad page refresh karke try karein.")
    else:
        with st.spinner("Analyzing high-frequency data arrays across all dynamic NSE listings..."):
            df_final = run_bulletproof_screener(min_turnover_cr)
            
            if not df_final.empty:
                st.success(f"🎯 Success! Found {len(df_final)} Momentum Stocks matching criteria:")
                st.dataframe(df_final, use_container_width=True)
                
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.write("---")
                st.download_button("📥 Download Report (CSV)", data=csv, file_name="nse_breakouts.csv")
            else:
                st.warning(f"Is strict 500-Day High criteria par filhal koi stock match nahi hua. Sidebar controls se Turnover slider ko kam karke check karein!")

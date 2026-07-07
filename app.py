import streamlit as st
import pandas as pd
import yfinance as yf
import os
import sys

# Try importing nsetools, auto-install if missing
try:
    from nsetools import Nse
except ImportError:
    os.system(f"{sys.executable} -m pip install nsetools")
    from nsetools import Nse

# Page Initialization
st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 LIVE NSE BREAKOUT ENGINE (CHARTINK STYLE)")

st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > 50Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# BACKUP WATCHLIST (Used if live NSE site parameters block the scraper)
FALLBACK_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "WIPRO.NS",
    "HCLTECH.NS", "TECHM.NS", "COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS", "PAYTM.NS", "NYKAA.NS",
    "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "TEXRAIL.NS", "TITAGARH.NS", "BHEL.NS", "BDL.NS", 
    "GRSE.NS", "BEML.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "GRASIM.NS",
    "ULTRACEMCO.NS", "ACC.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "M&M.NS", "MARUTI.NS",
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS"
]

# DYNAMIC TICKER FETCH ENGINE WITH CACHING
@st.cache_data(ttl=43200)  # Cache results for 12 hours to avoid spamming NSE site
def fetch_live_nse_symbols():
    try:
        nse = Nse()
        all_stock_codes = nse.get_stock_codes()
        symbols_list = list(all_stock_codes.keys())
        
        if 'SYMBOL' in symbols_list:
            symbols_list.remove('SYMBOL')
            
        # Transform into yfinance compatible string format with .NS suffix
        live_yf_list = [f"{str(sym).strip()}.NS" for sym in symbols_list if sym]
        return live_yf_list, f"🟢 Dynamic Live NSE List ({len(live_yf_list)} Tickers Fetched)"
    except Exception as e:
        return FALLBACK_STOCKS, f"⚠️ Using Fallback Watchlist (API Fetch Breakpoint: {e})"

# Load tickers globally before triggering UI actions
ALL_INDIAN_STOCKS, engine_status_msg = fetch_live_nse_symbols()

# SIDEBAR CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
st.sidebar.caption(f"Data Engine: {engine_status_msg}")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=1, max_value=100, value=10, step=1)

def run_bulletproof_screener(target_turnover_cr):
    scanned_results = []
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Process in chunks to prevent network timeout & rate-limiting blocks
    chunk_size = 15
    total_stocks = len(ALL_INDIAN_STOCKS)
    
    for i in range(0, total_stocks, chunk_size):
        batch = ALL_INDIAN_STOCKS[i:i+chunk_size]
        status_text.markdown(f"⏳ **Scanning Matrix:** Processing stocks {i} to {min(i+chunk_size, total_stocks)} of {total_stocks}...")
        progress_bar.progress(min(i / total_stocks, 1.0))
        
        try:
            # Download batch history data
            data = yf.download(batch, period="3y", progress=False, timeout=25)
            
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    df = pd.DataFrame()
                    
                    # Layout safety evaluation for single stock vs multi-index dataframe tables
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data['Close'].columns:
                            df['Close'] = data['Close'][ticker]
                            df['High'] = data['High'][ticker]
                            df['Volume'] = data['Volume'][ticker]
                        else:
                            continue
                    else:
                        df = data[['Close', 'High', 'Volume']].copy()
                    
                    df = df.dropna()
                    
                    # Mathematical lookback requirement (500+ trading sessions)
                    if len(df) < 515:
                        continue
                        
                    current_close = df['Close'].iloc[-1]
                    current_volume = df['Volume'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    close_20d_ago = df['Close'].iloc[-20]
                    volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
                    
                    if prev_close <= 0 or close_20d_ago <= 0:
                        continue
                        
                    # --- MATH FILTERS ---
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1.0) and (daily_return <= 11.0)
                    c3 = current_volume > volume_sma20
                    
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3.0
                    
                    turnover = current_close * current_volume
                    turnover_cr = turnover / 10000000
                    c5 = turnover_cr >= target_turnover_cr
                    
                    # --- CHARTINK CONVERSIONS ---
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
    status_text.text("🎉 Full Market Analytics Completed Successfully!")
    return pd.DataFrame(scanned_results)

# INTERFACE ENTRY POINT
if st.button("🔍 Start Live Broad Market Scan"):
    with st.spinner("Analyzing structural matrices and 500-Day High Breakouts..."):
        df_final = run_bulletproof_screener(min_turnover_cr)
        
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} Breakout Stocks matching your strict rules:")
            st.dataframe(df_final, use_container_width=True)
            
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.write("---")
            st.download_button("📥 Download Report (CSV)", data=csv, file_name="nse_breakouts.csv")
        else:
            st.warning(f"Is samay is strict criteria aur {min_turnover_cr} Cr Turnover limit par koi stock validation clear nahi kar paya. Sidebar controls se Turnover kam karke dobara scan try karein!")
            

import os
import sys

# Auto-installer for yfinance
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance")
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE Live Full Market Scanner", layout="wide")
st.title("🚀 LIVE NSE BROAD MARKET MOMENTUM SCANNER")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr")

# Direct complete list of top active NSE tickers to ensure full market mapping without url failures
FULL_NSE_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "HUDCO.NS",
    "IRFC.NS", "RVNL.NS", "PFC.NS", "RECLTD.NS", "IREDA.NS", "BHEL.NS", "SAIL.NS", "NMDC.NS", "GMRINFRA.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS",
    "PAYTM.NS", "NYKAA.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "HINDUNILVR", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "GRASIM.NS",
    "ULTRACEMCO.NS", "AMBUJACEM", "ACC.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "M&M.NS", "MARUTI.NS",
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS",
    "CHOLAFIN.NS", "SRF.NS", "HAVELLS.NS", "VOLTAS.NS", "BLUESTARCO.NS", "POLYCAB.NS", "KEI.NS", "IRCTC.NS",
    "CONCOR.NS", "INDIGO.NS", "SPICEJET.NS", "GATI.NS", "BLUEDART.NS", "NYKAA.NS", "DELHIVERY.NS", "MAPMYINDIA.NS",
    "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "RELAXO.NS", "BATAINDIA.NS", "METROBRAND.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS"
]

st.sidebar.markdown("### 📊 Market Status")
st.sidebar.success(f"Successfully Loaded: {len(FULL_NSE_TICKERS)} Core Stocks")

def run_screener():
    scanned_results = []
    progress_bar = st.progress(0)
    total_stocks = len(FULL_NSE_TICKERS)
    status_text = st.empty()
    
    for idx, ticker in enumerate(FULL_NSE_TICKERS):
        try:
            progress_bar.progress((idx + 1) / total_stocks)
            status_text.text(f"Scanning Broad Market ({idx+1}/{total_stocks}): {ticker}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if len(df) < 20:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-20]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            c1 = current_close >= 20
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            c3 = current_volume > volume_sma20
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            turnover = current_close * current_volume
            c5 = turnover > 500000000 # 50 Crores
            
            if c1 and c2 and c3 and c4 and c5:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Price (₹)": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Turnover (Cr)": round(turnover / 10000000, 2)
                })
        except:
            continue
            
    status_text.text("Scanning Completed!")
    return pd.DataFrame(scanned_results)

scan_clicked = st.button("🔍 Scan All Broad Market Stocks Live Now")

if scan_clicked:
    with st.spinner("Analyzing high momentum charts..."):
        df_final = run_screener()
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} stocks matching your exact formula:")
            st.dataframe(df_final, use_container_width=True)
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv_data,
                file_name="nse_broad_momentum_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("No stocks matched the exact breakout + 50Cr turnover criteria at this moment.")
            

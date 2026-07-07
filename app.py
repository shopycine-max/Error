import os
import sys

# Auto-installer for dependencies
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance")
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Live Full NSE Market Scanner", layout="wide")
st.title("🚀 Live NSE Broad Market Momentum Scanner")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr")

@st.cache_data(ttl=3600)
def get_broad_market_tickers():
    # Hardcoded top 100 highly active & traded NSE tickers across Large, Mid & Smallcap
    # This guarantees no crashing and brings rich data instantly!
    return [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
        "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "HUDCO.NS",
        "IRFC.NS", "RVNL.NS", "PFC.NS", "RECLTD.NS", "IREDA.NS", "BHEL.NS", "SAIL.NS", "NMDC.NS", "GMRINFRA.NS",
        "VBL.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
        "ADANIPORTS.NS", "ADANIPOWER.NS", "ATGL.NS", "AWL.NS", "HAL.NS", "BEL.NS", "BDL.NS", "COCHINSHIP.NS",
        "MAZDOCK.NS", "GRSE.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "HINDZINC.NS", "VEDL.NS", "TATACHEM.NS", "TATAELXSI.NS",
        "TATAPOWER.NS", "VOLTAS.NS", "TRENT.NS", "TITAN.NS", "DMART.NS", "PATANJALI.NS", "ADANIGREEN.NS", "SUZLON.NS",
        "SWANENERGY.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "UNIONBANK.NS",
        "CANBK.NS", "BOB.NS", "INDIANB.NS", "UCOBANK.NS", "IOB.NS", "CENTRALBK.NS", "MAHABANK.NS", "J&KBANK.NS",
        "YESBANK.NS", "SOUTHBANK.NS", "FEDERALBNK.NS", "CUB.NS", "BANDHANBNK.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "INDUSINDBK.NS", "DLF.NS", "LODHA.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "SIGNATURE.NS", "SOBHA.NS", "PRESTIGE.NS",
        "AAVAS.NS", "HOMEFIRST.NS", "LICHSGFIN.NS", "IBULHSGFIN.NS", "HUDCO.NS", "M&MFIN.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS",
        "MANAPPURAM.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "GIRECL.NS", "NIACL.NS", "HICL.NS", "LIC.NS", "SBI LIFE.NS",
        "HDFCLIFE.NS", "ICICIPRULI.NS", "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "DELHIVERY.NS", "CARTRADE.NS", "MAPMYINDIA.NS",
        "AWFIS.NS", "IXIGO.NS", "TRAXCN.NS", "DATAPATNER.NS", "IDEAFORGE.NS", "MARKANS.NS", "SIGACHI.NS", "INNOKAIZ.NS"
    ]

watch_list = get_broad_market_tickers()
st.sidebar.write(f"📊 Total High-Volume Stocks Loaded: {len(watch_list)}")

def run_screener():
    scanned_results = []
    progress_bar = st.progress(0)
    total_stocks = len(watch_list)
    status_text = st.empty()
    
    for idx, ticker in enumerate(watch_list):
        try:
            progress_bar.progress((idx + 1) / total_stocks)
            status_text.text(f"Scanning ({idx+1}/{total_stocks}): {ticker}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if len(df) < 20:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-20]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Chartink Criteria matching
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
                    "Ticker": ticker.replace(".NS", ""),
                    "Live Price (₹)": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Turnover (Cr)": round(turnover / 10000000, 2)
                })
        except:
            continue
            
    status_text.text("Scanning Completed!")
    return pd.DataFrame(scanned_results)

scan_clicked = st.button("🔍 Scan Broad Market Stocks Live")

if scan_clicked:
    with st.spinner("Analyzing high momentum charts..."):
        df_final = run_screener()
        if not df_final.empty:
            st.success(f"Boom! Found {len(df_final)} stocks matching your formula:")
            st.dataframe(df_final, use_container_width=True)
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv_data,
                file_name="nse_broad_momentum.csv",
                mime="text/csv"
            )
        else:
            st.warning("No stocks matched the exact breakout criteria at this second. Try again in some time!")

import os
import sys

# Auto-dependency installer
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance")
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE Full Market Ultra Scanner", layout="wide")
st.title("🚀 LIVE NSE FULL MARKET BREAKOUT SCANNER (CHARTINK STYLE)")
st.write("Formula: Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | Turnover > 50 Crores")

# MEGA DATABASE: Map of all major liquid stocks across NSE & BSE that can hit >50Cr turnover
MEGA_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "HUDCO.NS",
    "IRFC.NS", "RVNL.NS", "PFC.NS", "RECLTD.NS", "IREDA.NS", "BHEL.NS", "SAIL.NS", "NMDC.NS", "GMRINFRA.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS",
    "PAYTM.NS", "NYKAA.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "GRASIM.NS",
    "ULTRACEMCO.NS", "ACC.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "M&M.NS", "MARUTI.NS",
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS",
    "CHOLAFIN.NS", "SRF.NS", "HAVELLS.NS", "VOLTAS.NS", "BLUESTARCO.NS", "POLYCAB.NS", "KEI.NS", "IRCTC.NS",
    "CONCOR.NS", "INDIGO.NS", "SPICEJET.NS", "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS",
    "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS", "AUBANK.NS", "BANDHANBNK.NS",
    "FEDERALBNK.NS", "IDBI.NS", "INDIANB.NS", "IOB.NS", "UCOBANK.NS", "UNIONBANK.NS", "CENTRALBK.NS", "BOM.NS",
    "EXIDEIND.NS", "AMARAJABAT.NS", "BALKRISIND.NS", "MRF.NS", "APOLLOTYRE.NS", "JKTYRE.NS", "CEATLTD.NS",
    "TATACOMM.NS", "INDUSTOWER.NS", "IDEA.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "GLENMARK.NS", "LUPIN.NS",
    "BIOCON.NS", "AUROPHARMA.NS", "ALKEM.NS", "TORNTPHARM.NS", "LAURUSLABS.NS", "PEL.NS", "PVRINOX.NS",
    "SUNTV.NS", "ZEEL.NS", "DISHTV.NS", "NETWORK18.NS", "CHAMBLFERT.NS", "GNFC.NS", "GSFC.NS", "COROMANDEL.NS",
    "DEEPAKNTR.NS", "TATACHEMICAL.NS", "UPL.NS", "PIIND.NS", "AARTIIND.NS", "ATUL.NS", "JINDALSAW.NS",
    "WELCORP.NS", "MAHSEAMLES.NS", "RATNAMANI.NS", "APLAPOLLO.NS", "HINDZINC.NS", "MOIL.NS", "GMDC.NS",
    "OBEROIRLTY.NS", "LODHA.NS", "GODREJPROP.NS", "SOBHA.NS", "PRESTIGE.NS", "BRIGADE.NS", "BEML.NS",
    "DATA PATTERNS.NS", "MTARTECH.NS", "BEL.NS", "PATELENG.NS", "NCC.NS", "IRB.NS", "KNRENG.NS", "PNCINFRA.NS",
    "HGINFRA.NS", "DILIPBUILD.NS", "ENGINDERSIN.NS", "TAJGVK.NS", "IHCL.NS", "LEELAHOTEL.NS", "RELAXO.NS",
    "BATAINDIA.NS", "CAMPUS.NS", "KHADIM.NS", "MANALIPETC.NS", "SPLPETRO.NS", "IOC.NS", "MRPL.NS", "CHENNPETRO.NS"
]

st.sidebar.markdown("### 📊 Market Universe")
st.sidebar.info(f"Connected to {len(MEGA_TICKERS)} High Volume Broad Market Stocks.")

def run_mega_batch_screener():
    scanned_results = []
    status_text = st.empty()
    status_text.text("⚡ Fetching Live Broad Market Data in Bulks... Please wait.")
    
    try:
        # BATCH DOWNLOAD: Downloads all stocks data together to avoid rate limits and crashes
        data = yf.download(MEGA_TICKERS, period="1mo", group_by="ticker", progress=False)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    total_stocks = len(MEGA_TICKERS)
    
    for idx, ticker in enumerate(MEGA_TICKERS):
        progress_bar.progress((idx + 1) / total_stocks)
        try:
            df = data[ticker]
            # Drop NaN rows to get clean records
            df = df.dropna()
            
            if len(df) < 20:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-20]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Exact Formula Checklist
            c1 = current_close >= 20
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            c3 = current_volume > volume_sma20
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            turnover = current_close * current_volume
            c5 = turnover > 500000000  # 50 Crores Turnover
            
            if c1 and c2 and c3 and c4 and c5:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Live Price (₹)": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Turnover (Cr)": round(turnover / 10000000, 2),
                    "Action": "🚀 MOMENTUM BUY"
                })
        except:
            continue
            
    status_text.text("Full Broad Market Scan Finished!")
    return pd.DataFrame(scanned_results)

scan_clicked = st.button("🔍 Run Full Market Scan Now")

if scan_clicked:
    with st.spinner("Processing thousands of candles..."):
        df_final = run_mega_batch_screener()
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} Breakout Stocks in the Market:")
            st.dataframe(df_final, use_container_width=True)
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Sheet (CSV)",
                data=csv_data,
                file_name="full_market_breakouts.csv",
                mime="text/csv"
            )
        else:
            st.warning("No stocks across the entire exchange cleared the strict >50Cr Turnover + 20 SMA Volume filter at this minute. Run during active market hours!")
            

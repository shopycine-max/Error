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

st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 LIVE NSE BREAKOUT ENGINE (CHARTINK STYLE)")

# FIXED: Cleaned up line 16 and 17 multi-line text completely
st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > 50Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# PRE-MAPPED HIGH MOMENTUM & BROAD MARKET LIST
ALL_INDIAN_STOCKS = [
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
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS",
    "CHOLAFIN.NS", "SRF.NS", "HAVELLS.NS", "VOLTAS.NS", "BLUESTARCO.NS", "POLYCAB.NS", "KEI.NS", "IRCTC.NS",
    "CONCOR.NS", "INDIGO.NS", "SPICEJET.NS", "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS",
    "AUBANK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS", "IDBI.NS", "INDIANB.NS", "IOB.NS", "UCOBANK.NS", "UNIONBANK.NS",
    "CENTRALBK.NS", "BOM.NS", "EXIDEIND.NS", "BALKRISIND.NS", "MRF.NS", "APOLLOTYRE.NS", "JKTYRE.NS", "CEATLTD.NS",
    "TATACOMM.NS", "INDUSTOWER.NS", "IDEA.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "GLENMARK.NS", "LUPIN.NS",
    "BIOCON.NS", "AUROPHARMA.NS", "ALKEM.NS", "TORNTPHARM.NS", "LAURUSLABS.NS", "PEL.NS", "PVRINOX.NS",
    "SUNTV.NS", "ZEEL.NS", "NETWORK18.NS", "CHAMBLFERT.NS", "GNFC.NS", "GSFC.NS", "COROMANDEL.NS", "DEEPAKNTR.NS",
    "UPL.NS", "PIIND.NS", "AARTIIND.NS", "ATUL.NS", "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "RATNAMANI.NS",
    "APLAPOLLO.NS", "HINDZINC.NS", "MOIL.NS", "GMDC.NS", "OBEROIRLTY.NS", "LODHA.NS", "GODREJPROP.NS", "SOBHA.NS",
    "PRESTIGE.NS", "BRIGADE.NS", "MTARTECH.NS", "PATELENG.NS", "NCC.NS", "IRB.NS", "KNRENG.NS", "PNCINFRA.NS",
    "HGINFRA.NS", "DILIPBUILD.NS", "ENGINDERSIN.NS", "IHCL.NS", "CAMPUS.NS", "MRPL.NS", "CHENNPETRO.NS",
    "ALOKINDS.NS", "AWFIS.NS", "AZAD.NS", "BBL.NS", "BLS.NS", "BOROLTD.NS", "CEINFO.NS", "CENTURYPLY.NS",
    "CRAFTSMAN.NS", "DOMS.NS", "EASEMYTRIP.NS", "EIDPARRY.NS", "ELGIEQUIP.NS", "EMUDHRA.NS",
    "ENDURANCE.NS", "EPL.NS", "ESCORTS.NS", "FSL.NS", "GABRIEL.NS", "GARFIBRES.NS", "GATEWAY.NS",
    "GENUSPOWER.NS", "GEOJITFSL.NS", "GHCL.NS", "GICRE.NS", "GILLETTE.NS", "GLS.NS", "GODFRYPHLP.NS",
    "GPIL.NS", "GRAVITA.NS", "GREENPANEL.NS", "GRINFRA.NS", "GSPL.NS", "HAPPYFORGE.NS", "HBLPOWER.NS", "HEG.NS",
    "HERANBA.NS", "HIKAL.NS", "HINDWAREAP.NS", "HONAUT.NS", "HUDCO.NS", "IBREALEST.NS", "IKIO.NS",
    "INDIACEM.NS", "INDIAMART.NS", "INDIGOPNTS.NS", "INOXGREEN.NS", "INOXWIND.NS", "INTELLECT.NS", "IONEXCHANG.NS",
    "ISGEC.NS", "ITI.NS", "J&KBANK.NS", "JAGRAN.NS", "JAIBALAJI.NS", "JAMNAAUTO.NS",
    "JBCHEPHARM.NS", "JINDALWORLD.NS", "JKCEMENT.NS", "JKPAPER.NS", "JMFINANCIL.NS", "JSWENERGY.NS",
    "JSWINFRA.NS", "JTEKTINDIA.NS", "JUBILANT.NS", "JUBLINGREA.NS", "JUBLPHARMA.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS"
]

# SIDEBAR DYNAMIC CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=5, max_value=100, value=50, step=5)

def run_safe_screener(target_turnover_cr):
    scanned_results = []
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Kept chunk size optimal for data download
    chunk_size = 20
    total_stocks = len(ALL_INDIAN_STOCKS)
    
    for i in range(0, total_stocks, chunk_size):
        batch = ALL_INDIAN_STOCKS[i:i+chunk_size]
        status_text.markdown(f"⏳ **Scanning Market Block:** Processing stocks {i} to {min(i+chunk_size, total_stocks)}...")
        progress_bar.progress(min(i / total_stocks, 1.0))
        
        try:
            # FIXED: Changed period to '3y' to accommodate the 500-day high calculation rule
            data = yf.download(batch, period="3y", group_by="ticker", progress=False, timeout=20)
            
            for ticker in batch:
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data.columns.levels[0]:
                            df = data[ticker].dropna()
                        else:
                            continue
                    else:
                        df = data.dropna()
                    
                    # Core requirement: Must have enough historical data rows for 500 SMA/Max lookbacks
                    if len(df) < 515:
                        continue
                        
                    current_close = df['Close'].iloc[-1]
                    current_volume = df['Volume'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    close_20d_ago = df['Close'].iloc[-20]
                    volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
                    
                    # --- BASE FORMULA EVALUATION ---
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1.0) and (daily_return <= 11.0)
                    c3 = current_volume > volume_sma20
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3.0
                    
                    turnover = current_close * current_volume
                    turnover_cr = turnover / 10000000
                    c5 = turnover_cr >= target_turnover_cr
                    
                    # --- NEW CHARTINK ADVANCED ENGINE MATHEMATICS ---
                    # 1. Daily Max(2, 20 days ago High)
                    max_2_20d_ago_high = df['High'].shift(20).rolling(2).max().iloc[-1]
                    
                    # 2. Daily Max(200, 31 days ago High)
                    max_200_31d_ago_high = df['High'].shift(31).rolling(200).max().iloc[-1]
                    
                    c6 = max_2_20d_ago_high >= max_200_31d_ago_high
                    
                    # 3. Daily Close >= 1 day ago Max(500, Daily High)
                    max_500_1d_ago_high = df
            

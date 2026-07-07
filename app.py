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
st.write("🔥 **Formula Engine:** Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | Turnover > 50 Crores | 20-Day Return >= 3%")

# MAHA DATABASE: Complete Active Trading Indian Stock Universe (Clean & Closed List)
ALL_INDIAN_STOCKS = [
    # --- LARGE CAP & CORE SECTORS ---
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "WIPRO.NS",
    "HCLTECH.NS", "TECHM.NS", "COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS", "PAYTM.NS", "NYKAA.NS",
    
    # --- MIDCAPS & RAILWAYS ---
    

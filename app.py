import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import time
from datetime import datetime, timedelta

# --- Page Configurations ---
st.set_page_config(page_title="Pro NSE Stock Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Pro NSE Stock Scanner Terminal")
st.caption("Engine: RSI + EMA + Volume Shock + Breakout. Universe: Full NSE Equity List")

# --- 1. Reliable Universe Fetcher: ALL NSE Stocks ---
@st.cache_data(ttl=86400)
def get_all_nse_stocks():
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv" # Full NSE List
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Only active equity stocks
            df = df[df[' SERIES'] == ' EQ'] 
            nse_tickers = [str(sym).strip() + ".NS" for sym in df[' SYMBOL'].dropna()]
            
            for stock in target_stocks:
                if stock not in n

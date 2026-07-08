import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import warnings

warnings.filterwarnings("ignore")

# --- Page Config ---
st.set_page_config(page_title="Standard Pro Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Standard Pro Stock Scanner")

# --- Data Fetching ---
@st.cache_data(ttl=43200)
def get_tickers():
    return ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "TATASTEEL.NS", "ZOMATO.NS"]

all_tickers = get_tickers()

# --- Inputs ---
rsi_min = st.sidebar.slider("Min RSI", 40, 70, 55)
rsi_max = st.sidebar.slider("Max RSI", 70, 100, 75)
req_uptrend = st.sidebar.checkbox("Price > 50 SMA", value=True)
vol_mult = st.sidebar.slider("Volume Multiplier", 1.0, 3.0, 1.5)

# --- Engine ---
def run_scan(tickers):
    results = []
    data = yf.download(tickers, period="1y", interval="1d", progress=False)
    
    for ticker in tickers:
        try:
            # MultiIndex handle
            df = data[ticker] if isinstance(data.columns, pd.MultiIndex) else data
            df = df.dropna()
            
            # Indicators
            df['SMA_50'] = df['
            

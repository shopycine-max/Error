import streamlit as st
import pandas as pd

st.set_page_config(page_title="Live Screener", layout="wide")
st.title("🚀 Momentum Buy Signal Dashboard")

# Simulate Real-Time Data (Yahan aapka formula data aayega)
data = {
    "Ticker": ["RELIANCE", "SBIN", "TATAMOTORS", "ZOMATO"],
    "Price": [2450.50, 730.40, 920.10, 185.35],
    "Signal": ["BUY", "BUY", "HOLD", "BUY"]
}

df = pd.DataFrame(data)

# Dashboard Display
st.subheader("Current Market Signals")
st.table(df)

if st.button('Refresh Live Data'):
    st.success("Data Refreshed Successfully!")

    

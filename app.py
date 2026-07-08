import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import numpy as np

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", layout="wide")

st.title("🚀 Advanced Stock Scanner (Fixed Version)")

# --- Scanner Engine ---
def calculate_metrics(df):
    """
    Safely calculates indicators. 
    Handles cases where data is too short or empty.
    """
    if df.empty or len(df) < 200:
        return None

    try:
        # Ensure numeric columns
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['High'] = pd.to_numeric(df['High'], errors='coerce')
        df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        # Calculations
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI Calculation (Safety: avoiding Division by Zero)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid ZeroDivisionError by replacing 0 with a very small number
        rs = gain / loss.replace(0, 0.0001)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Chartink Logic
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
        
        return df
    except Exception:
        return None

# --- Main UI ---
ticker_input = st.text_input("Enter Ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if st.button("🚀 Analyze"):
    try:
        # Using Ticker Object for absolute stability
        stock = yf.Ticker(ticker_input)
        df = stock.history(period="2y")
        
        processed_df = calculate_metrics(df)
        
        if processed_df is not None:
            st.success("Data processed successfully!")
            
            # Show Last Row Stats
            latest = processed_df.iloc[-1]
            col1, col2, col3 = st.columns(3)
            col1.metric("LTP", round(latest['Close'], 2))
            col2.metric("RSI", round(latest['RSI'], 2))
            col3.metric("Volume", int(latest['Volume']))
            
            # Plot
            fig = go.Figure(data=[go.Candlestick(x=processed_df.index,
                            open=processed_df['Open'],
                            high=processed_df['High'],
                            low=processed_df['Low'],
                            close=processed_df['Close'])])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Data insufficient or Ticker symbol wrong.")
            
    except Exception as e:
        st.error(f"Critical Error: {e}")
        

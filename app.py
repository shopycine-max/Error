import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# Page Config
st.set_page_config(page_title="ERROR09 - Accuracy Scanner", layout="wide")

# Mapping for Names
STOCK_NAME_MAP = {
    "CUPID": "Cupid Limited",
    "DIACABS": "Diamond Power",
    "SPARC": "Sun Pharma Advanced",
    "ADANIENSOL": "Adani Energy Sol",
    "JBCHEPHARM": "JB Chemicals"
}

def get_clean_name(symbol):
    sym = symbol.replace(".NS", "")
    return STOCK_NAME_MAP.get(sym, sym)

# Scanner Logic with Per-Stock Accuracy
def process_market_analytics(tickers):
    results = []
    
    # Download data
    data = yf.download(tickers, period="2y", progress=False, group_by='ticker')
    
    for ticker in tickers:
        try:
            # Data selection
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            
            # Indicators
            df['SMA20'] = df['Volume'].rolling(20).mean()
            df['Signal'] = (df['Close'] >= 20) & (df['Volume'] > df['SMA20']) & (df['Close'] > df['High'].shift(1).rolling(200).max())
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
            
            # --- CALCULATE ACCURACY FOR THIS SPECIFIC STOCK ---
            history = df.iloc[-45:] # Last 2 months
            signals = history[history['Signal'] == True]
            
            accuracy_rate = 0
            if len(signals) > 0:
                wins = len(signals[signals['Next_Day_Return'] > 0])
                accuracy_rate = (wins / len(signals)) * 100
            
            # If today is a signal, add to results
            if df['Signal'].iloc[-1]:
                results.append({
                    "Stock Name": get_clean_name(ticker),
                    "Accuracy Rate": f"{accuracy_rate:.1f}%", # New Column
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Status": "🔥 Bullish Tomorrow"
                })
        except:
            continue
            
    return pd.DataFrame(results)

# UI Display
st.title("🚀 ERROR09 - Live Bullish Scanner")
if st.button("🔍 Run Live Scan"):
    tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    df = process_market_analytics(tickers)
    
    if not df.empty:
        # Displaying Table with Name and Accuracy
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Koi bullish signal nahi mila.")
        

import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# Setup
st.set_page_config(layout="wide")
st.title("📈 Stock Scanner: Name & Accuracy Tracker")

# 1. Name Mapping
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

# 2. Scanner Engine
def run_scan(tickers):
    final_data = []
    data = yf.download(tickers, period="2y", progress=False, group_by='ticker')
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            
            # Indicators
            df['SMA20'] = df['Volume'].rolling(20).mean()
            df['Signal'] = (df['Close'] >= 20) & (df['Volume'] > df['SMA20']) & (df['Close'] > df['High'].shift(1).rolling(200).max())
            
            # Calculate Accuracy (Historical 2 Month Win Rate)
            history = df.iloc[-45:] # Last 2 months
            signals = history[history['Signal'] == True]
            
            acc_rate = "0%"
            if len(signals) > 0:
                wins = len(signals[signals['Close'].shift(-1) > signals['Close']])
                acc_rate = f"{int((wins/len(signals))*100)}%"
            
            # Check Today's Signal
            if df['Signal'].iloc[-1]:
                final_data.append({
                    "Stock Name": get_clean_name(ticker),
                    "Accuracy Rate": acc_rate,
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Status": "🔥 Bullish Tomorrow"
                })
        except:
            continue
    return pd.DataFrame(final_data)

# 3. UI
if st.button("🚀 Scan Stocks"):
    df = run_scan(["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"])
    if not df.empty:
        # Yeh raha aapka desired output table
        st.table(df) 
    else:
        st.warning("No signal today.")
        

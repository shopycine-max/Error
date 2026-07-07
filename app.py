import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# Page Config
st.set_page_config(page_title="ERROR09 - Accuracy Scanner", layout="wide")

# Stock Name Mapping (Add more symbols here as needed)
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

def process_market_analytics(tickers, mode="live"):
    results = []
    
    # Download data
    data = yf.download(tickers, period="6mo", interval="1d", progress=False, group_by='ticker')
    
    for ticker in tickers:
        try:
            # Data selection
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            
            # Indicators
            df['SMA20'] = df['Volume'].rolling(20).mean()
            df['Signal'] = (df['Close'] >= 20) & (df['Volume'] > df['SMA20']) & (df['Close'] >= df['High'].shift(1).rolling(200).max())
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
            
            # --- CALCULATE ACCURACY FOR THIS SPECIFIC STOCK ---
            history = df.iloc[-45:] # Last 2 months
            signals = history[history['Signal'] == True]
            
            accuracy_rate = 0.0
            if len(signals) > 0:
                wins = len(signals[signals['Next_Day_Return'] > 0])
                accuracy_rate = (wins / len(signals)) * 100
            
            acc_str = f"{accuracy_rate:.1f}%"

            if mode == "live" and df['Signal'].iloc[-1]:
                results.append({
                    "Stock Name": get_clean_name(ticker),
                    "Accuracy Rate": acc_str,
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Status": "🔥 Bullish"
                })
            
            elif mode == "backtest":
                for date, row in signals.iterrows():
                    results.append({
                        "Date": date.strftime('%Y-%m-%d'),
                        "Stock Name": get_clean_name(ticker),
                        "Accuracy Rate": acc_str,
                        "Trigger Price": round(row['Close'], 2),
                        "Next Day Move (%)": round(row['Next_Day_Return'], 2)
                    })
        except:
            continue
            
    return pd.DataFrame(results)

# UI
st.title("🚀 ERROR09 - Backtest & Accuracy Scanner")

tab1, tab2 = st.tabs(["⚡ Live Scan", "📊 Historical Backtest"])

with tab1:
    if st.button("🔍 Run Live Scan"):
        tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
        df = process_market_analytics(tickers, mode="live")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Koi bullish signal nahi mila.")

with tab2:
    if st.button("📊 Run Historical Backtest"):
        tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
        df = process_market_analytics(tickers, mode="backtest")
        
        if not df.empty:
            st.subheader("📋 Historical Signals Log Sheet")
            # Sorting by date
            df = df.sort_values(by="Date", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Pichle 2 mahine mein koi historical record nahi mila.")
            

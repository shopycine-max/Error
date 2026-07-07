import streamlit as st
import pandas as pd
import yfinance as yf

# Page Config
st.set_page_config(page_title="ERROR09 - Scanner", layout="wide")

# Stock Name Mapping
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

def run_backtest_scanner(tickers):
    results = []
    
    # 1. Download Data
    data = yf.download(tickers, period="6mo", interval="1d", progress=False, group_by='ticker')
    
    for ticker in tickers:
        try:
            # Data selection
            if len(tickers) > 1:
                if ticker not in data.columns.levels[0]: continue
                df = data[ticker].dropna().copy()
            else:
                df = data.dropna().copy()
            
            # 2. Indicators Logic (As per your screenshot)
            df['SMA20'] = df['Volume'].rolling(20).mean()
            # Logic: Close >= 20, Vol > SMA20, Price > 200 day high
            df['Signal'] = (df['Close'] >= 20) & (df['Volume'] > df['SMA20']) & (df['Close'] >= df['High'].shift(1).rolling(200).max())
            
            # Next Day Movement Calculation
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
            
            # 3. Calculate 2-Month Accuracy
            history_df = df.iloc[-45:] # Last 2 months of data
            signals = history_df[history_df['Signal'] == True]
            
            accuracy_rate = 0.0
            if len(signals) > 0:
                # Count how many times the next day was positive
                wins = len(signals[signals['Next_Day_Return'] > 0])
                accuracy_rate = (wins / len(signals)) * 100
            
            # 4. Check Today's Signal (Live)
            if df['Signal'].iloc[-1]:
                results.append({
                    "Stock Name": get_clean_name(ticker),
                    "Accuracy Rate": f"{accuracy_rate:.1f}%",
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Status": "🔥 Bullish"
                })
        except:
            continue
            
    return pd.DataFrame(results)

# UI
st.title("🚀 ERROR09 - Bullish Scanner with Backtest")
if st.button("🔍 Run Live Scan"):
    tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    df = run_backtest_scanner(tickers)
    
    if not df.empty:
        st.success("Scanner Results Found:")
        # Displaying Table with Name and Accuracy
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Aaj market mein koi stock criteria match nahi kar raha hai.")
        

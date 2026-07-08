import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# Page Configuration
st.set_page_config(layout="wide", page_title="ERROR09 Scanner")

def get_scanned_data(tickers):
    # Fetch Data
    # Hum 550 days ka data lete hain taaki 500 days ka max rolling window calculate ho sake
    data = yf.download(tickers, period="2y", interval="1d", group_by='ticker', progress=False)
    
    final_results = []
    
    for ticker in tickers:
        try:
            # Data cleaning
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 500: continue
            
            # --- FORMULA TRANSLATION ---
            # 1. Volume > SMA(Volume, 20)
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            
            # 2. Daily % Change (1 candle ago)
            df['Pct_Change'] = df['Close'].pct_change() * 100
            
            # 3. 20 Days Return >= 3%
            df['Ret_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
            
            # 4. Turnover (Close * Volume) > 50Cr (500,000,000)
            df['Turnover'] = df['Close'] * df['Volume']
            
            # 5. Max(2, 20 days ago High) >= Max(200, 31 days ago High)
            df['Max_2_20_Ago'] = df['High'].shift(20).rolling(2).max()
            df['Max_200_31_Ago'] = df['High'].shift(31).rolling(200).max()
            
            # 6. Close >= 1 day ago Max(500, Daily High)
            df['Max_500_1_Ago'] = df['High'].shift(1).rolling(500).max()
            
            # --- COMBINED SIGNAL ---
            # Formula: Close>=20 AND %Change(1-11) AND Vol>SMA20 AND Ret20d>=3 AND Turnover>50cr AND Condition5 AND Condition6
            df['Signal'] = (
                (df['Close'] >= 20) &
                (df['Pct_Change'] >= 1) & (df['Pct_Change'] <= 11) &
                (df['Volume'] > df['Vol_SMA20']) &
                (df['Ret_20d'] >= 3) &
                (df['Turnover'] > 500000000) &
                (df['Max_2_20_Ago'] >= df['Max_200_31_Ago']) &
                (df['Close'] >= df['Max_500_1_Ago'])
            )
            
            # Next Day Move for Accuracy
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100
            
            # --- ANALYTICS ---
            # If Signal is true today
            if df['Signal'].iloc[-1]:
                # Backtest Accuracy Calculation (Last 2 months)
                hist = df.iloc[-45:]
                signals = hist[hist['Signal'] == True]
                acc = 0
                if len(signals) > 0:
                    acc = (len(signals[signals['Next_Day_Return'] > 0]) / len(signals)) * 100
                
                final_results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Accuracy": f"{round(acc, 2)}%",
                    "Status": "✅ Breakout"
                })
        except Exception:
            continue
            
    return pd.DataFrame(final_results)

# UI Implementation
st.title("📈 ERROR09 - Chartink Logic Scanner")
tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]

if st.button("🚀 Run Scanner"):
    df = get_scanned_data(tickers)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Abhi koi stock formula match nahi kar raha hai.")
        

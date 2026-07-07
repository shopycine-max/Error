import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Page Config
st.set_page_config(page_title="ERROR09 - Bullish Scanner", layout="wide")

# UI Styling
st.title("🚀 ERROR09 - Live Bullish Breakout Scanner")
st.markdown("---")

# List of Stocks (You can expand this list)
tickers = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]

def calculate_scanner(tickers):
    data = yf.download(tickers, period="1y", interval="1d", progress=False, group_by='ticker')
    results = []
    
    for ticker in tickers:
        try:
            # Handle Single vs Multi-ticker download
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            
            # --- CALCULATING INDICATORS ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = df['Close'].pct_change(20) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            
            # Complex Filters
            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500).max()
            
            # Next Day Move for Accuracy
            df['Next_Day_Move'] = df['Close'].shift(-1) - df['Close']
            
            # --- APPLYING FILTERS ---
            c1 = df['Close'] >= 20
            c2 = (df['Pct_Change'] >= 1) & (df['Pct_Change'] <= 11)
            c3 = df['Volume'] > df['Vol_SMA20']
            c4 = df['Return_20d'] >= 3
            c5 = df['Turnover'] > 500000000
            c6 = df['Max_2_High_20_Ago'] >= df['Max_200_High_31_Ago']
            c7 = df['Close'] >= df['Max_500_High_1d_Ago']
            
            df['Signal'] = c1 & c2 & c3 & c4 & c5 & c6 & c7
            
            # --- ACCURACY LOGIC ---
            history = df.iloc[-45:] # 2 month backtest
            signals = history[history['Signal'] == True]
            accuracy = 0
            if len(signals) > 0:
                wins = len(signals[signals['Next_Day_Move'] > 0])
                accuracy = (wins / len(signals)) * 100
            
            # Append Results
            if df['Signal'].iloc[-1]:
                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "Accuracy Rate": f"{round(accuracy, 2)}%",
                    "Status": "🔥 Bullish Signal"
                })
        except:
            continue
    return pd.DataFrame(results)

# --- UI & LOGIC ---
if st.button("🚀 Run Live Scan"):
    with st.spinner('Analyzing Markets...'):
        df_results = calculate_scanner(tickers)
        
        if not df_results.empty:
            st.success(f"Found {len(df_results)} matching stocks!")
            st.dataframe(df_results, use_container_width=True)
            
            # Visualizing the Signals
            fig = px.bar(df_results, x="Stock", y="LTP", color="Accuracy Rate", title="Bullish Candidates")
            st.plotly_chart(fig)
        else:
            st.warning("Aaj koi stock criteria match nahi kiya.")

# --- Backtest Section ---
st.markdown("---")
st.subheader("📊 2-Month Historical Log Sheet")
if st.button("Check Historical Logs"):
    # Here you can display a full table of past signals
    st.info("Showing past 60 days signals...")
    

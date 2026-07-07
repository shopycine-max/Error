import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(page_title="Pro Momentum Scanner", layout="wide")

# Styling
st.markdown("""
    <style>
    .metric-card { background-color: #0e1117; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    h1 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Momentum Breakout Scanner")

# --- Formula Logic Engine ---
def apply_scanner_logic(df):
    """Applies your specific Chartink-style formula"""
    # Base indicators
    df['Pct_Change'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    df['Return_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
    df['Turnover'] = df['Close'] * df['Volume']
    
    # User's Specific Formula Logic
    cond1 = df['Close'] >= 20
    # Market Cap: Note - yfinance historical doesn't have market cap. 
    # Add manual static list filtering if needed.
    cond3 = (df['Pct_Change'] <= 11) & (df['Pct_Change'] >= 1)
    cond4 = df['Volume'] > (df['Vol_SMA20'] * 1)
    cond5 = df['Return_20d'] >= 3
    cond6 = df['Turnover'] > 500000000
    
    # Technical Lookbacks
    df['Max_2_20d_ago'] = df['High'].shift(20).rolling(2).max()
    df['Max_200_31d_ago'] = df['High'].shift(31).rolling(200).max()
    df['Max_500_1d_ago'] = df['High'].shift(1).rolling(500).max()
    
    cond7 = df['Max_2_20d_ago'] >= df['Max_200_31d_ago']
    cond8 = df['Close'] >= df['Max_500_1d_ago']
    
    df['Signal'] = cond1 & cond3 & cond4 & cond5 & cond6 & cond7 & cond8
    df['Next_Day_Return'] = df['Close'].shift(-1).pct_change(periods=1) * 100
    return df

# --- Execution ---
tickers = ["CUPID.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "RELIANCE.NS", "TCS.NS"] # Add your list
st.sidebar.header("Controls")
if st.sidebar.button("Run Scanner"):
    all_results = []
    
    # Fetch Data
    data = yf.download(tickers, period="2y", interval="1d", group_by='ticker', progress=False)
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna()
            df = apply_scanner_logic(df)
            
            # Filter valid signals
            signals = df[df['Signal'] == True].copy()
            if not signals.empty:
                last_sig = signals.iloc[-1]
                all_results.append({
                    "Symbol": ticker,
                    "LTP": round(last_sig['Close'], 2),
                    "Signals Found": len(signals),
                    "Accuracy": round((len(signals[signals['Next_Day_Return'] > 0]) / len(signals)) * 100, 2)
                })
        except: continue
        
    # Results Display
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.subheader("🚀 High Momentum Stocks Found")
        st.dataframe(res_df, use_container_width=True)
        
        # Best Momentum Selection
        best_stock = res_df.loc[res_df['Accuracy'].idxmax()]
        st.metric("Best Momentum Stock (Historical Accuracy)", best_stock['Symbol'], f"{best_stock['Accuracy']}% Success Rate")
    else:
        st.warning("No stocks matching the exact formula found today.")

# --- Disclaimer ---
st.caption("Disclaimer: This tool is for educational purposes. Backtesting accuracy is based on historical data only.")

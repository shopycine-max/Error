import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io

# --- Page Config ---
st.set_page_config(page_title="Pro Momentum Terminal", layout="wide")

# Theme
st.markdown("""
    <style>
    .metric-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Pro Momentum Scanner Terminal")

# --- Logic: Indicators ---
def add_pro_indicators(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return df

# --- Logic: Scanner ---
def run_scanner(tickers):
    data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
    results = []
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            df = add_pro_indicators(df)
            
            # --- Original Formula ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            # (Adding conditions here)
            is_valid = (df['Close'] >= 20) & \
                       (df['Pct_Change'].between(1, 11)) & \
                       (df['Volume'] > df['Volume'].rolling(20).mean()) & \
                       (df['Close'] > df['EMA_20']) # Momentum Confirmation
            
            if is_valid.iloc[-1]:
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Trend": "Bullish" if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] else "Neutral"
                })
        except: continue
    return pd.DataFrame(results)

# --- UI: Sidebar ---
st.sidebar.header("Filter Settings")
# (Universe logic here)
all_tickers = ["CUPID.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "RELIANCE.NS"] # Add yours

# --- Main Dashboard ---
if st.button("🚀 Execute Market Scan"):
    res_df = run_scanner(all_tickers)
    
    if not res_df.empty:
        # Metrics Row
        col1, col2, col3 = st.columns(3)
        col1.metric("Signals Found", len(res_df))
        col2.metric("Market Sentiment", "Bullish" if len(res_df) > 0 else "Neutral")
        col3.metric("Avg RSI", round(res_df['RSI'].mean(), 2))
        
        st.subheader("📋 Top Momentum Picks")
        st.dataframe(res_df, use_container_width=True)
        
        # Pro Visualizer
        st.subheader("📉 Technical Visualizer")
        sel_stock = st.selectbox("Analyze Stock", res_df['Symbol'].tolist())
        
        # Charting
        df_chart = yf.download(f"{sel_stock}.NS", period="6mo", interval="1d", progress=False)
        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].ewm(span=20).mean(), line=dict(color='orange'), name='EMA 20'))
        fig.update_layout(template="plotly_dark", title=f"{sel_stock} Trend Analysis")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No high-momentum setups detected today.")
        

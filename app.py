import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io

# --- Page Configurations ---
st.set_page_config(page_title="Pro Momentum Terminal", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Pro Momentum Terminal")

# --- Universe Helper ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    if universe_type == "📸 Chartink Test (5 Stocks)":
        return target_stocks
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        return [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()] + target_stocks
    except:
        return target_stocks

# --- Scanner Engine ---
def process_market_analytics(tickers, rsi_limit, vol_mult):
    results = []
    data = yf.download(tickers, period="6mo", interval="1d", progress=False, group_by='ticker')
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            
            # --- Technical Indicators ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            # RSI Calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # --- Your Original Formula ---
            cond_momentum = (df['Close'] >= 20) & \
                            (df['Pct_Change'].between(1, 11)) & \
                            (df['Volume'] > (df['Vol_SMA20'] * vol_mult)) & \
                            (df['RSI'] >= rsi_limit) & \
                            (df['Close'] > df['EMA_20']) # Trend Confirmation
            
            if cond_momentum.iloc[-1]:
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(df['Close'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Trend": "Bullish" if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1] else "Neutral"
                })
        except: continue
        
    return pd.DataFrame(results)

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Scanner Controls")
universe = st.sidebar.selectbox("Scanning Universe", ["📸 Chartink Test (5 Stocks)", "Nifty 500"])
rsi_threshold = st.sidebar.slider("Min RSI Strength", 40, 70, 55)
vol_sensitivity = st.sidebar.slider("Volume Sensitivity (Multiplier)", 1.0, 3.0, 1.2, 0.1)

# --- App Logic ---
all_tickers = get_scanning_universe(universe)

if st.sidebar.button("🚀 Run Professional Scan"):
    res_df = process_market_analytics(all_tickers, rsi_threshold, vol_sensitivity)
    
    if not res_df.empty:
        st.success(f"Found {len(res_df)} potential breakout candidates.")
        st.dataframe(res_df, use_container_width=True)
        
        # --- Interactive Visualizer ---
        st.subheader("📊 Technical Visualizer")
        selected_stock = st.selectbox("Analyze Selected Stock", res_df['Symbol'].tolist())
        
        data_chart = yf.download(f"{selected_stock}.NS", period="6mo", interval="1d", progress=False)
        fig = go.Figure(data=[go.Candlestick(x=data_chart.index, open=data_chart['Open'], high=data_chart['High'], low=data_chart['Low'], close=data_chart['Close'])])
        fig.add_trace(go.Scatter(x=data_chart.index, y=data_chart['Close'].ewm(span=20).mean(), line=dict(color='orange', width=1.5), name='EMA 20'))
        fig.update_layout(template="plotly_dark", title=f"{selected_stock} Trend Analysis")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No stocks met the criteria. Try lowering the 'Min RSI' or 'Volume Sensitivity' in the sidebar.")
        

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io

# Page Configurations
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

# CSS Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Pro Momentum Stock Scanner")

# --- Helper: Data Fetching ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    if universe_type == "📸 Chartink Test (5 Stocks)":
        return target_stocks
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
        return nse_tickers + [s for s in target_stocks if s not in nse_tickers]
    except:
        return target_stocks

# --- Helper: Technical Indicators ---
def add_indicators(df):
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- Helper: Charting ---
def plot_stock_chart(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    
    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].ewm(span=20).mean(), name='EMA 20', line=dict(color='orange')))
    fig.update_layout(title=f"{ticker} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Scanner Controls")
universe_choice = st.sidebar.selectbox("Universe", ["📸 Chartink Test (5 Stocks)", "Nifty 500"])
rsi_min = st.sidebar.slider("Min RSI", 40, 70, 60)
vol_mult = st.sidebar.slider("Volume Multiplier (vs 20SMA)", 1.0, 3.0, 1.5, 0.1)

all_tickers = get_scanning_universe(universe_choice)

# --- Scanner Engine ---
def run_scanner(mode="live"):
    results = []
    data = yf.download(all_tickers, period="2y", interval="1d", progress=False, group_by='ticker')
    
    for ticker in all_tickers:
        try:
            df = data[ticker].dropna() if len(all_tickers) > 1 else data.dropna()
            df = add_indicators(df)
            
            # Logic
            cond_momentum = (df['RSI'] > rsi_min) & (df['EMA_20'] > df['EMA_50']) & (df['Volume'] > df['Vol_SMA20'] * vol_mult)
            
            if mode == "live" and cond_momentum.iloc[-1]:
                results.append({"Symbol": ticker.replace(".NS", ""), "LTP": round(df['Close'].iloc[-1], 2), "RSI": round(df['RSI'].iloc[-1], 2)})
            elif mode == "backtest":
                signals = df[cond_momentum]
                for date, row in signals.tail(5).iterrows():
                    results.append({"Date": date.strftime('%Y-%m-%d'), "Symbol": ticker.replace(".NS", ""), "Price": round(row['Close'], 2)})
        except: continue
    return pd.DataFrame(results)

# --- Main App ---
tab1, tab2 = st.tabs(["⚡ Live Radar", "📊 Historical Scan"])

with tab1:
    if st.button("🚀 Run Live Scan"):
        res = run_scanner("live")
        if not res.empty:
            st.dataframe(res)
            selected_stock = st.selectbox("View Chart", res['Symbol'].tolist())
            plot_stock_chart(f"{selected_stock}.NS")
        else: st.warning("No stocks matching current criteria.")

with tab2:
    if st.button("📊 Run Backtest"):
        res = run_scanner("backtest")
        st.dataframe(res)
        

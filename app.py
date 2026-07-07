import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io

# --- Page Config ---
st.set_page_config(page_title="Pro Momentum Scanner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    h1 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Momentum Breakout Scanner")

# --- 1. Data Universe ---
@st.cache_data(ttl=43200)
def get_tickers():
    # Including Target Stocks + Nifty 500
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        nse = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
        return list(set(nse + target_stocks))
    except:
        return target_stocks

# --- 2. Indicators Calculation ---
def calculate_indicators(df):
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    df['Return_20d'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
    df['Turnover'] = df['Close'] * df['Volume']
    
    # Technicals
    df['Max_2_20d_ago'] = df['High'].shift(20).rolling(2).max()
    df['Max_200_31d_ago'] = df['High'].shift(31).rolling(200).max()
    df['Max_500_1d_ago'] = df['High'].shift(1).rolling(500).max()
    return df

# --- 3. Scanner Core ---
def run_scanner(tickers, relaxed_mode):
    results = []
    # Download data (Batch download for speed)
    data = yf.download(tickers, period="2y", interval="1d", group_by='ticker', progress=False)
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            df = calculate_indicators(df)
            
            # --- Your Formula Logic ---
            c1 = df['Close'] >= 20
            c3 = (df['Pct_Change'] <= 11) & (df['Pct_Change'] >= 1)
            c4 = df['Volume'] > df['Vol_SMA20']
            c5 = df['Return_20d'] >= 3
            c6 = df['Turnover'] > 500000000 # 50 Cr
            c7 = df['Max_2_20d_ago'] >= df['Max_200_31d_ago']
            c8 = df['Close'] >= df['Max_500_1d_ago']
            
            if relaxed_mode:
                df['Signal'] = c1 & c3 & c4 & c5
            else:
                df['Signal'] = c1 & c3 & c4 & c5 & c6 & c7 & c8
            
            if df['Signal'].iloc[-1]:
                results.append({"Symbol": ticker.replace(".NS", ""), "LTP": round(df['Close'].iloc[-1], 2)})
        except: continue
    return pd.DataFrame(results)

# --- 4. Dashboard UI ---
st.sidebar.header("⚙️ Controls")
relaxed = st.sidebar.checkbox("Relax Filters (If no results found)", value=False)
if st.sidebar.button("Run Scan"):
    with st.spinner("Scanning Market..."):
        all_tickers = get_tickers()
        df_res = run_scanner(all_tickers, relaxed)
        
        if not df_res.empty:
            st.success(f"Found {len(df_res)} stocks!")
            st.dataframe(df_res, use_container_width=True)
            
            # Charting
            sel_stock = st.selectbox("Select stock to view chart", df_res['Symbol'].tolist())
            data = yf.download(f"{sel_stock}.NS", period="6mo", interval="1d", progress=False)
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", title=f"{sel_stock} Chart")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No stocks matching this formula today. Try turning on 'Relax Filters'.")

st.info("Formula: Price > 20, 1% < Day Change < 11%, Volume > SMA20, 20D Return > 3%.")

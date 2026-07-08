import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner v2.0", page_icon="🚀", layout="wide")

# Custom Dark Premium Theme & Table Styling
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; border-radius: 8px; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #2ea043; border-color: white; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    h1, h2, h3 { color: #58a6ff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .css-1d391kg { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 AlphaTrade Momentum Terminal")
st.caption("Advanced Engine: RSI, MACD, Bollinger Bands, & Volume Shocks for High-Conviction Breakouts")

# --- Reliable Universe Fetcher ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS", "ZOMATO.NS", "TATASTEEL.NS"]
    
    if universe_type == "📸 Quick Test (7 Stocks)":
        return target_stocks

    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            nse_tickers = [str(sym).strip() + ".NS" for sym in df['Symbol'].dropna()]
            
            for stock in target_stocks:
                if stock not in nse_tickers:
                    nse_tickers.append(stock)
            return nse_tickers
    except Exception:
        pass
    return target_stocks

# --- Sidebar Pro Settings Panel ---
st.sidebar.header("⚙️ Terminal Controls")
universe_choice = st.sidebar.selectbox("Scanning Universe", ["📸 Quick Test (7 Stocks)", "Nifty 500"])

with st.sidebar.expander("📈 Trend & Momentum Filters", expanded=True):
    rsi_filter = st.slider("Min RSI (Strength)", 50, 80, 60)
    req_macd = st.checkbox("Require MACD Bullish", value=True)
    req_bb = st.checkbox("Price Near Upper Bollinger Band", value=False)
    dist_52w = st.slider("Max Distance from 52W High (%)", 5, 50, 20)

with st.sidebar.expander("📊 Volume & Price Filters", expanded=True):
    volume_multiplier = st.slider("Volume Shock (Multiplier)", 1.0, 5.0, 2.0, step=0.1)
    min_price = st.number_input("Minimum Stock Price (₹)", value=20)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.success(f"Total Stocks Loaded: **{len(all_tickers)}**")

# --- Core Scanner Engine ---
def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: return pd.DataFrame()

    try:
        data = yf.download(tickers, period="2y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0, text="Scanning Market Data...")
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers), text=f"Analyzing {ticker}...")
        try:
            if len(tickers) > 1:
                if ticker in data.columns.levels[0]: df = data[ticker].dropna(subset=['Close']).copy()
                else: continue
            else:
                df = data.dropna(subset=['Close']).copy()

            if len(df) < 260: continue # Need enough data for 52W High (approx 252 trading days)

            # --- Base Metrics ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Turnover'] = df['Close'] * df['Volume']
            df['High_52W'] = df['High'].rolling(252).max()
            df['Dist_52W_High'] = ((df['High_52W'] - df['Close']) / df['High_52W']) * 100
            
            # --- Indicators: RSI, EMA, Bollinger Bands, MACD ---
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # MACD
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            # Bollinger Bands
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['STD_20'] = df['Close'].rolling(window=20).std()
            df['Upper_BB'] = df['SMA_20'] + (df['STD_20'] * 2)

            df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

            # --- Filter Logic ---
            cond_price = df['Close'] >= min_price
            cond_vol = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
            cond_rsi = df['RSI'] >= rsi_filter
            cond_trend = df['Close'] > df['EMA_20']
            cond_52w = df['Dist_52W_High'] <= dist_52w
            
            cond_macd = (df['MACD'] > df['MACD_Signal']) if req_macd else True
            cond_bb = (df['Close'] >= (df['Upper_BB'] * 0.98)) if req_bb else True # Within 2% of Upper BB

            df['Signal'] = cond_price & cond_vol & cond_rsi & cond_trend & cond_52w & cond_macd & cond_bb

            if mode == "live" and df['Signal'].iloc[-1]:
                vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(df['Close'].iloc[-1], 2),
                    "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Vol Spike (x)": round(vol_spike, 1),
                    "From 52W High (%)": round(df['Dist_52W_High'].iloc[-1], 2),
                    "Score": round(df['RSI'].iloc[-1] + (vol_spike * 15), 2)
                })
                
            elif mode == "backtest":
                history_slice = df.iloc[-60:-1] 
                triggers = history_slice[history_slice['Signal'] == True]
                for date, row in triggers.iterrows():
                    results.append({
                        "Date": date.strftime('%Y-%m-%d'),
                        "Symbol": ticker.replace(".NS", ""),
                        "Trigger Price (₹)": round(row['Close'], 2),
                        "RSI": round(row['RSI'], 2),
                        "Next Day Move (%)": round(row['Next_Day_Return'], 2) if not pd.isna(row['Next_Day_Return']) else 0.0
                    })
        except Exception: continue

    progress_bar.empty()
    return pd.DataFrame(results)

# --- Style Functions ---
def color_surplus(val):
    if type(val) == str: return ''
    color = '#00ff00' if val > 0 else '#ff4b4b' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold;'

def color_rsi(val):
    if type(val) == str: return ''
    color = '#00ff00' if val >= 70 else '#ffa500' if val >= 60 else 'white'
    return f'color: {color};'

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Radar", "⏳ Backtester"])

with tab1:
    st.subheader("📡 Live Momentum Breakout Radar")
    if st.button("🚀 Run Advanced Scan", key="live_btn"):
        res_df = process_market_analytics(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🔥 Found {len(res_df)} explosive momentum stocks!")
            
            # Use .map() instead of .applymap() to avoid Pandas errors
            styled_df = res_df.style.map(color_surplus, subset=['Day Change (%)'])\
                                    .map(color_rsi, subset=['RSI'])\
                                    .background_gradient(subset=['Score'], cmap='Greens')
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Interactive Premium Chart for Top Stock
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Pick Analysis: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="6mo", interval="1d", progress=False)
            
            if not chart_data.empty:
                chart_data['SMA_20'] = chart_data['Close'].rolling(20).mean()
                chart_data['Upper_BB'] = chart_data['SMA_20'] + (chart_data['Close'].rolling(20).std() * 2)
                chart_data['Lower_BB'] = chart_data['SMA_20'] - (chart_data['Close'].rolling(20).std() * 2)
                
                # Subplots for Price and Volume
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # Candlesticks
                fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Upper_BB'], line=dict(color='cyan', width=1, dash='dot'), name='Upper BB'), row=1, col=1)
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Lower_BB'], line=dict(color='cyan', width=1, dash='dot'), name='Lower BB'), row=1, col=1)
                
                # Volume
                colors = ['green' if close >= open else 'red' for close, open in zip(chart_data['Close'], chart_data['Open'])]
                fig.add_trace(go.Bar(x=chart_data.index, y=chart_data['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                
                fig.update_layout(template="plotly_dark", title=f"{top_stock} - Pro Chart View", height=600, showlegend=False)
                fig.update_yaxes(title_text="Price", row=1, col=1)
                fig.update_yaxes(title_text="Volume", row=2, col=1)
                fig.update_xaxes(rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Koi stock in strict conditions ko meet nahi kar raha. Sidebar se filters thode relax karein (jaise Volume ya RSI kam karein).")

with tab2:
    st.subheader("⏳ Historical Analytics (Last 60 Days)")
    st.caption("Test karein ki aapki strategy pichle 2 mahino mein kaisa perform ki hai.")
    
    if st.button("📊 Run Backtest", key="bt_btn"):
        bt_df = process_market_analytics(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            bullish_days = len(bt_df[bt_df['Next Day Move (%)'] > 0])
            accuracy = round((bullish_days / len(bt_df)) * 100, 2) if len(bt_df) > 0 else 0
            avg_return = round(bt_df['Next Day Move (%)'].mean(), 2)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Signals", len(bt_df))
            col2.metric("Bullish Accuracy", f"{accuracy}%", f"{accuracy-50}% vs Coin Flip")
            col3.metric("Avg Next Day Return", f"{avg_return}%", color_normal="normal")
            
            # Use .map() instead of .applymap() here as well
            styled_bt = bt_df.style.map(color_surplus, subset=['Next Day Move (%)'])
            st.dataframe(styled_bt, use_container_width=True, hide_index=True)
            
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Excel Sheet", data=csv_data, file_name="pro_backtest.csv", mime="text/csv")
        else:
            st.warning("Pichle 60 dino mein in parameters par koi trades trigger nahi huye.")
            

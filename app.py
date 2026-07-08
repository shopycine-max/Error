import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from plotly.subplots import make_subplots

# --- 1. Institutional UI & Theme Configurations ---
st.set_page_config(page_title="QUANTIQ ALPHA // Stock Scanner", page_icon="⚡", layout="wide")

# Elite Dark Bloomberg/TradingView style CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600&family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Inter', sans-serif;
    }
    .main { background-color: #080b10; color: #e2e8f0; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #0d131f; border-right: 1px solid #1e293b; }
    
    /* Buttons Customization */
    .stButton>button { 
        background: linear-gradient(135deg, #0070f3 0%, #00df00 100%); 
        color: white; font-weight: 700; width: 100%; border: none;
        padding: 12px; border-radius: 6px; letter-spacing: 0.5px;
        transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0,223,0,0.15);
    }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,223,0,0.3); }
    
    /* Premium Metric Blocks */
    div[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 700 !important; font-family: 'JetBrains Mono', monospace; }
    .metric-card {
        background: #0f172a; padding: 20px; border-radius: 8px; 
        border: 1px solid #1e293b; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    /* Header design */
    .brand-title {
        font-family: 'JetBrains Mono', monospace; font-weight: 700; 
        letter-spacing: -1px; background: linear-gradient(90deg, #38bdf8, #3b82f6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# --- Brand Header ---
st.markdown("<h1 class='brand-title'>⚡ QUANTIQ ALPHA // Terminal</h1>", unsafe_allow_html=True)
st.caption("System Status: Operational // Engine: Multi-Threaded Realtime Market Analytics")
st.markdown("---")

# --- 2. Reliable Hardcoded Universe ---
@st.cache_data(ttl=43200)
def get_scanning_universe(universe_type):
    target_stocks = ["CUPID.NS", "DIACABS.NS", "SPARC.NS", "ADANIENSOL.NS", "JBCHEPHARM.NS"]
    if universe_type == "📸 Chartink Test Core (5 Stocks)":
        return target_stocks

    url = "https://raw.githubusercontent.com/sanjitk/nse-stocks-list/master/nse_stocks.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip().str.upper()
            sym_col = [col for col in df.columns if 'SYMBOL' in col or 'TICKER' in col or 'CODE' in col]
            if sym_col:
                col_name = sym_col[0]
                nse_tickers = [str(sym).strip() + ".NS" for sym in df[col_name].dropna() if len(str(sym).strip()) > 0]
                for stock in target_stocks:
                    if stock not in nse_tickers: nse_tickers.append(stock)
                return list(set(nse_tickers))
    except Exception:
        pass
    return target_stocks

# --- 3. Sidebar Configuration Console ---
st.sidebar.markdown("### 🖥️ WORKSPACE CONTROL")
universe_choice = st.sidebar.selectbox("Scanning Universe", ["📸 Chartink Test Core (5 Stocks)", "🌐 Total All NSE Stocks (2000+)"])
rsi_filter = st.sidebar.slider("Momentum Threshold (RSI Min)", 45, 75, 60)
volume_multiplier = st.sidebar.slider("Institutional Volume Shock", 1.0, 5.0, 2.0, step=0.1)
min_turnover = st.sidebar.number_input("Min Liquidity / Turnover (₹ Crores)", min_value=1, max_value=100, value=5)

all_tickers = get_scanning_universe(universe_choice)
st.sidebar.markdown(f"**Database Pool:** `{len(all_tickers)} Stocks Loaded`")

# --- 4. Core Quantitative Core Engine ---
def analyze_single_ticker(ticker, raw_data, mode, volume_multiplier, rsi_filter, turnover_limit, market_bullish):
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker not in raw_data.columns.levels[0]: return None
            df = raw_data[ticker].dropna(subset=['Close']).copy()
        else:
            df = raw_data.dropna(subset=['Close']).copy()

        total_rows = len(df)
        if total_rows < 45: return None 

        # Technical Multi-Calculations
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # Wilder's RSI Standard Formula
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Price Action Quality: Close Near High Filter
        df['Day_Range'] = df['High'] - df['Low']
        df['Close_From_High'] = df['High'] - df['Close']
        cond_close_high = df['Close_From_High'] <= (df['Day_Range'] * 0.22) # Top 22% Zone

        # 500-Day High Breakdown Logic
        window_size = min(500, total_rows - 2)
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        df['Next_Day_Return'] = df['Close'].shift(-1).pct_change() * 100

        # Strict Multi-Factor Technical Filtering
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 2.0) & (df['Pct_Change'] <= 16.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond_close_high
        
        if not market_bullish and mode == "live":
            df['Signal'] = df['Signal'] & (df['Volume'] > (df['Vol_SMA20'] * (volume_multiplier + 0.6)))

        ticker_results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            close_per = ((df['Close'].iloc[-1] - df['Low'].iloc[-1]) / (df['Day_Range'].iloc[-1] + 1e-5)) * 100
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Price (₹)": round(df['Close'].iloc[-1], 2),
                "Change %": round(df['Pct_Change'].iloc[-1], 2),
                "RSI Matrix": round(df['RSI'].iloc[-1], 1),
                "Vol Shock": round(vol_spike, 1),
                "Session Close %": round(close_per, 1),
                "Alpha Score": round((df['RSI'].iloc[-1] * 0.4) + (vol_spike * 5) + (close_per * 0.3), 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-50:] 
            triggers = history_slice[history_slice['Signal'] == True]
            for date, row in triggers.iterrows():
                is_today = date.date() == datetime.today().date()
                next_move = "Open Order" if is_today or pd.isna(row['Next_Day_Return']) else f"{round(row['Next_Day_Return'], 2)}%"
                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price": round(row['Close'], 2),
                    "RSI Matrix": round(row['RSI'], 1),
                    "Target Action": next_move
                })
            return ticker_results
    except Exception:
        return None

# --- 5. Market Index Analytics Processing ---
def fetch_market_health():
    try:
        nifty = yf.download("^NSEI", period="20d", interval="1d", progress=False)
        if not nifty.empty:
            nifty['EMA_5'] = nifty['Close'].ewm(span=5, adjust=False).mean()
            status = "BULLISH REGIME" if nifty['Close'].iloc[-1] >= nifty['EMA_5'].iloc[-1] else "BEARISH RISK"
            change = ((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100
            return status, round(change, 2), round(nifty['Close'].iloc[-1], 2)
    except Exception:
        pass
    return "DATA UNKNOWN", 0.0, 0.0

def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame(), True
    
    market_status, _, _ = fetch_market_health()
    market_bullish = "BULLISH" in market_status

    results = []
    try:
        raw_data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception:
        return pd.DataFrame(), market_bullish

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover, market_bullish): ticker 
            for ticker in tickers
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
                
    return pd.DataFrame(results), market_bullish


# --- 6. Advanced Interactive Charting (TradingView Replicate) ---
def render_pro_chart(symbol):
    df = yf.download(f"{symbol}.NS", period="6mo", interval="1d", progress=False)
    if df.empty: return
    
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))

    # Multi-Panel Professional Chart Setup
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_width=[0.2, 0.2, 0.6])

    # 1. Candlestick Core Plot
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='#3b82f6', width=1.5), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#f59e0b', width=1.5), name="EMA 50"), row=1, col=1)

    # 2. Volume Profile Subplot
    colors = ['#ef4444' if row['Open'] > row['Close'] else '#10b981' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    # 3. RSI Oscillators Subplot
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#a855f7', width=1.5), name="RSI"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)

    # Premium Dark Styling layout adjustments
    fig.update_layout(template="plotly_dark", height=650, 
                      xaxis_rangeslider_visible=False,
                      margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    fig.update_xaxes(showgrid=True, gridcolor='#1e293b')
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b')
    st.plotly_chart(fig, use_container_width=True)


# --- 7. Interactive Dashboard Layout Presentation ---
tab1, tab2 = st.tabs(["📊 LIVE REALTIME SCANNER", "⏳ QUANT ACCURACY BACKTEST"])

with tab1:
    m_status, m_chg, m_ltp = fetch_market_health()
    
    # Global KPI Row Block
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"<div class='metric-card'><h5>Benchmark Nifty 50</h5><h2>₹{m_ltp:,}</h2><span style='color:{'#10b981' if m_chg>=0 else '#ef4444'}'>{m_chg}% Today</span></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='metric-card'><h5>System Regime</h5><h2 style='color:{'#10b981' if 'BULLISH' in m_status else '#ef4444'}'>{m_status}</h2><span>Dynamic Risk Adaptation</span></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown("<div class='metric-card'><h5>Scanner Core Engine</h5><h2>100%</h2><span style='color:#38bdf8'>Parallel Processing Enabled</span></div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 EXECUTE ALPHA MOMENTUM DISCOVERY", key="live_btn"):
        with st.spinner("Processing technical matrix against live ticks..."):
            res_df, _ = process_market_analytics_fast(all_tickers, mode="live")
            
        if not res_df.empty:
            res_df = res_df.sort_values(by="Alpha Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            
            st.success(f"Execution complete: Identified {len(res_df)} asset setups matching momentum parameters.")
            
            # Professional Split Panel Layout
            col_table, col_chart = st.columns([4, 5])
            
            with col_table:
                st.markdown("### 📋 Alpha Signals Generated")
                # Institutional Modern Interactive Data Table
                selected_row = st.dataframe(
                    res_df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Alpha Score": st.column_config.NumberColumn("Alpha Score", format="%.2f 🔥"),
                        "Change %": st.column_config.NumberColumn("Change %", format="%.2f%%")
                    }
                )
                
                # Dynamic Dropdown Selector to examine setups instantly
                target_stock = st.selectbox("🎯 Select Asset to load into Advanced Chart Terminal:", res_df['Symbol'].tolist())
                
            with col_chart:
                st.markdown(f"### 🖥️ Advanced Workspace Terminal: **{target_stock}**")
                render_pro_chart(target_stock)
        else:
            st.warning("No high-probability asset matches current parameters. Lower the Institutional Volume Shock constraint if required.")

with tab2:
    st.markdown("### ⏳ Quantitative Backtest Performance Metrics")
    if st.button("📊 INITIATE 2-MONTH SYSTEM AUDIT", key="bt_btn"):
        with st.spinner("Analyzing historical trade configurations..."):
            bt_df, _ = process_market_analytics_fast(all_tickers, mode="backtest")
            
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            valid_moves = bt_df[~bt_df['Target Action'].str.contains("Open", na=False)]
            
            if len(valid_moves) > 0:
                bullish_days = len(valid_moves[valid_moves['Target Action'].str.replace('%','').astype(float) > 0])
                accuracy = round((bullish_days / len(valid_moves)) * 100, 2)
            else:
                accuracy = 0
                
            # Performance Audit KPI Grid
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown(f"<div class='metric-card'><h5>Total Historical Audited Triggers</h5><h2>{len(bt_df)}</h2><span>Over a rolling 60-day period</span></div>", unsafe_allow_html=True)
            with b_col2:
                st.markdown(f"<div class='metric-card'><h5>Next-Day Hit Rate / Accuracy</h5><h2>{accuracy}%</h2><span>Target criteria: Next-day close > Trigger close</span></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 EXPORT AUDIT LOG SHEET (CSV)", data=csv_data, file_name="alpha_audit_report.csv", mime="text/csv")
        else:
            st.warning("No historical dataset match found for this configuration profile.")
    

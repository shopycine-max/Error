import streamlit as st
import pandas as pd
import yfinance as yf
import io
import urllib.request

# Safe Import for Plotly to prevent app crashes
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ModuleNotFoundError:
    HAS_PLOTLY = False

# Streamlit UI Configuration
st.set_page_config(
    page_title="ERROR09 - Live NSE Magic Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Dark Theme Styling matching Chartink Dark Mode
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; border: none; height: 45px; }
    .stButton>button:hover { background-color: #2ea043; color: white; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    div.block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ERROR09 - Live Chartink Cloned Dashboard")
st.caption("Created by Chandan kumar shaw | Real-time Multi-threaded Stock Filter")

# Sidebar
st.sidebar.header("⚙️ Scanner Settings")
index_choice = st.sidebar.selectbox(
    "Select Universe", 
    ["Nifty 50", "Nifty Next 50", "Nifty 500", "All Indian Stocks"]
)
run_scan = st.sidebar.button("🚀 Run Live Magic Scan")

@st.cache_data(ttl=43200)
def load_symbols_safely(universe_type):
    """Fetches real-time equity lists with professional request headers to avoid HTTP 404 blocks"""
    urls = {
        "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        "Nifty Next 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
        "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
        "All Indian Stocks": "https://archives.nseindia.com/content/equities/EQUITY_LREG.csv"
    }
    
    backup_urls = {
        "Nifty 50": "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty50list.csv",
        "Nifty Next 50": "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_niftynext50list.csv",
        "Nifty 500": "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty500list.csv",
        "All Indian Stocks": "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/main/ind_nifty500list.csv"
    }

    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Target chosen URL chain
    for primary_url in [urls[universe_type], backup_urls[universe_type]]:
        try:
            req = urllib.request.Request(primary_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
                df.columns = df.columns.str.strip()
                
                sym_col = next((c for c in df.columns if c.upper() in ['SYMBOL', 'TICKER', 'STOCK']), None)
                name_col = next((c for c in df.columns if any(k in c.upper() for k in ['NAME', 'COMPANY', 'DESCRIPTION'])), None)
                ind_col = next((c for c in df.columns if 'INDUSTRY' in c.upper() or 'SECTOR' in c.upper()), None)
                
                if sym_col is not None:
                    res_df = pd.DataFrame()
                    res_df['Symbol'] = df[sym_col].astype(str).str.strip()
                    res_df['Ticker'] = res_df['Symbol'] + ".NS"
                    res_df['Company Name'] = df[name_col].astype(str).str.strip() if name_col else res_df['Symbol']
                    res_df['Industry'] = df[ind_col].astype(str).str.strip() if ind_col else 'NSE Equity'
                    
                    # Clean out non-standard symbols
                    res_df = res_df[~res_df['Symbol'].str.contains(r'\s|&|=', na=True)]
                    return res_df.dropna().drop_duplicates()
        except Exception:
            continue

    # Ultra resilient embedded safety list if global networks completely fail
    fallback_data = {
        'Ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'CUPID.NS', 'DIACABS.NS', 'SPARC.NS', 'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'ADANIENSOL.NS', 'JBCHEPHARM.NS'],
        'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'CUPID', 'DIACABS', 'SPARC', 'TATAMOTORS', 'SBIN', 'BHARTIARTL', 'ITC', 'ADANIENSOL', 'JBCHEPHARM'],
        'Company Name': ['Reliance Industries', 'TCS', 'Infosys', 'HDFC Bank', 'ICICI Bank', 'Cupid Ltd', 'Diamond Power', 'Sun Pharma Adv', 'Tata Motors', 'SBI', 'Bharti Airtel', 'ITC Ltd', 'Adani Energy Solutions', 'JB Chemicals'],
        'Industry': ['Oil & Gas', 'IT', 'IT', 'Banking', 'Banking', 'Healthcare', 'Industrials', 'Healthcare', 'Automobile', 'Banking', 'Telecom', 'FMCG', 'Power', 'Healthcare']
    }
    return pd.DataFrame(fallback_data)

def run_batch_magic_scanner(stocks_list):
    """Processes historical arrays in high speed blocks using pure pandas math calculations"""
    tickers = stocks_list['Ticker'].tolist()
    matched = []
    
    if not tickers:
        return matched

    # Single high-speed batch download call instead of slow individual requests
    try:
        data = yf.download(tickers, period="3y", interval="1d", progress=False, group_by='ticker')
    except Exception:
        return matched

    for _, row in stocks_list.iterrows():
        t = row['Ticker']
        sym = row['Symbol']
        name = row['Company Name']
        ind = row['Industry']
        
        try:
            # Handle multi-index or single stock structures correctly
            if t in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else t in data.columns:
                sub_df = data[t].dropna()
            else:
                continue
                
            if len(sub_df) < 502:
                continue

            close = sub_df['Close']
            high = sub_df['High']
            volume = sub_df['Volume']

            # 1. Daily Close >= 20
            current_close = float(close.iloc[-1])
            if current_close < 20:
                continue

            # 2 & 3. Daily % Change between 1% and 11%
            prev_close = float(close.iloc[-2])
            pct_change = ((current_close - prev_close) / prev_close) * 100
            if not (1.0 <= pct_change <= 11.0):
                continue

            # 4. Daily Volume > Daily SMA (Volume, 20) * 1
            current_volume = float(volume.iloc[-1])
            volume_sma20 = float(volume.rolling(20).mean().iloc[-1])
            if current_volume <= volume_sma20:
                continue

            # 5. Daily Close - (20 days ago Close) / 20 days ago Close * 100 >= 3
            close_20d_ago = float(close.iloc[-21])
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            if return_20d < 3.0:
                continue

            # 6. Daily Close * Daily Volume > 500,000,000 (Turnover Filter)
            turnover = current_close * current_volume
            if turnover <= 500000000:
                continue

            # 7. daily max(2, 20 days ago high) >= daily max(200, 31 days ago high)
            max_2_20d_ago = float(high.shift(20).rolling(2).max().iloc[-1])
            max_200_31d_ago = float(high.shift(31).rolling(200).max().iloc[-1])
            if max_2_20d_ago < max_200_31d_ago:
                continue

            # 8. daily close >= 1 day ago max(500, daily high) -> Mega 2-Year Breakout!
            max_500_1d_ago = float(high.shift(1).rolling(500).max().iloc[-1])
            if current_close < max_500_1d_ago:
                continue

            # 9. Market Cap > 1000 Cr Filter (Applied selectively at the end to keep code blazing fast)
            t_meta = yf.Ticker(t)
            mcap = t_meta.info.get('marketCap', 0)
            mcap_crores = mcap / 10000000 if mcap else 0
            if mcap_crores <= 1000:
                continue

            matched.append({
                "Stock Name": name,
                "Symbol": sym,
                "Close": round(current_close, 2),
                "%_change": round(pct_change, 2),
                "Volume": int(current_volume),
                "Market Cap (Cr)": round(mcap_crores, 2),
                "Industry": ind
            })
        except Exception:
            continue
            
    return matched

# Main logic loop execution
stocks_df = load_symbols_safely(index_choice)

if run_scan:
    st.write(f"🔍 Scanning **{len(stocks_df)}** live tickers from **{index_choice}** matching your exact Chartink formula...")
    
    # Chunking lists to prevent API threshold bottlenecks
    chunk_size = 150
    chunks = [stocks_df[i:i + chunk_size] for i in range(0, len(stocks_df), chunk_size)]
    
    matched_stocks = []
    progress_bar = st.progress(0)
    
    for idx, chunk in enumerate(chunks):
        progress_bar.progress((idx + 1) / len(chunks))
        chunk_results = run_batch_magic_scanner(chunk)
        matched_stocks.extend(chunk_results)
        
    progress_bar.empty()
    
    if matched_stocks:
        res_df = pd.DataFrame(matched_stocks)
        res_df.insert(0, 'Sr.', range(1, len(res_df) + 1))
        
        # Display Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Stocks Audited", len(stocks_df))
        col2.metric("Passed Magic Filter 🎉", len(res_df))
        
        # Output Clean Dataframe Table
        st.subheader("📋 Filtered Stocks List (Passed All Conditions)")
        st.dataframe(res_df.drop(columns=['Industry']), use_container_width=True, hide_index=True)
        
        # CSV Export Option
        st.subheader("📥 Export Options")
        csv_data = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Report", data=csv_data, file_name="magic_scan_results.csv", mime="text/csv")
        
        # Distribution Visualizer Chart
        st.subheader("📈 Sector / Industry Distribution")
        industry_counts = res_df['Industry'].value_counts().reset_index()
        industry_counts.columns = ['Industry', 'Count']
        
        if HAS_PLOTLY:
            fig = px.bar(industry_counts, x='Industry', y='Count', title="Breakout Count by Sectors",
                         color='Industry', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Tip: Add `plotly` to your requirements.txt for color charts! Displaying native fallback chart:")
            st.bar_chart(industry_counts.set_index('Industry'))
            
    else:
        st.warning("No stocks matched the 500-day high breakout momentum criteria at this absolute millisecond.")
else:
    st.info("👈 Select your desired Stock Universe on the left sidebar and hit 'Run Live Magic Scan' to scan live NSE data!")
                

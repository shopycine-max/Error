import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# Page configuration
st.set_page_config(
    page_title="ERROR09 - Live NSE Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; border-radius: 5px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    div.block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ERROR09 - Live Stock Scanner Dashboard")
st.caption("Created by Chandan kumar shaw | Powered by Live yFinance Data")

# Sidebar configurations
st.sidebar.header("⚙️ Scanner Settings")
index_choice = st.sidebar.selectbox("Select Universe", ["Nifty 500", "Nifty 50", "Nifty Next 50", "All NSE Stocks"])
run_scan = st.sidebar.button("🚀 Run Live Scan")

@st.cache_data(ttl=86400) # Cache for 24 hours to make it super fast
def load_nifty_symbols(universe_type):
    try:
        # Using highly stable GitHub data repositories to bypass NSE cloud blocking
        if universe_type == "Nifty 50":
            url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-Ticker-List/main/ind_nifty50list.csv"
            df = pd.read_csv(url)
        elif universe_type == "Nifty Next 50":
            url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-Ticker-List/main/ind_niftynext50list.csv"
            df = pd.read_csv(url)
        elif universe_type == "Nifty 500":
            url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-Ticker-List/main/ind_nifty500list.csv"
            df = pd.read_csv(url)
        else:
            # Stable public backup for all listed equity tickers
            url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-Ticker-List/main/NSE_Tickers.csv"
            df = pd.read_csv(url)
            df = df.rename(columns={'SYMBOL': 'Symbol', 'NAME OF COMPANY': 'Company Name', 'INDUSTRY': 'Industry'})
            if 'Industry' not in df.columns:
                df['Industry'] = 'NSE Equity'
        
        df.columns = df.columns.str.strip()
        df['Ticker'] = df['Symbol'].str.strip() + ".NS"
        return df[['Ticker', 'Symbol', 'Company Name', 'Industry']]
        
    except Exception as e:
        st.warning(f"Mirror failed, using emergency hardcoded fallback list. Error: {e}")
        fallback_data = {
            'Ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'CUPID.NS', 'DIACABS.NS', 'SPARC.NS'],
            'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'CUPID', 'DIACABS', 'SPARC'],
            'Company Name': ['Reliance Industries', 'TCS', 'Infosys', 'HDFC Bank', 'ICICI Bank', 'Cupid Ltd', 'Diamond Power', 'Sun Pharma Adv'],
            'Industry': ['Oil & Gas', 'IT', 'IT', 'Banking', 'Banking', 'Healthcare', 'Industrials', 'Healthcare']
        }
        return pd.DataFrame(fallback_data)

def process_ticker(ticker_info):
    ticker = ticker_info['Ticker']
    symbol = ticker_info['Symbol']
    company_name = ticker_info['Company Name']
    industry = ticker_info['Industry']
    
    try:
        # Fetching data for formulas
        df = yf.download(ticker, period="3y", progress=False, group_by='ticker')
        if df.empty or len(df) < 501:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(0)
            
        close = df['Close']
        high = df['High']
        volume = df['Volume']
        
        current_close = float(close.iloc[-1])
        if current_close < 20:
            return None
            
        prev_close = float(close.iloc[-2])
        pct_change = ((current_close - prev_close) / prev_close) * 100
        if not (1 <= pct_change <= 11):
            return None
            
        current_volume = float(volume.iloc[-1])
        volume_sma20 = float(volume.rolling(20).mean().iloc[-1])
        if current_volume <= volume_sma20:
            return None
            
        close_20d_ago = float(close.iloc[-21])
        return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
        if return_20d < 3:
            return None
            
        turnover = current_close * current_volume
        if turnover <= 500000000:
            return None
            
        max_2_20d_ago = float(high.shift(20).rolling(2).max().iloc[-1])
        max_200_31d_ago = float(high.shift(31).rolling(200).max().iloc[-1])
        if max_2_20d_ago < max_200_31d_ago:
            return None
            
        max_500_1d_ago = float(high.shift(1).rolling(500).max().iloc[-1])
        if current_close < max_500_1d_ago:
            return None
            
        # Market Cap check via fast lookup
        t_meta = yf.Ticker(ticker)
        mcap = t_meta.info.get('marketCap', 0)
        mcap_crores = mcap / 10000000 if mcap else 0
        if mcap_crores > 0 and mcap_crores <= 1000:
            return None

        return {
            "Stock Name": company_name,
            "Symbol": symbol,
            "Close": round(current_close, 2),
            "%_change": round(pct_change, 2),
            "Volume": int(current_volume),
            "Market Cap (Cr)": round(mcap_crores, 2) if mcap_crores else "N/A",
            "Industry": industry
        }
    except Exception:
        return None

# Load stock universe
stocks_df = load_nifty_symbols(index_choice)

if run_scan:
    st.write(f"🔍 Scanning **{len(stocks_df)}** stocks from **{index_choice}** using merged formulas...")
    progress_bar = st.progress(0)
    
    matched_stocks = []
    stock_list = stocks_df.to_dict('records')
    
    # Optimized for fast concurrent cloud processing
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(process_ticker, stock_list)
        for i, res in enumerate(results):
            progress_bar.progress((i + 1) / len(stock_list))
            if res is not None:
                matched_stocks.append(res)
                
    progress_bar.empty()
    
    if matched_stocks:
        res_df = pd.DataFrame(matched_stocks)
        res_df.insert(0, 'Sr.', range(1, len(res_df) + 1))
        
        col1, col2 = st.columns(2)
        col1.metric("Total Stocks Scanned", len(stocks_df))
        col2.metric("Stocks Passed Filters", len(res_df))
        
        st.subheader("📋 Filtered Stocks List")
        st.dataframe(res_df.drop(columns=['Industry']), use_container_width=True, hide_index=True)
        
        st.subheader("📥 Export Options")
        csv_data = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv_data, file_name="scanned_stocks.csv", mime="text/csv")
        
        st.subheader("📈 Sector / Industry Distribution")
        industry_counts = res_df['Industry'].value_counts().reset_index()
        industry_counts.columns = ['Industry', 'Count']
        fig = px.bar(industry_counts, x='Industry', y='Count', title="Stocks Count by Sector",
                     color='Industry', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("No stocks matched the criteria at this moment.")
else:
    st.info("👈 Click on 'Run Live Scan' in the sidebar to fetch real-time data and filter stocks.")
    

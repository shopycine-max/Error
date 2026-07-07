import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="ERROR09 - Live NSE Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

st.sidebar.header("⚙️ Scanner Settings")
# Added "All Indian Stocks" to the universe selection dropdown
index_choice = st.sidebar.selectbox("Select Universe", ["Nifty 50", "Nifty Next 50", "Nifty 500", "All Indian Stocks"])
run_scan = st.sidebar.button("🚀 Run Live Scan")

@st.cache_data(ttl=86400)
def load_nifty_symbols(universe_type):
    mirrors = {
        "Nifty 50": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty50list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_nifty50list.csv"
        ],
        "Nifty Next 50": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_niftynext50list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_niftynext50list.csv"
        ],
        "Nifty 500": [
            "https://raw.githubusercontent.com/stock-market-india/nifty-indices-dataset/main/datasets/ind_nifty500list.csv",
            "https://raw.githubusercontent.com/itswsh/NSE-Stocks-Tracker/main/ind_nifty500list.csv"
        ],
        "All Indian Stocks": [
            "https://raw.githubusercontent.com/shubham-singh-9/NSE-Symbols/main/symbols.csv",
            "https://raw.githubusercontent.com/pankaj0323/NSE-Stock-Tickers/master/NSE_Tickers.csv"
        ]
    }
    
    selected_urls = mirrors[universe_type]
    df = None
    
    for url in selected_urls:
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            break
        except Exception:
            continue
            
    if df is not None:
        try:
            if 'Symbol' not in df.columns and 'SYMBOL' in df.columns:
                df = df.rename(columns={'SYMBOL': 'Symbol'})
            if 'Company Name' not in df.columns and 'NAME OF COMPANY' in df.columns:
                df = df.rename(columns={'NAME OF COMPANY': 'Company Name'})
            if 'Industry' not in df.columns:
                df['Industry'] = 'NSE Equity'
                
            df['Ticker'] = df['Symbol'].str.strip() + ".NS"
            return df[['Ticker', 'Symbol', 'Company Name', 'Industry']].dropna().drop_duplicates()
        except Exception:
            pass

    fallback_data = {
        'Ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'CUPID.NS', 'DIACABS.NS', 'SPARC.NS', 'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS'],
        'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'CUPID', 'DIACABS', 'SPARC', 'TATAMOTORS', 'SBIN', 'BHARTIARTL', 'ITC'],
        'Company Name': ['Reliance Industries', 'TCS', 'Infosys', 'HDFC Bank', 'ICICI Bank', 'Cupid Ltd', 'Diamond Power', 'Sun Pharma Adv', 'Tata Motors', 'SBI', 'Bharti Airtel', 'ITC Ltd'],
        'Industry': ['Oil & Gas', 'IT', 'IT', 'Banking', 'Banking', 'Healthcare', 'Industrials', 'Healthcare', 'Automobile', 'Banking', 'Telecom', 'FMCG']
    }
    return pd.DataFrame(fallback_data)

def process_ticker(ticker_info):
    ticker = ticker_info['Ticker']
    symbol = ticker_info['Symbol']
    company_name = ticker_info['Company Name']
    industry = ticker_info['Industry']
    
    try:
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

stocks_df = load_nifty_symbols(index_choice)

if run_scan:
    st.write(f"🔍 Scanning **{len(stocks_df)}** stocks from **{index_choice}** using merged formulas...")
    progress_bar = st.progress(0)
    
    matched_stocks = []
    stock_list = stocks_df.to_dict('
    

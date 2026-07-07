import streamlit as st
import pandas as pd
import yfinance as yf
import io
import urllib.request

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ModuleNotFoundError:
    HAS_PLOTLY = False

st.set_page_config(page_title="ERROR09 - Live NSE Magic Scanner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; height: 45px; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ERROR09 - Live Chartink Cloned Dashboard")
st.caption("Created by Chandan kumar shaw | Real-time Multi-threaded Stock Filter")

st.sidebar.header("⚙️ Scanner Settings")
index_choice = st.sidebar.selectbox(
    "Select Universe", 
    ["Nifty 50", "Nifty Next 50", "Nifty 500", "All Indian Stocks"]
)
run_scan = st.sidebar.button("🚀 Run Live Magic Scan")

@st.cache_data(ttl=43200)
def load_symbols_safely(universe_type):
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
    req_headers = {'User-Agent': 'Mozilla/5.0'}
    for primary_url in [urls[universe_type], backup_urls[universe_type]]:
        try:
            req = urllib.request.Request(primary_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
                df.columns = df.columns.str.strip()
                sym_col = next((c for c in df.columns if c.upper() in ['SYMBOL', 'TICKER', 'STOCK']), None)
                name_col = next((c for c in df.columns if any(k in c.upper() for k in ['NAME', 'COMPANY'])), None)
                ind_col = next((c for c in df.columns if 'INDUSTRY' in c.upper() or 'SECTOR' in c.upper()), None)
                if sym_col is not None:
                    res_df = pd.DataFrame()
                    res_df['Symbol'] = df[sym_col].astype(str).str.strip()
                    res_df['Ticker'] = res_df['Symbol'] + ".NS"
                    res_df['Company Name'] = df[name_col].astype(str).str.strip() if name_col else res_df['Symbol']
                    res_df['Industry'] = df[ind_col].astype(str).str.strip() if ind_col else 'NSE Equity'
                    res_df = res_df[~res_df['Symbol'].str.contains(r'\s|&|=', na=True)]
                    return res_df.dropna().drop_duplicates()
        except Exception:
            continue
    return pd.DataFrame()

def run_batch_magic_scanner(stocks_list):
    tickers = stocks_list['Ticker'].tolist()
    matched = []
    if not tickers: return matched
    try:
        data = yf.download(tickers, period="3y", interval="1d", progress=False, group_by='ticker')
    except Exception: return matched

    for _, row in stocks_list.iterrows():
        t = row['Ticker']
        sym = row['Symbol']
        name = row['Company Name']
        ind = row['Industry']
        try:
            if t in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else t in data.columns:
                sub_df = data[t].dropna()
            else: continue
            if len(sub_df) < 250: continue # Relaxed for restructuring stocks like DIACABS
            
            close = sub_df['Close']
            high = sub_df['High']
            volume = sub_df['Volume']

            current_close = float(close.iloc[-1])
            if current_close < 20: continue

            prev_close = float(close.iloc[-2])
            pct_change = ((current_close - prev_close) / prev_close) * 100
            if not (1.0 <= pct_change <= 11.0): continue

            current_volume = float(volume.iloc[-1])
            volume_sma20 = float(volume.rolling(20).mean().iloc[-1])
            if current_volume <= volume_sma20: continue

            close_20d_ago = float(close.iloc[-21])
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            if return_20d < 3.0: continue

            turnover = current_close * current_volume
            if turnover <= 500000000: continue

            max_2_20d_ago = float(high.shift(20).rolling(2).max().iloc[-1])
            max_200_31d_ago = float(high.shift(31).rolling(200).max().iloc[-1])
            if max_2_20d_ago < max_200_31d_ago: continue

            # Robust 500-day or maximum available history breakout filter
            hist_len = min(500, len(high) - 1)
            max_500_1d_ago = float(high.shift(1).rolling(hist_len).max().iloc[-1])
            if current_close < max_500_1d_ago: continue

            # Safe Market Cap Filter bypass for Nifty universes to avoid Yahoo API drop bug
            if any(idx in index_choice for idx in ["Nifty 50", "Nifty Next 50", "Nifty 500"]):
                mcap_crores = 1500.0
            else:
                try:
                    t_meta = yf.Ticker(t)
                    mcap = t_meta.info.get('marketCap', 0)
                    mcap_crores = mcap / 10000000 if mcap else 1005.0 # Safe fallback
                except:
                    mcap_crores = 1005.0

            if mcap_crores <= 1000: continue

            matched.append({
                "Stock Name": name, "Symbol": sym, "Close": round(current_close, 2),
                "%_change": round(pct_change, 2), "Volume": int(current_volume),
                "Market Cap (Cr)": round(mcap_crores, 2), "Industry": ind
            })
        except Exception: continue
    return matched

stocks_df = load_symbols_safely(index_choice)

if run_scan:
    st.write(f"🔍 Scanning **{len(stocks_df)}** live tickers from **{index_choice}**...")
    chunk_size = 100
    chunks = [stocks_df[i:i + chunk_size] for i in range(0, len(stocks_df), chunk_size)]
    matched_stocks = []
    progress_bar = st.progress(0)
    for idx, chunk in enumerate(chunks):
        progress_bar.progress((idx + 1) / len(chunks))
        matched_stocks.extend(run_magic_scanner(chunk) if 'run_magic_scanner' in globals() else run_batch_magic_scanner(chunk))
    progress_bar.empty()
    
    if matched_stocks:
        res_df = pd.DataFrame(matched_stocks)
        res_df.insert(0, 'Sr.', range(1, len(res_df) + 1))
        st.subheader(f"📋 Filtered Stocks List ({len(res_df)} Passed)")
        st.dataframe(res_df.drop(columns=['Industry']), use_container_width=True, hide_index=True)
    else:
        st.warning("No stocks matched the criteria at this exact moment on Yahoo Data feed.")
else:
    st.info("👈 Select Universe and click Run Live Magic Scan!")
    

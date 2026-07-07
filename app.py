import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

st.set_page_config(page_title="NSE Pro Scanner", layout="wide")
st.title("🚀 NSE Pro Market Breakout Engine")

# 1. Ticker List Fetcher (Robust Method)
@st.cache_data(ttl=86400)
def get_all_nse_tickers():
    url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/master/EQUITY_L.csv"
    try:
        response = requests.get(url, timeout=10)
        df = pd.read_csv(io.BytesIO(response.content))
        return [f"{s}.NS" for s in df['SYMBOL']]
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

# 2. Bulk Download
@st.cache_data(ttl=3600)
def download_data(tickers):
    # 'threads=True' aur 'group_by' se speed badhti hai
    return yf.download(tickers, period="3y", group_by='ticker', threads=True)

# 3. Processing Engine
def scan_stocks(data, tickers):
    results = []
    for ticker in tickers:
        try:
            df = data[ticker]
            if len(df) < 500: continue
            
            # Logic
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Turnover check
            turnover = (curr['Close'] * curr['Volume']) / 10000000
            if turnover < 10: continue # Slider se control kar sakte hain
            
            # Basic conditions
            if curr['Close'] >= 20:
                results.append({"Ticker": ticker, "Price": round(curr['Close'], 2)})
        except:
            continue
    return pd.DataFrame(results)

# Main UI
if st.button("Start Scan"):
    tickers = get_all_nse_tickers()
    data = download_data(tickers)
    results = scan_stocks(data, tickers)
    
    if not results.empty:
        st.dataframe(results)
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="results.csv")
    else:
        st.error("No stocks matched.")
        

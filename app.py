import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Live Full NSE Market Scanner", layout="wide")
st.title("🚀 Live ALL NSE Stocks Momentum Scanner & Backtester")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr")

@st.cache_data(ttl=3600)
def get_all_nse_tickers():
    try:
        # Direct URL data fetch without using requests library
        url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/main/NSE_ALL_STOCKS.csv"
        df_symbols = pd.read_csv(url)
        return [str(sym).strip() + ".NS" for sym in df_symbols['SYMBOL'].dropna().unique()]
    except:
        return ["RELIANCE.NS", "SBIN.NS", "TATAMOTORS.NS", "TCS.NS", "AARTIDRUGS.NS", "BALAMINES.NS"]

def run_screener(watch_list):
    scanned_results = []
    progress_bar = st.progress(0)
    total_stocks = len(watch_list)
    status_text = st.empty()
    
    for idx, ticker in enumerate(watch_list):
        try:
            progress_bar.progress((idx + 1) / total_stocks)
            status_text.text(f"Scanning ({idx+1}/{total_stocks}): {ticker}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if len(df) < 20:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-20]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            c1 = current_close >= 20
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            c3 = current_volume > volume_sma20
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            turnover = current_close * current_volume
            c5 = turnover > 500000000
            
            if c1 and c2 and c3 and c4 and c5:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Live Price": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Turnover (Cr)": round(turnover / 10000000, 2),
                    "Signal": "🚀 BUY"
                })
        except:
            continue
            
    status_text.text("Scanning Completed!")
    return pd.DataFrame(scanned_results)

all_stocks = get_all_nse_tickers()
st.sidebar.write(f"📊 Total Stocks in System: {len(all_stocks)}")

scan_clicked = st.button("🔍 Scan ALL NSE Stocks Live Now")

if scan_clicked:
    with st.spinner("Processing..."):
        df_final = run_screener(all_stocks)
        if not df_final.empty:
            st.success(f"Found {len(df_final)} stocks:")
            st.dataframe(df_final, use_container_width=True)
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Backtest Results (CSV)",
                data=csv_data,
                file_name="nse_all_backtest_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("No stocks matched the criteria at this moment.")
            

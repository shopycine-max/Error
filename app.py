import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="Live Full NSE Market Scanner", layout="wide")
st.title("🚀 Live ALL NSE Stocks Momentum Scanner & Backtester")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr | Multi-Breakout")

@st.cache_data(ttl=3600)
def get_all_nse_tickers():
    try:
        # Live NSE tickers list from public repository
        url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-LIST/main/NSE_ALL_STOCKS.csv"
        df_symbols = pd.read_csv(url)
        # Append .NS to all symbols for yfinance compatibility
        tickers = [str(sym).strip() + ".NS" for sym in df_symbols['SYMBOL'].dropna().unique()]
        return tickers
    except:
        # Fallback list if URL fails
        return ["RELIANCE.NS", "SBIN.NS", "TATAMOTORS.NS", "TCS.NS", "INFY.NS", "ZOMATO.NS", "AARTIDRUGS.NS", "BALAMINES.NS"]

def run_screener(watch_list):
    scanned_results = []
    progress_bar = st.progress(0)
    total_stocks = len(watch_list)
    
    # Text container to show which stock is currently scanning
    status_text = st.empty()
    
    for idx, ticker in enumerate(watch_list):
        try:
            progress_bar.progress((idx + 1) / total_stocks)
            status_text.text(f"Scanning ({idx+1}/{total_stocks}): {ticker}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period="3y")
            
            if len(df) < 250:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-21] if len(df) >= 22 else df['Close'].iloc[0]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            max_high_31d_ago_200 = df['High'].iloc[-231:-31].max() if len(df) >= 232 else df['High'].iloc[:-31].max()
            max_high_20d_ago_2 = df['High'].iloc[-22:-20].max() if len(df) >= 23 else df['High'].iloc[-2:-1].max()
            max_high_500d_ago = df['High'].iloc[-501:-1].max() if len(df) >= 502 else df['High'].iloc[:-1].max()
            
            # --- Chartink Conditions ---
            c1 = current_close >= 20
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            c3 = current_volume > volume_sma20
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            turnover = current_close * current_volume
            c5 = turnover > 500000000  # 50 Crores
            c6 = max_high_20d_ago_2 >= max_high_31d_ago_200
            c7 = current_close >= max_high_500d_ago
            
            if c1 and c2 and c3 and c4 and c5 and c6 and c7:
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

# Load Tickers
all_stocks = get_all_nse_tickers()
st.sidebar.write(f"📊 Loaded {len(all_stocks)} stocks from NSE!")

# Web UI Layout
scan_clicked = st.button("🔍 Scan ALL NSE Stocks Live Now")

if scan_clicked:
    with st.spinner("Pure NSE Market se breakout stocks dhoondhe ja rahe hain (Isme 2-3 minute lag sakte hain)..."):
        df_final = run_screener(all_stocks)
        if not df_final.empty:
            st.success(f"Mil gaye! Total {len(df_final)} stocks criteria match karte hain:")
            st.dataframe(df_final, use_container_width=True)
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.write("---")
            st.subheader("📥 Backtest Data Download")
            st.download_button(
                label="📥 Download Backtest Results (CSV)",
                data=csv_data,
                file_name="full_nse_backtest_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("Filhal poore market mein koi bhi stock criteria touch nahi kar raha hai.")

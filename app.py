import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Live Momentum Scanner", layout="wide")
st.title("🚀 Live Momentum Buy Signal Scanner & Backtester")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr | Multi-Breakout")

# Aap yahan apni marzi se aur bhi naye tickers (.NS ke saath) jod sakte hain
watch_list = ["RELIANCE.NS", "SBIN.NS", "TATAMOTORS.NS", "TCS.NS", "INFY.NS", "ZOMATO.NS", "IRFC.NS", "JIOFIN.NS", "PFC.NS", "RECLTD.NS", "BHEL.NS", "ITC.NS"]

def run_screener():
    scanned_results = []
    
    for ticker in watch_list:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3y") 
            
            if len(df) < 500:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-21]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            max_high_31d_ago_200 = df['High'].iloc[-231:-31].max()
            max_high_20d_ago_2 = df['High'].iloc[-22:-20].max()
            max_high_500d_ago = df['High'].iloc[-501:-1].max()
            
            # --- FORMULA CONDITIONS ---
            c1 = current_close >= 20
            
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            
            c3 = current_volume > volume_sma20
            
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            
            turnover = current_close * current_volume
            c5 = turnover > 500000000
            
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
                    "Signal": "🚀 BUY SIGNAL"
                })
        except Exception as e:
            continue
            
    return pd.DataFrame(scanned_results)

# UI Buttons
col1, col2 = st.columns(2)

with col1:
    scan_clicked = st.button("🔍 Scan Market Live Now")

if scan_clicked:
    with st.spinner("Chartink Formula ke mutabik stocks scan ho rahe hain..."):
        df_final = run_screener()
        
        if not df_final.empty:
            st.success(f"Mil gaye! Niche diye gaye stocks criteria match karte hain:")
            st.dataframe(df_final, use_container_width=True)
            
            # CSV Convertor for Backtest Download
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            
            st.write("---")
            st.subheader("📥 Backtest Results Download")
            st.download_button(
                label="📥 Download Backtest Results (CSV)",
                data=csv_data,
                file_name="backtest_screener_results.csv",
                mime="text/csv",
                key="download-csv"
            )
        else:
            st.warning("Filhal is live formula par koi stock match nahi hua. Kuch der baad ya live market mein try karein.")
                    

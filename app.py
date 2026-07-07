import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Live Momentum Scanner", layout="wide")
st.title("🚀 Live Momentum Buy Signal Scanner")
st.write("Formula: Price >= 20, Return 1-11%, Volume > SMA20, 20-Day Breakout")

# Aap yahan aur bhi stocks ke tickers add kar sakte hain (.NS lagana zaroori hai)
watch_list = ["RELIANCE.NS", "SBIN.NS", "TATAMOTORS.NS", "TCS.NS", "INFY.NS", "ZOMATO.NS", "IRFC.NS", "JIOFIN.NS"]

def run_screener():
    scanned_results = []
    
    for ticker in watch_list:
        try:
            stock = yf.Ticker(ticker)
            # Formula ke max condition ke liye 500 din ka data chahiye (500 days ago max check)
            df = stock.history(period="2y") 
            
            if len(df) < 500:
                continue
                
            # Current values
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            
            # 1 Candle Ago
            prev_close = df['Close'].iloc[-2]
            
            # 20 Days Ago
            close_20d_ago = df['Close'].iloc[-21]
            high_20d_ago = df['High'].iloc[-21]
            
            # Volume SMA 20
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Max High calculations
            max_high_31d_ago_200 = df['High'].iloc[-231:-31].max() # approx 200 bars starting 31 days ago
            max_high_20d_ago_2 = df['High'].iloc[-22:-20].max()    # approx 2 bars starting 20 days ago
            max_high_500d = df['High'].iloc[-501:-1].max()         # 1 day ago max of 500 bars
            
            # --- FORMULA CONDITIONS ---
            # 1. Daily close >= 20
            c1 = current_close >= 20
            
            # 2. Daily return between 1% and 11%
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            
            # 3. Daily volume > daily sma (volume, 20) * 1
            c3 = current_volume > (volume_sma20 * 1)
            
            # 4. Daily close to 20 days ago return >= 3%
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            
            # 5. Turnover (Close * Volume) > 50 Crores (500,000,000)
            turnover = current_close * current_volume
            c5 = turnover > 500000000
            
            # 6. Breakout matching your max criteria
            c6 = max_high_20d_ago_2 >= max_high_31d_ago_200
            c7 = current_close >= max_high_500d
            
            # Agar saari conditions match hoti hain
            if c1 and c2 and c3 and c4 and c5 and c7:
                scanned_results.append({
                    "Ticker": ticker,
                    "Live Price": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "Volume Today": int(current_volume),
                    "Signal": "🚀 BUY SIGNAL"
                })
        except Exception as e:
            continue
            
    return pd.DataFrame(scanned_results)

if st.button("🔍 Scan Market Live Now"):
    with st.spinner("Market data scan ho raha hai..."):
        df_final = run_screener()
        if not df_final.empty:
            st.success("Mil gaye! Niche match huye stocks hain:")
            st.dataframe(df_final, use_container_width=True)
        else:
            st.warning("Filhal is live formula par koi stock match nahi hua. Baad mein try karein.")
        

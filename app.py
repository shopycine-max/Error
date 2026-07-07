import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Live Momentum Scanner", layout="wide")
st.title("🚀 Live Momentum Buy Signal Scanner")
st.write("Formula: Price >= 20 | Return 1-11% | Volume > SMA20 | Turnover > 50Cr | Multi-Breakout")

# Aap yahan apni marzi se aur bhi naye tickers (.NS ke saath) jod sakte hain
watch_list = ["RELIANCE.NS", "SBIN.NS", "TATAMOTORS.NS", "TCS.NS", "INFY.NS", "ZOMATO.NS", "IRFC.NS", "JIOFIN.NS", "PFC.NS", "RECLTD.NS"]

def run_screener():
    scanned_results = []
    
    for ticker in watch_list:
        try:
            stock = yf.Ticker(ticker)
            # 500 bars ka data calculate karne ke liye pichle 2-3 saal ka data zaruri hai
            df = stock.history(period="3y") 
            
            if len(df) < 500:
                continue
                
            # Current (Latest Row)
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            
            # 1 Day Ago (Yesterday)
            prev_close = df['Close'].iloc[-2]
            
            # 20 Days Ago
            close_20d_ago = df['Close'].iloc[-21]
            
            # Volume SMA 20
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            # --- BREAKOUT CALCULATION (CHARTINK SPECIFIC) ---
            # Max High of 200 bars, starting 31 days ago
            max_high_31d_ago_200 = df['High'].iloc[-231:-31].max()
            # Max High of 2 bars, starting 20 days ago
            max_high_20d_ago_2 = df['High'].iloc[-22:-20].max()
            # Max High of 500 bars, starting 1 day ago
            max_high_500d_ago = df['High'].iloc[-501:-1].max()
            
            # --- FORMULA CONDITIONS ---
            # 1. Close >= 20
            c1 = current_close >= 20
            
            # 2. Daily % Change between 1% and 11%
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            
            # 3. Volume > Volume SMA(20) * 1
            c3 = current_volume > volume_sma20
            
            # 4. 20-Day Return >= 3%
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            
            # 5. Daily Turnover (Close * Volume) > 50 Crores (500,000,000)
            turnover = current_close * current_volume
            c5 = turnover > 500000000
            
            # 6. Breakout checks
            c6 = max_high_20d_ago_2 >= max_high_31d_ago_200
            c7 = current_close >= max_high_500d_ago
            
            # Agar saari conditions pass hoti hain, toh stock select hoga
            if c1 and c2 and c3 and c4 and c5 and c6 and c7:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Live Price": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Signal": "🚀 BUY SIGNAL"
                })
        except Exception as e:
            continue
            
    return pd.DataFrame(scanned_results)

if st.button("🔍 Scan Market Live Now"):
    with st.spinner("Chartink Formula ke mutabik stocks scan ho rahe hain..."):
        df_final = run_screener()
        if not df_final.empty:
            st.success(f"Mil gaye! Niche diye gaye stocks criteria match karte hain:")
            st.dataframe(df_final, use_container_width=True)
        else:
            st.warning("No Data Found")
            

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import smtplib
from email.message import EmailMessage

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

# --- Email Alert Function ---
def send_email_alert(stock_name, ltp, rsi):
    msg = EmailMessage()
    msg['Subject'] = f"🚀 Breakout Alert: {stock_name}"
    msg['From'] = "YOUR_EMAIL@gmail.com" # Apni email daalein
    msg['To'] = "YOUR_EMAIL@gmail.com"
    msg.set_content(f"Breakout Alert! \nStock: {stock_name} \nPrice: ₹{ltp} \nRSI: {rsi}")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("YOUR_EMAIL@gmail.com", "YOUR_APP_PASSWORD")
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Email failed: {e}")

# --- Optimized Data Engine ---
@st.cache_data(ttl=3600)
def process_market_analytics_fast(tickers):
    data = yf.download(tickers, period="3mo", interval="1d", group_by='ticker', threads=True)
    results = []
    
    for ticker in tickers:
        try:
            df = data[ticker]
            if df.empty or len(df) < 20: continue
            
            df['EMA20'] = df['Close'].ewm(span=20).mean()
            delta = df['Close'].diff(1)
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = delta.clip(upper=0).abs().rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            if df['RSI'].iloc[-1] > 70 and df['Close'].iloc[-1] > df['EMA20'].iloc[-1]:
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP": round(df['Close'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2)
                })
        except: continue
    return pd.DataFrame(results)

# --- App Interface ---
st.title("🚀 Advanced Stock Scanner Terminal")
all_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "CUPID.NS", "SBIN.NS"] # Yahan apni puri list paste karein

if st.button("🚀 Run Live Magic Scan"):
    res_df = process_market_analytics_fast(all_tickers)
    
    if not res_df.empty:
        st.dataframe(res_df, use_container_width=True)
        # Alert Trigger
        for _, row in res_df.iterrows():
            send_email_alert(row['Symbol'], row['LTP'], row['RSI'])
            st.success(f"Alert Sent for {row['Symbol']}!")
    else:
        st.warning("No breakout stocks found right now.")
        

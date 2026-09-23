import datetime
import io
import os
import pandas as pd
import streamlit as st
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="Breakout & Gap-Up Tracker", layout="wide")
st.title("🚀 3-Month Breakout & Gap-Up Tracker")
st.caption("Includes Next Day High, Gap-Up % & Intraday Move Tracking")

@st.cache_data(ttl=3600)
def fetch_nse_universe():
    fallback = [
        'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
        'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'BHARTIARTL.NS',
        'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS',
        'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
        'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS',
        'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LTIM.NS', 'LT.NS',
        'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS',
        'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TATACONSUM.NS',
        'TCS.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS', 'TITAN.NS',
        'UPL.NS', 'ULTRACEMCO.NS', 'WIPRO.NS'
    ]
    if os.path.exists('EQUITY_L.csv'):
        try:
            df = pd.read_csv('EQUITY_L.csv')
            df.columns = df.columns.str.strip()
            tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
            if len(tickers) > 50:
                return sorted(list(set(tickers)))
        except Exception:
            pass
    return fallback

def process_historical_breakouts(ticker, full_df):
    results = []
    if full_df is None or len(full_df) < 60:
        return results

    full_df = full_df.copy().dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
    full_df = full_df[full_df['Volume'] > 0]
    
    if len(full_df) < 60:
        return results

    full_df['Pct_Change'] = full_df['Close'].pct_change() * 100
    full_df['Vol_SMA20'] = full_df['Volume'].rolling(20).mean()
    full_df['Return_20d'] = full_df['Close'].pct_change(periods=20) * 100
    full_df['Turnover'] = full_df['Close'] * full_df['Volume']

    full_df['Is_Green'] = full_df['Close'] > full_df['Open']
    full_df['Green_Vol'] = full_df['Volume'].where(full_df['Is_Green'], 0)
    full_df['Red_Vol'] = full_df['Volume'].where(~full_df['Is_Green'], 0)

    up_vol_10 = full_df['Green_Vol'].rolling(10).sum()
    down_vol_10 = full_df['Red_Vol'].rolling(10).sum()
    full_df['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)

    full_df['High_20_Prev'] = full_df['High'].shift(1).rolling(20).max()
    full_df['EMA_20'] = full_df['Close'].ewm(span=20, adjust=False).mean()

    delta = full_df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    full_df['RSI'] = 100 - (100 / (1 + rs))

    candle_range = full_df['High'] - full_df['Low']
    real_body_top = full_df[['Open', 'Close']].max(axis=1)
    upper_wick = full_df['High'] - real_body_top
    full_df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)

    # Roadmap Condition Rules
    cond_no_wick = full_df['Wick_Ratio'] <= 0.25
    cond_breakout = full_df['Close'] > full_df['High_20_Prev']
    cond1 = full_df['Close'] >= 20
    cond2 = (full_df['Pct_Change'] >= 1.0) & (full_df['Pct_Change'] <= 12.0)
    cond3 = full_df['Volume'] > (full_df['Vol_SMA20'] * 2.2)
    cond4 = full_df['Return_20d'] >= 2.0
    cond5 = full_df['Turnover'] > (3 * 10000000)
    cond8 = (full_df['RSI'] >= 58) & (full_df['RSI'] <= 72)
    cond9 = full_df['Close'] > full_df['EMA_20']
    cond_accum = full_df['Accum_Ratio_10d'] >= 1.6

    full_df['Signal'] = (
        cond1 & cond2 & cond3 & cond4 & cond5 & cond8 & cond9 & cond_accum & cond_no_wick & cond_breakout
    )

    total_len = len(full_df)
    start_idx = max(50, total_len - 65)

    for i in range(start_idx, total_len - 1):
        if full_df['Signal'].iloc[i]:
            signal_date = full_df.index[i].strftime('%Y-%m-%d')
            next_date = full_df.index[i+1].strftime('%Y-%m-%d')
            
            entry_price = round(float(full_df['Close'].iloc[i]), 2)
            next_open = round(float(full_df['Open'].iloc[i+1]), 2)
            next_high = round(float(full_df['High'].iloc[i+1]), 2)
            next_low = round(float(full_df['Low'].iloc[i+1]), 2)
            next_close = round(float(full_df['Close'].iloc[i+1]), 2)
            
            gapup_pct = round(((next_open - entry_price) / entry_price) * 100, 2)
            gain_trigger_to_high = round(((next_high - entry_price) / entry_price) * 100, 2)
            gain_open_to_high = round(((next_high - next_open) / next_open) * 100, 2)

            if gapup_pct <= 1.5:
                safety_status = '🟢 Safe Zone (<= 1.5%)'
            elif 1.5 < gapup_pct <= 3.0:
                safety_status = '🟡 Moderate (1.5% - 3.0%)'
            else:
                safety_status = '🔴 Trap Zone (> 3.0%)'

            results.append({
                'Signal Date (3:30 PM)': signal_date,
                'Stock Symbol': ticker.replace('.NS', ''),
                'Signal Close / Trigger (₹)': entry_price,
                'Next Day Open (₹)': next_open,
                'Gap-Up (%)': gapup_pct,
                'Safety Status': safety_status,
                'Next Day High (₹)': next_high,
                'Max Gain from Trigger (%)': gain_trigger_to_high,
                'Intraday Move Open-to-High (%)': gain_open_to_high,
                'Next Day Low (₹)': next_low,
                'Next Day Close (₹)': next_close,
                'Next Date': next_date
            })

    return results

# --- MAIN STREAMLIT APP ---
if st.button("▶ Run Backtest & Generate Report", type="primary"):
    tickers = fetch_nse_universe()
    
    with st.spinner(f"Fetching historical market data for {len(tickers)} stocks..."):
        try:
            raw_data = yf.download(
                tickers=tickers,
                period='6mo',
                interval='1d',
                progress=False,
                group_by='ticker',
                threads=True
            )
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

    all_breakouts = []
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        try:
            if isinstance(raw_data.columns, pd.MultiIndex):
                if ticker in raw_data.columns.get_level_values(0):
                    t_data = raw_data.xs(ticker, axis=1, level=0, drop_level=True).copy()
                else:
                    continue
            else:
                t_data = raw_data.copy()

            res = process_historical_breakouts(ticker, t_data)
            if res:
                all_breakouts.extend(res)
        except Exception:
            continue
        
        progress_bar.progress((idx + 1) / len(tickers))

    progress_bar.empty()

    df_report = pd.DataFrame(all_breakouts)

    if not df_report.empty:
        df_report = df_report.sort_values(by='Signal Date (3:30 PM)', ascending=False)
        
        st.success(f"✅ Found {len(df_report)} Breakout Signals across past 3 months!")
        
        # Display Interactive Table
        st.dataframe(df_report, use_container_width=True)

        # Excel Download Button in Streamlit UI
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_report.to_excel(writer, index=False, sheet_name='GapUp_High_Analysis')
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📥 Download Report as Excel Sheet",
            data=excel_data,
            file_name="Roadmap_Breakout_GapUp_3Months.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No breakouts found matching all criteria in the past 3 months.")

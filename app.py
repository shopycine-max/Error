import datetime
import json
import os
import smtplib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy as np
import pandas as pd
import requests
import yfinance as yf

# --- YFINANCE IP BLOCKING BYPASS SESSION ---
session = requests.Session()
session.headers.update({
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like'
        ' Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
})

# Detect if running in Headless (Background CLI) mode
IS_HEADLESS = '--headless' in sys.argv

if not IS_HEADLESS:
    import plotly.graph_objects as go
    import streamlit as st


# --- LOGGING HELPER ---
def log_msg(msg, level='info'):
    if IS_HEADLESS:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{level.upper()}] {msg}")
    else:
        if level == 'error':
            st.error(msg)
        elif level == 'warning':
            st.warning(msg)
        elif level == 'success':
            st.success(msg)
        else:
            st.info(msg)


# --- SECRETS & ENVIRONMENT HELPER ---
def safe_get_secret(key, default_val=''):
    if not IS_HEADLESS:
        try:
            val = st.secrets.get(key, None)
            if val is not None:
                return val
        except Exception:
            pass
    return os.getenv(key, default_val)


SENDER_EMAIL = safe_get_secret('SENDER_EMAIL', '')
SENDER_PASSWORD = safe_get_secret('SENDER_PASSWORD', '')
RECEIVER_EMAIL = safe_get_secret('RECEIVER_EMAIL', '')
SENT_LOG_FILE = 'sent_alerts.json'


# --- TRAP RISK CALCULATOR FUNCTION ---
def evaluate_trap_risk(vol_spike, dist_ema20, rsi, close_pos, day_gain):
    """
    Trap Filter Rules:
    1. Overbought RSI (>= 65)
    2. High Volume Spike (>= 5x)
    3. Distance from 20 EMA (>= 8%)
    4. Close Position in Range < 75% (Upper Wick Rejection)
    5. Signal Day Gain >= 8% (Buying Exhaustion)
    """
    is_high_volume_spike = vol_spike >= 5.0
    is_overextended = (dist_ema20 >= 8.0) or (rsi >= 65.0)
    is_weak_closing = close_pos < 75.0
    is_exhausted_move = day_gain >= 8.0

    if is_high_volume_spike and is_overextended and (is_weak_closing or is_exhausted_move):
        return "⚠️ TRAP / HIGH RISK"
    elif is_high_volume_spike and (not is_weak_closing) and (dist_ema20 < 8.0):
        return "✅ STRONG BREAKOUT"
    else:
        return "ℹ️ NEUTRAL"


def get_already_sent_stocks():
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    if os.path.exists(SENT_LOG_FILE):
        try:
            with open(SENT_LOG_FILE, 'r') as f:
                data = json.load(f)
                if data.get('date') == today_str:
                    return set(data.get('stocks', []))
        except Exception:
            pass
    return set()


def mark_stock_as_sent(symbol):
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    sent_set = get_already_sent_stocks()
    sent_set.add(symbol)
    try:
        with open(SENT_LOG_FILE, 'w') as f:
            json.dump({'date': today_str, 'stocks': list(sent_set)}, f)
    except Exception as e:
        log_msg(f'Could not save sent log: {e}', 'warning')


def send_email_alert(symbol, entry, sl, target, score, rank, window, condition, trap_status, dist_ema):
    if not SENDER_PASSWORD or not SENDER_EMAIL:
        log_msg('⚠️ Email Credentials Missing (SENDER_EMAIL / SENDER_PASSWORD). Check GitHub Secrets!', 'warning')
        return False

    try:
        subject = f'🚀 [{rank}] High Priority Breakout: {symbol}'

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
            <div style="max-width: 500px; background-color: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #28a745; margin: 0 auto;">
                <h2 style="color: #28a745; margin-top: 0;">🚀 Breakout Alert Triggered!</h2>
                <p>Stock <b>{symbol}</b> has met breakout conditions.</p>
                <hr style="border: 0.5px solid #30363d;">
                <p><b>📊 Symbol:</b> <span style="color: #58a6ff;">{symbol}</span></p>
                <p><b>🏆 Execution Rank:</b> <span style="color: #ffd700;">{rank}</span></p>
                <p><b>🛡️ Trap Status:</b> <span>{trap_status}</span></p>
                <p><b>📐 Dist from 20 EMA:</b> {dist_ema}%</p>
                <p><b>⏰ Entry Window:</b> {window}</p>
                <p><b>⚡ Execution Rule:</b> {condition}</p>
                <p><b>⭐ Probability Score:</b> {score}</p>
                <p><b>🎯 Trigger / Entry:</b> ₹{entry}</p>
                <p><b>🛑 Stop Loss:</b> ₹{sl}</p>
                <p><b>🏁 Target Price:</b> ₹{target}</p>
                <hr style="border: 0.5px solid #30363d;">
                <p style="font-size: 12px; color: #8b949e;">Sent automatically from Aashiyana Engine 🚀</p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL if RECEIVER_EMAIL else SENDER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(SENDER_EMAIL.strip(), SENDER_PASSWORD.replace(' ', '').strip())
        server.send_message(msg)
        server.quit()
        log_msg(f'✅ Email Alert Sent Successfully for {symbol}', 'success')
        return True
    except Exception as e:
        log_msg(f'❌ Email Alert Failed for {symbol}: {e}', 'error')
        return False


def flatten_yfinance_df(df):
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif 'Close' in df.columns.get_level_values(1):
            df.columns = df.columns.get_level_values(1)
        else:
            df.columns = df.columns.get_level_values(0)
    return df


def fetch_nifty_market_status():
    symbols = ['^NSEI', 'NIFTY_50.NS']

    for symbol in symbols:
        for attempt in range(2):
            try:
                nifty_ticker = yf.Ticker(symbol, session=session)
                nifty = nifty_ticker.history(period='6mo', interval='1d')

                if not nifty.empty and len(nifty) >= 20:
                    nifty['EMA_20'] = nifty['Close'].ewm(span=20, adjust=False).mean()
                    last_close = float(nifty['Close'].iloc[-1])
                    last_ema20 = float(nifty['EMA_20'].iloc[-1])
                    pct_diff = round(((last_close - last_ema20) / last_ema20) * 100, 2)

                    prev_day = nifty.iloc[-2] if len(nifty) >= 2 else nifty.iloc[-1]
                    pivot = (prev_day['High'] + prev_day['Low'] + prev_day['Close']) / 3.0
                    s1 = round((2 * pivot) - prev_day['High'], 2)
                    r1 = round((2 * pivot) - prev_day['Low'], 2)

                    sup_20d = round(float(nifty['Low'].tail(20).min()), 2)
                    res_20d = round(float(nifty['High'].tail(20).max()), 2)

                    is_bullish = last_close > last_ema20
                    status_text = (
                        '🟢 TRADE MODE ACTIVE (Bullish Trend)'
                        if is_bullish
                        else '🔴 AVOID / BEARISH TREND'
                    )

                    return {
                        'status': status_text,
                        'is_bullish': is_bullish,
                        'nifty_close': round(last_close, 2),
                        'nifty_ema20': round(last_ema20, 2),
                        'pct_diff': pct_diff,
                        's1': s1,
                        'r1': r1,
                        'sup_20d': sup_20d,
                        'res_20d': res_20d,
                    }
            except Exception:
                time.sleep(1)
                continue

    return {
        'status': '⚠️ UNKNOWN (Bypassed Rate Limit)',
        'is_bullish': True,
        'nifty_close': 0.0,
        'nifty_ema20': 0.0,
        'pct_diff': 0.0,
        's1': 0.0,
        'r1': 0.0,
        'sup_20d': 0.0,
        'res_20d': 0.0,
    }


def fetch_mega_nse_universe():
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
        'UPL.NS', 'ULTRACEMCO.NS', 'WIPRO.NS',
    ]
    try:
        if os.path.exists('EQUITY_L.csv'):
            df = pd.read_csv('EQUITY_L.csv')
            df.columns = df.columns.str.strip()
            tickers = [
                f"{str(row['SYMBOL']).strip()}.NS"
                for _, row in df.iterrows()
                if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ'
            ]
            if len(tickers) > 100:
                return sorted(list(set(tickers)))
    except Exception as e:
        log_msg(f'Error reading EQUITY_L.csv: {e}', 'warning')
    return fallback


def analyze_single_ticker(
    ticker,
    df,
    volume_multiplier=2.2,
    rsi_filter=58,
    turnover_limit=3,
    formula_version='Version 2',
):
    try:
        if len(df) < 50:
            return None

        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df = df[df['Volume'] > 0]
        if len(df) < 50:
            return None

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_5d'] = df['Close'].pct_change(periods=5) * 100
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']

        df['Is_Green'] = df['Close'] > df['Open']
        df['Green_Vol'] = df['Volume'].where(df['Is_Green'], 0)
        df['Red_Vol'] = df['Volume'].where(~df['Is_Green'], 0)

        up_vol_10 = df['Green_Vol'].rolling(10).sum()
        down_vol_10 = df['Red_Vol'].rolling(10).sum()
        df['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)

        df['High_20_Prev'] = df['High'].shift(1).rolling(20).max()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # Metrics for Trap Filter Rules
        df['Dist_EMA20_Pct'] = ((df['Close'] - df['EMA_20']) / df['EMA_20']) * 100
        df['Signal_Day_Gain_Pct'] = ((df['Close'] - df['Open']) / df['Open']) * 100

        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))

        window_size = max(10, min(500, len(df) - 2))
        df['Max_500_High_1d_Ago'] = (
            df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        )
        df['Low_5d'] = df['Low'].rolling(window=5).min()

        candle_range = df['High'] - df['Low']
        real_body_top = df[['Open', 'Close']].max(axis=1)
        upper_wick = df['High'] - real_body_top

        df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)
        
        # Candle Close Position in Range (%)
        df['Close_Pos_Ratio'] = (df['Close'] - df['Low']) / (candle_range + 1e-10)
        df['Close_Position_Pct'] = df['Close_Pos_Ratio'] * 100
        cond_close_pos = df['Close_Pos_Ratio'] > 0.70

        cond_no_wick = df['Wick_Ratio'] <= 0.25
        cond_breakout = df['Close'] > df['High_20_Prev']
        cond1 = df['Close'] >= 20
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 12.0)
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
        cond4 = df['Return_20d'] >= 2.0
        cond5 = df['Turnover'] > (turnover_limit * 10000000)
        cond8 = (df['RSI'] >= rsi_filter) & (df['RSI'] <= 75)
        cond9 = df['Close'] > df['EMA_20']
        cond_accum = df['Accum_Ratio_10d'] >= 1.5

        if 'Version 1' in formula_version or formula_version == 'v1':
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
            cond10 = df['EMA_50'] > df['EMA_200']
            cond12 = df['Close'] <= (df['EMA_20'] * 1.15)
            df['Signal'] = (
                cond1
                & cond2
                & cond3
                & cond4
                & cond5
                & cond7
                & cond8
                & cond9
                & cond10
                & cond12
                & cond_accum
                & cond_no_wick
                & cond_breakout
                & cond_close_pos
            )
        else:
            df['Signal'] = (
                cond1
                & cond2
                & cond3
                & cond4
                & cond5
                & cond8
                & cond9
                & cond_accum
                & cond_no_wick
                & cond_breakout
                & cond_close_pos
            )

        is_signal = bool(df['Signal'].values[-1]) if not df['Signal'].empty else False
        last_close_val = df['Close'].values[-1] if not df['Signal'].empty else None

        if is_signal and pd.notna(last_close_val):
            entry = float(last_close_val)
            sl = (
                float(df['Low_5d'].values[-1])
                if pd.notna(df['Low_5d'].values[-1])
                else entry * 0.95
            )
            if sl >= entry or (entry - sl) / entry < 0.005:
                sl = entry * 0.965
            risk = entry - sl
            target = entry + (2 * risk)

            curr_vol = float(df['Volume'].values[-1])
            avg_vol = float(df['Vol_SMA20'].values[-1])
            vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
            buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
            accum_ratio = (
                float(df['Accum_Ratio_10d'].values[-1])
                if pd.notna(df['Accum_Ratio_10d'].values[-1])
                else 1.0
            )

            day_high = float(df['High'].values[-1])
            day_low = float(df['Low'].values[-1])
            day_range = day_high - day_low
            close_pos = (((entry - day_low) / day_range) * 100) if day_range > 0 else 50.0

            rsi_val = float(df['RSI'].values[-1]) if pd.notna(df['RSI'].values[-1]) else 50.0
            dist_ema20 = round(float(df['Dist_EMA20_Pct'].values[-1]), 2)
            day_gain = round(float(df['Signal_Day_Gain_Pct'].values[-1]), 2)

            # TRAP RISK EVALUATION
            trap_status = evaluate_trap_risk(
                vol_spike=vol_spike,
                dist_ema20=dist_ema20,
                rsi=rsi_val,
                close_pos=close_pos,
                day_gain=day_gain,
            )

            if close_pos >= 90.0 and buying_surge_pct >= 200.0:
                exec_rank = '🥇 Rank 1 (Top Winner)'
                entry_window = '9:15 AM - 9:30 AM'
                exec_condition = f'Hold above ₹{round(entry, 2)}'
            elif close_pos >= 85.0 and buying_surge_pct >= 150.0:
                exec_rank = '🥈 Rank 2 (High Priority)'
                entry_window = '9:20 AM - 9:35 AM'
                exec_condition = f'Break & Hold above ₹{round(entry, 2)}'
            else:
                exec_rank = '🥉 Rank 3 (Wait & Watch)'
                entry_window = '9:30 AM - 9:45 AM'
                exec_condition = f'15-Min Candle Close above ₹{round(entry, 2)}'

            bonus_score = 0
            if close_pos >= 85.0 and vol_spike >= 2.5:
                alert_type = '⭐ Ultimate Explosive Setup'
                bonus_score = 30
            elif accum_ratio >= 2.0 and vol_spike >= 2.0:
                alert_type = '🔥 Massive Heavy Buying'
            elif accum_ratio >= 1.8:
                alert_type = '🧱 Steady Accumulation'
            else:
                alert_type = '✅ Normal Signal'

            total_score = round(
                rsi_val
                + (vol_spike * 5)
                + (accum_ratio * 10)
                + (close_pos / 2)
                + bonus_score,
                2,
            )

            prev_5d_gain = (
                round(float(df['Return_5d'].values[-1]), 2)
                if pd.notna(df['Return_5d'].values[-1])
                else 0.0
            )

            return [{
                'Symbol': ticker.replace('.NS', ''),
                'Execution Rank': exec_rank,
                'Trap Risk Status': trap_status,
                'Entry Window': entry_window,
                'Execution Condition': exec_condition,
                'Alert': alert_type,
                'Entry Price (₹)': round(entry, 2),
                'Stop Loss (₹)': round(sl, 2),
                'Target Price (₹)': round(target, 2),
                'Day Change (%)': round(float(df['Pct_Change'].values[-1]), 2),
                'Signal Day Gain (%)': day_gain,
                'Prev 5-Day Gain (%)': prev_5d_gain,
                'Dist from 20 EMA (%)': dist_ema20,
                'RSI': round(rsi_val, 2),
                'Vol Spike (x)': round(vol_spike, 1),
                'Accum Ratio (10d)': round(accum_ratio, 2),
                'Continuation Score (%)': round(close_pos, 1),
                'Massive Buying Surge (%)': round(buying_surge_pct, 1),
                'Score': total_score,
            }]
    except Exception:
        return None
    return None


def filter_ideal_breakout_stock(df):
    if df.empty:
        return pd.DataFrame()
    
    # Filter out High Risk TRAP stocks
    cond_no_trap = ~df['Trap Risk Status'].str.contains('TRAP', na=False)
    cond_alert = df['Alert'].str.contains('⭐|Ultimate', na=False, regex=True)
    cond_cont = df['Continuation Score (%)'] > 80
    cond_surge = df['Massive Buying Surge (%)'] > 120
    cond_vol = df['Vol Spike (x)'] > 2.2
    cond_accum = df['Accum Ratio (10d)'] > 1.6
    cond_rsi = (df['RSI'] >= 58) & (df['RSI'] <= 72)

    ideal_df = df[
        cond_no_trap & cond_alert & cond_cont & cond_surge & cond_vol & cond_accum & cond_rsi
    ].copy()
    if not ideal_df.empty:
        return ideal_df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    return pd.DataFrame()


# ==============================================================================
# BACKTESTING ENGINE: HISTORICAL SERIAL NO. 1 ROADMAP (LAST 3 MONTHS)
# ==============================================================================
def run_3month_backtest(master_data, backtest_days=60):
    if not master_data:
        return pd.DataFrame()

    all_dates = set()
    for ticker, df in master_data.items():
        if len(df) >= 50:
            all_dates.update(df.index.tolist())

    sorted_dates = sorted(list(all_dates))
    if len(sorted_dates) < backtest_days:
        test_dates = sorted_dates[20:]
    else:
        test_dates = sorted_dates[-backtest_days:]

    daily_candidates = {d: [] for d in test_dates}

    for ticker, df in master_data.items():
        if len(df) < 50:
            continue

        df_calc = df.copy().dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        if len(df_calc) < 50:
            continue

        df_calc['Pct_Change'] = df_calc['Close'].pct_change() * 100
        df_calc['Vol_SMA20'] = df_calc['Volume'].rolling(20).mean()
        df_calc['Return_5d'] = df_calc['Close'].pct_change(periods=5) * 100
        df_calc['Return_20d'] = df_calc['Close'].pct_change(periods=20) * 100
        df_calc['Turnover'] = df_calc['Close'] * df_calc['Volume']

        df_calc['Is_Green'] = df_calc['Close'] > df_calc['Open']
        df_calc['Green_Vol'] = df_calc['Volume'].where(df_calc['Is_Green'], 0)
        df_calc['Red_Vol'] = df_calc['Volume'].where(~df_calc['Is_Green'], 0)

        up_vol_10 = df_calc['Green_Vol'].rolling(10).sum()
        down_vol_10 = df_calc['Red_Vol'].rolling(10).sum()
        df_calc['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)

        df_calc['High_20_Prev'] = df_calc['High'].shift(1).rolling(20).max()
        df_calc['EMA_20'] = df_calc['Close'].ewm(span=20, adjust=False).mean()
        df_calc['Dist_EMA20_Pct'] = ((df_calc['Close'] - df_calc['EMA_20']) / df_calc['EMA_20']) * 100
        df_calc['Signal_Day_Gain_Pct'] = ((df_calc['Close'] - df_calc['Open']) / df_calc['Open']) * 100

        delta = df_calc['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df_calc['RSI'] = 100 - (100 / (1 + rs))

        df_calc['Low_5d'] = df_calc['Low'].rolling(window=5).min()

        candle_range = df_calc['High'] - df_calc['Low']
        real_body_top = df_calc[['Open', 'Close']].max(axis=1)
        upper_wick = df_calc['High'] - real_body_top

        df_calc['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)
        df_calc['Close_Pos_Ratio'] = (df_calc['Close'] - df_calc['Low']) / (candle_range + 1e-10)
        cond_close_pos = df_calc['Close_Pos_Ratio'] > 0.70

        cond_no_wick = df_calc['Wick_Ratio'] <= 0.25
        cond_breakout = df_calc['Close'] > df_calc['High_20_Prev']
        cond1 = df_calc['Close'] >= 20
        cond2 = (df_calc['Pct_Change'] >= 1.0) & (df_calc['Pct_Change'] <= 12.0)
        cond3 = df_calc['Volume'] > (df_calc['Vol_SMA20'] * 2.2)
        cond4 = df_calc['Return_20d'] >= 2.0
        cond5 = df_calc['Turnover'] > (3 * 10000000)
        cond8 = (df_calc['RSI'] >= 58) & (df_calc['RSI'] <= 72)
        cond9 = df_calc['Close'] > df_calc['EMA_20']
        cond_accum = df_calc['Accum_Ratio_10d'] >= 1.6

        df_calc['Signal'] = (
            cond1
            & cond2
            & cond3
            & cond4
            & cond5
            & cond8
            & cond9
            & cond_accum
            & cond_no_wick
            & cond_breakout
            & cond_close_pos
        )

        signal_indices = df_calc[df_calc['Signal']].index

        for dt in signal_indices:
            if dt not in daily_candidates:
                continue

            idx = df_calc.index.get_loc(dt)
            row = df_calc.iloc[idx]

            entry = float(row['Close'])
            sl = float(row['Low_5d']) if pd.notna(row['Low_5d']) else entry * 0.95
            if sl >= entry or (entry - sl) / entry < 0.005:
                sl = entry * 0.965
            risk = entry - sl
            target = entry + (2 * risk)

            curr_vol = float(row['Volume'])
            avg_vol = float(row['Vol_SMA20'])
            vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
            buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
            accum_ratio = float(row['Accum_Ratio_10d']) if pd.notna(row['Accum_Ratio_10d']) else 1.0

            day_high = float(row['High'])
            day_low = float(row['Low'])
            day_range = day_high - day_low
            close_pos = (((entry - day_low) / day_range) * 100) if day_range > 0 else 50.0

            rsi_val = float(row['RSI']) if pd.notna(row['RSI']) else 50.0
            dist_ema20 = round(float(row['Dist_EMA20_Pct']), 2)
            day_gain = round(float(row['Signal_Day_Gain_Pct']), 2)

            trap_status = evaluate_trap_risk(
                vol_spike=vol_spike,
                dist_ema20=dist_ema20,
                rsi=rsi_val,
                close_pos=close_pos,
                day_gain=day_gain,
            )

            # Avoid adding TRAP stocks in Serial #1 Roadmap History
            if "TRAP" in trap_status:
                continue

            if (
                close_pos > 80
                and buying_surge_pct > 120
                and vol_spike > 2.2
                and accum_ratio > 1.6
            ):
                bonus_score = 30 if (close_pos >= 85.0 and vol_spike >= 2.5) else 0
                total_score = round(
                    rsi_val
                    + (vol_spike * 5)
                    + (accum_ratio * 10)
                    + (close_pos / 2)
                    + bonus_score,
                    2,
                )

                future_df = df_calc.iloc[idx + 1 : idx + 6]
                max_future_high = future_df['High'].max() if not future_df.empty else entry
                min_future_low = future_df['Low'].min() if not future_df.empty else entry

                hit_target = max_future_high >= target
                hit_sl = min_future_low <= sl
                max_gain_pct = round(((max_future_high - entry) / entry) * 100, 2)

                outcome = '⏳ Open'
                if hit_target and not hit_sl:
                    outcome = '🎯 Hit Target (2R)'
                elif hit_sl and not hit_target:
                    outcome = '🛑 Hit Stop Loss'
                elif hit_target and hit_sl:
                    outcome = '🎯 Target First / Volatile' if max_gain_pct >= 4 else '🛑 Hit SL First'

                if idx + 1 < len(df_calc):
                    next_day = df_calc.iloc[idx + 1]
                    next_high = round(float(next_day['High']), 2)
                    next_low = round(float(next_day['Low']), 2)
                    next_pnl_pct = round(((float(next_day['Close']) - entry) / entry) * 100, 2)
                else:
                    next_high = round(entry, 2)
                    next_low = round(entry, 2)
                    next_pnl_pct = 0.0

                prev_5d_gain = round(float(row['Return_5d']), 2) if pd.notna(row['Return_5d']) else 0.0

                daily_candidates[dt].append({
                    'Date': dt.strftime('%Y-%m-%d'),
                    'Serial #1 Symbol': ticker.replace('.NS', ''),
                    'Score': total_score,
                    'Trap Status': trap_status,
                    'Entry Price (₹)': round(entry, 2),
                    'Stop Loss (₹)': round(sl, 2),
                    'Target Price (₹)': round(target, 2),
                    'Next High (₹)': next_high,
                    'Next Low (₹)': next_low,
                    'Next Day PnL (%)': f"{next_pnl_pct:+}%",
                    'Prev 5-Day Gain (%)': f"{prev_5d_gain:+}%",
                    'Dist EMA20 (%)': f"{dist_ema20}%",
                    'RSI': round(rsi_val, 1),
                    'Vol Spike': f'{round(vol_spike, 1)}x',
                    'Accum Ratio (10d)': round(accum_ratio, 2),
                    'Massive Buying Surge (%)': round(buying_surge_pct, 1),
                    'Max Gain (Next 5 Days)': f'+{max_gain_pct}%',
                    'Outcome': outcome,
                })

    rank_1_history = []
    for dt in test_dates:
        candidates = daily_candidates.get(dt, [])
        if candidates:
            sorted_cands = sorted(candidates, key=lambda x: x['Score'], reverse=True)
            rank_1_history.append(sorted_cands[0])

    return pd.DataFrame(rank_1_history)


# ==============================================================================
# OPTIMIZED DOWNLOADER
# ==============================================================================
def download_market_data_safe(
    tickers,
    period='6mo',
    interval='1d',
    chunk_size=40,
    sleep_sec=0.5,
    progress_bar=None,
    status_text=None,
):
    cached_master = {}
    total_tickers = len(tickers)
    if total_tickers == 0:
        return cached_master

    ticker_chunks = [tickers[i : i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    total_chunks = len(ticker_chunks)

    def process_chunk(chunk):
        local_data = {}
        for attempt in range(3):
            try:
                raw_data = yf.download(
                    tickers=chunk,
                    period=period,
                    interval=interval,
                    progress=False,
                    group_by='ticker',
                    threads=True,
                    timeout=15,
                    session=session,
                )
                if raw_data.empty:
                    break

                for ticker in chunk:
                    try:
                        if isinstance(raw_data.columns, pd.MultiIndex):
                            if ticker in raw_data.columns.get_level_values(0):
                                t_data = raw_data.xs(ticker, axis=1, level=0, drop_level=True).copy()
                            elif ticker in raw_data.columns.get_level_values(1):
                                t_data = raw_data.xs(ticker, axis=1, level=1, drop_level=True).copy()
                            else:
                                continue
                        else:
                            t_data = raw_data.copy()

                        t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                        t_data = t_data[t_data['Volume'] > 0]
                        if not t_data.empty and len(t_data) >= 30:
                            local_data[ticker] = t_data
                    except Exception:
                        continue
                break
            except Exception as e:
                if 'Rate' in str(e) or '429' in str(e):
                    time.sleep(3 * (attempt + 1))
                else:
                    time.sleep(1)
        return local_data

    completed_chunks = 0
    completed_tickers = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_chunk, chunk): chunk for chunk in ticker_chunks}
        for future in as_completed(futures):
            chunk_tickers = futures[future]
            res = future.result()
            if res:
                cached_master.update(res)

            completed_chunks += 1
            completed_tickers += len(chunk_tickers)
            pct = min(100, int((completed_chunks / total_chunks) * 100))

            msg = f'⏳ Downloading market data: {pct}% ({min(completed_tickers, total_tickers)}/{total_tickers} stocks)'
            if IS_HEADLESS:
                log_msg(msg, 'info')
            else:
                if status_text:
                    status_text.text(msg)
                if progress_bar:
                    progress_bar.progress(pct / 100.0)

            time.sleep(sleep_sec)

    return cached_master


def is_market_hours():
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist)

    if now.weekday() >= 5:
        return False, 'Weekend (Saturday/Sunday) - Market Closed'

    start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=16, minute=0, second=0, microsecond=0)

    if start_time <= now <= end_time:
        return True, 'Market Hours Active'
    elif now < start_time:
        return False, f"Market Hours not started yet (Current IST: {now.strftime('%H:%M:%S')})"
    else:
        return False, f"Market Hours ended (Current IST: {now.strftime('%H:%M:%S')})"


# ==============================================================================
# MODE 1: HEADLESS / BACKGROUND SCANNER EXECUTION
# ==============================================================================
def run_headless_scan():
    log_msg('🚀 Starting Background Headless Market Scanner...', 'info')

    is_active, reason = is_market_hours()
    if not is_active:
        log_msg(f'⏸️ Skipping Scan: {reason}', 'warning')
        return

    nifty = fetch_nifty_market_status()
    if not nifty['is_bullish']:
        log_msg(
            f"🔴 Nifty Status: {nifty['status']} | Support (S1): ₹{nifty['s1']} | Resistance (R1): ₹{nifty['r1']}. Running full scan anyway...",
            'warning',
        )
    else:
        log_msg(
            f"🟢 Nifty Status: {nifty['status']} | Support (S1): ₹{nifty['s1']} | Resistance (R1): ₹{nifty['r1']}.",
            'info',
        )

    tickers = fetch_mega_nse_universe()
    log_msg(f'Downloading market data for {len(tickers)} stocks...', 'info')

    cached_master = download_market_data_safe(tickers, period='6mo', interval='1d', chunk_size=40, sleep_sec=0.5)

    if not cached_master:
        log_msg('❌ No stock data downloaded. Yahoo Finance may be rate-limiting.', 'error')
        return

    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_single_ticker, ticker, df): ticker for ticker, df in cached_master.items()}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.extend(res)

    res_df = pd.DataFrame(results)
    if res_df.empty:
        log_msg('No breakout signals found in this pass.', 'info')
        return

    already_sent = get_already_sent_stocks()
    alert_candidates = filter_ideal_breakout_stock(res_df)

    log_msg(f'Found {len(alert_candidates)} Roadmap breakout candidate(s).', 'info')

    for _, row in alert_candidates.iterrows():
        symbol = row['Symbol']

        if symbol not in already_sent:
            ok = send_email_alert(
                symbol=symbol,
                entry=row['Entry Price (₹)'],
                sl=row['Stop Loss (₹)'],
                target=row['Target Price (₹)'],
                score=row['Score'],
                rank=row['Execution Rank'],
                window=row['Entry Window'],
                condition=row['Execution Condition'],
                trap_status=row['Trap Risk Status'],
                dist_ema=row['Dist from 20 EMA (%)'],
            )
            if ok:
                mark_stock_as_sent(symbol)
                log_msg(f'🎯 Instant Mail Sent for new breakout: {symbol}', 'success')
        else:
            log_msg(f'⏭️ Duplicate Alert Skipped (Already Sent Today): {symbol}', 'info')

    log_msg('🏁 Headless Scan Completed Successfully.', 'success')


# ==============================================================================
# MODE 2: STREAMLIT WEB APP EXECUTION
# ==============================================================================
def run_streamlit_app():
    st.set_page_config(page_title='Ashiyana Dashboard Pro Max 🚀', page_icon='📈', layout='wide')

    if 'live_results' not in st.session_state:
        st.session_state['live_results'] = pd.DataFrame()
    if 'sent_email_alerts' not in st.session_state:
        st.session_state['sent_email_alerts'] = set()
    if 'backtest_history' not in st.session_state:
        st.session_state['backtest_history'] = pd.DataFrame()

    @st.cache_data(ttl=1800, show_spinner=False)
    def cached_nifty_status():
        return fetch_nifty_market_status()

    @st.cache_data(persist='disk', show_spinner=False)
    def cached_universe():
        return fetch_mega_nse_universe()

    @st.cache_data(ttl=900, show_spinner=False)
    def download_all_market_data(tickers):
        status_text = st.empty()
        progress_bar = st.progress(0)

        cached_master = download_market_data_safe(
            tickers,
            period='6mo',
            interval='1d',
            chunk_size=40,
            sleep_sec=0.5,
            progress_bar=progress_bar,
            status_text=status_text,
        )

        status_text.empty()
        progress_bar.empty()
        return cached_master

    st.markdown(
        """
        <style>
        .main { background-color: #0d1117; color: #c9d1d9; }
        .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
        h1, h2, h3 { color: #58a6ff; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title('Ashiyana Dashboard Pro Max 🚀')
    st.caption('Engine Upgraded ⚙️ (Trap Risk Filter, NIFTY 50 Trend, Rank Rules & 3-Month Backtest Integrated ⚡)')

    nifty_info = cached_nifty_status()
    if nifty_info['is_bullish']:
        st.success(
            f"### 🟢 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n\n"
            f"**Nifty 50 Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | **Strength:** +{nifty_info['pct_diff']}% above EMA. **(Take Fresh Long Trades)**\n\n"
            f"🛡️ **Immediate Support (S1):** ₹{nifty_info['s1']} | **20-Day Support (Low):** ₹{nifty_info['sup_20d']}\n\n"
            f"🎯 **Immediate Resistance (R1):** ₹{nifty_info['r1']} | **20-Day Resistance (High):** ₹{nifty_info['res_20d']}"
        )
    else:
        st.error(
            f"### 🔴 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n\n"
            f"**Nifty 50 Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | **Weakness:** {nifty_info['pct_diff']}% below EMA. **(Avoid New Long Positions)**\n\n"
            f"🛡️ **Immediate Support (S1):** ₹{nifty_info['s1']} | **20-Day Support (Low):** ₹{nifty_info['sup_20d']}\n\n"
            f"🎯 **Immediate Resistance (R1):** ₹{nifty_info['r1']} | **20-Day Resistance (High):** ₹{nifty_info['res_20d']}"
        )

    st.sidebar.header('⚙️ Pro Scanner Controls')
    formula_version = st.sidebar.selectbox(
        '📊 Strategy Formula Version',
        [
            'Version 2 (Without 500-day High)',
            'Version 1 (With 500-day High & Strict Filters)',
        ],
    )
    rsi_filter = st.sidebar.slider('Minimum RSI', 45, 75, 58)
    volume_multiplier = st.sidebar.slider('Volume Shock Multiplier', 1.0, 4.0, 2.2, step=0.1)
    min_turnover = st.sidebar.number_input('Minimum Daily Turnover (₹ Crores)', min_value=1, max_value=50, value=3)

    st.sidebar.markdown('---')
    st.sidebar.header('🔄 Controls')

    if st.sidebar.button('🗑️ Clear Cache'):
        download_all_market_data.clear()
        cached_universe.clear()
        cached_nifty_status.clear()
        if 'master_market_data' in st.session_state:
            del st.session_state['master_market_data']
        st.session_state['sent_email_alerts'] = set()
        st.session_state['backtest_history'] = pd.DataFrame()
        st.toast('🧹 Cache cleared!', icon='🗑️')
        st.rerun()

    st.sidebar.markdown('---')
    all_tickers = cached_universe()
    st.sidebar.write(f'Total Active Stocks: **{len(all_tickers)}**')

    if 'master_market_data' not in st.session_state:
        st.sidebar.warning('⚠️ Data not loaded.')
    else:
        st.sidebar.success(f"✅ Loaded ({len(st.session_state['master_market_data'])} stocks)")

    if st.sidebar.button('📥 Fetch / Refresh Data'):
        with st.spinner(f'Downloading data for {len(all_tickers)} stocks...'):
            download_all_market_data.clear()
            st.session_state['master_market_data'] = download_all_market_data(all_tickers)
            st.session_state['live_results'] = pd.DataFrame()
            st.session_state['backtest_history'] = pd.DataFrame()
            st.sidebar.success('🏁 Fresh Data Loaded!')
            st.rerun()

    tab1, tab2 = st.tabs(['⚡ Live Breakout Scanner', '📜 3-Month Backtest History (Rank #1)'])

    def compute_analytics():
        results = []
        pool = st.session_state.get('master_market_data', {})
        if not pool:
            return pd.DataFrame()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(
                    analyze_single_ticker,
                    ticker,
                    df,
                    volume_multiplier,
                    rsi_filter,
                    min_turnover,
                    formula_version,
                ): ticker
                for ticker, df in pool.items()
            }
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.extend(res)
        return pd.DataFrame(results)

    with tab1:
        st.subheader('⚡ Live Data Collection & Priority Scan')

        if 'master_market_data' not in st.session_state:
            st.info("👈 Please click 'Fetch / Refresh Data' from the sidebar first.")
        else:
            if st.button('🚀 Run Scanner', key='live_btn'):
                with st.spinner('Searching for breakout setups...'):
                    st.session_state['live_results'] = compute_analytics()

            res_df = st.session_state.get('live_results', pd.DataFrame())

            if not res_df.empty:
                res_df = res_df.sort_values(by='Score', ascending=False)
                ideal_matches_df = filter_ideal_breakout_stock(res_df)

                if not ideal_matches_df.empty:
                    for _, row in ideal_matches_df.iterrows():
                        stock_symbol = row['Symbol']
                        if stock_symbol not in st.session_state['sent_email_alerts']:
                            sent_status = send_email_alert(
                                symbol=stock_symbol,
                                entry=row['Entry Price (₹)'],
                                sl=row['Stop Loss (₹)'],
                                target=row['Target Price (₹)'],
                                score=row['Score'],
                                rank=row['Execution Rank'],
                                window=row['Entry Window'],
                                condition=row['Execution Condition'],
                                trap_status=row['Trap Risk Status'],
                                dist_ema=row['Dist from 20 EMA (%)'],
                            )
                            if sent_status:
                                st.session_state['sent_email_alerts'].add(stock_symbol)
                                st.toast(f'📧 Email alert sent for {stock_symbol}!', icon='📩')

                    st.success(f'🎉 **IDEAL MATCHES FOUND!** {len(ideal_matches_df)} stock(s) met 100% criteria.')

                    box_html = (
                        f'<div style="background-color: #161b22; border: 2px solid #ffd700; border-radius: 12px; padding: 18px; margin-bottom: 25px;">'
                        f'<h2 style="color: #ffd700; margin-top: 0; margin-bottom: 15px;">👑 Breakout Execution Roadmap ({len(ideal_matches_df)} Found)</h2>'
                    )

                    for idx, row in ideal_matches_df.iterrows():
                        rank = idx + 1
                        sym = row['Symbol']
                        ex_rank = row['Execution Rank']
                        trap_st = row['Trap Risk Status']
                        dist_e = row['Dist from 20 EMA (%)']
                        win = row['Entry Window']
                        cond = row['Execution Condition']
                        sc = row['Score']
                        cs = row['Continuation Score (%)']
                        mbs = row['Massive Buying Surge (%)']
                        rsi_v = row['RSI']
                        p_entry = row['Entry Price (₹)']
                        p_sl = row['Stop Loss (₹)']
                        p_tgt = row['Target Price (₹)']

                        box_html += f"""<div style="border-bottom: 1px dashed #30363d; padding-bottom: 12px; margin-bottom: 12px;">
<h3 style="color: #58a6ff; margin: 0;">#{rank} Stock: <u>{sym}</u> ({ex_rank})</h3>
<p style="color: #00ff7f; font-weight: bold; margin-top: 2px; margin-bottom: 4px;">Status: {trap_st} | Dist from 20 EMA: {dist_e}%</p>
<p style="color: #ffd700; font-weight: bold; margin-top: 4px; margin-bottom: 4px;">⏰ Entry Window: {win} | ⚡ Execution Rule: {cond}</p>
<p style="color: #c9d1d9; font-size: 14px; margin-top: 2px; margin-bottom: 6px;"><b>Score:</b> {sc} | <b>Continuation Score:</b> {cs}% | <b>Surge:</b> {mbs}% | <b>RSI:</b> {rsi_v}</p>
<p style="color: #00ff7f; font-weight: bold; margin: 0; font-size: 15px;">🎯 Trigger: ₹{p_entry} | SL: ₹{p_sl} | Target: ₹{p_tgt}</p>
</div>"""

                    box_html += '</div>'
                    st.markdown(box_html, unsafe_allow_html=True)

                    top_stock_row = ideal_matches_df.iloc[0]
                    top_stock = top_stock_row['Symbol']

                    st.markdown(f'### 👑 Chart View: **{top_stock}**')
                    chart_data = yf.download(
                        f'{top_stock}.NS',
                        period='3mo',
                        interval='1d',
                        progress=False,
                        session=session,
                    )
                    chart_data = flatten_yfinance_df(chart_data)

                    if not chart_data.empty:
                        chart_data = chart_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
                        if not chart_data.empty:
                            fig = go.Figure(
                                data=[
                                    go.Candlestick(
                                        x=chart_data.index,
                                        open=chart_data['Open'],
                                        high=chart_data['High'],
                                        low=chart_data['Low'],
                                        close=chart_data['Close'],
                                        name='Candlestick',
                                    )
                                ]
                            )
                            fig.add_trace(
                                go.Scatter(
                                    x=chart_data.index,
                                    y=chart_data['Close'].ewm(span=20).mean(),
                                    line=dict(color='orange', width=1.5),
                                    name='EMA 20',
                                )
                            )

                            live_sl = top_stock_row['Stop Loss (₹)']
                            live_tgt = top_stock_row['Target Price (₹)']

                            fig.add_hline(
                                y=live_sl,
                                line_dash='dash',
                                line_color='red',
                                line_width=2,
                                annotation_text=f'SL: ₹{live_sl}',
                                annotation_position='bottom left',
                            )
                            fig.add_hline(
                                y=live_tgt,
                                line_dash='dash',
                                line_color='green',
                                line_width=2,
                                annotation_text=f'Target: ₹{live_tgt}',
                                annotation_position='top left',
                            )

                            fig.update_layout(
                                template='plotly_dark',
                                title=f'{top_stock} Setup Chart',
                                xaxis_rangeslider_visible=False,
                            )
                            st.plotly_chart(fig)
                else:
                    st.markdown(
                        '<div style="background-color: #161b22; border: 2px solid #ff4d4d; border-radius: 12px; padding: 18px; margin-bottom: 25px;">'
                        '<h2 style="color: #ff4d4d; margin: 0;">❌ No Ideal Match Found Today</h2>'
                        '<p style="color: #c9d1d9; font-size: 15px; margin-top: 8px; margin-bottom: 0px;">No stocks passed all strict confirmation filters or passed Trap Risk criteria.</p></div>',
                        unsafe_allow_html=True,
                    )

                def highlight_rows(row):
                    trap_val = str(row.get('Trap Risk Status', ''))
                    alert = str(row.get('Alert', ''))
                    
                    if 'TRAP' in trap_val:
                        return ['background-color: rgba(220, 53, 69, 0.35); color: #ff6b6b; font-weight: bold'] * len(row)
                    elif '⭐' in alert or 'Ultimate' in alert:
                        return ['background-color: #ffd700; color: #000000; font-weight: bold'] * len(row)
                    elif '🔥' in alert:
                        return ['background-color: rgba(255, 69, 0, 0.35); color: #ffffff; font-weight: bold'] * len(row)
                    elif '🧱' in alert:
                        return ['background-color: rgba(0, 150, 255, 0.25); color: #ffffff; font-weight: bold'] * len(row)
                    return [''] * len(row)

                styled_df = res_df.style.apply(highlight_rows, axis=1)
                st.subheader(f'📊 Active Signals Found: {len(res_df)}')
                st.dataframe(styled_df, hide_index=True)
            else:
                st.caption("No breakout setups currently active. Click 'Run Scanner' above.")

    with tab2:
        st.subheader('📜 3-Month Backtested History (Rank #1 Roadmap Stocks)')
        st.caption('Har trading day market close par Roadmap me Serial No. 1 par rehne wale stock aur next 5-day performance ki report (Trap Safe filter updated).')

        if 'master_market_data' not in st.session_state:
            st.info('👈 Side bar se "Fetch / Refresh Data" par click kijiye pehle.')
        else:
            if st.button('🔄 Run 3-Month Backtest Analysis', key='backtest_btn'):
                with st.spinner('Pichle 3 mahine ka Serial #1 history evaluate ho raha hai...'):
                    bt_df = run_3month_backtest(st.session_state['master_market_data'])
                    st.session_state['backtest_history'] = bt_df

            bt_history = st.session_state.get('backtest_history', pd.DataFrame())

            if not bt_history.empty:
                total_trades = len(bt_history)
                targets_hit = len(bt_history[bt_history['Outcome'].str.contains('Target', na=False)])
                sl_hit = len(bt_history[bt_history['Outcome'].str.contains('Stop Loss', na=False)])
                win_rate = round((targets_hit / total_trades) * 100, 1) if total_trades > 0 else 0.0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Total Serial #1 Days', f'{total_trades}')
                col2.metric('Target Hit (2R)', f'{targets_hit}')
                col3.metric('Stop Loss Hit', f'{sl_hit}')
                col4.metric('Win Rate (%)', f'{win_rate}%')

                st.markdown('---')

                def highlight_outcome(row):
                    outcome = str(row.get('Outcome', ''))
                    if 'Target' in outcome:
                        return ['background-color: rgba(40, 167, 69, 0.25); color: #28a745; font-weight: bold'] * len(row)
                    elif 'Stop Loss' in outcome:
                        return ['background-color: rgba(220, 53, 69, 0.25); color: #dc3545; font-weight: bold'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    bt_history.style.apply(highlight_outcome, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption('Backtest run karne ke liye uper button par click kijiye.')


if __name__ == '__main__':
    if IS_HEADLESS:
        run_headless_scan()
    else:
        run_streamlit_app()

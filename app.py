import datetime
import json
import os
import smtplib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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


def send_email_alert(symbol, entry, sl, target, score, rank, window, condition):
    if not SENDER_PASSWORD or not SENDER_EMAIL:
        log_msg('⚠️ Email Credentials Missing. Check Secrets!', 'warning')
        return False

    try:
        subject = f'🚀 [{rank}] High Priority Breakout: {symbol}'
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
            <div style="max-width: 500px; background-color: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #28a745; margin: 0 auto;">
                <h2 style="color: #28a745; margin-top: 0;">🚀 Breakout Alert Triggered!</h2>
                <p>Stock <b>{symbol}</b> has met strict breakout conditions.</p>
                <hr style="border: 0.5px solid #30363d;">
                <p><b>📊 Symbol:</b> <span style="color: #58a6ff;">{symbol}</span></p>
                <p><b>🏆 Execution Rank:</b> <span style="color: #ffd700;">{rank}</span></p>
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


def fetch_nifty_market_status():
    status_data = {'status': '⚠️ UNKNOWN', 'is_bullish': True, 'nifty_close': 0.0, 'nifty_ema20': 0.0}
    try:
        nifty_ticker = yf.Ticker('^NSEI', session=session)
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

            is_bullish = last_close > last_ema20
            status_text = '🟢 TRADE MODE ACTIVE (Bullish Market)' if is_bullish else '🔴 AVOID / BEARISH MARKET'

            return {
                'status': status_text,
                'is_bullish': is_bullish,
                'nifty_close': round(last_close, 2),
                'nifty_ema20': round(last_ema20, 2),
                'pct_diff': pct_diff,
                's1': s1,
                'r1': r1,
                'sup_20d': round(float(nifty['Low'].tail(20).min()), 2),
                'res_20d': round(float(nifty['High'].tail(20).max()), 2),
            }
    except Exception:
        pass
    return status_data


def fetch_mega_nse_universe():
    fallback = [
        'ADANIENT.NS', 'ADANIPORTS.NS', 'AXISBANK.NS', 'BHARTIARTL.NS', 'HDFCBANK.NS',
        'ICICIBANK.NS', 'INFY.NS', 'ITC.NS', 'LT.NS', 'RELIANCE.NS', 'SBIN.NS', 'TCS.NS'
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
    turnover_limit=10,
    min_avg_vol=50000,
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
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']

        df['Is_Green'] = df['Close'] > df['Open']
        df['Green_Vol'] = df['Volume'].where(df['Is_Green'], 0)
        df['Red_Vol'] = df['Volume'].where(~df['Is_Green'], 0)

        up_vol_10 = df['Green_Vol'].rolling(10).sum()
        down_vol_10 = df['Red_Vol'].rolling(10).sum()
        df['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)

        df['High_20_Prev'] = df['High'].shift(1).rolling(20).max()
        df['High_50_Prev'] = df['High'].shift(1).rolling(50).max()

        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))

        df['Low_5d'] = df['Low'].rolling(window=5).min()

        candle_range = df['High'] - df['Low']
        real_body_top = df[['Open', 'Close']].max(axis=1)
        upper_wick = df['High'] - real_body_top

        df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)

        cond_no_wick = df['Wick_Ratio'] <= 0.20
        cond_breakout = (df['Close'] > df['High_20_Prev']) & (df['Close'] >= df['High_50_Prev'])
        cond1 = df['Close'] >= 20
        cond2 = (df['Pct_Change'] >= 1.5) & (df['Pct_Change'] <= 8.0)
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
        cond4 = df['Return_20d'] >= 2.0
        cond5 = df['Turnover'] >= (turnover_limit * 10000000)
        cond_vol_floor = df['Vol_SMA20'] >= min_avg_vol
        cond8 = (df['RSI'] >= rsi_filter) & (df['RSI'] <= 72)
        cond9 = (df['Close'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50'])
        cond_accum = df['Accum_Ratio_10d'] >= 1.5

        df['Signal'] = (
            cond1 & cond2 & cond3 & cond4 & cond5 & cond_vol_floor
            & cond8 & cond9 & cond_accum & cond_no_wick & cond_breakout
        )

        is_signal = bool(df['Signal'].values[-1]) if not df['Signal'].empty else False
        last_close_val = df['Close'].values[-1] if not df['Signal'].empty else None

        if is_signal and pd.notna(last_close_val):
            entry = float(last_close_val)
            sl = float(df['Low_5d'].values[-1]) if pd.notna(df['Low_5d'].values[-1]) else entry * 0.95
            if sl >= entry or (entry - sl) / entry < 0.005:
                sl = entry * 0.965
            risk = entry - sl
            target = entry + (2 * risk)

            curr_vol = float(df['Volume'].values[-1])
            avg_vol = float(df['Vol_SMA20'].values[-1])
            vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
            buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
            accum_ratio = float(df['Accum_Ratio_10d'].values[-1]) if pd.notna(df['Accum_Ratio_10d'].values[-1]) else 1.0

            day_high = float(df['High'].values[-1])
            day_low = float(df['Low'].values[-1])
            day_range = day_high - day_low
            close_pos = ((entry - day_low) / day_range * 100) if day_range > 0 else 50

            if close_pos < 75.0:
                return None

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

            rsi_val = float(df['RSI'].values[-1]) if pd.notna(df['RSI'].values[-1]) else 50.0
            total_score = round(rsi_val + (vol_spike * 5) + (accum_ratio * 10) + (close_pos / 2), 2)

            return [{
                'Symbol': ticker.replace('.NS', ''),
                'Execution Rank': exec_rank,
                'Entry Window': entry_window,
                'Execution Condition': exec_condition,
                'Alert': '⭐ Explosive Clean Breakout',
                'Entry Price (₹)': round(entry, 2),
                'Stop Loss (₹)': round(sl, 2),
                'Target Price (₹)': round(target, 2),
                'Day Change (%)': round(float(df['Pct_Change'].values[-1]), 2),
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
    cond_cont = df['Continuation Score (%)'] >= 75.0
    cond_surge = df['Massive Buying Surge (%)'] >= 100.0
    cond_vol = df['Vol Spike (x)'] >= 2.2
    cond_accum = df['Accum Ratio (10d)'] >= 1.5

    ideal_df = df[cond_cont & cond_surge & cond_vol & cond_accum].copy()
    if not ideal_df.empty:
        return ideal_df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    return pd.DataFrame()


# ==============================================================================
# 📜 1-MONTH BACKTEST ENGINE
# ==============================================================================
def run_1month_backtest(market_data, volume_multiplier=2.2, rsi_filter=58, min_turnover=10, min_avg_vol=50000):
    """
    Simulates strategy rules day-by-day over the past 30 days (~22 trading days).
    Evaluates signal entries and checks forward price action for Target/SL outcomes.
    """
    trades = []
    
    for ticker, df in market_data.items():
        if len(df) < 50:
            continue
            
        df = df.copy()
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        if len(df) < 50:
            continue

        # Look back approx 22 trading days (1 month)
        lookback_days = min(22, len(df) - 50)
        if lookback_days <= 0:
            continue
            
        start_idx = len(df) - lookback_days - 1

        for idx in range(start_idx, len(df) - 1):
            sub_df = df.iloc[:idx + 1].copy()
            res = analyze_single_ticker(
                ticker, sub_df, volume_multiplier, rsi_filter, min_turnover, min_avg_vol
            )
            
            if res and len(res) > 0:
                trade_info = res[0]
                signal_date = sub_df.index[-1]
                entry_price = trade_info['Entry Price (₹)']
                sl_price = trade_info['Stop Loss (₹)']
                target_price = trade_info['Target Price (₹)']
                
                # Check forward candles for Target / SL outcome
                forward_df = df.iloc[idx + 1:]
                outcome = 'OPEN ⏳'
                exit_price = float(forward_df['Close'].iloc[-1]) if not forward_df.empty else entry_price
                exit_date = forward_df.index[-1] if not forward_df.empty else signal_date
                pnl_pct = 0.0

                for f_date, f_row in forward_df.iterrows():
                    high = float(f_row['High'])
                    low = float(f_row['Low'])
                    
                    # Target hit first
                    if high >= target_price:
                        outcome = 'TARGET HIT 🎯'
                        exit_price = target_price
                        exit_date = f_date
                        pnl_pct = round(((target_price - entry_price) / entry_price) * 100, 2)
                        break
                    # SL hit first
                    elif low <= sl_price:
                        outcome = 'STOP LOSS HIT 🛑'
                        exit_price = sl_price
                        exit_date = f_date
                        pnl_pct = round(((sl_price - entry_price) / entry_price) * 100, 2)
                        break

                if outcome == 'OPEN ⏳':
                    pnl_pct = round(((exit_price - entry_price) / entry_price) * 100, 2)

                trades.append({
                    'Signal Date': signal_date.strftime('%Y-%m-%d'),
                    'Symbol': trade_info['Symbol'],
                    'Entry Price (₹)': entry_price,
                    'Stop Loss (₹)': sl_price,
                    'Target Price (₹)': target_price,
                    'Outcome': outcome,
                    'Exit Price (₹)': round(exit_price, 2),
                    'Exit Date': exit_date.strftime('%Y-%m-%d') if hasattr(exit_date, 'strftime') else str(exit_date),
                    'P&L (%)': pnl_pct,
                    'Score': trade_info['Score']
                })

    return pd.DataFrame(trades)


# ==============================================================================
# DOWNLOADER WITH PERCENTAGE TRACKING
# ==============================================================================
def download_market_data_safe(
    tickers, period='3mo', interval='1d', chunk_size=40, sleep_sec=0.5, progress_bar=None, status_text=None
):
    cached_master = {}
    total_tickers = len(tickers)
    if total_tickers == 0:
        return cached_master

    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
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

            msg = f"⏳ Downloading market data: {pct}% ({min(completed_tickers, total_tickers)}/{total_tickers} stocks)"
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
        return False, "Weekend - Market Closed"
    start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if start_time <= now <= end_time:
        return True, "Market Hours Active"
    return False, f"Market Hours Inactive (IST: {now.strftime('%H:%M:%S')})"


# ==============================================================================
# EXECUTION MODES
# ==============================================================================
def run_headless_scan():
    log_msg('🚀 Starting Background Headless Market Scanner...', 'info')
    is_active, reason = is_market_hours()
    if not is_active:
        log_msg(f'⏸️ Skipping Scan: {reason}', 'warning')
        return

    nifty = fetch_nifty_market_status()
    log_msg(f"Nifty Status: {nifty['status']}", 'info')

    tickers = fetch_mega_nse_universe()
    cached_master = download_market_data_safe(tickers, period='3mo', interval='1d')

    if not cached_master:
        log_msg('❌ No stock data downloaded.', 'error')
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
        log_msg('No high-conviction breakout signals found in this pass.', 'info')
        return

    already_sent = get_already_sent_stocks()
    alert_candidates = filter_ideal_breakout_stock(res_df)

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
            )
            if ok:
                mark_stock_as_sent(symbol)


def run_streamlit_app():
    st.set_page_config(page_title='Ashiyana Dashboard Pro Max 🚀', page_icon='📈', layout='wide')

    if 'live_results' not in st.session_state:
        st.session_state['live_results'] = pd.DataFrame()
    if 'backtest_results' not in st.session_state:
        st.session_state['backtest_results'] = pd.DataFrame()

    st.title('Ashiyana Dashboard Pro Max 🚀')
    st.caption('Engine Upgraded ⚙️ (Strict False Breakout Mitigation + 1-Month Backtest Active 🛡️)')

    nifty_info = fetch_nifty_market_status()
    if nifty_info['is_bullish']:
        st.success(f"### 🟢 MARKET TREND: **{nifty_info['status']}** | Nifty 50: ₹{nifty_info['nifty_close']}")
    else:
        st.error(f"### 🔴 MARKET TREND: **{nifty_info['status']}** | Nifty 50: ₹{nifty_info['nifty_close']}")

    st.sidebar.header('⚙️ Pro Scanner Controls')
    rsi_filter = st.sidebar.slider('Minimum RSI', 45, 75, 58)
    volume_multiplier = st.sidebar.slider('Volume Shock Multiplier', 1.0, 4.0, 2.2, step=0.1)
    min_turnover = st.sidebar.number_input('Minimum Daily Turnover (₹ Crores)', min_value=1, max_value=50, value=10)
    min_avg_vol = st.sidebar.number_input('Minimum 20-Day Avg Volume', min_value=10000, max_value=500000, value=50000)

    all_tickers = fetch_mega_nse_universe()
    st.sidebar.write(f'Total Active Stocks: **{len(all_tickers)}**')

    if st.sidebar.button('📥 Fetch / Refresh Data'):
        p_bar = st.progress(0)
        s_text = st.empty()
        st.session_state['master_market_data'] = download_market_data_safe(
            all_tickers, progress_bar=p_bar, status_text=s_text
        )
        st.session_state['live_results'] = pd.DataFrame()
        st.session_state['backtest_results'] = pd.DataFrame()
        st.success('Fresh Data Loaded!')
        st.rerun()

    tab1, tab2 = st.tabs(['🚀 Live Scanner', '📜 1-Month Backtest History'])

    with tab1:
        if 'master_market_data' in st.session_state:
            if st.button('🚀 Run Pro Scanner', key='live_btn'):
                results = []
                pool = st.session_state.get('master_market_data', {})
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {
                        executor.submit(
                            analyze_single_ticker, ticker, df, volume_multiplier, rsi_filter, min_turnover, min_avg_vol
                        ): ticker
                        for ticker, df in pool.items()
                    }
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            results.extend(res)
                st.session_state['live_results'] = pd.DataFrame(results)

        res_df = st.session_state.get('live_results', pd.DataFrame())
        if not res_df.empty:
            st.subheader(f'📊 High Conviction Breakouts Found: {len(res_df)}')
            st.dataframe(res_df, hide_index=True)
        else:
            st.info('Data fetch karein aur "Run Pro Scanner" par click karein.')

    with tab2:
        if 'master_market_data' in st.session_state:
            if st.button('📜 Run 1-Month Backtest Engine', key='bt_btn'):
                with st.spinner('Pichle 1 mahine ke sabhi breakout signals evaluate kiye ja rahe hain...'):
                    bt_df = run_1month_backtest(
                        st.session_state['master_market_data'],
                        volume_multiplier,
                        rsi_filter,
                        min_turnover,
                        min_avg_vol,
                    )
                    st.session_state['backtest_results'] = bt_df

        bt_df = st.session_state.get('backtest_results', pd.DataFrame())
        if not bt_df.empty:
            # Calculate Backtest Metrics
            total_trades = len(bt_df)
            wins = len(bt_df[bt_df['Outcome'] == 'TARGET HIT 🎯'])
            losses = len(bt_df[bt_df['Outcome'] == 'STOP LOSS HIT 🛑'])
            open_trades = len(bt_df[bt_df['Outcome'] == 'OPEN ⏳'])
            
            closed_trades = wins + losses
            win_rate = round((wins / closed_trades) * 100, 1) if closed_trades > 0 else 0.0
            avg_pnl = round(bt_df['P&L (%)'].mean(), 2)

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Signals", total_trades)
            col2.metric("Target Hit 🎯", wins)
            col3.metric("SL Hit 🛑", losses)
            col4.metric("Win Rate (%)", f"{win_rate}%")
            col5.metric("Avg Return (%)", f"{avg_pnl}%")

            st.subheader('📋 Detailed Signal History (Past 30 Days)')
            st.dataframe(bt_df.sort_values(by='Signal Date', ascending=False), hide_index=True)
        else:
            st.info('Pehle "Fetch / Refresh Data" dabaen, fir "Run 1-Month Backtest Engine" par click karein.')


if __name__ == '__main__':
    if IS_HEADLESS:
        run_headless_scan()
    else:
        run_streamlit_app()

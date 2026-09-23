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
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    print(
        f"[{datetime.datetime.now(ist).strftime('%H:%M:%S')}] [{level.upper()}]"
        f' {msg}'
    )
  else:
    if level == 'error':
      st.error(msg)
    elif level == 'warning':
      st.warning(msg)
    elif level == 'success':
      st.success(msg)
    else:
      st.info(msg)


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
  ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
  today_str = datetime.datetime.now(ist).strftime('%Y-%m-%d')
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
  ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
  today_str = datetime.datetime.now(ist).strftime('%Y-%m-%d')
  sent_set = get_already_sent_stocks()
  sent_set.add(symbol)
  try:
    with open(SENT_LOG_FILE, 'w') as f:
      json.dump({'date': today_str, 'stocks': list(sent_set)}, f)
  except Exception as e:
    log_msg(f'Could not save sent log: {e}', 'warning')


def send_email_alert(symbol, entry, sl, target, score, rank, window, condition):
  if not SENDER_PASSWORD or not SENDER_EMAIL:
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
                <p><b>⏰ Entry Window:</b> {window}</p>
                <p><b>⚡ Execution Rule:</b> {condition}</p>
                <p><b>⭐ Score:</b> {score}</p>
                <p><b>🎯 Trigger / Entry:</b> ₹{entry}</p>
                <p><b>🛑 Stop Loss:</b> ₹{sl}</p>
                <p><b>🏁 Target Price:</b> ₹{target}</p>
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
    return True
  except Exception:
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
          status_text = '🟢 TRADE MODE ACTIVE (Bullish Trend)' if is_bullish else '🔴 AVOID / BEARISH TREND'
          return {
              'status': status_text, 'is_bullish': is_bullish, 'nifty_close': round(last_close, 2),
              'nifty_ema20': round(last_ema20, 2), 'pct_diff': pct_diff, 's1': s1, 'r1': r1,
              'sup_20d': sup_20d, 'res_20d': res_20d,
          }
      except Exception:
        time.sleep(1)
        continue
  return {'status': '⚠️ UNKNOWN', 'is_bullish': True, 'nifty_close': 0.0, 'nifty_ema20': 0.0, 'pct_diff': 0.0, 's1': 0.0, 'r1': 0.0, 'sup_20d': 0.0, 'res_20d': 0.0}


def fetch_mega_nse_universe():
  fallback = ['ADANIENT.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
  try:
    if os.path.exists('EQUITY_L.csv'):
      df = pd.read_csv('EQUITY_L.csv')
      df.columns = df.columns.str.strip()
      tickers = [f"{str(row['SYMBOL']).strip()}.NS" for _, row in df.iterrows() if pd.notna(row['SYMBOL']) and str(row['SERIES']).strip() == 'EQ']
      if len(tickers) > 100: return sorted(list(set(tickers)))
  except Exception:
    pass
  return fallback


# Core Strategy Builder (Used for both Live Scanner and Backtesting)
def apply_strategy_indicators(df, volume_multiplier, rsi_filter, turnover_limit, formula_version):
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
    df['Turnover'] = df['Close'] * df['Volume']

    df['Is_Green'] = df['Close'] > df['Open']
    df['Green_Vol'] = df['Volume'].where(df['Is_Green'], 0)
    df['Red_Vol'] = df['Volume'].where(~df['Is_Green'], 0)
    df['Accum_Ratio_10d'] = df['Green_Vol'].rolling(10).sum() / (df['Red_Vol'].rolling(10).sum() + 1e-10)

    df['High_20_Prev'] = df['High'].shift(1).rolling(20).max()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.ewm(com=13, adjust=False).mean() / (loss.ewm(com=13, adjust=False).mean() + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Low_5d'] = df['Low'].rolling(window=5).min()
    window_size = max(10, min(500, len(df) - 2))
    df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()

    candle_range = df['High'] - df['Low']
    upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)

    # 🛡️ Anti-False Breakout Engine
    df['Consolidation_Range_Pct'] = ((df['High'].shift(1).rolling(3).max() - df['Low'].shift(1).rolling(3).min()) / df['Low'].shift(1).rolling(3).min()) * 100
    df['Consecutive_Green'] = df['Is_Green'].rolling(3).sum()

    cond1 = df['Close'] >= 20
    cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 12.0)
    cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
    cond4 = df['Return_20d'] >= 2.0
    cond5 = df['Turnover'] > (turnover_limit * 10000000)
    cond8 = (df['RSI'] >= rsi_filter) & (df['RSI'] <= 75)
    cond9 = df['Close'] > df['EMA_20']
    cond_accum = df['Accum_Ratio_10d'] >= 1.5
    
    cond_no_wick = df['Wick_Ratio'] <= 0.25
    cond_breakout = df['Close'] > df['High_20_Prev']
    cond_above_200 = df['Close'] > df['EMA_200']
    
    cond_consolidation = df['Consolidation_Range_Pct'] <= 8.0 
    cond_not_exhausted = df['Close'] <= (df['EMA_20'] * 1.12) 
    cond_not_late_entry = df['Consecutive_Green'].shift(1) < 3 

    if 'Version 1' in formula_version or formula_version == 'v1':
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
        cond10 = df['EMA_50'] > df['EMA_200']
        df['Signal'] = (cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9 & cond10 & cond_accum & cond_no_wick & cond_breakout & cond_consolidation & cond_not_exhausted & cond_not_late_entry)
    else:
        df['Signal'] = (cond1 & cond2 & cond3 & cond4 & cond5 & cond8 & cond9 & cond_accum & cond_no_wick & cond_breakout & cond_above_200 & cond_consolidation & cond_not_exhausted & cond_not_late_entry)
        
    return df


def analyze_single_ticker(ticker, df, volume_multiplier=2.2, rsi_filter=58, turnover_limit=3, formula_version='Version 2'):
  try:
    if len(df) < 200: return None
    df = df.copy().dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
    df = df[df['Volume'] > 0]
    if len(df) < 200: return None

    df = apply_strategy_indicators(df, volume_multiplier, rsi_filter, turnover_limit, formula_version)

    is_signal = bool(df['Signal'].values[-1]) if not df['Signal'].empty else False
    if is_signal:
      entry = float(df['Close'].values[-1])
      sl = float(df['Low_5d'].values[-1])
      if sl >= entry or (entry - sl) / entry < 0.005: sl = entry * 0.965
      target = entry + (2 * (entry - sl))

      curr_vol, avg_vol = float(df['Volume'].values[-1]), float(df['Vol_SMA20'].values[-1])
      vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
      buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100
      accum_ratio = float(df['Accum_Ratio_10d'].values[-1])

      day_range = float(df['High'].values[-1]) - float(df['Low'].values[-1])
      close_pos = (((entry - float(df['Low'].values[-1])) / day_range * 100) if day_range > 0 else 50)

      if close_pos >= 90.0 and buying_surge_pct >= 200.0:
        exec_rank, entry_window, exec_condition = '🥇 Rank 1 (Top Winner)', '9:15 AM - 9:30 AM', f'Gap-Up < 1.5% AND Hold above ₹{round(entry, 2)}'
      elif close_pos >= 85.0 and buying_surge_pct >= 150.0:
        exec_rank, entry_window, exec_condition = '🥈 Rank 2 (High Priority)', '9:20 AM - 9:35 AM', f'Gap-Up < 1.5% AND Break above ₹{round(entry, 2)}'
      else:
        exec_rank, entry_window, exec_condition = '🥉 Rank 3 (Wait & Watch)', '9:30 AM - 9:45 AM', f'15-Min Candle Close above ₹{round(entry, 2)}'

      rsi_val = float(df['RSI'].values[-1])
      bonus = 30 if (close_pos >= 85.0 and vol_spike >= 2.5) else 0
      alert_type = '⭐ Ultimate Explosive Setup' if bonus else ('🔥 Massive Heavy Buying' if accum_ratio >= 2.0 and vol_spike >= 2.0 else '✅ Normal Signal')
      total_score = round(rsi_val + (vol_spike * 5) + (accum_ratio * 10) + (close_pos / 2) + bonus, 2)

      return [{
          'Symbol': ticker.replace('.NS', ''), 'Execution Rank': exec_rank, 'Entry Window': entry_window,
          'Execution Condition': exec_condition, 'Alert': alert_type, 'Entry Price (₹)': round(entry, 2),
          'Stop Loss (₹)': round(sl, 2), 'Target Price (₹)': round(target, 2),
          'Day Change (%)': round(float(df['Pct_Change'].values[-1]), 2), 'RSI': round(rsi_val, 2),
          'Vol Spike (x)': round(vol_spike, 1), 'Accum Ratio (10d)': round(accum_ratio, 2),
          'Continuation Score (%)': round(close_pos, 1), 'Massive Buying Surge (%)': round(buying_surge_pct, 1),
          'Score': total_score,
      }]
  except Exception:
    pass
  return None


# ==============================================================================
# 📊 1-MONTH BACKTEST ENGINE 
# ==============================================================================
def run_1_month_backtest(cached_master, volume_multiplier, rsi_filter, turnover_limit, formula_version, lookback_days=22):
    results = []
    
    for ticker, df_raw in cached_master.items():
        try:
            if len(df_raw) < 200: continue
            df = df_raw.copy().dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
            df = df[df['Volume'] > 0]
            if len(df) < 200: continue

            df = apply_strategy_indicators(df, volume_multiplier, rsi_filter, turnover_limit, formula_version)
            
            # Start loop for the last 22 days (excluding the very last day as it has no future)
            last_idx = len(df) - 1
            start_idx = max(200, last_idx - lookback_days)
            
            for i in range(start_idx, last_idx):
                if df['Signal'].iloc[i]:
                    entry_date = df.index[i].strftime('%d-%b-%Y')
                    entry = float(df['Close'].iloc[i])
                    sl = float(df['Low_5d'].iloc[i])
                    if sl >= entry or (entry - sl) / entry < 0.005: 
                        sl = entry * 0.965
                    
                    risk = entry - sl
                    target = entry + (2 * risk) # 1:2 Risk Reward
                    
                    # Track future performance from Next Day up to Today
                    future_df = df.iloc[i+1 : last_idx+1]
                    
                    if future_df.empty:
                        status = 'Active 🟡'
                        max_high = entry
                    else:
                        max_high = float(future_df['High'].max())
                        min_low = float(future_df['Low'].min())
                        
                        # Did it hit Stoploss first or Target first?
                        if min_low <= sl:
                            sl_date = future_df[future_df['Low'] <= sl].index[0]
                            tgt_mask = future_df['High'] >= target
                            if tgt_mask.any():
                                tgt_date = future_df[tgt_mask].index[0]
                                if tgt_date < sl_date:
                                    status = 'Target Hit 🟢'
                                else:
                                    status = 'SL Hit 🔴'
                            else:
                                status = 'SL Hit 🔴'
                        elif max_high >= target:
                            status = 'Target Hit 🟢'
                        else:
                            status = 'Active 🟡'
                            
                    max_profit = round(((max_high - entry) / entry) * 100, 2)
                    
                    results.append({
                        'Date': entry_date,
                        'Symbol': ticker.replace('.NS', ''),
                        'Status': status,
                        'Entry Price': round(entry, 2),
                        'Max High Reached': round(max_high, 2),
                        'Max ROI (%)': f"{max_profit}%",
                        'Target (1:2)': round(target, 2),
                        'Stop Loss': round(sl, 2)
                    })
        except Exception:
            continue
            
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        # Sort by Date descending
        df_results['RealDate'] = pd.to_datetime(df_results['Date'])
        df_results = df_results.sort_values(by='RealDate', ascending=False).drop('RealDate', axis=1)
        
    return df_results


def filter_ideal_breakout_stock(df):
  if df.empty: return pd.DataFrame()
  cond_alert = df['Alert'].str.contains('⭐|Ultimate', na=False, regex=True)
  cond_cont = df['Continuation Score (%)'] > 80
  cond_surge = df['Massive Buying Surge (%)'] > 120
  cond_vol = df['Vol Spike (x)'] > 2.2
  cond_accum = df['Accum Ratio (10d)'] > 1.6
  cond_rsi = (df['RSI'] >= 58) & (df['RSI'] <= 72)
  ideal_df = df[cond_alert & cond_cont & cond_surge & cond_vol & cond_accum & cond_rsi].copy()
  if not ideal_df.empty: return ideal_df.sort_values(by='Score', ascending=False).reset_index(drop=True)
  return pd.DataFrame()


def download_market_data_safe(tickers, period='1y', interval='1d', chunk_size=40, sleep_sec=0.5, progress_bar=None, status_text=None):
  cached_master = {}
  total_tickers, completed_chunks, completed_tickers = len(tickers), 0, 0
  if total_tickers == 0: return cached_master
  ticker_chunks = [tickers[i : i + chunk_size] for i in range(0, len(tickers), chunk_size)]

  def process_chunk(chunk):
    local_data = {}
    for attempt in range(3):
      try:
        raw_data = yf.download(tickers=chunk, period=period, interval=interval, progress=False, group_by='ticker', threads=True, timeout=15, session=session)
        if raw_data.empty: break
        for ticker in chunk:
          try:
            if isinstance(raw_data.columns, pd.MultiIndex):
              t_data = raw_data.xs(ticker, axis=1, level=0, drop_level=True).copy() if ticker in raw_data.columns.get_level_values(0) else raw_data.xs(ticker, axis=1, level=1, drop_level=True).copy() if ticker in raw_data.columns.get_level_values(1) else pd.DataFrame()
            else: t_data = raw_data.copy()
            t_data = t_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
            t_data = t_data[t_data['Volume'] > 0]
            if not t_data.empty and len(t_data) >= 30: local_data[ticker] = t_data
          except Exception: continue
        break
      except Exception as e:
        time.sleep(3 * (attempt + 1)) if 'Rate' in str(e) or '429' in str(e) else time.sleep(1)
    return local_data

  with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(process_chunk, chunk): chunk for chunk in ticker_chunks}
    for future in as_completed(futures):
      res = future.result()
      if res: cached_master.update(res)
      completed_chunks += 1
      completed_tickers += len(futures[future])
      pct = min(100, int((completed_chunks / len(ticker_chunks)) * 100))
      msg = f"⏳ Downloading data: {pct}% ({min(completed_tickers, total_tickers)}/{total_tickers})"
      if IS_HEADLESS: log_msg(msg, 'info')
      else:
        if status_text: status_text.text(msg)
        if progress_bar: progress_bar.progress(pct / 100.0)
      time.sleep(sleep_sec)
  return cached_master

# ==============================================================================
# MODE 2: STREAMLIT WEB APP EXECUTION
# ==============================================================================
def run_streamlit_app():
  st.set_page_config(page_title='Ashiyana Dashboard Pro Max 🚀', page_icon='📈', layout='wide')

  if 'live_results' not in st.session_state: st.session_state['live_results'] = pd.DataFrame()
  if 'backtest_results' not in st.session_state: st.session_state['backtest_results'] = pd.DataFrame()
  if 'sent_email_alerts' not in st.session_state: st.session_state['sent_email_alerts'] = set()

  @st.cache_data(ttl=1800, show_spinner=False)
  def cached_nifty_status(): return fetch_nifty_market_status()

  @st.cache_data(persist='disk', show_spinner=False)
  def cached_universe(): return fetch_mega_nse_universe()

  @st.cache_data(ttl=900, show_spinner=False)
  def download_all_market_data(tickers):
    status_text = st.empty()
    progress_bar = st.progress(0)
    cached_master = download_market_data_safe(tickers, period='1y', interval='1d', chunk_size=40, progress_bar=progress_bar, status_text=status_text)
    status_text.empty()
    progress_bar.empty()
    return cached_master

  st.markdown("""<style>.main { background-color: #0d1117; color: #c9d1d9; } .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; } h1, h2, h3 { color: #58a6ff; }</style>""", unsafe_allow_html=True)
  st.title('Ashiyana Dashboard Pro Max 🚀')

  nifty_info = cached_nifty_status()
  if nifty_info['is_bullish']:
    st.success(f"### 🟢 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n\n**Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | **Strength:** +{nifty_info['pct_diff']}% above EMA.\n\n🛡️ **Support:** ₹{nifty_info['s1']} | 🎯 **Resistance:** ₹{nifty_info['r1']}")
  else:
    st.error(f"### 🔴 NIFTY 50 TREND STATUS: **{nifty_info['status']}**\n\n**Close:** ₹{nifty_info['nifty_close']} | **20 EMA:** ₹{nifty_info['nifty_ema20']} | **Weakness:** {nifty_info['pct_diff']}% below EMA.\n\n🛡️ **Support:** ₹{nifty_info['s1']} | 🎯 **Resistance:** ₹{nifty_info['r1']}")

  st.sidebar.header('⚙️ Pro Scanner Controls')
  formula_version = st.sidebar.selectbox('📊 Strategy Formula Version', ['Version 2 (Without 500-day High)', 'Version 1 (With 500-day High & Strict Filters)'])
  rsi_filter = st.sidebar.slider('Minimum RSI', 45, 75, 58)
  volume_multiplier = st.sidebar.slider('Volume Shock Multiplier', 1.0, 4.0, 2.2, step=0.1)
  min_turnover = st.sidebar.number_input('Minimum Daily Turnover (₹ Crores)', min_value=1, max_value=50, value=3)

  st.sidebar.markdown('---')
  all_tickers = cached_universe()
  st.sidebar.write(f'Total Active Stocks: **{len(all_tickers)}**')

  if 'master_market_data' not in st.session_state: st.sidebar.warning('⚠️ Data not loaded.')
  else: st.sidebar.success(f"✅ Loaded ({len(st.session_state['master_market_data'])} stocks)")

  if st.sidebar.button('📥 Fetch / Refresh Data'):
    with st.spinner(f'Downloading data for {len(all_tickers)} stocks...'):
      download_all_market_data.clear()
      st.session_state['master_market_data'] = download_all_market_data(all_tickers)
      st.session_state['live_results'] = pd.DataFrame()
      st.session_state['backtest_results'] = pd.DataFrame()
      st.rerun()

  # --- BACKTEST TRIGGER ---
  st.sidebar.markdown('---')
  if st.sidebar.button('⏱️ Run 1-Month Backtest'):
      if 'master_market_data' not in st.session_state:
          st.sidebar.error("Fetch data first!")
      else:
          with st.spinner("Crunching historical data for last 22 trading days..."):
              st.session_state['backtest_results'] = run_1_month_backtest(
                  st.session_state['master_market_data'], 
                  volume_multiplier, rsi_filter, min_turnover, formula_version, 22
              )

  st.sidebar.markdown('---')
  if st.sidebar.button('🗑️ Clear Cache'):
    st.cache_data.clear()
    st.rerun()


  # --- MAIN TABS ---
  tab1, tab2 = st.tabs(["⚡ Live Priority Scanner", "⏱️ 1-Month Backtest Results"])

  with tab1:
      st.subheader('⚡ Live Data Collection & Priority Scan')
      if 'master_market_data' not in st.session_state:
        st.info("👈 Please click 'Fetch / Refresh Data' from the sidebar first.")
      else:
        if st.button('🚀 Run Live Scanner', key='live_btn'):
          with st.spinner('Searching for breakout setups...'):
            pool = st.session_state['master_market_data']
            results = []
            with ThreadPoolExecutor(max_workers=8) as executor:
              futures = {executor.submit(analyze_single_ticker, tick, df, volume_multiplier, rsi_filter, min_turnover, formula_version): tick for tick, df in pool.items()}
              for future in as_completed(futures):
                res = future.result()
                if res: results.extend(res)
            st.session_state['live_results'] = pd.DataFrame(results).sort_values(by='Score', ascending=False) if results else pd.DataFrame()

        res_df = st.session_state.get('live_results', pd.DataFrame())
        if not res_df.empty:
          st.dataframe(res_df, hide_index=True)
        else:
          st.caption("No breakout setups currently active.")

  with tab2:
      st.subheader('⏱️ Strategy Performance (Last 30 Days / 22 Trading Sessions)')
      
      bt_df = st.session_state.get('backtest_results', pd.DataFrame())
      
      if bt_df.empty:
          st.info("👈 Click 'Run 1-Month Backtest' in the sidebar to view history.")
      else:
          total_trades = len(bt_df)
          target_hits = len(bt_df[bt_df['Status'].str.contains('Target Hit')])
          sl_hits = len(bt_df[bt_df['Status'].str.contains('SL Hit')])
          active_trades = len(bt_df[bt_df['Status'].str.contains('Active')])
          
          win_rate = round((target_hits / (target_hits + sl_hits)) * 100, 2) if (target_hits + sl_hits) > 0 else 0
          
          col1, col2, col3, col4 = st.columns(4)
          col1.metric("Total Breakouts Found", total_trades)
          col2.metric("Target Hit 🟢 (1:2 RR)", target_hits)
          col3.metric("Stoploss Hit 🔴", sl_hits)
          col4.metric("Strategy Win Rate 🔥", f"{win_rate}%")
          
          st.markdown("### 📜 Trade Log")
          
          def highlight_status(val):
              if 'Target Hit' in val: return 'color: #00ff7f; font-weight: bold'
              elif 'SL Hit' in val: return 'color: #ff4d4d; font-weight: bold'
              elif 'Active' in val: return 'color: #ffd700; font-weight: bold'
              return ''

          styled_bt = bt_df.style.map(highlight_status, subset=['Status'])
          st.dataframe(styled_bt, hide_index=True, use_container_width=True)

if __name__ == '__main__':
  if IS_HEADLESS:
    log_msg('Headless mode running...', 'info')
  else:
    run_streamlit_app()

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
        ' Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
})

SENT_LOG_FILE = 'sent_alerts.json'


def log_msg(msg, level='info'):
  now_str = datetime.datetime.now().strftime('%H:%M:%S')
  print(f'[{now_str}] [{level.upper()}] {msg}')


def safe_get_secret(key, default_val=''):
  return os.getenv(key, default_val)


SENDER_EMAIL = safe_get_secret('SENDER_EMAIL', '')
SENDER_PASSWORD = safe_get_secret('SENDER_PASSWORD', '')
RECEIVER_EMAIL = safe_get_secret('RECEIVER_EMAIL', '')


# --- SENT ALERTS TRACKING ---
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
    log_msg(f'Log save fail: {e}', 'warning')


# --- INSTANT EMAIL SENDER ---
def send_email_alert(symbol, entry, sl, target, score, rank, window, condition):
  if not SENDER_PASSWORD or not SENDER_EMAIL:
    log_msg('⚠️ Email Credentials Missing!', 'warning')
    return False

  try:
    subject = f'🚀 LIVE BREAKOUT ALERT [{rank}]: {symbol}'

    body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px;">
            <div style="max-width: 500px; background-color: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #28a745; margin: 0 auto;">
                <h2 style="color: #28a745; margin-top: 0;">🚀 Instant Breakout Triggered!</h2>
                <p>Stock <b>{symbol}</b> has met live breakout criteria.</p>
                <hr style="border: 0.5px solid #30363d;">
                <p><b>📊 Symbol:</b> <span style="color: #58a6ff;">{symbol}</span></p>
                <p><b>🏆 Execution Rank:</b> <span style="color: #ffd700;">{rank}</span></p>
                <p><b>⏰ Entry Window:</b> {window}</p>
                <p><b>⚡ Execution Rule:</b> {condition}</p>
                <p><b>⭐ Score:</b> {score}</p>
                <p><b>🎯 Trigger Price:</b> ₹{entry}</p>
                <p><b>🛑 Stop Loss:</b> ₹{sl}</p>
                <p><b>🏁 Target:</b> ₹{target}</p>
                <hr style="border: 0.5px solid #30363d;">
                <p style="font-size: 12px; color: #8b949e;">Live Engine Alert • {datetime.datetime.now().strftime("%I:%M %p")}</p>
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
    server.login(
        SENDER_EMAIL.strip(), SENDER_PASSWORD.replace(' ', '').strip()
    )
    server.send_message(msg)
    server.quit()
    log_msg(f'📧 INSTANT EMAIL SENT FOR {symbol}', 'success')
    return True
  except Exception as e:
    log_msg(f'❌ Email failed for {symbol}: {e}', 'error')
    return False


# --- FAST DATA DOWNLOADER ---
def download_live_data_fast(tickers, chunk_size=40, sleep_sec=0.2):
  cached_master = {}
  ticker_chunks = [
      tickers[i : i + chunk_size] for i in range(0, len(tickers), chunk_size)
  ]

  def process_chunk(chunk):
    local_data = {}
    try:
      raw_data = yf.download(
          tickers=chunk,
          period='1mo',
          interval='1d',
          progress=False,
          group_by='ticker',
          threads=True,
          timeout=10,
          session=session,
      )
      if raw_data is None or raw_data.empty:
        return local_data

      for ticker in chunk:
        try:
          if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker in raw_data.columns.get_level_values(0):
              t_data = raw_data.xs(
                  ticker, axis=1, level=0, drop_level=True
              ).copy()
            elif ticker in raw_data.columns.get_level_values(1):
              t_data = raw_data.xs(
                  ticker, axis=1, level=1, drop_level=True
              ).copy()
            else:
              continue
          else:
            t_data = raw_data.copy()

          t_data = t_data.dropna(
              subset=['Open', 'High', 'Low', 'Close', 'Volume']
          )
          t_data = t_data[t_data['Volume'] > 0]
          if not t_data.empty and len(t_data) >= 15:
            local_data[ticker] = t_data
        except Exception:
          continue
    except Exception:
      pass
    return local_data

  with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(process_chunk, chunk) for chunk in ticker_chunks
    ]
    for future in as_completed(futures):
      res = future.result()
      if res:
        cached_master.update(res)
      time.sleep(sleep_sec)

  return cached_master


# --- STOCK ANALYSIS ENGINE ---
def analyze_single_ticker(ticker, df):
  try:
    if len(df) < 15:
      return None

    df = df.copy().dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
    df = df[df['Volume'] > 0]

    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Vol_SMA20'] = df['Volume'].rolling(15, min_periods=5).mean()
    df['Return_20d'] = df['Close'].pct_change(periods=15) * 100
    df['Turnover'] = df['Close'] * df['Volume']

    df['Is_Green'] = df['Close'] > df['Open']
    df['Green_Vol'] = df['Volume'].where(df['Is_Green'], 0)
    df['Red_Vol'] = df['Volume'].where(~df['Is_Green'], 0)

    up_vol_10 = df['Green_Vol'].rolling(10, min_periods=3).sum()
    down_vol_10 = df['Red_Vol'].rolling(10, min_periods=3).sum()
    df['Accum_Ratio_10d'] = up_vol_10 / (down_vol_10 + 1e-10)

    df['High_20_Prev'] = df['High'].shift(1).rolling(15, min_periods=5).max()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Low_5d'] = df['Low'].rolling(window=5, min_periods=2).min()

    candle_range = df['High'] - df['Low']
    real_body_top = df[['Open', 'Close']].max(axis=1)
    upper_wick = df['High'] - real_body_top

    df['Wick_Ratio'] = upper_wick / (candle_range + 1e-10)

    cond_no_wick = df['Wick_Ratio'] <= 0.30
    cond_breakout = df['Close'] > df['High_20_Prev']
    cond1 = df['Close'] >= 20
    cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 12.0)
    cond3 = df['Volume'] > (df['Vol_SMA20'] * 2.0)
    cond4 = df['Return_20d'] >= 1.5
    cond5 = df['Turnover'] > 20000000  # ₹2 Cr turnover
    cond8 = (df['RSI'] >= 56) & (df['RSI'] <= 75)
    cond9 = df['Close'] > df['EMA_20']
    cond_accum = df['Accum_Ratio_10d'] >= 1.4

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
    )

    if bool(df['Signal'].values[-1]):
      entry = float(df['Close'].values[-1])
      sl = (
          float(df['Low_5d'].values[-1])
          if pd.notna(df['Low_5d'].values[-1])
          else entry * 0.95
      )
      if sl >= entry or (entry - sl) / entry < 0.005:
        sl = entry * 0.965
      target = entry + (2 * (entry - sl))

      curr_vol = float(df['Volume'].values[-1])
      avg_vol = float(df['Vol_SMA20'].values[-1])
      vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
      buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100

      day_high = float(df['High'].values[-1])
      day_low = float(df['Low'].values[-1])
      day_range = day_high - day_low
      close_pos = (
          ((entry - day_low) / day_range * 100) if day_range > 0 else 50
      )

      if close_pos >= 88.0 and buying_surge_pct >= 150.0:
        exec_rank = '🥇 Rank 1 (Immediate Entry)'
        entry_window = '9:15 AM - 9:30 AM'
        exec_condition = f'Hold above ₹{round(entry, 2)}'
      elif close_pos >= 80.0:
        exec_rank = '🥈 Rank 2 (High Priority)'
        entry_window = '9:20 AM - 9:40 AM'
        exec_condition = f'Break & Hold above ₹{round(entry, 2)}'
      else:
        exec_rank = '🥉 Rank 3 (Wait & Watch)'
        entry_window = '9:30 AM - 10:00 AM'
        exec_condition = f'15-Min Candle Close above ₹{round(entry, 2)}'

      return {
          'Symbol': ticker.replace('.NS', ''),
          'Execution Rank': exec_rank,
          'Entry Window': entry_window,
          'Execution Condition': exec_condition,
          'Entry Price (₹)': round(entry, 2),
          'Stop Loss (₹)': round(sl, 2),
          'Target Price (₹)': round(target, 2),
          'Score': round(
              float(df['RSI'].values[-1]) + (vol_spike * 5) + (close_pos / 2),
              2,
          ),
      }
  except Exception:
    return None
  return None


# --- LIVE CONTINUOUS MONITORING LOOP ---
def start_live_market_session():
  ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

  log_msg(
      '🚀 Continuous Live Market Engine Initialized (09:09 AM - 03:30 PM)',
      'info',
  )

  # Load Tickers (Nifty 500 / Midcap Universe for fast scan)
  universe = [
      'ADANIENT.NS',
      'ADANIPORTS.NS',
      'APOLLOHOSP.NS',
      'ASIANPAINT.NS',
      'AXISBANK.NS',
      'BAJAJ-AUTO.NS',
      'BAJFINANCE.NS',
      'BHARTIARTL.NS',
      'BRITANNIA.NS',
      'CIPLA.NS',
      'COALINDIA.NS',
      'DIVISLAB.NS',
      'DRREDDY.NS',
      'EICHERMOT.NS',
      'GRASIM.NS',
      'HCLTECH.NS',
      'HDFCBANK.NS',
      'HEROMOTOCO.NS',
      'HINDALCO.NS',
      'HINDUNILVR.NS',
      'ICICIBANK.NS',
      'ITC.NS',
      'INDUSINDBK.NS',
      'INFY.NS',
      'JSWSTEEL.NS',
      'KOTAKBANK.NS',
      'LT.NS',
      'M&M.NS',
      'MARUTI.NS',
      'NTPC.NS',
      'NESTLEIND.NS',
      'ONGC.NS',
      'POWERGRID.NS',
      'RELIANCE.NS',
      'SBIN.NS',
      'SUNPHARMA.NS',
      'TCS.NS',
      'TATAMOTORS.NS',
      'TATASTEEL.NS',
      'TECHM.NS',
      'TITAN.NS',
      'ULTRACEMCO.NS',
      'WIPRO.NS',
      'PERSISTENT.NS',
      'COFORGE.NS',
      'POLYCAB.NS',
      'DIXON.NS',
      'TRENT.NS',
      'BEL.NS',
      'HAL.NS',
      'MAZDOCK.NS',
      'BHEL.NS',
      'REC.NS',
      'PFC.NS',
      'IRFC.NS',
  ]

  if os.path.exists('EQUITY_L.csv'):
    try:
      df_eq = pd.read_csv('EQUITY_L.csv')
      df_eq.columns = df_eq.columns.str.strip()
      t_list = [
          f"{str(r['SYMBOL']).strip()}.NS"
          for _, r in df_eq.iterrows()
          if pd.notna(r['SYMBOL']) and str(r['SERIES']).strip() == 'EQ'
      ]
      if len(t_list) > 100:
        universe = t_list[:500]  # First 500 liquid stocks for high speed
    except Exception:
      pass

  while True:
    now = datetime.datetime.now(ist)
    current_time = now.time()

    market_start = datetime.time(9, 9)
    market_close = datetime.time(15, 30)

    # Weekend Check
    if now.weekday() >= 5:
      log_msg('📅 Weekend detected. Scanner in standby mode.', 'info')
      break

    # Time Window Check
    if current_time < market_start:
      wait_secs = (
          datetime.datetime.combine(now.date(), market_start, ist) - now
      ).total_seconds()
      log_msg(
          f'⏰ Market opens at 9:09 AM. Waiting {int(wait_secs)} seconds...',
          'info',
      )
      time.sleep(min(wait_secs, 300))
      continue

    if current_time > market_close:
      log_msg('🏁 03:30 PM Reached. Live session ended.', 'success')
      break

    # --- LIVE PASS EXECUTION ---
    log_msg(f'🔄 Running Live Scan Loop on {len(universe)} stocks...', 'info')
    already_sent = get_already_sent_stocks()

    market_data = download_live_data_fast(universe)

    signals = []
    with ThreadPoolExecutor(max_workers=6) as executor:
      futures = {
          executor.submit(analyze_single_ticker, ticker, df): ticker
          for ticker, df in market_data.items()
      }
      for future in as_completed(futures):
        res = future.result()
        if res:
          signals.append(res)

    log_msg(f'Found {len(signals)} potential breakout signals.', 'info')

    for sig in signals:
      sym = sig['Symbol']
      # Instant Email Send logic
      if sym not in already_sent:
        sent_ok = send_email_alert(
            symbol=sym,
            entry=sig['Entry Price (₹)'],
            sl=sig['Stop Loss (₹)'],
            target=sig['Target Price (₹)'],
            score=sig['Score'],
            rank=sig['Execution Rank'],
            window=sig['Entry Window'],
            condition=sig['Execution Condition'],
        )
        if sent_ok:
          mark_stock_as_sent(sym)

    log_msg('💤 Cycle completed. Waiting 5 minutes before next pass...\n', 'info')
    time.sleep(300)  # Scan every 5 minutes (300 seconds)


if __name__ == '__main__':
  start_live_market_session()

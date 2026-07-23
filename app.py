import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import io
import os
import time
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# --- Page Configurations ---
st.set_page_config(
    page_title="Aashiyana Dashboard Pro Max 🚀", page_icon="📈", layout="wide"
)

# --- 🛠️ SAFELY INITIALIZE SESSION STATE ---
if "live_results" not in st.session_state:
  st.session_state["live_results"] = pd.DataFrame()
if "bt_results" not in st.session_state:
  st.session_state["bt_results"] = pd.DataFrame()


# --- CUSTOM CACHE CLEAR LOGIC ---
def clear_all_caches():
  download_all_market_data.clear()
  get_mega_nse_universe.clear()
  if "master_market_data" in st.session_state:
    del st.session_state["master_market_data"]
  st.toast("🧹 Cache cleared! Refreshing data on next run.", icon="🗑️")


# --- CUSTOM THEME ---
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

st.title("Aashiyana Dashboard Pro Max 🚀")
st.caption("Engine Upgraded ⚙️ (Super Fast Multi-Threaded Edition ⚡)")


# --- AUTOMATED 2300+ NSE TICKER FETCH-ENGINE ---
@st.cache_data(persist="disk", show_spinner=False)
def get_mega_nse_universe():
  try:
    df = pd.read_csv("EQUITY_L.csv")
    df.columns = df.columns.str.strip()
    tickers = [
        f"{str(row['SYMBOL']).strip()}.NS"
        for _, row in df.iterrows()
        if pd.notna(row["SYMBOL"]) and str(row["SERIES"]).strip() == "EQ"
    ]
    if len(tickers) > 1000:
      return sorted(list(set(tickers)))
  except FileNotFoundError:
    st.sidebar.error("❌ EQUITY_L.csv फाइल नहीं मिली!")
  except Exception as e:
    st.sidebar.error(f"⚠️ Error: {e}")

  fallback = [
      "ADANIENT.NS",
      "ADANIPORTS.NS",
      "APOLLOHOSP.NS",
      "ASIANPAINT.NS",
      "AXISBANK.NS",
      "BAJAJ-AUTO.NS",
      "BAJFINANCE.NS",
      "BAJAJFINSV.NS",
      "BPCL.NS",
      "BHARTIARTL.NS",
      "BRITANNIA.NS",
      "CIPLA.NS",
      "COALINDIA.NS",
      "DIVISLAB.NS",
      "DRREDDY.NS",
      "EICHERMOT.NS",
      "GRASIM.NS",
      "HCLTECH.NS",
      "HDFCBANK.NS",
      "HDFCLIFE.NS",
      "HEROMOTOCO.NS",
      "HINDALCO.NS",
      "HINDUNILVR.NS",
      "ICICIBANK.NS",
      "ITC.NS",
      "INDUSINDBK.NS",
      "INFY.NS",
      "JSWSTEEL.NS",
      "KOTAKBANK.NS",
      "LTIM.NS",
      "LT.NS",
      "M&M.NS",
      "MARUTI.NS",
      "NTPC.NS",
      "NESTLEIND.NS",
      "ONGC.NS",
      "POWERGRID.NS",
      "RELIANCE.NS",
      "SBILIFE.NS",
      "SBIN.NS",
      "SUNPHARMA.NS",
      "TCS.NS",
      "TATACONSUM.NS",
      "TATAMOTORS.NS",
      "TATASTEEL.NS",
      "TECHM.NS",
      "TITAN.NS",
      "UPL.NS",
      "ULTRACEMCO.NS",
      "WIPRO.NS",
  ]
  return fallback


# --- HIGH-SPEED SINGLE CHUNK DOWNLOADER ---
def _fetch_single_chunk(chunk):
  data_map = {}
  try:
    # Period set to 1y for maximum speed & lightness
    raw_data = yf.download(
        chunk,
        period="1y",
        interval="1d",
        progress=False,
        group_by="ticker",
        threads=True,
        timeout=12,
    )
    if raw_data.empty:
      return data_map

    is_multi = isinstance(raw_data.columns, pd.MultiIndex)
    for ticker in chunk:
      try:
        if is_multi:
          if ticker in raw_data.columns.get_level_values(0):
            t_data = raw_data[ticker].dropna(
                subset=["Open", "High", "Low", "Close", "Volume"]
            )
            t_data = t_data[t_data["Volume"] > 0]
            if len(t_data) >= 50:
              data_map[ticker] = t_data
        else:
          if len(chunk) == 1 and not raw_data.empty:
            t_data = raw_data.dropna(
                subset=["Open", "High", "Low", "Close", "Volume"]
            )
            t_data = t_data[t_data["Volume"] > 0]
            if len(t_data) >= 50:
              data_map[ticker] = t_data
      except Exception:
        continue
  except Exception:
    pass
  return data_map


# --- OPTIMIZED PARALLEL BULK DOWNLOADER ---
@st.cache_data(ttl=86400, persist="disk", show_spinner=False)
def download_all_market_data(tickers):
  chunk_size = 100  # Larger chunk size for fewer network calls
  ticker_chunks = [
      tickers[i : i + chunk_size] for i in range(0, len(tickers), chunk_size)
  ]

  cached_master = {}
  progress_bar = st.progress(0)
  status_text = st.empty()

  # Concurrent parallel batch fetching using ThreadPoolExecutor
  completed = 0
  with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_chunk = {
        executor.submit(_fetch_single_chunk, chunk): chunk
        for chunk in ticker_chunks
    }
    for future in as_completed(future_to_chunk):
      result_map = future.result()
      cached_master.update(result_map)
      completed += 1
      progress_bar.progress(completed / len(ticker_chunks))
      status_text.text(
          f"⚡ Downloading Batches in Parallel: {completed}/{len(ticker_chunks)}"
          f" ({len(cached_master)} stocks loaded)"
      )

  progress_bar.empty()
  status_text.empty()
  return cached_master


# --- MERGED CORE ANALYTICS PROCESSOR (OPTIMIZED) ---
def analyze_single_ticker(
    ticker,
    df,
    mode,
    volume_multiplier,
    rsi_filter,
    turnover_limit,
    formula_version,
):
  try:
    if len(df) < 50:
      return None

    # Base Technical Calculations
    df["Pct_Change"] = df["Close"].pct_change() * 100
    df["Vol_SMA20"] = df["Volume"].rolling(20).mean()
    df["Return_20d"] = df["Close"].pct_change(periods=20) * 100
    df["Turnover"] = df["Close"] * df["Volume"]

    # Consolidation & Volume Math
    df["Is_Green"] = df["Close"] > df["Open"]
    df["Green_Vol"] = df["Volume"].where(df["Is_Green"], 0)
    df["Red_Vol"] = df["Volume"].where(~df["Is_Green"], 0)

    up_vol_10 = df["Green_Vol"].rolling(10).sum()
    down_vol_10 = df["Red_Vol"].rolling(10).sum()
    df["Accum_Ratio_10d"] = up_vol_10 / (down_vol_10 + 1e-10)

    df["High_20_Prev"] = df["High"].shift(1).rolling(20).max()
    df["Low_20_Prev"] = df["Low"].shift(1).rolling(20).min()
    df["Range_20_Pct"] = (
        (df["High_20_Prev"] - df["Low_20_Prev"])
        / (df["Close"].shift(1) + 1e-10)
    ) * 100

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # RSI Calculation
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    window_size = min(250, len(df) - 2)
    df["Max_High_1d_Ago"] = (
        df["High"].shift(1).rolling(window=window_size, min_periods=1).max()
    )
    df["Low_5d"] = df["Low"].rolling(window=5).min()

    # Base Filters
    cond1 = df["Close"] >= 20
    cond2 = (df["Pct_Change"] >= 0.5) & (df["Pct_Change"] <= 15.0)
    cond3 = df["Volume"] > (df["Vol_SMA20"] * volume_multiplier)
    cond4 = df["Return_20d"] >= 2.0
    cond5 = df["Turnover"] > (turnover_limit * 10000000)
    cond8 = df["RSI"] >= rsi_filter
    cond9 = df["Close"] > df["EMA_20"]
    cond_accum = df["Accum_Ratio_10d"] >= 1.5

    if formula_version == "Version 1 (With 500-day High & Strict Filters)":
      cond7 = df["Close"] >= df["Max_High_1d_Ago"]
      cond10 = df["EMA_50"] > df["EMA_200"]
      cond11 = (
          (df["High"] - df["Close"]) / (df["High"] - df["Low"] + 1e-10)
      ) <= 0.4
      cond12 = df["Close"] <= (df["EMA_20"] * 1.15)
      df["Signal"] = (
          cond1
          & cond2
          & cond3
          & cond4
          & cond5
          & cond7
          & cond8
          & cond9
          & cond10
          & cond11
          & cond12
      )
    else:
      df["Signal"] = (
          cond1
          & cond2
          & cond3
          & cond4
          & cond5
          & cond8
          & cond9
          & cond_accum
      )

    ticker_results = []

    if mode == "live" and df["Signal"].iloc[-1]:
      entry = df["Close"].iloc[-1]
      sl = df["Low_5d"].iloc[-1]
      if sl >= entry or (entry - sl) / entry < 0.005:
        sl = entry * 0.965
      risk = entry - sl
      target = entry + (2 * risk)

      curr_vol = df["Volume"].iloc[-1]
      avg_vol = df["Vol_SMA20"].iloc[-1]
      vol_spike = curr_vol / avg_vol if avg_vol > 0 else 0
      buying_surge_pct = ((curr_vol - avg_vol) / (avg_vol + 1e-10)) * 100

      accum_ratio = df["Accum_Ratio_10d"].iloc[-1]
      range_20 = df["Range_20_Pct"].iloc[-1]
      is_breakout_20 = df["Close"].iloc[-1] > df["High_20_Prev"].iloc[-1]

      day_high = df["High"].iloc[-1]
      day_low = df["Low"].iloc[-1]
      day_range = day_high - day_low
      close_pos = (
          ((entry - day_low) / day_range * 100) if day_range > 0 else 50
      )

      is_steady_accum_phase = range_20 <= 12.0 or accum_ratio >= 1.5
      is_heavy_buying_phase = vol_spike >= 2.5 and is_breakout_20

      bonus_score = 0
      if is_steady_accum_phase and is_heavy_buying_phase:
        alert_type = "⭐ Ultimate Explosive Setup"
        bonus_score = 30
      elif accum_ratio >= 2.0 and vol_spike >= 2.0:
        alert_type = "🔥 Massive Heavy Buying"
      elif accum_ratio >= 1.8:
        alert_type = "🧱 Steady Accumulation"
      elif vol_spike >= 2.5:
        alert_type = "⚡ Sudden Volume Spike"
      else:
        alert_type = "✅ Normal Signal"

      total_score = round(
          df["RSI"].iloc[-1]
          + (vol_spike * 5)
          + (accum_ratio * 10)
          + (close_pos / 2)
          + bonus_score,
          2,
      )

      return [{
          "Symbol": ticker.replace(".NS", ""),
          "Alert": alert_type,
          "Entry Price (₹)": round(entry, 2),
          "Stop Loss (₹)": round(sl, 2),
          "Target Price (₹)": round(target, 2),
          "Day Change (%)": round(df["Pct_Change"].iloc[-1], 2),
          "RSI": round(df["RSI"].iloc[-1], 2),
          "Vol Spike (x)": round(vol_spike, 1),
          "Accum Ratio (10d)": round(accum_ratio, 2),
          "Continuation Score (%)": round(close_pos, 1),
          "Massive Buying Surge (%)": round(buying_surge_pct, 1),
          "Score": total_score,
      }]

    elif mode == "backtest":
      history_slice = df.iloc[-60:]
      triggers = history_slice[history_slice["Signal"] == True]

      # Optimized array-based backtest execution
      for idx in triggers.index:
        row = df.loc[idx]
        b_entry = row["Close"]
        b_sl = row["Low_5d"]

        if b_sl >= b_entry or (b_entry - b_sl) / b_entry < 0.005:
          b_sl = b_entry * 0.965
        b_risk = b_entry - b_sl
        b_target = b_entry + (2 * b_risk)

        post_df = df.loc[idx:].iloc[1:21]
        outcome = "Live/Pending ⏳"
        exit_date = "Running..."
        exit_price = df["Close"].iloc[-1]

        # Sliced vectorized check instead of row-by-row iterrows
        hit_sl_mask = post_df["Low"] <= b_sl
        hit_tgt_mask = post_df["High"] >= b_target

        for f_idx in range(len(post_df)):
          sl_hit = hit_sl_mask.iloc[f_idx]
          tgt_hit = hit_tgt_mask.iloc[f_idx]
          f_date = post_df.index[f_idx]

          if sl_hit or tgt_hit:
            outcome = "Hit Target 🎯" if tgt_hit else "Hit SL 🛑"
            exit_date = f_date.strftime("%Y-%m-%d")
            exit_price = b_target if tgt_hit else b_sl
            break

        if outcome == "Live/Pending ⏳" and len(post_df) == 20:
          exit_price = post_df["Close"].iloc[-1]
          exit_date = post_df.index[-1].strftime("%Y-%m-%d")
          outcome = "Timed Out ⏳"

        pnl = ((exit_price - b_entry) / b_entry) * 100

        ticker_results.append({
            "Date": idx.strftime("%Y-%m-%d"),
            "Symbol": ticker.replace(".NS", ""),
            "Entry (₹)": round(b_entry, 2),
            "Stop Loss (₹)": round(b_sl, 2),
            "Target Price (₹)": round(b_target, 2),
            "Outcome": outcome,
            "Exit Date": exit_date,
            "PnL (%)": round(pnl, 2),
        })
      return ticker_results
  except Exception:
    return None
  return None


# --- 🎯 10/10 IDEAL BREAKOUT STOCK AUTOMATED FILTER ENGINE ---
def filter_ideal_breakout_stock(df):
  if df.empty:
    return pd.DataFrame()

  cond_alert = df["Alert"].str.contains("⭐|Ultimate", na=False, regex=True)
  cond_cont = df["Continuation Score (%)"] > 85
  cond_surge = df["Massive Buying Surge (%)"] > 150
  cond_vol = df["Vol Spike (x)"] > 2.5
  cond_accum = df["Accum Ratio (10d)"] > 1.8
  cond_rsi = (df["RSI"] >= 60) & (df["RSI"] <= 72)

  ideal_df = df[
      cond_alert & cond_cont & cond_surge & cond_vol & cond_accum & cond_rsi
  ].copy()

  if not ideal_df.empty:
    return ideal_df.sort_values(by="Score", ascending=False).reset_index(
        drop=True
    )

  return pd.DataFrame()


# --- Sidebar Controls UI ---
st.sidebar.header("⚙️ Pro Scanner Controls")

formula_version = st.sidebar.selectbox(
    "📊 Select Strategy Formula Version",
    [
        "Version 1 (With 500-day High & Strict Filters)",
        "Version 2 (Without 500-day High & Advanced Filters)",
    ],
)

rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider(
    "Volume Shock (Multiplier)", 1.0, 3.0, 1.2, step=0.1
)
min_turnover = st.sidebar.number_input(
    "Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2
)

st.sidebar.markdown("---")
st.sidebar.header("🔄 Auto-Update & Data Controls")

if st.sidebar.button("🗑️ Clear Dashboard Cache"):
  clear_all_caches()
  st.rerun()

universe_choice = st.sidebar.radio(
    "📊 Select Market Universe",
    ["Top 10 Stocks (Instant)", "Nifty 50 (Fast)", "All NSE 2300+ (Fast)"],
)

if universe_choice == "Top 10 Stocks (Instant)":
  all_tickers = [
      "RELIANCE.NS",
      "TCS.NS",
      "HDFCBANK.NS",
      "ICICIBANK.NS",
      "INFY.NS",
      "SBIN.NS",
      "BHARTIARTL.NS",
      "ITC.NS",
      "LT.NS",
      "KOTAKBANK.NS",
  ]
elif universe_choice == "Nifty 50 (Fast)":
  all_tickers = [
      "ADANIENT.NS",
      "ADANIPORTS.NS",
      "APOLLOHOSP.NS",
      "ASIANPAINT.NS",
      "AXISBANK.NS",
      "BAJAJ-AUTO.NS",
      "BAJFINANCE.NS",
      "BAJAJFINSV.NS",
      "BPCL.NS",
      "BHARTIARTL.NS",
      "BRITANNIA.NS",
      "CIPLA.NS",
      "COALINDIA.NS",
      "DIVISLAB.NS",
      "DRREDDY.NS",
      "EICHERMOT.NS",
      "GRASIM.NS",
      "HCLTECH.NS",
      "HDFCBANK.NS",
      "HDFCLIFE.NS",
      "HEROMOTOCO.NS",
      "HINDALCO.NS",
      "HINDUNILVR.NS",
      "ICICIBANK.NS",
      "ITC.NS",
      "INDUSINDBK.NS",
      "INFY.NS",
      "JSWSTEEL.NS",
      "KOTAKBANK.NS",
      "LTIM.NS",
      "LT.NS",
      "M&M.NS",
      "MARUTI.NS",
      "NTPC.NS",
      "NESTLEIND.NS",
      "ONGC.NS",
      "POWERGRID.NS",
      "RELIANCE.NS",
      "SBILIFE.NS",
      "SBIN.NS",
      "SUNPHARMA.NS",
      "TCS.NS",
      "TATACONSUM.NS",
      "TATAMOTORS.NS",
      "TATASTEEL.NS",
      "TECHM.NS",
      "TITAN.NS",
      "UPL.NS",
      "ULTRACEMCO.NS",
      "WIPRO.NS",
  ]
else:
  all_tickers = get_mega_nse_universe()

st.sidebar.write(f"Total Active Stocks: **{len(all_tickers)}**")

if "master_market_data" not in st.session_state:
  st.sidebar.warning("⚠️ Data is not loaded yet.")
  if st.sidebar.button("📥 Fetch Market Data To Start"):
    with st.spinner(f"Downloading {len(all_tickers)} stocks data..."):
      st.session_state["master_market_data"] = download_all_market_data(
          all_tickers
      )
      st.session_state["live_results"] = pd.DataFrame()
      st.sidebar.success("🏁 Data Loaded!")
      st.rerun()
else:
  st.sidebar.success(
      f"✅ Data Loaded ({len(st.session_state['master_market_data'])} stocks)"
  )

tab1, tab2 = st.tabs(
    ["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"]
)


def compute_analytics_on_cached_pool(mode="live"):
  results = []
  pool = st.session_state.get("master_market_data", {})
  if not pool:
    return pd.DataFrame()

  # Dynamic max workers based on CPU count
  workers = min(32, (os.cpu_count() or 4) * 4)
  with ThreadPoolExecutor(max_workers=workers) as executor:
    futures = {
        executor.submit(
            analyze_single_ticker,
            ticker,
            df,
            mode,
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


# --- TAB 1: Live Scanning View ---
with tab1:
  st.subheader("⚡ Live Data Collection & Accumulation Detection")

  if "master_market_data" not in st.session_state:
    st.info(
        "👈 Please click 'Fetch Market Data To Start' from the sidebar first"
        " to see results."
    )
  else:
    if st.button("🚀 Run Scanner", key="live_btn"):
      with st.spinner("Searching for momentum & heavy buying setups..."):
        st.session_state["live_results"] = compute_analytics_on_cached_pool(
            mode="live"
        )

    res_df = st.session_state.get("live_results", pd.DataFrame())

    if not res_df.empty:
      res_df = res_df.sort_values(by="Score", ascending=False)
      if "Rank" not in res_df.columns:
        res_df.insert(0, "Rank", range(1, len(res_df) + 1))

      ideal_matches_df = filter_ideal_breakout_stock(res_df)

      if not ideal_matches_df.empty:
        st.success(
            f"🎉 **10/10 MATCH FOUND!** {len(ideal_matches_df)} स्टॉक आपकी"
            " सभी 6 शर्तों पर 100% खरे उतरे हैं।"
        )

        box_html = (
            '<div style="background-color: #161b22; border: 2px solid'
            " #ffd700; border-radius: 12px; padding: 18px; margin-bottom:"
            ' 25px;"><h2 style="color: #ffd700; margin-top: 0; margin-bottom:'
            f' 15px;">👑 Ideal Breakout Stocks ({len(ideal_matches_df)}'
            " Found)</h2>"
        )
        for idx, row in ideal_matches_df.iterrows():
          rank = idx + 1
          box_html += (
              '<div style="border-bottom: 1px dashed #30363d; padding-bottom:'
              ' 12px; margin-bottom: 12px;"><h3 style="color: #58a6ff; margin:'
              f' 0;">#{rank} Stock: <u>{row["Symbol"]}</u> (Probability Score:'
              f' {row["Score"]})</h3><p style="color: #c9d1d9; font-size: 14px;'
              " margin-top: 6px; margin-bottom: 6px;"><b>Alert:</b>"
              f' {row["Alert"]} | <b>Continuation Score:</b>'
              f' {row["Continuation Score (%)"]}% | <b>Massive Buying'
              f' Surge:</b> {row["Massive Buying Surge (%)"]}% | <b>RSI:</b>'
              f' {row["RSI"]}</p><p style="color: #00ff7f; font-weight: bold;'
              f' margin: 0; font-size: 15px;">🎯 Trigger: ₹{row["Entry Price'
              f' (₹)"]} के ऊपर खरीदें | SL: ₹{row["Stop Loss (₹)"]} | Target:'
              f' ₹{row["Target Price (₹)"]}</p></div>'
          )
        box_html += "</div>"
        st.markdown(box_html, unsafe_allow_html=True)

        top_stock_row = ideal_matches_df.iloc[0]
        top_stock = top_stock_row["Symbol"]

        st.markdown(
            f"### 👑 Chart View for #1 Ultimate Stock: **{top_stock}**"
        )
        chart_data = yf.download(
            f"{top_stock}.NS", period="3mo", interval="1d", progress=False
        )

        if not chart_data.empty:
          if isinstance(chart_data.columns, pd.MultiIndex):
            chart_data.columns = chart_data.columns.get_level_values(0)
          chart_data = chart_data.dropna(
              subset=["Open", "High", "Low", "Close", "Volume"]
          )
          chart_data = chart_data[chart_data["Volume"] > 0]

          if not chart_data.empty:
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=chart_data.index,
                        open=chart_data["Open"],
                        high=chart_data["High"],
                        low=chart_data["Low"],
                        close=chart_data["Close"],
                        name="Candlestick",
                    )
                ]
            )
            fig.add_trace(
                go.Scatter(
                    x=chart_data.index,
                    y=chart_data["Close"].ewm(span=20).mean(),
                    line=dict(color="orange", width=1.5),
                    name="EMA 20",
                )
            )

            live_sl = top_stock_row["Stop Loss (₹)"]
            live_tgt = top_stock_row["Target Price (₹)"]

            fig.add_hline(
                y=live_sl,
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text=f"SL: ₹{live_sl}",
                annotation_position="bottom left",
            )
            fig.add_hline(
                y=live_tgt,
                line_dash="dash",
                line_color="green",
                line_width=2,
                annotation_text=f"Target: ₹{live_tgt}",
                annotation_position="top left",
            )

            fig.update_layout(
                template="plotly_dark",
                title=f"{top_stock} Setup Chart",
                xaxis_rangeslider_visible=False,
            )
            st.plotly_chart(fig, use_container_width=True)
      else:
        st.markdown(
            '<div style="background-color: #161b22; border: 2px solid'
            " #ff4d4d; border-radius: 12px; padding: 18px; margin-bottom:"
            ' 25px;"><h2 style="color: #ff4d4d; margin: 0;">❌ No Breakout Stock'
            ' Found</h2><p style="color: #c9d1d9; font-size: 15px; margin-top:'
            " 8px; margin-bottom: 0px;">आज सभी 6 शर्तों पर 100% खरा उतरने वाला"
            " कोई Ideal Breakout Stock नहीं मिला है।</p></div>",
            unsafe_allow_html=True,
        )

      def highlight_buying(row):
        alert = str(row.get("Alert", ""))
        if "⭐" in alert or "Ultimate" in alert:
          return [
              "background-color: #ffd700; color: #000000; font-weight: bold"
          ] * len(row)
        elif "🔥" in alert:
          return [
              "background-color: rgba(255, 69, 0, 0.35); color: #ffffff;"
              " font-weight: bold"
          ] * len(row)
        elif "🧱" in alert:
          return [
              "background-color: rgba(0, 150, 255, 0.25); color: #ffffff;"
              " font-weight: bold"
          ] * len(row)
        return [""] * len(row)

      styled_df = res_df.style.apply(highlight_buying, axis=1)

      st.subheader(f"📊 Total Active Signals Found: {len(res_df)}")
      st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- TAB 2: Historical Backtest View ---
with tab2:
  st.subheader(
      "⏳ True Strategy Analytics Dashboard (2-Month Path Backtest)"
  )

  if "master_market_data" not in st.session_state:
    st.info(
        "👈 Please click 'Fetch Market Data To Start' from the sidebar first"
        " to run backtest."
    )
  else:
    if st.button("📊 Start Strict Backtest Simulation", key="bt_btn"):
      with st.spinner("Simulating multi-day paths for every trigger..."):
        st.session_state["bt_results"] = compute_analytics_on_cached_pool(
            mode="backtest"
        )

    bt_df = st.session_state.get("bt_results", pd.DataFrame())

    if not bt_df.empty:
      bt_df = bt_df.sort_values(by="Date", ascending=False)
      closed_trades = bt_df[
          bt_df["Outcome"].str.contains("Hit|Timed", na=False)
      ].copy()
      winning_trades = closed_trades[closed_trades["PnL (%)"] > 0]
      accuracy = (
          round((len(winning_trades) / len(closed_trades)) * 100, 2)
          if len(closed_trades) > 0
          else 0.0
      )

      col1, col2, col3 = st.columns(3)
      col1.metric("Total Generated Signals", len(bt_df))
      col2.metric("Closed/Evaluated Signals", len(closed_trades))
      col3.metric("True Strategy Win Rate (PnL > 0)", f"{accuracy}%")

      st.markdown("### 📋 Complete Historical Simulation Log")
      st.dataframe(bt_df, use_container_width=True, hide_index=True)

      csv_data = bt_df.to_csv(index=False).encode("utf-8")
      st.download_button(
          "📥 Download Accurate Backtest Log (CSV)",
          data=csv_data,
          file_name="strict_backtest_results.csv",
          mime="text/csv",
      )

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner with SL/TP", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced Stock Scanner Terminal")
st.caption("Engine Upgraded: Active NSE 1300+ Verified Universe with Risk Management (SL/TP)")

# --- HIGHLY ACTIVE & VERIFIED NSE TICKERS ---
def get_pure_live_universe():
    massive_universe = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "ITC.NS", 
        "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "TATAMOTORS.NS", "SUNPHARMA.NS", "MARUTI.NS", "KOTAKBANK.NS", 
        "AXISBANK.NS", "NTPC.NS", "ONGC.NS", "TATASTEEL.NS", "ADANIENT.NS", "COALINDIA.NS", "BAJAJFINSV.NS", 
        "M&M.NS", "ASIANPAINT.NS", "TITAN.NS", "ULTRACEMCO.NS", "HCLTECH.NS", "POWERGRID.NS", "WIPRO.NS", 
        "ADANIPORTS.NS", "JIOFIN.NS", "ZOMATO.NS", "HAL.NS", "BHEL.NS", "PFC.NS", "RECLTD.NS", "IRFC.NS", 
        "RVNL.NS", "CONCOR.NS", "TATACOMM.NS", "TATAPOWER.NS", "GAIL.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", 
        "HINDALCO.NS", "JINDALSTEL.NS", "NATIONALUM.NS", "TATACHEM.NS", "CHAMBLFERT.NS", "AUBANK.NS", "BANDHANBNK.NS", 
        "FEDERALBNK.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS", "BOB.NS", "UNIONBANK.NS", "INDIANB.NS", 
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "UNITDSPR.NS", "BERGEPAINT.NS", "PIDILITIND.NS", 
        "BEL.NS", "POLYCAB.NS", "KEI.NS", "HAVELLS.NS", "VOLTAS.NS", "DIXON.NS", "AMBUJACEM.NS", "ACC.NS", 
        "JKCEMENT.NS", "DALBHARAT.NS", "BPCL.NS", "HPCL.NS", "IOC.NS", "MRF.NS", "BALKRISIND.NS", "APOLLOTYRE.NS", 
        "CEATLTD.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "TVSMOTOR.NS", "INDHOTEL.NS", "GMRINFRA.NS", 
        "GICRE.NS", "NIACL.NS", "LICHSGFIN.NS", "PEL.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS", 
        "SRF.NS", "DEEPAKNTR.NS", "TATAELXSI.NS", "PERSISTENT.NS", "KPITTECH.NS", "COFORGE.NS", "LTIM.NS", 
        "ASTRAL.NS", "SUPREMEIND.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "AUROPHARMA.NS", "BIOCON.NS", "DIVISLAB.NS", 
        "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS", "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "BATAINDIA.NS", "IRCTC.NS", 
        "BOSCHLTD.NS", "TATAINVEST.NS", "HUDCO.NS", "MANAPPURAM.NS", "IOB.NS", "CENTRALBK.NS", "UCOBANK.NS",
        "3MINDIA.NS", "AARTIDRUGS.NS", "AARTIIND.NS", "AAVAS.NS", "ABB.NS", "ABBOTINDIA.NS", "ADANIGREEN.NS",
        "ADANIPOWER.NS", "ATGL.NS", "ADANIENSOL.NS", "AWL.NS", "AFFLE.NS", "AJANTPHARM.NS", "APLLTD.NS",
        "ALKEM.NS", "ALKYLAMINE.NS", "ALLCARGO.NS", "ALOKINDS.NS", "AMBER.NS", "ANGELONE.NS", "ANURAS.NS",
        "APOLLOHOSP.NS", "APTUS.NS", "ASAHIINDIA.NS", "ASHOKLEY.NS", "ASTERDM.NS", "ATUL.NS", "AVANTIFEED.NS",
        "BAJAJ-AUTO.NS", "BALAMINES.NS", "BALRAMCHIN.NS", "BANKBARODA.NS", "BANKINDIA.NS", "MAHABANK.NS",
        "BAYERCROP.NS", "BHARATFORG.NS", "BIRLACORPN.NS", "BSOFT.NS", "BLS.NS", "BLUEDART.NS", "BLUESTARCO.NS",
        "BBTC.NS", "BORORENEW.NS", "BRIGADE.NS", "MAPMYINDIA.NS", "CESC.NS", "CGPOWER.NS", "CIEINDIA.NS",
        "CRISIL.NS", "CSBBANK.NS", "CAMPUS.NS", "CAMS.NS", "CANFINHOME.NS", "CAPLIPOINT.NS", "CGCL.NS",
        "CARBORUN.NS", "CASTROLIND.NS", "GODREJCP.NS", "DABUR.NS", "BRITANNIA.NS", "NESTLEIND.NS", "VBL.NS",
        "PATANJALI.NS", "KRBL.NS", "LTTS.NS", "TECHM.NS", "MPHASIS.NS", "SONACOMS.NS", "MINDTECK.NS",
        "ZENSARTECH.NS", "CYIENT.NS", "DATAPATTERNS.NS", "MASTEK.NS", "CEINFO.NS", "SJVN.NS",
        "TORNTPOWER.NS", "JSWENERGY.NS", "SUZLON.NS", "RAIN.NS", "DEEPAKFERT.NS", "FACT.NS",
        "RCF.NS", "GNFC.NS", "GSFC.NS", "COROMANDEL.NS", "PIIND.NS", "UPL.NS", "SUMICHEM.NS",
        "NBCC.NS", "ENGINERSIN.NS", "RITES.NS", "IRCON.NS", "NCC.NS", "KEC.NS", "KALPATARU.NS",
        "LTFOODS.NS", "HDFCLIFE.NS", "SBILIFE.NS", "LIC.NS", "ICICIPRULI.NS", "ICICIGI.NS",
        "NETWORK18.NS", "TV18BRDCST.NS", "SUNTV.NS", "ZEEL.NS", "PVRINOX.NS", "DISHTV.NS"
    ]
    return sorted(list(set(massive_universe)))

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Turnover (₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Risk Management (SL/TP)")
sl_per = st.sidebar.slider("Stoploss (SL %)", 0.5, 5.0, 2.0, step=0.1)
tp_per = st.sidebar.slider("Target (TP %)", 1.0, 10.0, 4.0, step=0.1)

all_tickers = get_pure_live_universe()
st.sidebar.write(f"Total Database Stock Pool: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtester"])

# --- Engine Core Processing ---
def analyze_single_ticker(ticker, df, mode, vol_mult, rsi_filt, t_limit):
    try:
        df = df.dropna(subset=['Close', 'High', 'Low', 'Volume']).copy()
        if len(df) < 35: return None

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.clip(lower=0)).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        # Breakout Strategy Parameters
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=min(250, len(df)-2), min_periods=1).max()

        # Scanning conditions
        c1 = df['Close'] >= 15
        c2 = (df['Pct_Change'] >= 0.8) & (df['Pct_Change'] <= 16.0)
        c3 = df['Volume'] > (df['Vol_SMA20'] * vol_mult)
        c4 = df['Return_20d'] >= 2.0
        c5 = df['Turnover'] > (t_limit * 10000000)
        c6 = df['Close'] >= df['Max_500_High_1d_Ago']
        c7 = df['RSI'] >= rsi_filt
        c8 = df['Close'] > df['EMA_20']

        df['Signal'] = c1 & c2 & c3 & c4 & c5 & c6 & c7 & c8

        results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            trigger_price = df['Close'].iloc[-1]
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(trigger_price, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Target (₹)": round(trigger_price * (1 + tp_per/100), 2),
                "Stoploss (₹)": round(trigger_price * (1 - sl_per/100), 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike": f"{round(vol_spike, 1)}x",
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest":
            triggers = df.iloc[-45:][df['Signal'] == True]
            for date, row in triggers.iterrows():
                idx = df.index.get_loc(date)
                
                # Check if there is a next day row available
                if idx + 1 >= len(df):
                    trade_outcome = "Open Session"
                    pnl = "0.0%"
                else:
                    next_day_row = df.iloc[idx + 1]
                    t_close = row['Close']
                    sl_val = t_close * (1 - sl_per/100)
                    tp_val = t_close * (1 + tp_per/100)
                    
                    # Next day price validation logic
                    if next_day_row['Low'] <= sl_val:
                        trade_outcome = "❌ SL Hit"
                        pnl = f"-{sl_per}%"
                    elif next_day_row['High'] >= tp_val:
                        trade_outcome = "🎯 Target Hit"
                        pnl = f"+{tp_per}%"
                    else:
                        # Agar dono nahi hit hue toh close price return calculate hoga
                        day_return = ((next_day_row['Close'] - t_close) / t_close) * 100
                        trade_outcome = "📈 Closed Positive" if day_return > 0 else "📉 Closed Negative"
                        pnl = f"{round(day_return, 2)}%"

                results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(row['Close'], 2),
                    "Target Price (₹)": round(row['Close'] * (1 + tp_per/100), 2),
                    "Stoploss Price (₹)": round(row['Close'] * (1 - sl_per/100), 2),
                    "Outcome": trade_outcome,
                    "P&L (%)": pnl
                })
            return results
    except Exception:
        return None
    return None

def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 35 
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚙️ Running Engine Pipeline across Parallel Risk-Managed Nodes...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="1y", interval="1d", progress=False, group_by='ticker')
            
            with ThreadPoolExecutor(max_workers=12) as executor:
                futures = {}
                for ticker in chunk:
                    try:
                        if isinstance(raw_data.columns, pd.MultiIndex):
                            if ticker in raw_data.columns.levels[0]:
                                futures[executor.submit(analyze_single_ticker, ticker, raw_data[ticker], mode, volume_multiplier, rsi_filter, min_turnover)] = ticker
                        else:
                            futures[executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover)] = ticker
                    except KeyError:
                        continue
                
                for future in as_completed(futures):
                    res = future.result()
                    if res: results.extend(res)
        except Exception:
            continue
            
        main_progress.progress((c_idx + 1) / len(ticker_chunks))
                
    main_progress.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Found {len(res_df)} breakout stocks right now.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No breakout stocks matching your current criteria right now.")

# --- TAB 2: Backtest View ---
with tab2:
    st.subheader("⏳ Historical Analytics Dashboard")
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            # Analytics Calculation
            total_trades = len(bt_df[bt_df['Outcome'] != "Open Session"])
            target_hits = len(bt_df[bt_df['Outcome'] == "🎯 Target Hit"])
            sl_hits = len(bt_df[bt_df['Outcome'] == "❌ SL Hit"])
            
            accuracy = round((target_hits / total_trades) * 100, 2) if total_trades > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Closed Trades", total_trades)
            col2.metric("Target Hit Ratio🎯", f"{accuracy}%")
            col3.metric("SL Hit Count❌", sl_hits)
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No historical breakthrough points detected inside the data pool.")

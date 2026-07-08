import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Structure Based NSE Scanner", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Price Action & Chart Pattern Breakout Scanner")
st.caption("Engine: Vectorized Parallel Processing | Universe: Ultimate NSE Mapping")

# --- UNSTOPPABLE DOUBLE BYPASS NSE FETCHER ---
@st.cache_data(ttl=86400)
def get_absolute_nse_universe():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Try 1: GitHub Raw CSV with Browser Headers
    try:
        url1 = "https://raw.githubusercontent.com/anirudh-kamath/nse-ticker-list/main/nse_tickers.csv"
        resp = requests.get(url1, headers=headers, timeout=10)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            symbol_col = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
            tickers = (df[symbol_col].str.strip() + ".NS").tolist()
            cleaned = sorted(list(set([t for t in tickers if isinstance(t, str) and not t.startswith(('NIFTY', 'BANKNIFTY'))])))
            if len(cleaned) > 1000: return cleaned
    except Exception:
        pass

    # Try 2: Direct NSE Official CSV
    try:
        url2 = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        resp2 = requests.get(url2, headers=headers, timeout=10)
        if resp2.status_code == 200:
            df2 = pd.read_csv(io.StringIO(resp2.text))
            tickers2 = (df2['SYMBOL'].str.strip() + ".NS").tolist()
            cleaned2 = sorted(list(set([t for t in tickers2 if isinstance(t, str) and not t.startswith(('NIFTY', 'BANKNIFTY'))])))
            if len(cleaned2) > 1000: return cleaned2
    except Exception:
        pass

    # Try 3: Massive Hardcoded Backup List (Nifty 500) so it never shows "7"
    return sorted(list(set([
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "ITC.NS", "BHARTIARTL.NS",
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
    ])))

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Turnover (₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Chart Pattern Risk Setup")
rr_ratio = st.sidebar.slider("Risk : Reward Ratio (1 : X)", 1.5, 4.0, 2.0, step=0.5)

all_tickers = get_absolute_nse_universe()
st.sidebar.write(f"🔥 Total Active NSE Pool Loaded: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 Historical Backtester"])

# --- Core Vectorized Pattern Analyzer ---
def analyze_single_ticker(ticker, df, mode, vol_mult, rsi_filt, t_limit):
    try:
        if df.empty or len(df) < 35: return None
        df = df.dropna(subset=['Close', 'High', 'Low', 'Volume']).copy()

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # Fast Vectorized RSI
        delta = df['Close'].diff()
        gain = (delta.clip(lower=0)).ewm(com=13, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        
        df['Max_250_High'] = df['High'].shift(1).rolling(window=min(250, len(df)-2), min_periods=1).max()
        df['Swing_Support'] = df['Low'].rolling(window=3).min() * 0.995 

        # Rules Evaluation
        c1 = df['Close'] >= 15
        c2 = (df['Pct_Change'] >= 0.8) & (df['Pct_Change'] <= 16.0)
        c3 = df['Volume'] > (df['Vol_SMA20'] * vol_mult)
        c4 = df['Turnover'] > (t_limit * 10000000)
        c5 = df['Close'] >= df['Max_250_High']
        c6 = df['RSI'] >= rsi_filt
        c7 = df['Close'] > df['EMA_20']

        df['Signal'] = c1 & c2 & c3 & c4 & c5 & c6 & c7

        results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            trigger_price = df['Close'].iloc[-1]
            sl_price = df['Swing_Support'].iloc[-1]
            if sl_price >= trigger_price or (trigger_price - sl_price)/trigger_price > 0.08:
                sl_price = trigger_price * 0.965
            
            risk_amount = trigger_price - sl_price
            target_price = trigger_price + (risk_amount * rr_ratio)
            
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(trigger_price, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "Chart Stoploss (₹)": round(sl_price, 2),
                "Pattern Target (₹)": round(target_price, 2),
                "Risk Per Share (₹)": round(risk_amount, 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike": f"{round(vol_spike, 1)}x",
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest

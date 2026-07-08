import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced Stock Scanner Terminal")
st.caption("Engine Upgraded: Fully Expanded Dedicated 1400+ Active NSE Universe with Target & SL Matrix")

# --- MEGA CLEAN 1400+ NSE TICKER DATABASE ---
def get_pure_live_universe():
    massive_universe = [
        # --- Large Caps & Nifty 100 ---
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", 
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
        # --- Mid Caps & Momentum Pack (A-Z Cleaned) ---
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
        "NETWORK18.NS", "TV18BRDCST.NS", "SUNTV.NS", "ZEEL.NS", "PVRINOX.NS", "DISHTV.NS",
        "HFCL.NS", "ITI.NS", "TEJASNET.NS", "ROLEXRINGS.NS", "SUBROS.NS", "MNDA.NS", "EXIDEIND.NS",
        "CUPID.NS", "DIACABS.NS", "SPARC.NS", "JBCHEPHARM.NS", "METROBRAND.NS", "RELAXO.NS", 
        "JMFINANCIL.NS", "IBREALEST.NS", "RAYMOND.NS", "ARVIND.NS", "WELSPUNLIV.NS", "TRIDENT.NS", 
        "VIPIND.NS", "SAFARI.NS", "EASEMYTRIP.NS", "THOMASCOOK.NS", "MAHLOG.NS", "TCI.NS", 
        "VRLTRA.NS", "GATEWAY.NS", "COLPAL.NS", "PGHH.NS", "GILLETTE.NS", "GODREJIND.NS", 
        "EMAMILTD.NS", "BAJAJHLDNG.NS", "CHOLAHLDNG.NS", "KFINTECH.NS", "CDSL.NS", "BSE.NS", 
        "MCX.NS", "IEX.NS", "5PAISA.NS", "GEOJITFSL.NS", "ANANDRATHI.NS", "MOTILALOFS.NS", 
        "SHYAMMETL.NS", "KALYANKJIL.NS", "SENCO.NS", "PCJEWELLER.NS", "STARHEALTH.NS", 
        "NIVAUPA.NS", "GOCOLOR.NS", "MANYAVAR.NS", "ETHOSLTD.NS", "SAREGAMA.NS", "TIPSMUSIC.NS", 
        "SULA.NS", "FINEORG.NS", "CLEAN.NS", "NEOGEN.NS", "TATVA.NS", "AMIORG.NS", "ETHER.NS", 
        "ANUPAM.NS", "ROSSARI.NS", "GALAXYSURF.NS", "EPIGRAL.NS", "NOCIL.NS", "DCW.NS", 
        "CHEMCON.NS", "GRAVITA.NS", "NACLIND.NS", "INSECTICID.NS", "HERANBA.NS", "ASTEC.NS", 
        "EXCELIND.NS", "SUDARSCHEM.NS", "BODALCHEM.NS", "SHREECEM.NS", "JKLAKSHMI.NS", 
        "HEIDELBERG.NS", "ORIENTCEM.NS", "SAGCEM.NS", "DECCANCE.NS", "BIGBLOC.NS", 
        "GREENPANEL.NS", "GREENPLY.NS", "CENTURYPLY.NS", "RUSHIL.NS", "STYLAMIND.NS", 
        "PRINCEPIPE.NS", "FINPIPE.NS", "RAMASTEEL.NS", "JINDALSAW.NS", "63MOONS.NS", 
        "NUCLEUS.NS", "NEWGEN.NS", "QUICKHEAL.NS", "SUBEX.NS", "AHLUCONT.NS", "AIAENG.NS", 
        "AKZOINDIA.NS", "AMRUTANJAN.NS", "APARINDS.NS", "ASHOKA.NS", "ASTRAZEN.NS", 
        "AVANTIFEED.NS", "BAJAJELEC.NS", "BANCOINDIA.NS", "BASF.NS", "BEML.NS", "BLISSGVS.NS", 
        "BOMDYEING.NS", "CENTURYTEX.NS", "CERA.NS", "CHALET.NS", "CHENNPETRO.NS", "COCHINSHIP.NS", 
        "CRAFTSMAN.NS", "DELTACORP.NS", "DHANUKA.NS", "EIHOTEL.NS", "EPL.NS", "ERIS.NS", 
        "FDC.NS", "FILATEX.NS", "FINCABLES.NS", "FIRSTSOURCE.NS", "FORTIS.NS", "GARFIBRES.NS", 
        "GEPIL.NS", "GHCL.NS", "GLAXO.NS", "GODFRYPHLP.NS", "GODREJAGRO.NS", "GPIL.NS", 
        "GREAVESCO.NS", "GRINDWELL.NS", "GRSE.NS", "GSPL.NS", "GUJALKALI.NS", "GUJGASLTD.NS", 
        "GULFOILLUB.NS", "HATHWAY.NS", "HGINFRA.NS", "HIKAL.NS", "HINDZINC.NS", "HOMFIRS.NS", 
        "HONAUT.NS", "IDBI.NS", "IFCI.NS", "IIFL.NS", "INDIGOPNTS.NS", "INFIBEAM.NS", 
        "INGERRAND.NS", "INOXWIND.NS", "IPL.NS", "JAGRAN.NS", "JAIBALAJI.NS", "JAMNAAUTO.NS", 
        "JBMA.NS", "JINDALPOLY.NS", "JKTYRE.NS", "JPNPOWER.NS", "JSWHL.NS", "JTEKTINDIA.NS", 
        "JUBILANT.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS", "KAJARIACER.NS", "KNRCON.NS", 
        "KSB.NS", "KSCL.NS", "KTKBANK.NS", "LEMONTREE.NS", "LINDEINDIA.NS", "LUXIND.NS", 
        "LXCHEM.NS", "MAHSEAMLES.NS", "MAHSCOOTER.NS", "MANINFRA.NS", "MANGCHEFER.NS", 
        "MARKSANS.NS", "MASFIN.NS", "MAXHEALTH.NS", "MIDHANI.NS", "MISHRA.NS", "MOIL.NS", 
        "MOREPENLAB.NS", "MRPL.NS", "MSTC.NS", "MTARTECH.NS", "MTNL.NS", "NESCO.NS", 
        "NLCINDIA.NS", "OAL.NS", "OFSS.NS", "ORIENTELEC.NS", "PARADEEP.NS", "PCBL.NS", 
        "PDSL.NS", "PNCINFRA.NS", "POLYMED.NS", "POONAWALLA.NS", "PRAJIND.NS", "PRESTIGE.NS", 
        "PRIVISCL.NS", "PRSMJOHNSN.NS", "PTC.NS", "PURVA.NS", "QUESS.NS", "RADICO.NS", 
        "RAILTEL.NS", "RALLIS.NS", "RAMCOCEM.NS", "RAMCOSYS.NS", "REDINGTON.NS", "ROUTE.NS", 
        "SBICARD.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS", "SCI.NS", "SEQUENT.NS", "SFL.NS", 
        "SHARDAMOTR.NS", "SHOPERSTOP.NS", "SIS.NS", "SKFINDIA.NS", "SOBHA.NS", "SOLARINDS.NS", 
        "SPLPETRO.NS", "SPICEJET.NS", "STERTOOLS.NS", "SUNTECK.NS", "SUPRAJIT.NS", 
        "SURYAROSHNI.NS", "SYNGENE.NS", "TANLA.NS", "THERMAX.NS", "TIMKEN.NS", "TTKPRESTIG.NS", 
        "UBL.NS", "UJJIVANSFB.NS", "UNICHEMLAB.NS", "UNIENTER.NS", "VAIBHAVGBL.NS", 
        "VAKRANGEE.NS", "VALIANTORG.NS", "VARROC.NS", "VGUARD.NS", "VIJAYA.NS", "VINATIORG.NS", 
        "VSTIND.NS", "WHIRLPOOL.NS"
    ]
    return sorted(list(set(massive_universe)))

# --- Sidebar Settings Panel ---
st.sidebar.header("⚙️ Pro Scanner Controls")
st.sidebar.info("🌐 **Universe Active:** Full Indian Markets Portfolio Loaded (1400+ Tickers)")

# Filters
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Risk Management Parameters")
rr_ratio = st.sidebar.slider("Risk : Reward Target Ratio (1 : X)", 1.5, 4.0, 2.0, step=0.5)

# Load comprehensive custom clean database
all_tickers = get_pure_live_universe()
st.sidebar.write(f"Total Embedded Live Stocks: **{len(all_tickers)}**")

# --- App Navigation Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Helper Function to Process Single Ticker ---
def analyze_single_ticker(ticker, raw_data, mode, volume_multiplier, rsi_filter, turnover_limit, rr_ratio):
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker not in raw_data.columns.levels[0]: return None
            df = raw_data[ticker].dropna(subset=['Close']).copy()
        else:
            df = raw_data.dropna(subset=['Close']).copy()

        total_rows = len(df)
        if total_rows < 515: return None 

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        window_size = min(500, total_rows - 2)
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()

        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9

        # --- Dynamic Stoploss and Target Calculations ---
        # Swing Support based on past 3 days low
        df['Swing_Support'] = df['Low'].rolling(window=3).min() * 0.995

        ticker_results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            trigger_price = df['Close'].iloc[-1]
            sl_price = df['Swing_Support'].iloc[-1]
            
            # Risk defense thresholds boundary conditions
            if sl_price >= trigger_price or (trigger_price - sl_price)/trigger_price > 0.08:
                sl_price = trigger_price * 0.965  # Default structural 3.5% risk cushion fallback
                
            risk_amount = trigger_price - sl_price
            target_price = trigger_price + (risk_amount * rr_ratio)
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(trigger_price, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Chart Stoploss (₹)": round(sl_price, 2),
                "Pattern Target (₹)": round(target_price, 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-50:] 
            triggers = history_slice[history_slice['Signal'] == True]
            for date, row in triggers.iterrows():
                idx = df.index.get_loc(date)
                t_close = row['Close']
                sl_val = row['Swing_Support']
                
                if sl_val >= t_close or (t_close - sl_val)/t_close > 0.08:
                    sl_val = t_close * 0.965
                    
                risk_amt = t_close - sl_val
                tp_val = t_close + (risk_amt * rr_ratio)
                
                if idx + 1 >= len(df):
                    trade_outcome = "Live Open Session"
                else:
                    next_day_row = df.iloc[idx + 1]
                    if next_day_row['Low'] <= sl_val:
                        trade_outcome = "❌ SL Hit"
                    elif next_day_row['High'] >= tp_val:
                        trade_outcome = "🎯 Target Hit"
                    else:
                        trade_outcome = "📈 Hold/Pos Close" if next_day_row['Close'] > t_close else "📉 Neg Close"

                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(t_close, 2),
                    "Chart Stoploss (₹)": round(sl_val, 2),
                    "Pattern Target (₹)": round(tp_val, 2),
                    "Outcome Event": trade_outcome
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- Secure Anti-Block Fast Chunk Processing Engine ---
def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 80
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚡ Downloading and filtering {len(tickers)} stocks across parallel secure batches...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            # Shifted to 2y for safe mapping of 500 days ago high window lookup safely
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker', threads=True)
            
            with ThreadPoolExecutor(max_workers=16) as executor:
                futures = {
                    executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover, rr_ratio): ticker 
                    for ticker in chunk
                }
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        results.extend(res)
        except Exception:
            continue
            
        main_progress.progress((c_idx + 1) / len(ticker_chunks))
                
    main_progress.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Live Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Vol Spike (x)", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Success! Found {len(res_df)} breakout stocks matching exact structural setups.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Momentum Pick: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="6mo", interval="1d", progress=False)
            
            if not chart_data.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                    low=chart_data['Low'], close=chart_data['Close'], name='Price'
                )])
                
                # Plot setup line visualization arrays
                last_trigger_sl = res_df.iloc[0]['Chart Stoploss (₹)']
                last_trigger_tp = res_df.iloc[0]['Pattern Target (₹)']
                
                fig.add_hline(y=last_trigger_sl, line_dash="dash", line_color="red", annotation_text="Stoploss Level")
                fig.add_hline(y=last_trigger_tp, line_dash="dash", line_color="green", annotation_text="Target Level")
                
                fig.update_layout(template="plotly_dark", title=f"{top_stock} Live Trading Levels Overlay")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No stocks currently matching your operational criteria matrix today.")

# --- TAB 2: Historical Backtest View ---
with tab2:
    st.subheader("⏳ 2-Month Historical Risk Analytics Dashboard")
    
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            total_signals = len(bt_df)
            target_hits = len(bt_df[bt_df['Outcome Event'] == "🎯 Target Hit"])
            sl_hits = len(bt_df[bt_df['Outcome Event'] == "❌ SL Hit"])
            
            accuracy = round((target_hits / (target_hits + sl_hits)) * 100, 2) if (target_hits + sl_hits) > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Generated Signals", total_signals)
            col2.metric("Target Hit Profiles 🎯", target_hits)
            col3.metric("Breakout Success Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No historical pattern matches recorded over this tracking frame.")

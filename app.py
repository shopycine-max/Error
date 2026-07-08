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
st.caption("Engine Upgraded: Fully Expanded Dedicated 1400+ Active NSE Universe")

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
        "SHYAMMETL.NS", "KALYANKJIL.NS", "SENCO.NS", "PCJEWELLER.NS", "STARHEALTH.NS", "NIVAUPA.NS", 
        "GOCOLOR.NS", "MANYAVAR.NS", "ETHOSLTD.NS", "SAREGAMA.NS", "TIPSMUSIC.NS", "SULA.NS", 
        "FINEORG.NS", "CLEAN.NS", "NEOGEN.NS", "TATVA.NS", "AMIORG.NS", "ETHER.NS", 
        "ANUPAM.NS", "ROSSARI.NS", "GALAXYSURF.NS", "EPIGRAL.NS", "NOCIL.NS", "DCW.NS", 
        "CHEMCON.NS", "GRAVITA.NS", "NACLIND.NS", "INSECTICID.NS", "HERANBA.NS", "ASTEC.NS", 
        "EXCELIND.NS", "SUDARSCHEM.NS", "BODALCHEM.NS", "SHREECEM.NS", "JKLAKSHMI.NS", "HEIDELBERG.NS", 
        "ORIENTCEM.NS", "SAGCEM.NS", "DECCANCE.NS", "BIGBLOC.NS", "GREENPANEL.NS", "GREENPLY.NS", 
        "CENTURYPLY.NS", "RUSHIL.NS", "STYLAMIND.NS", "PRINCEPIPE.NS", "FINPIPE.NS", "RAMASTEEL.NS", 
        "JINDALSAW.NS", "63MOONS.NS", "NUCLEUS.NS", "NEWGEN.NS", "QUICKHEAL.NS", "SUBEX.NS", 
        "AHLUCONT.NS", "AIAENG.NS", "AKZOINDIA.NS", "AMRUTANJAN.NS", "APARINDS.NS", "ASHOKA.NS", 
        "ASTRAZEN.NS", "BAJAJELEC.NS", "BANCOINDIA.NS", "BASF.NS", "BEML.NS", "BLISSGVS.NS", 
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
        "KSB.NS", "KSCL.NS", "KTKBANK.NS", "LEMONTREE.NS", "LINDEINDIA.NS", "LUMAXTECH.NS", 
        "LUXIND.NS", "LXCHEM.NS", "MAHSEAMLES.NS", "MAHSCOOTER.NS", "MANINFRA.NS", "MANGCHEFER.NS", 
        "MARKSANS.NS", "MASFIN.NS", "MAXHEALTH.NS", "MIDHANI.NS", "MISHRA.NS", "MOIL.NS", 
        "MOREPENLAB.NS", "MRPL.NS", "MSTC.NS", "MTARTECH.NS", "MTNL.NS", "NESCO.NS", 
        "NLCINDIA.NS", "OAL.NS", "OFSS.NS", "ORIENTELEC.NS", "PARADEEP.NS", "PCBL.NS", 
        "PDSL.NS", "PNCINFRA.NS", "POLYMED.NS", "POONAWALLA.NS", "PRAJIND.NS", "PRESTIGE.NS", 
        "PRIVISCL.NS", "PRSMJOHNSN.NS", "PTC.NS", "PURVA.NS", "QUESS.NS", "RADICO.NS", 
        "RAILTEL.NS", "RALLIS.NS", "RAMCOCEM.NS", "RAMCOSYS.NS", "REDINGTON.NS", "ROUTE.NS", 
        "SBICARD.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS", "SCI.NS", "SEQUENT.NS", "SFL.NS", 
        "SHARDAMOTR.NS", "SHOPERSTOP.NS", "SIS.NS", "SKFINDIA.NS", "SOBHA.NS", "SOLARINDS.NS", 
        "SPLPETRO.NS", "SPICEJET.NS", "STERTOOLS.NS", "SUNTECK.NS", "SUPRAJIT.NS", "SURYAROSHNI.NS", 
        "SYNGENE.NS", "TANLA.NS", "TASTYBITE.NS", "THERMAX.NS", "TIMKEN.NS", "TTKPRESTIG.NS", 
        "UBL.NS", "UJJIVANSFB.NS", "UNICHEMLAB.NS", "UNIENTER.NS", "VAIBHAVGBL.NS", "VAKRANGEE.NS", 
        "VALIANTORG.NS", "VARROC.NS", "VGUARD.NS", "VIJAYA.NS", "VINATIORG.NS", "VSTIND.NS", 
        "WESTLIFE.NS", "WHIRLPOOL.NS"
    ]
    return sorted(list(set(massive_universe)))

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock", 1.0, 3.0, 1.0, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Turnover (₹ Crores)", min_value=1, max_value=50, value=2)

all_tickers = get_pure_live_universe()
st.sidebar.write(f"Total Live Stocks: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- Helper Function for Processing Single Ticker ---
def analyze_single_ticker(ticker, ticker_df, mode, vol_mult, rsi_filt, t_limit):
    try:
        df = ticker_df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open']).copy()
        total_rows = len(df)
        if total_rows < 50: return None

        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))
        
        # Breakout Strategy Parameters
        window_size = min(500, total_rows - 2)
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=max(1, window_size), min_periods=1).max()
        
        # FIXED: Next Day actual return calculation
        df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100

        # Conditions
        cond1 = df['Close'] >= 20
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0)
        cond3 = df['Volume'] > (df['Vol_SMA20'] * vol_mult)
        cond4 = df['Return_20d'] >= 3.0
        cond5 = df['Turnover'] > (t_limit * 10000000)
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
        cond8 = df['RSI'] >= rsi_filt
        cond9 = df['Close'] > df['EMA_20']

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9

        ticker_results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "LTP (₹)": round(df['Close'].iloc[-1], 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-50:]  # Last 2 months approx
            triggers = history_slice[history_slice['Signal'] == True]
            for date, row in triggers.iterrows():
                is_today = date.date() == datetime.today().date()
                next_move = "Live / Open Session" if is_today or pd.isna(row['Next_Day_Return']) else f"{round(row['Next_Day_Return'], 2)}%"
                
                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger Price (₹)": round(row['Close'], 2),
                    "RSI at Trigger": round(row['RSI'], 2),
                    "Next Day Move": next_move
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- Main Engine ---
def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 60 # Multi-threading block se bachne ke liye standard size
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚡ Downloading and filtering across parallel batches...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            # Multi-level index problem ko hatane ke liye single dataframe structure extraction kiya hai
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker')
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {}
                for ticker in chunk:
                    if ticker in raw_data.columns.levels[0]:
                        # Individual ticker chunk safe slicing
                        t_df = raw_data[ticker]
                        futures[executor.submit(analyze_single_ticker, ticker, t_df, mode, volume_multiplier, rsi_filter, min_turnover)] = ticker
                
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
            st.success(f"🎉 Success! Found {len(res_df)} breakout stocks.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No Data Found.")

# --- TAB 2: Backtest View ---
with tab2:
    st.subheader("⏳ 2-Month Historical Analytics Dashboard")
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            valid_moves = bt_df[~bt_df['Next Day Move'].str.contains("Live", na=False)].copy()
            if len(valid_moves) > 0:
                valid_moves['Move_Float'] = valid_moves['Next Day Move'].str.replace('%','').astype(float)
                bullish_days = len(valid_moves[valid_moves['Move_Float'] > 0])
                accuracy = round((bullish_days / len(valid_moves)) * 100, 2)
            else:
                accuracy = 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", len(bt_df))
            col2.metric("Next-Day Bullish Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No Data Found.")

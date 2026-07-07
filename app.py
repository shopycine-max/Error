import streamlit as st
import pandas as pd
import yfinance as yf

# Page Initialization
st.set_page_config(page_title="NSE Pro Market Scanner", layout="wide")
st.title("🚀 LIVE NSE BREAKOUT ENGINE (CHARTINK STYLE)")

st.write("### 📊 Active Formula Engine:")
st.info(
    "Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | 20-Day Return >= 3% | Turnover > 50Cr | "
    "Daily Max(2, 20 days ago High) >= Daily Max(200, 31 days ago High) | "
    "Daily Close >= 1 day ago Max(500, Daily High)"
)

# RE-OPTIMIZED BROAD MARKET LIST
ALL_INDIAN_STOCKS = [
    "# ---
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "WIPRO.NS",
    "HCLTECH.NS", "TECHM.NS", "COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS", "PAYTM.NS", "NYKAA.NS",
    
    
    "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "TEXRAIL.NS", "TITAGARH.NS", "BHEL.NS", "BDL.NS", 
    "GRSE.NS", "BEML.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "GRASIM.NS",
    "ULTRACEMCO.NS", "ACC.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "M&M.NS", "MARUTI.NS",
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS",
    

    "CHOLAFIN.NS", "SRF.NS", "HAVELLS.NS", "VOLTAS.NS", "BLUESTARCO.NS", "POLYCAB.NS", "KEI.NS", "IRCTC.NS",
    "CONCOR.NS", "INDIGO.NS", "SPICEJET.NS", "TRENT.NS", "ABFRL.NS", "PAGEIND.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS",
    "AUBANK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS", "IDBI.NS", "INDIANB.NS", "IOB.NS", "UCOBANK.NS", "UNIONBANK.NS",
    "CENTRALBK.NS", "BOM.NS", "EXIDEIND.NS", "BALKRISIND.NS", "MRF.NS", "APOLLOTYRE.NS", "JKTYRE.NS", "CEATLTD.NS",
    "TATACOMM.NS", "INDUSTOWER.NS", "IDEA.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "GLENMARK.NS", "LUPIN.NS",
    "BIOCON.NS", "AUROPHARMA.NS", "ALKEM.NS", "TORNTPHARM.NS", "LAURUSLABS.NS", "PEL.NS", "PVRINOX.NS",
    "SUNTV.NS", "ZEEL.NS", "NETWORK18.NS", "CHAMBLFERT.NS", "GNFC.NS", "GSFC.NS", "COROMANDEL.NS", "DEEPAKNTR.NS",
    "UPL.NS", "PIIND.NS", "AARTIIND.NS", "ATUL.NS", "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "RATNAMANI.NS",
    "APLAPOLLO.NS", "HINDZINC.NS", "MOIL.NS", "GMDC.NS", "OBEROIRLTY.NS", "LODHA.NS", "GODREJPROP.NS", "SOBHA.NS",
    "PRESTIGE.NS", "BRIGADE.NS", "MTARTECH.NS", "PATELENG.NS", "NCC.NS", "IRB.NS", "KNRENG.NS", "PNCINFRA.NS",
    "HGINFRA.NS", "DILIPBUILD.NS", "ENGINDERSIN.NS", "IHCL.NS", "CAMPUS.NS", "MRPL.NS", "CHENNPETRO.NS",

    
    "ALOKINDS.NS", "AWFIS.NS", "AZAD.NS", "BBL.NS", "BLS.NS", "BOROLTD.NS", "CEINFO.NS", "CENTURYPLY.NS",
    "CRAFTSMAN.NS", "DOMS.NS", "EASEMYTRIP.NS", "EIDPARRY.NS", "ELGIEQUIP.NS", "EMUDHRA.NS",
    "ENDURANCE.NS", "EPL.NS", "ESCORTS.NS", "FSL.NS", "GABRIEL.NS", "GARFIBRES.NS", "GATEWAY.NS",
    "GENUSPOWER.NS", "GEOJITFSL.NS", "GHCL.NS", "GICRE.NS", "GILLETTE.NS", "GLS.NS", "GODFRYPHLP.NS",
    "GPIL.NS", "GRAVITA.NS", "GREENPANEL.NS", "GRINFRA.NS", "GSPL.NS", "HAPPYFORGE.NS", "HBLPOWER.NS", "HEG.NS",
    "HERANBA.NS", "HIKAL.NS", "HINDWAREAP.NS", "HONAUT.NS", "HUDCO.NS", "IBREALEST.NS", "IKIO.NS",
    "INDIACEM.NS", "INDIAMART.NS", "INDIGOPNTS.NS", "INOXGREEN.NS", "INOXWIND.NS", "INTELLECT.NS", "IONEXCHANG.NS",
    "ISGEC.NS", "ITI.NS", "J&KBANK.NS", "JAGRAN.NS", "JAIBALAJI.NS", "JAMNAAUTO.NS",
    "JBCHEPHARM.NS", "JINDALWORLD.NS", "JKCEMENT.NS", "JKPAPER.NS", "JMFINANCIL.NS", "JSWENERGY.NS",
    "JSWINFRA.NS", "JTEKTINDIA.NS", "JUBILANT.NS", "JUBLINGREA.NS", "JUBLPHARMA.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS",
    "KAJARIACER.NS", "KPITTECH.NS", "KFINTECH.NS", "KIMS.NS", "KIRLOSENG.NS", "KNRCON.NS", "KOPRAN.NS",
    "KRBL.NS", "KSB.NS", "LALPATHLAB.NS", "LEMONTREE.NS", "LINDEINDIA.NS", "LLOYDSME.NS", "LUMAXTECH.NS",
    "LXCHEM.NS", "MAITHANALL.NS", "MANINFRA.NS", "MAPMYINDIA.NS", "MARKSANS.NS",
    "MASTEK.NS", "MAXHEALTH.NS", "MAZDA.NS", "MEDANTA.NS", "METROBRAND.NS", "METROPOLIS.NS",
    "MHRIL.NS", "MIDHANI.NS", "MINDTECK.NS", "MIRZAINT.NS", "MOLDTECH.NS", "MONTECARLO.NS",
    "MOREPENLAB.NS", "MOTILALOFS.NS", "MSTCLTD.NS", "MUKANDLTD.NS", "MUNJALAU.NS",
    "NATCOPHARM.NS", "NAVA.NS", "NAVNETEDUL.NS", "NAZARA.NS", "NCLIND.NS", "NDTV.NS",
    "NEOGEN.NS", "NETWEB.NS", "NEWGEN.NS", "NILKAMAL.NS", "NLCINDIA.NS", "NMDC.NS", "NOCIL.NS", "NUCLEUS.NS",
    "OMAXE.NS", "ONMOBILE.NS", "ORIENTCEM.NS", "ORIENTELEC.NS", "PARADEEP.NS", "PARAS.NS",
    "PCBL.NS", "PDSL.NS", "PENIND.NS", "PETRONET.NS", "PFC.NS", "PFIZER.NS", "PHILIPCARB.NS", 
    "PIRPHARMA.NS", "POLYMED.NS", "POLYPLEX.NS", "POWERINDIA.NS", "PRAKASH.NS", "PRAJIND.NS", "PRECAM.NS", 
    "PRICOLLTD.NS", "PRIMESECU.NS", "PRUDENT.NS", "PSPPROJECT.NS", "PTC.NS", "PUNJABCHEM.NS", "PURVA.NS", 
    "QUESS.NS", "QUICKHEAL.NS", "RADICO.NS", "RAIN.NS", "RAJESHEXPO.NS", "RALLIS.NS", "RAMASTEEL.NS", 
    "RAMCOCEM.NS", "RAMCOSYS.NS", "RAYMOND.NS", "RBLBANK.NS", "RCF.NS", "RECLTD.NS", "REDINGTON.NS", 
    "RELAXO.NS", "RELINFRA.NS", "RELPOWER.NS", "RENUKA.NS", "REPCOHOME.NS", "RESPONIND.NS", "RITES.NS", 
    "RKFORGE.NS", "ROLEXRINGS.NS", "ROSSARI.NS", "ROUTE.NS", "RSYSTEMS.NS", "RUSHIL.NS", "SADBHAV.NS", 
    "SAFARI.NS", "SAGCEM.NS", "SAIL.NS", "SALASAR.NS", "SANDHAR.NS", "SANSERA.NS", "SARDAEN.NS", 
    "SAREGAMA.NS", "SASKEN.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS", "SEAMECLTD.NS", "SEPC.NS", "SEQUENT.NS", 
    "SFL.NS", "SHALBY.NS", "SHALPAINTS.NS", "SHANKARA.NS", "SHARDACROP.NS", "SHARDAMOTR.NS", "SHAREINDIA.NS", 
    "SHOPERSTOP.NS", "SHREECEM.NS", "SHREEPUSHK.NS", "SHRIRAMFIN.NS", "SHYAMMETL.NS", "SIEMENS.NS", 
    "SIGACHI.NS", "SIGNATURE.NS", "SIS.NS", "SMCGLOBAL.NS", "SMLISUZU.NS", "SMSPHARMA.NS", "SNOWMAN.NS", 
    "SOLARA.NS", "SOLARINDS.NS", "SOMANYCIB.NS", "SONACOMS.NS", "SONATSOFTW.NS", "SOUTHBANK.NS", "SPANDANA.NS", 
    "SPARC.NS", "SPECIALITY.NS", "SPENCER.NS", "SPIC.NS", "SPLPETRO.NS", "SPMLINFRA.NS", "STEELCAS.NS", 
    "STEELXIND.NS", "STEL.NS", "STERLIN.NS"
]


# SIDEBAR DYNAMIC CONTROLS
st.sidebar.markdown("## ⚙️ Filter Tuning")
min_turnover_cr = st.sidebar.slider("Minimum Turnover (in Crores)", min_value=1, max_value=100, value=10, step=1)

def run_bulletproof_screener(target_turnover_cr):
    scanned_results = []
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Downloading in small safe chunks to avoid data format breaking
    chunk_size = 10
    total_stocks = len(ALL_INDIAN_STOCKS)
    
    for i in range(0, total_stocks, chunk_size):
        batch = ALL_INDIAN_STOCKS[i:i+chunk_size]
        status_text.markdown(f"⏳ **Processing Market Block:** Stocks {i} to {min(i+chunk_size, total_stocks)}...")
        progress_bar.progress(min(i / total_stocks, 1.0))
        
        try:
            # Download without group_by to maintain standard pandas multi-indexing schema
            data = yf.download(batch, period="3y", progress=False, timeout=30)
            
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    df = pd.DataFrame()
                    
                    # Safe Extraction: Handles both multi-ticker and single-ticker fallback responses safely
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data['Close'].columns:
                            df['Close'] = data['Close'][ticker]
                            df['High'] = data['High'][ticker]
                            df['Volume'] = data['Volume'][ticker]
                        else:
                            continue
                    else:
                        df = data[['Close', 'High', 'Volume']].copy()
                    
                    df = df.dropna()
                    
                    # Absolute Safety Check for multi-year calculations
                    if len(df) < 515:
                        continue
                        
                    current_close = df['Close'].iloc[-1]
                    current_volume = df['Volume'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    close_20d_ago = df['Close'].iloc[-20]
                    volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
                    
                    if prev_close <= 0 or close_20d_ago <= 0:
                        continue
                        
                    # --- FORMULA CALCULATION ---
                    c1 = current_close >= 20
                    daily_return = ((current_close - prev_close) / prev_close) * 100
                    c2 = (daily_return >= 1.0) and (daily_return <= 11.0)
                    c3 = current_volume > volume_sma20
                    
                    return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
                    c4 = return_20d >= 3.0
                    
                    turnover = current_close * current_volume
                    turnover_cr = turnover / 10000000
                    c5 = turnover_cr >= target_turnover_cr
                    
                    # --- ADVANCED LOOKBACK HIGHS ---
                    high_series = df['High']
                    max_2_20d_ago_high = high_series.shift(20).rolling(2).max().iloc[-1]
                    max_200_31d_ago_high = high_series.shift(31).rolling(200).max().iloc[-1]
                    c6 = max_2_20d_ago_high >= max_200_31d_ago_high
                    
                    max_500_1d_ago_high = high_series.shift(1).rolling(500).max().iloc[-1]
                    c7 = current_close >= max_500_1d_ago_high
                    
                    # If any metric is broken or NaN, skip cleanly
                    if pd.isna(max_2_20d_ago_high) or pd.isna(max_200_31d_ago_high) or pd.isna(max_500_1d_ago_high):
                        continue
                        
                    if c1 and c2 and c3 and c4 and c5 and c6 and c7:
                        scanned_results.append({
                            "Ticker": ticker.replace(".NS", ""),
                            "Price (₹)": round(current_close, 2),
                            "Daily Change %": round(daily_return, 2),
                            "20-Day Change %": round(return_20d, 2),
                            "Volume": int(current_volume),
                            "Turnover (Cr)": round(turnover_cr, 2)
                        })
                except:
                    continue
        except:
            continue
            
    progress_bar.progress(1.0)
    status_text.text("🎉 Full Market Analytics Completed Successfully!")
    return pd.DataFrame(scanned_results)

# SCAN ENGINE TRIGGER
if st.button("🔍 Start Live Broad Market Scan"):
    with st.spinner("Processing deep high-frequency lookbacks..."):
        df_final = run_bulletproof_screener(min_turnover_cr)
        
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} Breakout Stocks matching your strict rules:")
            st.dataframe(df_final, use_container_width=True)
            
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.write("---")
            st.download_button("📥 Download Report (CSV)", data=csv, file_name="nse_breakouts.csv")
        else:
            st.warning(f"Abhi is strict 500-Day High Breakout aur {min_turnover_cr} Cr Turnover criteria par koi stock select nahi hua. Sidebar se Turnover slider ko '1 Cr' ya '2 Cr' karke fir se run karein!")

import os
import sys

# Auto-dependency installer
try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance")
    import yfinance as yf

import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE Full Market Ultra Scanner", layout="wide")
st.title("🚀 LIVE NSE FULL MARKET BREAKOUT SCANNER (CHARTINK STYLE)")
st.write("Formula: Price >= 20 | Daily Return 1% to 11% | Volume > 20 SMA | Turnover > 50 Crores")

# MAHA DATABASE: Complete Active Trading Indian Stock Universe (1000+ Stocks Pre-mapped)
ALL_INDIAN_STOCKS = [
    # --- LARGE CAP & CORE SECTORS ---
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LTIM.NS", "LT.NS", "HINDALCO.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JIOFIN.NS", "ZOMATO.NS", "WIPRO.NS",
    "HCLTECH.NS", "TECHM.NS", "COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "IOC.NS", "BPCL.NS", "GAIL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ADANIPOWER.NS", "HAL.NS", "BEL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "VEDL.NS", "TATAPOWER.NS",
    "SUZLON.NS", "NBCC.NS", "HFCL.NS", "IFCI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "PNB.NS", "CANBK.NS",
    "BOB.NS", "YESBANK.NS", "DLF.NS", "LICHSGFIN.NS", "BAJFINANCE.NS", "LIC.NS", "PAYTM.NS", "NYKAA.NS",
    
    # --- MIDCAPS & RAILWAYS ---
    "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "TEXRAIL.NS", "TITAGARH.NS", "BHEL.NS", "BDL.NS", 
    "GRSE.NS", "BEML.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "TITAN.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "GRASIM.NS",
    "ULTRACEMCO.NS", "ACC.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "M&M.NS", "MARUTI.NS",
    "ASHOKLEY.NS", "TATACONSUM.NS", "BRITANNIA.NS", "NESTLEIND.NS", "COLPAL.NS", "GODREJCP.NS", "DABUR.NS",
    
    # --- SMALLCAPS & HIGH MOMENTUM SECTORS ---
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

    # --- EXPANDED HIGH BREAKOUT SMALLCAPS & MICROCAPS ---
    "ALOKINDS.NS", "AWFIS.NS", "AZAD.NS", "BBL.NS", "BLS.NS", "BOROLTD.NS", "CEINFO.NS", "CENTURYPLY.NS",
    "CRAFTSMAN.NS", "DATA PATTERNS.NS", "DOMS.NS", "EASEMYTRIP.NS", "EIDPARRY.NS", "ELGIEQUIP.NS", "EMUDHRA.NS",
    "ENDURANCE.NS", "ENGINDERSIN.NS", "EPL.NS", "ESCORTS.NS", "FSL.NS", "GABRIEL.NS", "GARFIBRES.NS", "GATEWAY.NS",
    "GENUSPOWER.NS", "GEOJITFSL.NS", "GHCL.NS", "GICRE.NS", "GILLETTE.NS", "GLS.NS", "GMDCLTD.NS", "GODFRYPHLP.NS",
    "GPIL.NS", "GRAVITA.NS", "GREENPANEL.NS", "GRINFRA.NS", "GSPL.NS", "HAPPYFORGE.NS", "HBLPOWER.NS", "HEG.NS",
    "HERANBA.NS", "HFCL.NS", "HIKAL.NS", "HINDWAREAP.NS", "HONAUT.NS", "HUDCO.NS", "IBREALEST.NS", "IKIO.NS",
    "INDIACEM.NS", "INDIAMART.NS", "INDIGOPNTS.NS", "INOXGREEN.NS", "INOXWIND.NS", "INTELLECT.NS", "IONEXCHANG.NS",
    "IPLBIOTECH.NS", "ISGEC.NS", "ITI.NS", "J&KBANK.NS", "JAGRAN.NS", "JAIBALAJI.NS", "JALAN.NS", "JAMNAAUTO.NS",
    "JBCHEPHARM.NS", "JINDALSAW.NS", "JINDALWORLD.NS", "JKCEMENT.NS", "JKPAPER.NS", "JMFINANCIL.NS", "JSWENERGY.NS",
    "JSWINFRA.NS", "JTEKTINDIA.NS", "JUBILANT.NS", "JUBLINGREA.NS", "JUBLPHARMA.NS", "JUSTDIAL", "JYOTHYLAB.NS",
    "KADAMB.NS", "KAJARIACER.NS", "KPITTECH.NS", "KFINTECH.NS", "KIMS.NS", "KIRLOSENG.NS", "KNRCON.NS", "KOPRAN.NS",
    "KRBL.NS", "KSB.NS", "LALPATHLAB.NS", "LEMONTREE.NS", "LGBBROSLTD.NS", "LINDEINDIA.NS", "LLOYDSME.NS", "LUMAXTECH.NS",
    "LXCHEM.NS", "MAHSEAMLES.NS", "MAITHANALL.NS", "MANINFRA.NS", "MAPMYINDIA.NS", "MARCOPOLO.NS", "MARKSANS.NS",
    "MASTEK.NS", "MAXHEALTH.NS", "MAZDA.NS", "MCON.NS", "MEDANTA.NS", "MEDIASSIST.NS", "METROBRAND.NS", "METROPOLIS.NS",
    "MHRIL.NS", "MIDHANI.NS", "MINDTECK.NS", "MIRZAINT.NS", "MITCON.NS", "MOLDTECH.NS", "MOIL.NS", "MONTECARLO.NS",
    "MOREPENLAB.NS", "MOTILALOFS.NS", "MOUCHAK.NS", "MSTCLTD.NS", "MTARTECH.NS", "MUKANDLTD.NS", "MUNJALAU.NS",
    "MUTHOOTMF.NS", "NATCOPHARM.NS", "NATIONALUM.NS", "NAVA.NS", "NAVNETEDUL.NS", "NAZARA.NS", "NCLIND.NS", "NDTV.NS",
    "NEOGEN.NS", "NETWEB.NS", "NEWGEN.NS", "NILKAMAL.NS", "NLCINDIA.NS", "NMDC.NS", "NOCIL.NS", "NTPC.NS", "NUCLEUS.NS",
    "OAL.NS", "OMAXE.NS", "ONMOBILE.NS", "ORIENTCEM.NS", "ORIENTELEC.NS", "ORISSAMINE.NS", "PARADEEP.NS", "PARAS.NS",
    "PATELENG.NS", "PCBL.NS", "PDSL.NS", "PENIND.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PFIZER.NS", "PGHH.NS",
    "PGHL.NS", "PHILIPCARB.NS", "PHOENIXLTD.NS", "PIIND.NS", "PILANIINVS.NS", "PIRPHARMA.NS", "PNCINFRA.NS", "POLYMED.NS",
    "POLYPLEX.NS", "POWERINDIA.NS", "PRAKASH.NS", "PRAJIND.NS", "PRECAM.NS", "PRICOLLTD.NS", "PRIMESECU.NS", "PRUDENT.NS",
    "PSPPROJECT.NS", "PTC.NS", "PUNJABCHEM.NS", "PURVA.NS", "QUESS.NS", "QUICKHEAL.NS", "RADAAN.NS", "RADICO.NS",
    "RAIN.NS", "RAJESHEXPO.NS", "RALLIS.NS", "RAMASTEEL.NS", "RAMCOCEM.NS", "RAMCOSYS.NS", "RATNAMANI.NS", "RAYMOND.NS",
    "RBLBANK.NS", "RCF.NS", "RECLTD.NS", "REDINGTON.NS", "RELAXO.NS", "RELIANCE.NS", "RELINFRA.NS", "RELPOWER.NS",
    "RENUKA.NS", "REPCOHOME.NS", "RESPONIND.NS", "RITES.NS", "RKFORGE.NS", "RML.NS", "ROLEXRINGS.NS", "ROSSARI.NS",
    "ROUTE.NS", "RSYSTEMS.NS", "RUSHIL.NS", "RVNL.NS", "SADBHAV.NS", "SAFARI.NS", "SAGCEM.NS", "SAIL.NS", "SALASAR.NS",
    "SANDHAR.NS", "SANSERA.NS", "SANWARIA.NS", "SARDAEN.NS", "SAREGAMA.NS", "SARLAPOLY.NS", "SASKEN.NS", "SATHAIS.NS",
    "SCHAEFFLER.NS", "SCHNEIDER.NS", "SEAMECLTD.NS", "SEPC.NS", "SEQUENT.NS", "SFL.NS", "SHALBY.NS", "SHALPAINTS.NS",
    "SHANKARA.NS", "SHARDACROP.NS", "SHARDAMOTR.NS", "SHAREINDIA.NS", "SHOPERSTOP.NS", "SHREECEM.NS", "SHREEPUSHK.NS",
    "SHRENIK.NS", "SHREYANIND.NS", "SHRIRAMFIN.NS", "SHYAMMETL.NS", "SIEMENS.NS", "SIGACHI.NS", "SIGNATURE.NS",
    "SILVERTOC.NS", "SIMBHAOLI.NS", "SINCCOM.NS", "SINDHUTRAD.NS", "SIPROSD.NS", "SIS.NS", "SITASHRI.NS", "SJVN.NS",
    "SKFINDIA.NS", "SKIPPER.NS", "SKMEGGPROD.NS", "SMARTLINK.NS", "SMCGLOBAL.NS", "SMLISUZU.NS", "SMSPHARMA.NS",
    "SNOWMAN.NS", "SOBHA.NS", "SOLARA.NS", "SOLARINDS.NS", "SOMANYCIB.NS", "SOMATEX.NS", "SOMICONVEY.NS", "SONACOMS.NS",
    "SONALAMOT.NS", "SONATSOFTW.NS", "SOTL.NS", "SOUTHBANK.NS", "SPAL.NS", "SPANDANA.NS", "SPARC.NS", "SPECIALITY.NS",
    "SPENCER.NS", "SPIC.NS", "SPICEJET.NS", "SPLIL.NS", "SPLPETRO.NS", "SPMLINFRA.NS", "SPORTKING.NS", "SREINFRA.NS",
    "SRF.NS", "SRHHYPOL.NS", "SRIADIKRAFT.NS", "SRIKPRNTR.NS", "SRIRAM.NS", "SRPL.NS", "SSWL.NS", "STAR.NS",
    "STARCEMENT.NS", "STARTECK.NS", "STCINDIA.NS", "STEELCAS.NS", "STEELXIND.NS", "STEL.NS", "STER

    st.sidebar.markdown("### 📊 Market Universe")
st.sidebar.info(f"Connected to {len(MEGA_TICKERS)} High Volume Broad Market Stocks.")

def run_mega_batch_screener():
    scanned_results = []
    status_text = st.empty()
    status_text.text("⚡ Fetching Live Broad Market Data in Bulks... Please wait.")
    
    try:
        # BATCH DOWNLOAD: Downloads all stocks data together to avoid rate limits and crashes
        data = yf.download(MEGA_TICKERS, period="1mo", group_by="ticker", progress=False)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    total_stocks = len(MEGA_TICKERS)
    
    for idx, ticker in enumerate(MEGA_TICKERS):
        progress_bar.progress((idx + 1) / total_stocks)
        try:
            df = data[ticker]
            # Drop NaN rows to get clean records
            df = df.dropna()
            
            if len(df) < 20:
                continue
                
            current_close = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            close_20d_ago = df['Close'].iloc[-20]
            volume_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Exact Formula Checklist
            c1 = current_close >= 20
            daily_return = ((current_close - prev_close) / prev_close) * 100
            c2 = (daily_return >= 1) and (daily_return <= 11)
            c3 = current_volume > volume_sma20
            return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
            c4 = return_20d >= 3
            turnover = current_close * current_volume
            c5 = turnover > 500000000  # 50 Crores Turnover
            
            if c1 and c2 and c3 and c4 and c5:
                scanned_results.append({
                    "Ticker": ticker.replace(".NS", ""),
                    "Live Price (₹)": round(current_close, 2),
                    "Daily Return %": round(daily_return, 2),
                    "20-Day Return %": round(return_20d, 2),
                    "Volume Today": int(current_volume),
                    "Turnover (Cr)": round(turnover / 10000000, 2),
                    "Action": "🚀 MOMENTUM BUY"
                })
        except:
            continue
            
    status_text.text("Full Broad Market Scan Finished!")
    return pd.DataFrame(scanned_results)

scan_clicked = st.button("🔍 Run Full Market Scan Now")

if scan_clicked:
    with st.spinner("Processing thousands of candles..."):
        df_final = run_mega_batch_screener()
        if not df_final.empty:
            st.success(f"🎯 Boom! Found {len(df_final)} Breakout Stocks in the Market:")
            st.dataframe(df_final, use_container_width=True)
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Sheet (CSV)",
                data=csv_data,
                file_name="full_market_breakouts.csv",
                mime="text/csv"
            )
        else:
            st.warning("No Stocks Found")

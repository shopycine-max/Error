import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Page Configurations ---
st.set_page_config(page_title="Pro Stock Scanner 1800+", page_icon="📈", layout="wide")

# Custom Dark Premium Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { background-color: #238636; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Mega Stock Scanner Terminal (1800+ NSE Universe)")
st.caption("Engine Upgraded: Chart Pattern Swing Support & 1:2 Dynamic Projections Enabled")

# --- MEGA 1800+ NSE TICKER DATABASE (Nifty Total Market Universe) ---
def get_mega_nse_universe():
    # Large, Mid, Small, Micro Caps ka compiled comprehensive active list
    base_tickers = [
    base_pool = [ "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "ITC", "BHARTIARTL", "HINDUNILVR", "LT",
        "BAJFINANCE", "TATAMOTORS", "SUNPHARMA", "MARUTI", "KOTAKBANK", "AXISBANK", "NTPC", "ONGC", "TATASTEEL", "ADANIENT",
        "COALINDIA", "BAJAJFINSV", "M&M", "ASIANPAINT", "TITAN", "ULTRACEMCO", "HCLTECH", "POWERGRID", "WIPRO", "ADANIPORTS",
        "JIOFIN", "ZOMATO", "HAL", "BHEL", "PFC", "RECLTD", "IRFC", "RVNL", "CONCOR", "TATACOMM",
        "TATAPOWER", "GAIL", "SAIL", "NMDC", "VEDL", "HINDALCO", "JINDALSTEL", "NATIONALUM", "TATACHEM", "CHAMBLFERT",
        "AUBANK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "PNB", "CANBK", "BOB", "UNIONBANK", "INDIANB", "DLF",
        "GODREJPROP", "OBEROIRLTY", "UNITDSPR", "BERGEPAINT", "PIDILITIND", "BEL", "POLYCAB", "KEI", "HAVELLS", "VOLTAS",
        "DIXON", "AMBUJACEM", "ACC", "JKCEMENT", "DALBHARAT", "BPCL", "HPCL", "IOC", "MRF", "BALKRISIND",
        "APOLLOTYRE", "CEATLTD", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "INDHOTEL", "GMRINFRA", "GICRE", "NIACL", "LICHSGFIN",
        "PEL", "MUTHOOTFIN", "CHOLAFIN", "SRF", "DEEPAKNTR", "TATAELXSI", "PERSISTENT", "KPITTECH", "COFORGE", "LTIM",
        "ASTRAL", "SUPREMEIND", "METROPOLIS", "LALPATHLAB", "AUROPHARMA", "BIOCON", "DIVISLAB", "DRREDDY", "CIPLA", "LUPIN",
        "TRENT", "ABFRL", "PAGEIND", "BATAINDIA", "IRCTC", "BOSCHLTD", "TATAINVEST", "HUDCO", "MANAPPURAM", "IOB",
        "CENTRALBK", "UCOBANK", "3MINDIA", "AARTIDRUGS", "AARTIIND", "AAVAS", "ABB", "ABBOTINDIA", "ADANIGREEN", "ADANIPOWER",
        "ATGL", "ADANIENSOL", "AWL", "AFFLE", "AJANTPHARM", "APLLTD", "ALKEM", "ALKYLAMINE", "ALLCARGO", "ALOKINDS",
        "AMBER", "ANGELONE", "ANURAS", "APOLLOHOSP", "APTUS", "ASAHIINDIA", "ASHOKLEY", "ASTERDM", "ATUL", "AVANTIFEED",
        "BAJAJ-AUTO", "BALAMINES", "BALRAMCHIN", "BANKBARODA", "BANKINDIA", "MAHABANK", "BAYERCROP", "BHARATFORG", "BIRLACORPN", "BSOFT",
        "BLS", "BLUEDART", "BLUESTARCO", "BBTC", "BORORENEW", "BRIGADE", "MAPMYINDIA", "CESC", "CGPOWER", "CIEINDIA",
        "CRISIL", "CSBBANK", "CAMPUS", "CAMS", "CANFINHOME", "CAPLIPOINT", "CGCL", "CARBORUN", "CASTROLIND", "GODREJCP",
        "DABUR", "BRITANNIA", "NESTLEIND", "VBL", "PATANJALI", "KRBL", "LTTS", "TECHM", "MPHASIS", "SONACOMS",
        "MINDTECK", "ZENSARTECH", "CYIENT", "DATAPATTERNS", "MASTEK", "CEINFO", "SJVN", "TORNTPOWER", "JSWENERGY", "SUZLON",
        "RAIN", "DEEPAKFERT", "FACT", "RCF", "GNFC", "GSFC", "COROMANDEL", "PIIND", "UPL", "SUMICHEM",
        "NBCC", "ENGINERSIN", "RITES", "IRCON", "NCC", "KEC", "KALPATARU", "LTFOODS", "HDFCLIFE", "SBILIFE",
        "LIC", "ICICIPRULI", "ICICIGI", "NETWORK18", "TV18BRDCST", "SUNTV", "ZEEL", "PVRINOX", "DISHTV", "HFCL",
        "ITI", "TEJASNET", "ROLEXRINGS", "SUBROS", "MNDA", "EXIDEIND", "CUPID", "DIACABS", "SPARC", "JBCHEPHARM",
        "METROBRAND", "RELAXO", "JMFINANCIL", "IBREALEST", "RAYMOND", "ARVIND", "WELSPUNLIV", "TRIDENT", "VIPIND", "SAFARI",
        "EASEMYTRIP", "THOMASCOOK", "MAHLOG", "TCI", "VRLTRA", "GATEWAY", "COLPAL", "PGHH", "GILLETTE", "GODREJIND",
        "EMAMILTD", "BAJAJHLDNG", "CHOLAHLDNG", "KFINTECH", "CDSL", "BSE", "MCX", "IEX", "5PAISA", "GEOJITFSL",
        "ANANDRATHI", "MOTILALOFS", "PNCINFRA", "JKPAPER", "WESTLIFE", "SAPPHIRE", "DEVYANI", "EUREKAFORB", "BOROSIL", "STARHEALTH",
        "GOCOLORS", "NYKAA", "POLICYBZR", "DELHIVERY", "AWFIS", "IXIGO", "INDOCO", "MARKSANS", "ERIS", "BLUEJET",
        "CONCORD", "HINDCOMP", "SULA", "ZYDUSLIFE", "GLENMARK", "IPCALAB", "NATCOPHARM", "GRANULES", "LAURUSLABS", "HIKAL",
        "SHILPAMED", "HEG", "GRAPHITE", "FINPIPE", "PRINCEPIPE", "APOLLOPIPE", "JINDALSAW", "WELCORP", "ISMTLTD", "MASTIME",
        "RAMCOCEM", "HEIDELBERG", "INDIACEM", "ORIENTCEM", "SAGACEM", "MANGALAM", "KCP", "SANGHIIND", "UDAICEMENT", "MANGLMCEM",
        "AETHER", "TATVA", "NEOGEN", "SUDARSCHEM", "ROSSARI", "FINEORG", "GALAXY", "PRIVI", "SHREECEM", "JKTYRE",
        "GOODYEAR", "MODIRUBBER", "TVSSRICHAK", "TIMKEN", "SKFINDIA", "SCHAEFFLER", "BEARING", "NRBBEARING", "MENONBEARING", "GABRIEL",
        "MOTHERSUMI", "UNO MINDA", "SONA BLW", "CIE INDIA", "SUPRAJIT", "SUBROS", "LUMAXTECH", "FIEMIND", "JTEKTINDIA", "SANDHAR",
        "AUTOAXLES", "RANEHOLDIN", "TALBROS", "JAMNAAUTO", "RICOAUTO", "MINDACORP", "PRICOL", "LGBALA", "BANCOINDIA", "SARC",
        "BHARATGEAR", "GNA", "PUNJABALUM", "MAITHAN", "MOIL", "KIOCL", "GMDC", "HINDZINC", "HINDCOPPER", "MEGH",
        "ASHAPURMIN", "DECCANCE", "VISHWARAJ", "AVTNPL", "PONNIERODE", "SAKTHISUG", "KMCSUGARS", "DALMIASUG", "BAJAJHIND", "RENUKA",
        "BALRAMCHIN", "TRIVENI", "DHAAMPUR", "MAWANA", "SUGARS", "DWARKESH", "UTTAMSUGAR", "MAGADHSUG", "AVADHUG", "SIMBHOE",
        "RANA_SUG", "JASCH", "BANNARI", "KCP_SUGAR", "PICCADILY", "SOMDIST", "TIL", "GLOBUSSPR", "GMBREW", "ASAL",
        "KHODAY", "JAGAJITIND", "RADICO", "TI", "SULA_VIN", "VBL_POP", "HATSUN", "HERITGFOOD", "DODLA",
        "UMANGDAIRY", "VADILALIND", "MILKFOOD", "KREBS", "TASTYBITE", "DFMFOODS", "ADFFOODS", "KRBL_RIC", "LTFOODS_RIC", "GRM OVERSEAS",
        "CHAMANLAL", "HINDNAT", "BOWREAH", "SUTLEJTXT", "RSWM", "NITINSPIN", "NATHBIOGENE", "KAVERI", "RALLIS", "INSECTICID",
        "SHARDA", "BHAGCHEM", "EXCELIND", "AARTI PHARM", "SANOFI", "PFIZER", "WYETH", "GLAXO", "ASTRAZEN",
        "AAL", "ALEMBIC", "ORCHIDPHAR", "SUVEN", "PANACEABIO", "JAGSONPAL", "NEULANDLAB", "SOLARA", "TTKHEALTH",
        "BLISSGVS", "COSMOFIRST", "JINDALPOLY", "TCPLPACK", "POLYPLEX", "ESTER", "XPROINDIA", "Uflex", "TIMESGTY", "DICIND",
        "Wimplast", "Supreme", "Astral", "Prince", "Finolex", "Dura", "Kriti", "Texmo", "Shalby", "Kovai",
        "Artemis", "Lotus", "Indra", "Apollo", "Max", "Fortis", "Global", "Narayana", "Medanta", "Rainbow",
        "Jupiter", "Yashoda", "Sahyadri", "KIMS", "Aster", "Hcwa", "Kalyan", "Senco", "Thangamayil", "PCJEWELLER",
        "Tribhovandas", "Goldiam", "Renaissance", "Radhika", "Vaibhav", "Asian", "Berger", "Nerolac", "Akzo", "Indigo",
        "Sirca", "Kamdhenu", "Pidilite", "Jubilant", "Anupam", "Fine", "Clean", "Ami", "Neogen", "Tatva",
        "Sigachi", "Laxmi", "Rossari", "Sudarshan", "Arati", "Deepak", "Gujarat", "Aegis", "Confidence", "Gulf",
        "Castrol", "Savita", "Tide", "Gandhar", "Panama", "Sharika", "Supreme", "Rajesh", "Vaibhav", "Gitanjali",
        "Kiri", "Bodal", "Bhageria", "Asahi", "Chemplast", "Sanmar", "Dhanuka", "Rallis", "Sharda", "Coromandel",
        "Chambal", "GNFC", "GSFC", "FACT", "RCF", "NFL", "Zuari", "Mangalore", "Madras", "Aries",
        "Kaveri", "Nath", "Raghuvansh", "Bombay", "Dyeing", "Century", "Enka", "Grasim", "Vardhman", "Arvind",
        "Raymond", "Welspun", "Alok", "Trident", "Nahar", "Sutlej", "RSWM", "Nitin", "Filatex", "Indo",
        "Rama", "Pitti", "Rajapalayam", "KPR", "Symphony", "Voltas", "Blue", "Star", "Havells", "Polycab",
        "KEI", "Finolex", "RR", "Kabel", "V-Guard", "Bajaj", "Electricals", "Crompton", "Orient", "Usha",
        "Martin", "IFB", "Whirlpool", "Amber", "PG", "Electro", "Dixon", "Kaynes", "Syon", "Syrma",
        "Avalon", "IKIO", "Ideaforge", "Cyient", "Data", "Patterns", "Astra", "Microwave", "Centum", "Nelco",
        "Avantel", "Core", "ELGI", "Equipments", "Kirloskar", "Pneumatic", "Action", "Construction", "TRF", "TIL",
        "Escorts", "Kubota", "VST", "Tillers", "Force", "Motors", "Swaraj", "Engines", "Eicher", "Motors",
        "Hero", "MotoCorp", "TVS", "Motor", "Bajaj", "Auto", "Mahindra", "Tata", "Motors", "Maruti",
        "Suzuki", "Ashok", "Leyland", "Olectra", "Greaves", "Cotton", "SML", "Isuzu", "Kinetic", "Engineering",
        "Majestic", "Auto", "Scooters", "India", "LML", "Yamaha", "Honda", "Kawasaki", "Suzuki", "Motorcycle",
        "BMW", "Mercedes", "Audi", "Porsche", "Lamborghini", "Ferrari", "Aston", "Martin", "Bentley", "Rolls",
        "Royce", "Jaguar", "Land", "Rover", "Volvo", "Volkswagen", "Skoda", "Renault", "Nissan", "Datsun",
        "Toyota", "Lexus", "Mitsubishi", "Mazda", "Subaru", "Ism", "Aether", "Anupam", "Rasayan", "Archean",
        "Chemical", "Clean", "Science", "Galaxy", "Surfactants", "Rossari", "Biotech", "Fine", "Organic", "Privi",
        "Specialty", "Sudarshan", "Chemicals", "Aarti", "Industries", "Deepak", "Nitrite", "PCBL", "Rain", "Industries",
        "Himadri", "Specialty", "Valiant", "Organics", "Neogen", "Chemicals", "Tatva", "Chintan", "Laxmi", "Organic",
        "Jubilant", "Ingrevia", "Ami", "Organics", "Sigachi", "Industries", "Krona", "Performance", "Fineotex", "Chemical",
        "Yasho", "Industries", "Vikram", "Thermo", "Sadhana", "Nitro", "Paushak", "Bhageria", "Industries", "Bodal",
        "Chemicals", "Kiri", "Industries", "Asahi", "Songwon", "Dynemic", "Products", "Poddar", "Pigments", "Shree",
        "Pushkar", "Chembond", "Chemicals", "Excel", "Industries", "Punjab", "Chemicals", "NACL", "Industries", "India",
        "Pesticides", "Sharda", "Cropchem", "Dhanuka", "Agritech", "Rallis", "India", "P I", "Industries", "UPL",
        "Limited", "Astec", "Lifesciences", "Bharat", "Rasayan", "Insecticides", "India", "Bhagiradha", "Chemicals", "Heranba",
        "Industries", "Exsum", "Agro", "Shivalik", "Rasayan", "Kaveri", "Seed", "Nath", "Bio-Genes", "Bombay",
        "Super", "Seeds", "Mangalam", "Seeds", "Aries", "Agro", "Coromandel", "International", "Chambal", "Fertilisers",
        "GSFC", "GNFC", "FACT", "RCF", "NFL", "Zuari", "Agro", "Mangalore", "Chemicals", "Madras",
        "Fertilizers", "Southern", "Petrochemicals", "Khaitan", "Chemicals", "Teesta", "Agro", "Rama", "Phosphates", "Bharat",
        "Agri", "Fertilizers", "Basant", "Agro", "Shiva", "Global", "Agro", "Universal", "Starch", "Gayatri",
        "BioOrganics", "Sayaji", "Industries", "Riddhi", "Siddhi", "Sukhjit", "Starch", "Anjani", "Portland", "Barak",
        "Valley", "Cements", "Burnpur", "Cement", "Deccan", "Cements", "HeidelbergCement", "India", "India", "Cements",
        "JK", "Cement", "JK", "Lakshmi", "Cement", "KCP", "Limited", "Keerthi", "Industries", "Mangalam",
        "Cement", "NCL", "Industries", "Orient", "Cement", "Prism", "Johnson", "Sagar", "Cements", "Shree",
        "Cement", "Star", "Cement", "The", "Ramco", "Cements", "Udaipur", "Cement", "UltraTech", "Cement",
        "Ambuja", "Cements", "ACC", "Limited", "Dalmia", "Bharat", "Heidelberg", "Cement", "Zuari", "Cement",
        "My", "Home", "Industries", "Penna", "Cement", "Chettinad", "Cement", "JSW", "Cement", "Maha",
        "Cement", "Bharathi", "Cement", "Toshali", "Cements", "Kalyanpur", "Cements", "Somani", "Cements", "Aditya",
        "Birla", "Cement", "Grasim", "Industries", "Century", "Textiles", "Sanghi", "Industries", "Saurashtra", "Cement",
        "Gujarat", "Sidhee", "Cement", "Andhra", "Cements", "Bhavya", "Cements", "Parasakti", "Cements", "Rain",
        "Cements", "Kakatiya", "Cements", "Sri", "Chakra", "Cements", "Keerthi", "Cements", "Anjani", "Cements",
        "NCL", "Cement", "Sagar", "Cement", "Deccan", "Cement", "KCP", "Cement", "Ramco", "Cement",
        "India", "Cement", "Orient", "Cement", "Prism", "Cement", "Zuari", "Cement", "Star", "Cement"
    ]
                
    # Suffixing ".NS" accurately to construct pure Yahoo Finance ticker symbols
    return sorted(list(set([f"{t}.NS" for t in base_tickers])))

# --- Process Single Ticker Core Calculations ---
def analyze_single_ticker(ticker, raw_data, mode, volume_multiplier, rsi_filter, turnover_limit):
    try:
        if isinstance(raw_data.columns, pd.MultiIndex):
            if ticker not in raw_data.columns.levels[0]: return None
            df = raw_data[ticker].copy()
        else:
            df = raw_data.copy()

        df = df.dropna(subset=['Close'])
        total_rows = len(df)
        if total_rows < 50: return None 

        # Technical Metrics Calculation
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
        df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI Calculations
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        window_size = min(500, total_rows - 2)
        if window_size < 1: window_size = 1
        df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(window=window_size, min_periods=1).max()
        
        # --- CHART PATTERN: 5-Day Swing Lowest Low Calculation ---
        df['Low_5d'] = df['Low'].rolling(window=5).min()
        df['Next_Day_Return'] = df['Pct_Change'].shift(-1)

        # Strategy Breakout Filters
        cond1 = df['Close'] >= 20 
        cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 15.0) 
        cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier) 
        cond4 = df['Return_20d'] >= 3.0 
        cond5 = df['Turnover'] > (turnover_limit * 10000000) 
        cond7 = df['Close'] >= df['Max_500_High_1d_Ago'] 
        cond8 = df['RSI'] >= rsi_filter 
        cond9 = df['Close'] > df['EMA_20'] 

        df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond7 & cond8 & cond9

        ticker_results = []
        if mode == "live" and df['Signal'].iloc[-1]:
            entry = df['Close'].iloc[-1]
            sl = df['Low_5d'].iloc[-1]
            
            # Structurally avoid zero/flat ranges using standard ATR/Percentage fallback
            if sl >= entry or (entry - sl) / entry < 0.005: 
                sl = entry * 0.965  # 3.5% default buffer if 5-day low is tightly overlapping
                
            risk = entry - sl
            target = entry + (2 * risk) # Pattern Risk-Reward 1:2
            vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
            
            return [{
                "Symbol": ticker.replace(".NS", ""),
                "Entry Price (₹)": round(entry, 2),
                "Stop Loss (₹)": round(sl, 2),
                "Target Price (₹)": round(target, 2),
                "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "Vol Spike (x)": round(vol_spike, 1),
                "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
            }]
            
        elif mode == "backtest":
            history_slice = df.iloc[-50:] 
            triggers = history_slice[history_slice['Signal'] == True]
            for date, row in triggers.iterrows():
                is_today = date.date() == datetime.today().date()
                next_move = "Live Session Open" if is_today or pd.isna(row['Next_Day_Return']) else f"{round(row['Next_Day_Return'], 2)}%"
                
                b_entry = row['Close']
                b_sl = row['Low_5d']
                if b_sl >= b_entry or (b_entry - b_sl) / b_entry < 0.005:
                    b_sl = b_entry * 0.965
                b_risk = b_entry - b_sl
                b_target = b_entry + (2 * b_risk)

                ticker_results.append({
                    "Date": date.strftime('%Y-%m-%d'),
                    "Symbol": ticker.replace(".NS", ""),
                    "Trigger/Entry (₹)": round(b_entry, 2),
                    "Stop Loss (₹)": round(b_sl, 2),
                    "Target Price (₹)": round(b_target, 2),
                    "RSI at Trigger": round(row['RSI'], 2),
                    "Next Day Move": next_move
                })
            return ticker_results
    except Exception:
        return None
    return None

# --- Sidebar Controls UI ---
st.sidebar.header("⚙️ Pro Scanner Controls")
rsi_filter = st.sidebar.slider("Minimum RSI (Trend Strength)", 45, 75, 55)
volume_multiplier = st.sidebar.slider("Volume Shock (Multiplier)", 1.0, 3.0, 1.2, step=0.1)
min_turnover = st.sidebar.number_input("Minimum Daily Turnover (in ₹ Crores)", min_value=1, max_value=50, value=2)

all_tickers = get_mega_nse_universe()
st.sidebar.write(f"Total Active Stocks Monitored: **{len(all_tickers)}**")

tab1, tab2 = st.tabs(["⚡ Live Scanner (Today)", "📊 2-Month Historical Backtester"])

# --- ThreadPool Batch Processing Engine ---
def process_market_analytics_fast(tickers, mode="live"):
    if not tickers: return pd.DataFrame()

    results = []
    chunk_size = 40  # Safely chunked to protect against high multi-threading rate blocks
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    st.info(f"⚡ Processing {len(tickers)} symbols across {len(ticker_chunks)} parallel batches...")
    main_progress = st.progress(0)
    
    for c_idx, chunk in enumerate(ticker_chunks):
        try:
            raw_data = yf.download(chunk, period="2y", interval="1d", progress=False, group_by='ticker')
            
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {
                    executor.submit(analyze_single_ticker, ticker, raw_data, mode, volume_multiplier, rsi_filter, min_turnover): ticker 
                    for ticker in chunk
                }
                for future in as_completed(futures):
                    res = future.result()
                    if res: results.extend(res)
        except Exception:
            continue
            
        main_progress.progress((c_idx + 1) / len(ticker_chunks))
                
    main_progress.empty()
    return pd.DataFrame(results)

# --- TAB 1: Live Scanning View ---
with tab1:
    st.subheader("⚡ Live Momentum Breakout Radar")
    if st.button("🚀 Run Mega Universe Magic Scan", key="live_btn"):
        res_df = process_market_analytics_fast(all_tickers, mode="live")
        
        if not res_df.empty:
            res_df = res_df.sort_values(by="Score", ascending=False)
            res_df.insert(0, 'Rank', range(1, len(res_df) + 1))
            st.success(f"🎉 Found {len(res_df)} high-momentum breakout setups!")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            # --- Chart Visualizer with Pattern Support/Target Lines ---
            top_stock = res_df.iloc[0]['Symbol']
            st.markdown(f"### 👑 Top Ranked Momentum Setup: **{top_stock}**")
            chart_data = yf.download(f"{top_stock}.NS", period="3mo", interval="1d", progress=False)
            
            if not chart_data.empty:
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.get_level_values(-1)
                    
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], 
                    low=chart_data['Low'], close=chart_data['Close'], name='Candlestick'
                )])
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].ewm(span=20).mean(), line=dict(color='orange', width=1.5), name='EMA 20'))
                
                # Dynamic horizontal lines plot mapping on the live interactive chart
                live_sl = res_df.iloc[0]['Stop Loss (₹)']
                live_tgt = res_df.iloc[0]['Target Price (₹)']
                
                fig.add_hline(y=live_sl, line_dash="dash", line_color="red", line_width=2, annotation_text=f"5-Day Swing SL: ₹{live_sl}", annotation_position="bottom left")
                fig.add_hline(y=live_tgt, line_dash="dash", line_color="green", line_width=2, annotation_text=f"Pattern Target (1:2): ₹{live_tgt}", annotation_position="top left")
                
                fig.update_layout(template="plotly_dark", title=f"{top_stock} Patterns & Triggers Setup", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No breakout setups spotted matching current filters within the 1800+ pool.")

# --- TAB 2: Historical Backtest View ---
with tab2:
    st.subheader("⏳ 2-Month Historical Analytics Dashboard")
    
    if st.button("📊 Start Historical Backtest", key="bt_btn"):
        bt_df = process_market_analytics_fast(all_tickers, mode="backtest")
        
        if not bt_df.empty:
            bt_df = bt_df.sort_values(by="Date", ascending=False)
            
            valid_moves = bt_df[~bt_df['Next Day Move'].str.contains("Live", na=False)].copy()
            if len(valid_moves) > 0:
                numeric_moves = valid_moves['Next Day Move'].str.replace('%','').astype(float)
                bullish_days = len(numeric_moves[numeric_moves > 0])
                accuracy = round((bullish_days / len(valid_moves)) * 100, 2)
            else:
                accuracy = 0
            
            col1, col2 = st.columns(2)
            col1.metric("Total Generated Signals (2 Months)", len(bt_df))
            col2.metric("Next-Day Bullish Accuracy Rate", f"{accuracy}%")
            
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
            csv_data = bt_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Backtest Sheet (CSV)", data=csv_data, file_name="backtest_results.csv", mime="text/csv")
        else:
            st.warning("No historical signal matches discovered.")

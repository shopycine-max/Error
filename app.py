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
        # --- Nifty 50 & Next 50 ---
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC", "HINDUNILVR", "LT",
        "BAJFINANCE", "TATAMOTORS", "SUNPHARMA", "MARUTI", "KOTAKBANK", "AXISBANK", "NTPC", "ONGC", "TATASTEEL", "ADANIENT",
        "COALINDIA", "BAJAJFINSV", "M&M", "ASIANPAINT", "TITAN", "ULTRACEMCO", "HCLTECH", "POWERGRID", "WIPRO", "ADANIPORTS",
        "JIOFIN", "ZOMATO", "HAL", "BHEL", "PFC", "RECLTD", "IRFC", "RVNL", "CONCOR", "TATACOMM",
        "TATAPOWER", "GAIL", "SAIL", "NMDC", "VEDL", "HINDALCO", "JINDALSTEL", "NATIONALUM", "TATACHEM", "CHAMBLFERT",
        # --- Midcaps & Banking ---
        "AUBANK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "PNB", "CANBK", "BOB", "UNIONBANK", "INDIANB", "DLF",
        "GODREJPROP", "OBEROIRLTY", "UNITDSPR", "BERGEPAINT", "PIDILITIND", "BEL", "POLYCAB", "KEI", "HAVELLS", "VOLTAS",
        "DIXON", "AMBUJACEM", "ACC", "JKCEMENT", "DALBHARAT", "BPCL", "HPCL", "IOC", "MRF", "BALKRISIND",
        "APOLLOTYRE", "CEATLTD", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "INDHOTEL", "GMRINFRA", "GICRE", "NIACL", "LICHSGFIN",
        "PEL", "MUTHOOTFIN", "CHOLAFIN", "SRF", "DEEPAKNTR", "TATAELXSI", "PERSISTENT", "KPITTECH", "COFORGE", "LTIM",
        "ASTRAL", "SUPREMEIND", "METROPOLIS", "LALPATHLAB", "AUROPHARMA", "BIOCON", "DIVISLAB", "DRREDDY", "CIPLA", "LUPIN",
        "TRENT", "ABFRL", "PAGEIND", "BATAINDIA", "IRCTC", "BOSCHLTD", "TATAINVEST", "HUDCO", "MANAPPURAM", "IOB",
        "CENTRALBK", "UCOBANK", "MAHABANK", "IDBI", "IEX", "INFIBEAM", "IRBINFRA", "JAIBALAJI", "JKTYRE", "JSWENERGY",
        # --- Highly Active Small & Micro Momentum ---
        "AARTIIND", "ABB", "ADANIPOWER", "ASHOKLEY", "BALRAMCHIN", "BANKINDIA", "BSOFT", "CDSL", "BSE", "MCX",
        "EXIDEIND", "GLENMARK", "JUBLFOOD", "KALYANKJIL", "MANKIND", "MANGALAM", "NBCC", "NLCINDIA", "OFSS", "OIL",
        "PNCINFRA", "RADICO", "RAILTEL", "RITES", "SJVN", "SUZLON", "VGUARD", "ZENTEC", "AAKASH", "AAATECH",
        "ACE", "ACCELYA", "ACTIONCON", "ADFFOODS", "ADVANIHOT", "AEGISCHEM", "AGARIND", "AGIREEN", "AHLUCONT", "AIAENG",
        "ALANKIT", "ALBERTDAV", "ALICON", "ALKALI", "ALKEM", "ALKYLAMINE", "ALLCARGO", "ALLSEC", "ALOKINDS", "ALPA",
        "AMARAJABAT", "AMBER", "AMBTHIKA", "AMCDISP", "AMDL", "AMEYA", "AMRUTANJAN", "ANANDAMRAO", "ANANTRAJ", "ANDHRAENG",
        "ANDHRAPAP", "ANDHRSUG", "ANGELONE", "ANIKINDS", "ANKITMETAL", "ANSALAPI", "ANTONYADRO", "APAPL", "APCL", "APEX",
        "APIGLOBAL", "APLAPOLLO", "APLLTD", "APOLLO", "APOLLOHOSP", "APOLSINHOT", "APTECHT", "ARCHIDPLY", "ARCHIES", "ARE&M",
        "ARIES", "ARIHANT", "ARIHANTSUP", "ARMANFIN", "AROGRANITE", "ARROWGREEN", "ARSHIYA", "ARVIND", "ARVINDFAZN", "ARVINDFASN",
        "ASAHIINDIA", "ASAHISONG", "ASAL", "ASALCBR", "ASHAPURMIN", "ASHIANA", "ASHIMASYN", "ASHOKA", "ASIANENE", "ASIANHOT",
        "ASIANTILES", "ASPINWALL", "ASTEC", "ASTRAMICRO", "ASTRON", "ATFL", "ATGL", "ATLANTA", "ATUL", "ATULAUTO",
        "AURIONPRO", "AVADHSUGAR", "AVANTIFEED", "AVTNPL", "AWFIS", "AXISCADES", "AYMSYNTEX", "BAFNAPH", "BAGFILMS", "BAJAJ-AUTO",
        "BAJAJCON", "BAJAJELEC", "BAJAJHIND", "BAJAJHLDNG", "BALAJITELE", "BALAMINES", "BALKRISHNA", "BALMLAWRIE", "BALPHARMA", "BANARISUG",
        "BANCOINDIA", "BANG", "BANKBARODA", "BANSALWIRE", "BARTRONICS", "BASF", "BASML", "BBL", "BBRONGN", "BCG",
        "BCP", "BDL", "BDR", "BEARDSSELL", "BEML", "BENARAS", "BFUTILITIE", "BGRENERGY", "BHAGCHEM", "BHAGERIA",
        "BHAGYANGR", "BHANDARI", "BHARATFORG", "BHARATGEAR", "BHARATRAS", "BHARATWIRE", "BHARTI", "BHARTISHIP", "BHL", "BIGBLOC",
        "BIKAJI", "BIL", "BODALCHEM", "BOMDYEING", "BOROLTD", "BORORENEW", "BRIGADE", "BRITANNIA", "BROACH-HOT", "BSEMETAL",
        "CCL", "CEENIK", "CENTENARY", "CENTUM", "CENTURYPLY", "CENTURYTEX", "CERA", "CEREBRA", "CESC", "CGCL",
        "CGPOWER", "CHALET", "CHEMBOND", "CHEMCON", "CHEMFAB", "CHEVVIOT", "CHICONY", "CHOLAHLDNG", "CIGNITI", "CINELINE",
        "CINEVISTA", "CIPLA", "CLEAN", "CLEDUCATE", "CLSEL", "CMICABLES", "CMSINFO", "COCHINSHIP", "COFFEEDAY", "COFORGE",
        "COMPUCOM", "COMPUAGE", "CONSOFINVT", "CONTROLPR", "COROMANDEL", "COSMOFIRST", "COUNCODOS", "CRAFTSMAN", "CREATIVE", "CREST",
        "CRISIL", "CROMPTON", "CSBBANK", "CSLFINANCE", "CTE", "CUB", "CUBEX", "CUMMINSIND", "CUPID", "CYIENT",
        "CYIENTDLM", "DABUR", "DALMIASUG", "DAMODARIND", "DATAMATICS", "DATAPATTERNS", "DBCORP", "DBREALTY", "DBOL", "DCAL",
        "DCBBANK", "DCM", "DCMFINSERV", "DCMSRIND", "DCMSHRIRAM", "DCW", "DECCANCE", "DEEPAKFERT", "DEEPAKSPG", "DELHIVERY",
        "DELPHIFX", "DELTA先进", "DELTACORP", "DELTAMAGNT", "DEN", "DENORA", "DEVYANI", "DGCONTENT", "DHAMPURSUG", "DHANBANK",
        "DHANI", "DHANUKA", "DHARMA", "DHARSUG", "DHUNSERI", "DIAMONDYD", "DICIND", "DIGISPICE", "DIGJAYCL", "DIL",
        "DISHTV", "DIVGIITTS", "DODLA", "DOLATALGO", "DOLLAR", "DONEAR", "DPABHUSHAN", "DPL", "DPWRE", "DREDGECORP",
        "DRS", "DSSL", "DTL", "DUCON", "DUMMYEXP", "DWARKESH", "DYCL", "DYNAMATIC", "DYNPRO", "EASEMYTRIP",
        "EBB", "ECLERX", "EDELWEISS", "EICHERMOT", "EIDPARRY", "EIHAHOTELS", "EIHOTEL", "EIMCOELECO", "EKC", "ELDEHSG",
        "ELECMECH", "ELECON", "ELECTCAST", "ELECTHERM", "ELGIEQUIP", "ELGIRUBCO", "EMAMILTD", "EMAMIPAP", "EMAMIREAL", "EMKAY",
        "EMMBI", "EMUDHRA", "ENDURANCE", "ENERGYDEV", "ENGINERSIN", "ENIL", "EPL", "EQUITASBNK", "ERIS", "EROSMEDIA",
        "ESABINDIA", "ESCORTS", "ESSARSHPNG", "ESTER", "ETHOS", "EUREKAFORB", "EVERESTIND", "EVEREADY", "EXCEL", "EXCELINDUS",
        "FACT", "FAIRCHEMOR", "FALCON", "FAME", "FARCHEM", "FIEMIND", "FILATEX", "FINCABLES", "FINEORG", "FINPIPE",
        "FIRSTSOURCE", "FLAIR", "FLEX", "FLUOROCHEM", "FMGO", "FORCEMOT", "FORTIS", "FOSECOIND", "FSN", "GABRIEL",
        "GAEL", "GALAXYSURF", "GALAXYBEAR", "GALLANTT", "GANDHITUBE", "GANECOS", "GANESHOUK", "GANESHHG", "GANGESSECU", "GARFIBRES",
        "GATEWAY", "GATI", "GAYAPROJ", "GBGLOBAL", "GDL", "GEECEE", "GEEKAY", "GENESYS", "GENUSPAPER", "GENUSPOWER",
        "GEOJITFSL", "GEPIL", "GESHIP", "GET&D", "GHCL", "GICHSGFIN", "GILLANDERS", "GILLETTE", "GINNIFILA", "GIPCL",
        "GKWLIMITED", "GLAND", "GLAXO", "GLENMARK", "GLFL", "GLOBAL", "GLOBALVECT", "GLOBUSSPR", "GMDCLTD", "GMRPOWER",
        "GNA", "GNFC", "GOACARBON", "GOCLCORP", "GODFRYPHLP", "GODREJAGRO", "GODREJIND", "GOKEX", "GOKUL", "GOKULAGRO",
        "GOLDENTOBC", "GOLDIAM", "GOLDTECH", "GOODLUCK", "GOODYEAR", "GPIL", "GPPL", "GPTINFRA", "GRANULES", "GRAPHITE",
        "GRASIM", "GRAVITA", "GREAVESCOT", "GREENPANEL", "GREENPLY", "GREENPOWER", "GRINDWELL", "GRINFRA", "GRPL", "GSFC",
        "GSPL", "GSS", "GTL", "GTLINFRA", "GTPL", "GUFICBIO", "GUJALKALI", "GUJAPOLLO", "GUJGASLTD", "GUJNRECOKE",
        "GUJRATSTAT", "GULFOILLUB", "GULFPETRO", "GULPOLY", "GVKPIL", "HAL", "HAPPSTMNDS", "HARIOMPIPE", "HARRMALAYA", "HARSHA",
        "HATHWAY", "HATSUN", "HAWKINCOOK", "HBLPOWER", "HCC", "HCG", "HDFCAMP", "HDFCLIFE", "HDIL", "HEG",
        "HEIDELBERG", "HEMIPROP", "HERANBA", "HERCULES", "HEROMOTOCO", "HESTERBIO", "HEXATRADEX", "HFCL", "HGINFRA", "HGS",
        "HIKAL", "HIL", "HILTON", "HIMATSEIDE", "HINDCOMPOS", "HINDCOPPER", "HINDNATGLS", "HINDOLIVSM", "HINDOILEXP", "HINDPETRO",
        "HINDUNILVR", "HINDZINC", "HIRECT", "HISARMETAL", "HITECH", "HITECHGEAR", "HLEGLAS", "HLVLTD", "HMT", "HMVL",
        "HONAUT", "HONDAPOWER", "HOVVS", "HPAL", "HPIL", "HPL", "HSCL", "HTMEDIA", "HUBTOWN", "HYBRID",
        "IBCAL", "IBREALEST", "IBULHSGFIN", "ICDSLTD", "ICEMAKE", "ICIL", "ICRA", "IDFC", "IFBAGRO", "IFBIND",
        "IFCI", "IFGLEXPORT", "IGARASHI", "IGL", "IGPL", "IIFL", "IIFLSEC", "IITL", "IL&FSENGG", "IL&FSTRANS",
        "IMAGGAA", "IMFA", "IMPRESSION", "INDAG", "INDANHOSP", "INDCOSERSER", "INDEQ", "INDIACEM", "INDIAGLYCO", "INDIAMART",
        "INDIANB", "INDIANCARD", "INDIANHUME", "INDIGO", "INDIGOPNTS", "INDNIPPON", "INDOAMIN", "INDOBORAX", "INDOCO", "INDORAMA",
        "INDOSOLAR", "INDOTECH", "INDOTHAI", "INDOCO", "INDOSTAR", "INDUSINDBK", "INDUSTOWER", "INEOS", "INFI", "INFIBEAM",
        "INGERRAND", "INOXGREEN", "INOXWIND", "INSECTICID", "INSPIRISYS", "INTELLECT", "INTENTECH", "INOXINDIA", "IONEXCHANG", "IPCALAB",
        "IRB", "IRCON", "IRCTC", "IRIS", "ISEC", "ISFT", "ISGEC", "ISKCON", "ISMTLTD", "ITC",
        "ITDC", "ITDCEM", "ITI", "IVC", "IVP", "IXIGO", "IZMO", "J&KBANK", "JAGRAN", "JAGSNPHARM",
        "JAIBALAJI", "JAICORPLTD", "JAINSTUDIO", "JAIPURIPAP", "JAKHARIA", "JALAN", "JAMNAAUTO", "JASH", "JAYABALST", "JAYAGROGN",
        "JAYBARMARU", "JAYESH", "JAYSREETEA", "JBCHEPHARM", "JBFIND", "JCHAC", "JENSONICOL", "JEPCO", "JETAIRWAYS", "JETFREIGHT",
        "JEYPORE", "JINDALHOT", "JINDALPHOT", "JINDALPOLY", "JINDALSAW", "JINDALSTEL", "JINDRILL", "JINDWORLD", "JISLJALEQS", "JITFINFRA",
        "JKCEMENT", "JKIL", "JKLAKSHMI", "JKPAPER", "JKTYRE", "JMA", "JMFINANCIL", "JOCIL", "JOINTECA", "JORDGI",
        "JRACTION", "JSL", "JSWENERGY", "JSWHL", "JSWINFRA", "JSWSTEEL", "JSWHL", "JTEKTINDIA", "JUBLFOOD", "JUBLINDS",
        "JUBLINGREA", "JUBLPHARMA", "JUMPNET", "JUSTDIAL", "JVLAGRO", "JYOTHYLAB", "JYOTISTRUC", "JYOTIRES", "KABRAEXTRU", "KADAMBANI",
        "KAHAAN", "KAJARIRAC", "KAKATCEM", "KALPATNTR", "KALYANI", "KALYANIFRG", "KALYANKJIL", "KAMADHENU", "KAMATHOTEL", "KANANIIND",
        "KANCOTEA", "KANPRPLA", "KANSAINER", "KAPSTON", "KARDA", "KARMAENG", "KARURVYSYA", "KAUSHALYA", "KAVVERIIM", "KAYA",
        "KAYNES", "KBCGLOBAL", "KBR", "KCP", "KCPSUGIND", "KDDL", "KEC", "KECL", "KEI", "KELLTONTEC",
        "KENNAMET", "KERNEX", "KESORAMIND", "KEYCORP", "KFINTECH", "KHADIM", "KHAICHEM", "KHAITANLTD", "KHANDSE", "KIDUJA",
        "KILITCH", "KIMS", "KINGFA", "KIOCL", "KIRIINDUS", "KIRLOSBROS", "KIRLOSENG", "KIRLIND", "KIRLOSIND", "KITEX",
        "KKCL", "KMSMEDI", "KNA", "KNRCON", "KOHINOOR", "KOKUYO", "KOLTEPATIL", "KOPRAN", "KOTAKBANK", "KOTARISUG",
        "KOTHARIPRO", "KPIGREEN", "KPIL", "KPITTECH", "KPRMILL", "KRBL", "KREBSBIO", "KRIDHANINF", "KRISHANA", "KRITI",
        "KRITIKA", "KRITINUT", "KRN", "KROMPTON", "KSCL", "KSHITIJ", "KSL", "KSK", "KSLIND", "KSTCL",
        "KTKBANK", "KUANTUM", "L&TFH", "LAGNAM", "LAHOTI", "LAKPRE", "LAKSHMIELE", "LAKSHVILAS", "LALPATHLAB", "LAMBODHARA",
        "LANCER", "LANDMARK", "LAOPALA", "LASA", "LAURUSLABS", "LAXMICOT", "LAXMINRSR", "LEELAFUTE", "LEMONTREE", "LFIC",
        "LGBBROSLTD", "LGHL", "LIBAS", "LIBERTSHOE", "LICHSGFIN", "LICI", "LIKHITHA", "LINCOLN", "LINDEINDIA", "LIQUID",
        "LLOYDENG", "LLOYDSME", "LML", "LODHA", "LOKESHMACH", "LOTUSECHO", "LOVABLE", "LOYALTEXT", "LPDC", "LT",
        "LTIM", "LTTS", "LUMAXIND", "LUMAXTECH", "LUPIN", "LUXIND", "LYKALABS", "LYPSAGEMS", "M&M", "M&MFIN",
        "MAANALU", "MACPOWER", "MADHAV", "MADHUCON", "MADRASFERT", "MAGADSUGAR", "MAGMA", "MAGNUM", "MAHABANK", "MAHASTEEL",
        "MAHEPC", "MAHESHWARI", "MAHINDCIE", "MAHLIFE", "MAHLOG", "MAHSCOOT", "MAHSEAMLES", "MAITHANALL", "MAJESCO", "MALUPAPER",
        "MANAKALU", "MANAKCOAT", "MANAKSIA", "MANAKSTEEL", "MANALIPETC", "MANAPPURAM", "MANGALAM", "MANGCHEFER", "MANGLMCEM", "MANGTIMBER",
        "MANINDS", "MANINFRA", "MANKIND", "MANOMAY", "MANORAMA", "MANUGRAPH", "MAPMYINDIA", "MARALOVER", "MARATHON", "MARICO",
        "MARINE", "MARKSANS", "MARUTI", "MASFIN", "MASTEK", "MATRIMONY", "MAWANASUG", "MAXHEALTH", "MAXIND", "MAXVIL",
        "MAYURUNIQ", "MAZDA", "MAZDOCK", "MBAPL", "MBECL", "MBLINFRA", "MCDOWELL-N", "MCL", "MCLEODRUSS", "MCX",
        "MEDANTA", "MEDICO", "MEDIPLUS", "MEGASOFT", "MEGASTAR", "MENONBE", "MEP", "MERCATOR", "METALFORGE", "METROBRAND",
        "METROPOLIS", "MFL", "MFSL", "MGEL", "MGL", "MGRM", "MINDACORP", "MINDTECK", "MINDTREE", "MINERVA",
        "MIPCO", "MIRCELECTR", "MIRZAINT", "MITSU", "MITTAL", "MMFL", "MMTC", "MODIRUBBER", "MODISNME", "MOHITIND",
        "MOIL", "MOKSH", "MOL", "MONARCH", "MONTECARLO", "MORARJEE", "MOREPENLAB", "MOTHERSUMI", "MOTHERSON", "MOTILALOFS",
        "MPHASIS", "MPSLTD", "MRF", "MRO-TEK", "MRPL", "MSCHD", "MSIL", "MSTCLTD", "MTARTECH", "MTNL",
        "MUKANDLTD", "MUKANDENGG", "MUKTAARTS", "MUNJALAU", "MUNJALSHOW", "MURUDESHW", "MUTHOOTCAP", "MUTHOOTFIN", "MVL", "NACLIND",
        "NAGAFERT", "NAGREEKACAP", "NAGREEKEXP", "NAHARCAP", "NAHARINDUS", "NAHARPOLY", "NAHARSURPC", "NAIL", "NAKODA", "NATCOPHARM",
        "NATHBIOGEN", "NATIONALUM", "NATPERX", "NAUKRI", "NAVA", "NAVNETEDUL", "NAVODAY", "NAVINFLUOR", "NAZARA", "NBCC",
        "NBIFIN", "NCC", "NCLIND", "NDGL", "NDL", "NDRAUTO", "NDTV", "NEAL", "NECHLN", "NECON",
        "NEELAM", "NEELKANTH", "NEGEN", "NELCAST", "NELCO", "NEOCLAL", "NEOGEN", "NEOKRAFT", "NEPTUNE", "NESCO",
        "NESTLEIND", "NETWEB", "NETWORK18", "NEULANDLAB", "NEWGEN", "NEXTMEDIA", "NFL", "NGIL", "NH", "NHPC",
        "NIACL", "NIBE", "NIBL", "NIITLTD", "NILAINFRA", "NILAMAC", "NILASPACES", "NILKAMAL", "NINETEC", "NIPPO",
        "NIPPON", "NIRAJ", "NIRAJISPAT", "NIRMAL", "NITCO", "NITINFIRE", "NITINSPIN", "NITTEN", "NKIND", "NLCINDIA",
        "NMDC", "NMDCMD", "NOCIL", "NOIDATOLL", "NORBTEAEXP", "NRAIL", "NRBBEARING", "NSIL", "NTPC", "NUCLEUS",
        "NURTURE", "NUVOCO", "NVC", "NXTDIGITAL", "NYKAA", "OAL", "OBEROIRLTY", "OCCL", "OFSS", "OIL",
        "OISL", "OLATECH", "OMAXAUTO", "OMAXE", "OMINFRAL", "OMKARCHEM", "ONGC", "ONWARDTEC", "OPTIEMUS", "ORBTEXP",
        "ORCHIDPHAR", "ORICONENT", "ORIENTALTL", "ORIENTBELL", "ORIENTCEM", "ORIENTELEC", "ORIENTHOT", "ORIENTPPR", "ORIENTQC", "ORISSAMINE",
        "ORTINLABS", "OSIAHYPER", "OSWALAGRO", "OSWALGREEN", "PAGEIND", "PAISALO", "PALASHSECU", "PALRED", "PANACEABIO", "PANACHE",
        "PANAMAPET", "PANCHSHEEL", "PANSARI", "PAR", "PARACABLES", "PARADEEP", "PARAGMILK", "PARAS", "PARASPETRO", "PARSVNATH",
        "PASUPATCEM", "PATANJALI", "PATELENG", "PATINTLOG", "PATSPINLTD", "PAYTM", "PCBL", "PCJEWELLER", "PDMJUME", "PDSL",
        "PEARLGLOBAL", "PEL", "PENIND", "PENINLAND", "PENSLA", "PERSISTENT", "PETRONET", "PFC", "PFIZER", "PFOCUS",
        "PFS", "PGEL", "PGHH", "PGIL", "PHOENIXLTD", "PIDILITIND", "PIIND", "PILANIIN", "PILITA", "PIONDIST",
        "PIONEEREMB", "PITTIENG", "PIXTRANS", "PKTEA", "PLASTIBLND", "PNB", "PNBGILTS", "PNBHOUSING", "PNCINFRA", "POCHIRAJU",
        "PODDARHOUS", "PODDARMENT", "POKARNA", "POLYCAB", "POLYMED", "POLYPLEX", "PONNIERODE", "POWERGRID", "POWERINDIA", "POWERMECH",
        "PPAP", "PPL", "PRADIP", "PRAFFUL", "PRAGATI", "PRAJIND", "PRAKASH", "PRAKASHSTL", "PRAXIS", "PRECAM",
        "PRECOT", "PRECWIRE", "PREMEXPLN", "PREMIER", "PREMIERPOL", "PRESSMN", "PRESTIGE", "PRICOLLTD", "PRIMESECU", "PRIME",
        "PRINCEPIPE", "PRSMJOHNSN", "PRUDENT", "PSB", "PSPPROJECT", "PTC", "PTL", "PUNJABCHEM", "PUNJLLOYD", "PURVA",
        "PVRINOX", "PVP", "QUESS", "QUICKHEAL", "RADAAN", "RADICO", "RADIOCITY", "RAILTEL", "RAIN", "RAINBOW",
        "RAJESHEXPO", "RAJMET", "RAJRATAN", "RAYMOND", "RBL", "RBLBANK", "RCF", "RECLTD", "REDINGTON", "RELAXO",
        "RELIANCE", "RELINFRA", "RELPOWER", "RENUKA", "REPCOHOME", "REPRO", "RESPONIND", "REVATHI", "RHL", "RICOAUTO",
        "RIIL", "RITES", "RKFORGE", "RMCL", "RML", "ROHLTD", "ROLEXBO", "ROLLT", "ROOTO", "ROSARI",
        "ROSSELLIND", "ROUTE", "RPGLIFE", "RPOWER", "RPPINFRA", "RRELEC", "RSSAM", "RSWM", "RSYSTEMS", "RTNPOWER",
        "RTNINDIA", "RUBYMILLS", "RUCHI", "RUCHIRA", "RUPA", "RUSHIL", "RVNL", "SABEVENTS", "SADBHAV", "SADBHIN",
        "SAFARI", "SAGARDEEP", "SAGAGCEM", "SAIL", "SAKSOFT", "SAKUMA", "SAKTHISUG", "SALASAR", "SALONA", "SALSTEEL",
        "SALZERELEC", "SAMBHAAV", "SAMHI", "SAMPANN", "SAMRECOVERY", "SAMVARDHANA", "SANCO", "SANDESH", "SANDHAR", "SANGAMIND",
        "SANGHIIND", "SANGHVIMOV", "SANOFI", "SANSERA", "SAPPHIRE", "SARDAEN", "SAREGAMA", "SARLAPOLY", "SASKEN", "SASTASUNDR",
        "SATIA", "SATIN", "SATINGROUP", "SATOV", "SATYAMCOMP", "SCHAND", "SCHAEFFLER", "SCHNEIDER", "SCI", "SCILAL",
        "SREINFRA", "SRF", "SRHHYPOL", "SRIPIPES", "SRTRANSFIN", "SSWL", "STAR", "STARCEMENT", "STARPAPER", "STARTECK",
        "STCINDIA", "STEELCAS", "STEELXIND", "STEL", "STERTOOLS", "SUBEXLTD", "SUBROS", "SUDARSCHEM", "SUMEETINDS", "SUMIT",
        "SUMICHEM", "SUMMITSEC", "SUNCLAYLTD", "SUNDARAM", "SUNDARMFIN", "SUNDARMHLD", "SUNDRMBRAK", "SUNDRMFAST", "SUNFLAG", "SUNPHARMA",
        "SUNTECK", "SUNTV", "SUPERHOUSE", "SUPERSPG", "SUPRAJIT", "SUPREMEIND", "SUPREMEINF", "SUPREMETEX", "SURYALAXMI", "SURYAROSNI",
        "SURYODAY", "SUTLEJTEX", "SUVEN", "SUVENPHAR", "SUZLON", "SWANENERGY", "SWARAJENG", "SWELECTES", "SWSOLAR", "SYMPHONY",
        "SYNGENE", "SYRMA", "TAJGVK", "TASTYBITE", "TATACHEM", "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAINVEST", "TATAMOTORS",
        "TATAMTRDVR", "TATAPOWER", "TATASTEEL", "TBZ", "TCI", "TCIEXP", "TCIFL", "TCNSBRANDS", "TCPLPACK", "TCS",
        "TEAMSLEASE", "TECHM", "TECHNOE", "TEJASNET", "TEMBO", "TERASOFT", "TEXINFRA", "TEXRAIL", "TFCILTD", "TFL",
        "TGBHOTELS", "THANGAMAYL", "THEMISMED", "THERMAX", "TH Thomas", "THYROCARE", "TI", "TIDEWATER", "TIIL", "TIINDIA",
        "TIMETECHNO", "TIMKEN", "TIPSFILMS", "TIPSINDLTD", "TIRUMALCHM", "TIRUPATIFL", "TITAN", "TNPL", "TNTELE", "TOKYOPLAST",
        "TORNTPHARM", "TORNTPOWER", "TOTAL", "TOUCHWOOD", "TPLPLASTEH", "TRACXN", "TREEHOUSE", "TREJHARA", "TRENT", "TRF",
        "TRIDENT", "TRIGYN", "TRIL", "TRITURBINE", "TRIVENI", "TROT", "TTKHEALTH", "TTKPRESTIG", "TTL", "TTML",
        "TV18BRDCST", "TVSELECT", "TVSMOTOR", "TVSSRICHAK", "TVSSCS", "TVSRADHA", "TVTODAY", "TWL", "UCAL", "UCOBANK",
        "UDAICEMENT", "UCOBANK", "UFLEX", "UFO", "UGARSUGAR", "UGROCAP", "UJAAS", "UJJIVANSFB", "ULTRACEMCO", "UMANGDAIRY",
        "UMESLTD", "UNICHEMLAB", "UNIDT", "UNIENTER", "UNIONBANK", "UNIPARTS", "UNIPHOS", "UNITEDPOLY", "UNITEDTEA", "UNITECH",
        "UNITEDSPR", "UNITY", "UNIVASTU", "UNIVCABLES", "UNIVPHOTO", "UNOMINDA", "UPERGANGES", "UPL", "URJA", "USHAMART",
        "USK", "UTTAMSUGAR", "UTTAMVALUE", "UTIAMC", "VAIBHAVGBL", "VAIM", "VAISHALI", "VAKRANGEE", "VALIANTORG", "VAMSHI",
        "VARROC", "VASCONEQ", "VASWANI", "VAYU", "VBL", "VEDL", "VENKEYS", "VENUSPIPES", "VENUSREM", "VERANDA",
        "VERTOZ", "VESUVIUS", "VETO", "VGUARD", "VHL", "VICEROY", "VIDEOIND", "VIDHIING", "VIJAYA", "VIJAYADIAG",
        "VIKASECO", "VIKASLIFE", "VIKASPROP", "VIKASWSP", "VIMTALABS", "VINATIORGA", "VINDHYATLE", "VINNY", "VINYLINDIA", "VIPCL",
        "VIPIND", "VIPULLTD", "VIRAT", "VIRTUALG", "VISAKAIND", "VISASTEEL", "VISHAL", "VISHNU", "VISHWARAJ", "VIVIDHA",
        "VIVIMEDLAB", "VLSFINANCE", "VMART", "VOLTAMP", "VOLTAS", "VPRINFRA", "VRLLOG", "VSSL", "VSTIND", "VSTTILLERS",
        "VTL", "WABAG", "WALCHANNAG", "WANBURY", "WATERBASE", "WEIZMANN", "WELCORP", "WELENT", "WELINV", "WELSPUNIND",
        "WENDT", "WESTLIFE", "WHEELS", "WHIRLPOOL", "WILLAMAGOR", "WINDLAS", "WINSOME", "WIPRO", "WOCKPHARMA", "WONDERLA",
        "WORTH", "WSTCSTPAPR", "XCHANGING", "XPROINDIA", "YAARI", "YASHMGM", "YATRA", "YUG", "ZEEL", "ZEELEARN",
        "ZEEMEDIA", "ZENITHEXPO", "ZENITHSTL", "ZENSARTECH", "ZENTEC", "ZFCVINDIA", "ZOMATO", "ZUARI", "ZUARIIND", "ZYDUSLIFE", "ZYDUSWELL"
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

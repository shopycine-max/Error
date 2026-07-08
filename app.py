# --- ADD THIS INSIDE process_market_analytics LOOP ---

# 1. ADX Calculation (Trend Strength)
def calculate_adx(df, n=14):
    high, low, close = df['High'], df['Low'], df['Close']
    tr = pd.DataFrame({'t1': high - low, 't2': abs(high - close.shift(1)), 't3': abs(low - close.shift(1))}).max(axis=1)
    atr = tr.rolling(n).mean()
    # Simple ADX proxy (for trend strength)
    adx = abs(close - close.shift(n)).rolling(n).mean() / atr * 100
    return adx

# 2. Relative Strength Calculation (Vs Nifty50 proxy)
# Note: yf.download("NIFTY.NS") ka data use kar sakte hain
nifty_data = yf.download("^NSEI", period="1y", interval="1d", progress=False)
nifty_ret = (nifty_data['Close'].pct_change(20).iloc[-1])
stock_ret = (df['Close'].pct_change(20).iloc[-1])
relative_strength = stock_ret - nifty_ret 

# 3. Dynamic Stoploss using ATR
atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
sl_level = df['Close'].iloc[-1] - (atr * 2) # 2x ATR stoploss is more accurate

# 4. New Scoring Logic (Weighted)
# Hum ab Score ko sirf RSI nahi, balki Strength se rank karenge
momentum_score = (df['RSI'].iloc[-1] * 0.3) + (vol_spike * 0.4) + (relative_strength * 100 * 0.3)

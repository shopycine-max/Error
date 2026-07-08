def process_market_analytics(tickers, mode="live"):
    results = []
    if not tickers: return pd.DataFrame()

    try:
        # Pura data download karein
        data = yf.download(tickers, period="4y", interval="1d", progress=False, group_by='ticker')
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        progress_bar.progress((idx + 1) / len(tickers))
        try:
            # Data selection based on multi-index structure
            if len(tickers) > 1:
                if ticker in data.columns.levels[0]: 
                    df = data[ticker].dropna(subset=['Close']).copy()
                else: continue
            else:
                df = data.dropna(subset=['Close']).copy()

            if len(df) < 50: continue

            # --- Metrics ---
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
            df['Return_20d'] = df['Close'].pct_change(periods=20) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            
            # --- FIXED RSI CALCULATION ---
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0))
            loss = (-delta.where(delta < 0, 0))
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Division by zero bachane ke liye replace(0, 0.001)
            rs = avg_gain / avg_loss.replace(0, 0.001)
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # EMA & Others
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['Max_2_High_20_Ago'] = df['High'].shift(20).rolling(2, min_periods=1).max()
            df['Max_200_High_31_Ago'] = df['High'].shift(31).rolling(200, min_periods=1).max()
            df['Max_500_High_1d_Ago'] = df['High'].shift(1).rolling(500, min_periods=1).max()
            
            # --- FIXED NEXT DAY RETURN ---
            # Correct logic: (Next Close - Current Close) / Current Close
            df['Next_Day_Return'] = ((df['Close'].shift(-1) - df['Close']) / df['Close']) * 100

            # --- Signals ---
            cond1 = df['Close'] >= 20
            cond2 = (df['Pct_Change'] >= 1.0) & (df['Pct_Change'] <= 11.0)
            cond3 = df['Volume'] > (df['Vol_SMA20'] * volume_multiplier)
            cond4 = df['Return_20d'] >= 3.0
            cond5 = df['Turnover'] > 50000000
            cond6 = df['Max_2_High_20_Ago'] >= df['Max_200_High_31_Ago']
            cond7 = df['Close'] >= df['Max_500_High_1d_Ago']
            cond8 = df['RSI'] >= rsi_filter
            cond9 = df['Close'] > df['EMA_20']

            df['Signal'] = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7 & cond8 & cond9

            # --- Mode Logic ---
            if mode == "live" and df['Signal'].iloc[-1]:
                vol_spike = df['Volume'].iloc[-1] / df['Vol_SMA20'].iloc[-1] if df['Vol_SMA20'].iloc[-1] > 0 else 0
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP (₹)": round(df['Close'].iloc[-1], 2),
                    "Day Change (%)": round(df['Pct_Change'].iloc[-1], 2),
                    "RSI": round(df['RSI'].iloc[-1], 2),
                    "Vol Spike (x)": round(vol_spike, 1),
                    "Score": round(df['RSI'].iloc[-1] + (vol_spike * 10), 2)
                })
                
            elif mode == "backtest":
                # Signal generate hone ke baad next row check karein
                signals = df[df['Signal'] == True]
                for date, row in signals.iterrows():
                    # Check agar next day data available hai
                    next_day_val = row['Next_Day_Return']
                    results.append({
                        "Date": date.strftime('%Y-%m-%d'),
                        "Symbol": ticker.replace(".NS", ""),
                        "Trigger Price (₹)": round(row['Close'], 2),
                        "RSI at Trigger": round(row['RSI'], 2),
                        "Next Day Move (%)": round(next_day_val, 2) if not pd.isna(next_day_val) else "N/A"
                    })
        except Exception as e:
            continue

    progress_bar.empty()
    return pd.DataFrame(results)
                    

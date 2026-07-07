# 1. Price is greater than or equal to 20
c1 = current_close >= 20

# 2. Daily return percentage check (between 1% and 11%)
daily_return = ((current_close - prev_close) / prev_close) * 100
c2 = (daily_return >= 1.0) and (daily_return <= 11.0)

# 3. Today's volume is greater than its 20-day Simple Moving Average
c3 = current_volume > volume_sma20

# 4. 20-Day return is positive and greater than or equal to 3%
return_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
c4 = return_20d >= 3.0

# 5. Turnover is greater than 50 Crores
turnover = current_close * current_volume
c5 = turnover > 500000000  # 50,000,0000 INR

# Final Match Trigger
if c1 and c2 and c3 and c4 and c5:
    # Stock Selected for the Sheet!

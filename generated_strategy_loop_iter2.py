# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
trading_value = data.get('price:成交金額')

# 2. Calculate factors

# Factor 1: Price Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume Change (current volume vs. 60-day average)
avg_volume_60d = volume.rolling(60).mean()
volume_factor = (volume / avg_volume_60d).shift(1)

# Factor 3: Revenue Growth (YoY)
# Align monthly revenue data to daily close prices by forward filling
revenue_yoy_daily = revenue_yoy.ffill().shift(1)

# Factor 4: ROE (Return on Equity)
# Align quarterly ROE data to daily close prices by forward filling
roe_daily = roe.ffill().shift(1)

# 3. Combine factors
# Give more weight to momentum and fundamental factors
combined_factor = (momentum * 0.4) + (volume_factor * 0.2) + (revenue_yoy_daily * 0.2) + (roe_daily * 0.2)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be above 10 TWD
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and select the top 10 stocks based on the combined factor
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Price Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume Surge (current volume vs. 60-day average)
avg_volume_60d = volume.rolling(60).mean().shift(1)
volume_surge = (volume / avg_volume_60d).shift(1)

# Factor 3: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth = revenue_yoy.shift(1)

# Factor 4: Return on Equity (ROE)
# Shift ROE by 1 to avoid look-ahead bias
roe_factor = roe.shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming relative scales are somewhat compatible or we want to emphasize certain factors.
# We'll give more weight to momentum and revenue growth.
combined_factor = (momentum * 0.4) + (volume_surge * 0.2) + (revenue_growth * 0.3) + (roe_factor * 0.1)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be greater than 50 million TWD
avg_trading_value_20d = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value_20d > 50_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 10 stocks
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
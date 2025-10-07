# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
pb_ratio = data.get('fundamental_features:股價淨值比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume strength (current volume vs. 60-day average)
avg_volume = volume.rolling(60).mean()
volume_strength = (volume / avg_volume).shift(1)

# Factor 3: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 4: Value (P/B ratio, lower is better)
# Invert P/B ratio so higher values indicate better value
value_factor = (1 / pb_ratio).shift(1)

# 3. Combine factors
# Normalize factors to a 0-1 range (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming relative scales are somewhat balanced or we want to emphasize certain factors.
# We'll give more weight to momentum and revenue growth.
combined_factor = (momentum * 0.4 + 
                   volume_strength * 0.2 + 
                   revenue_growth_factor * 0.3 + 
                   value_factor * 0.1)

# 4. Apply filters
# Filter 1: Liquidity filter (average daily trading value over 20 days > 50 million TWD)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter (stock price > 10 TWD to avoid penny stocks)
price_filter = close.shift(1) > 10

# Combine filters
overall_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[overall_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
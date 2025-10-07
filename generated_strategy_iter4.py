# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors
# Momentum factor (20-day returns)
momentum = close.pct_change(20).shift(1)

# ROE factor (shifted by 90 days to account for quarterly reporting lag)
# Assuming ROE is reported quarterly, shifting by 90 days (approx 3 months)
roe_factor = roe.shift(90)

# Revenue YoY growth factor
revenue_growth_factor = revenue_yoy.shift(1)

# Foreign investor buying strength
foreign_strength_factor = foreign_strength.shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining different scales)
# For simplicity, we'll combine directly, assuming relative ranks are what matter for is_largest

# Combine momentum and fundamental strength (ROE, Revenue Growth) and foreign interest
# Higher momentum, higher ROE, higher revenue growth, and stronger foreign buying are preferred
combined_factor = momentum * 0.4 + roe_factor * 0.3 + revenue_growth_factor * 0.2 + foreign_strength_factor * 0.1

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be greater than 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Stock price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Volume filter: Average daily volume over the last 20 days must be greater than 100,000 shares
volume_filter = volume.rolling(20).mean().shift(1) > 100_000

# Combine all filters
total_filter = liquidity_filter & price_filter & volume_filter

# 5. Select stocks
# Apply filters and then select the top 10 stocks based on the combined factor
position = combined_factor[total_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
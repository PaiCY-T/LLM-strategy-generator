# Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')

# Calculate momentum factor
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.shift(1)

# Calculate volume surge factor
avg_volume_60d = volume.rolling(60).mean()
volume_surge = (volume / avg_volume_60d).shift(1)

# Calculate foreign institutional strength factor
foreign_factor = foreign_strength.rolling(10).mean().shift(1)

# Calculate revenue growth factor
revenue_factor = revenue_yoy.rolling(3).mean().shift(1)

# Combine factors with weights
combined_factor = (momentum_factor * 0.3 +
                  volume_surge * 0.2 +
                  foreign_factor * 0.3 +
                  revenue_factor * 0.2)

# Apply liquidity filter
liquidity_filter = trading_value.rolling(20).mean() > 100_000_000

# Apply additional filters
price_filter = close > 20  # Avoid penny stocks
volume_filter = volume.rolling(20).mean() > 1_000_000  # Minimum volume

# Combine all filters
final_filter = liquidity_filter & price_filter & volume_filter

# Select top 10 stocks based on combined factor
position = combined_factor[final_filter].is_largest(10)

# Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)

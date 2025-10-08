# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')

# 2. Calculate factors

# Factor 1: Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume Surge (current volume vs. 60-day average)
avg_volume_60 = volume.rolling(60).mean().shift(1)
volume_surge = (volume / avg_volume_60).shift(1)

# Factor 3: ROE (smoothed to reduce noise)
# Preserve the successful ROE smoothing from Iteration 1
roe_smoothed = roe.rolling(window=1, min_periods=1).mean().shift(1)

# Factor 4: Revenue YoY Growth
revenue_growth = revenue_yoy.shift(1)

# Factor 5: Foreign Investor Buying Strength
foreign_buying_strength = foreign_strength.shift(1)

# 3. Apply filters

# Filter 1: Liquidity filter (average daily trading value > 50,000,000 TWD)
# PRESERVED from Iteration 1
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Filter 2: Price filter (close price > 10 TWD)
# PRESERVED from Iteration 1
price_filter = close.shift(1) > 10

# Filter 3: Volume filter (average daily volume > 100,000 shares)
# PRESERVED from Iteration 1
volume_filter = volume.rolling(20).mean().shift(1) > 100_000

# Combine filters
combined_filters = liquidity_filter & price_filter & volume_filter

# 4. Combine factors (adjusting weights slightly from Iteration 1)
# Iteration 1 weights: momentum * 0.3, volume_surge * 0.2, roe_smoothed * 0.5
# Adjusting weights within ±5% maximum as per requirements
# New weights: momentum * 0.31, volume_surge * 0.19, roe_smoothed * 0.48, revenue_growth * 0.01, foreign_buying_strength * 0.01
# Total weight: 0.31 + 0.19 + 0.48 + 0.01 + 0.01 = 1.00

combined_factor = (
    momentum * 0.31 +  # Slightly increased momentum weight
    volume_surge * 0.19 +  # Slightly decreased volume surge weight
    roe_smoothed * 0.48 +  # Slightly decreased ROE weight
    revenue_growth * 0.01 + # Added a small weight for revenue growth
    foreign_buying_strength * 0.01 # Added a small weight for foreign buying strength
)

# 5. Select stocks
# Apply filters before selecting the largest
filtered_factor = combined_factor[combined_filters]

# Select the top 10 stocks based on the combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
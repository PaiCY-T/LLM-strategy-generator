# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Factor 1: Momentum (20-day return)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume Surge (current volume vs. 60-day average)
avg_volume_60d = volume.rolling(60).mean()
volume_surge = (volume / avg_volume_60d).shift(1)

# Factor 3: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 4: ROE (Return on Equity)
# Shift ROE by 1 to avoid look-ahead bias
roe_factor = roe.shift(1)

# Factor 5: Inverse P/E Ratio (Value)
# Handle potential division by zero or negative P/E
inverse_pe = (1 / pe_ratio).replace([float('inf'), -float('inf')], 0).shift(1)


# 3. Combine factors
# Normalize factors (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming relative scales are somewhat compatible or we're looking for extremes.
# A more robust approach would involve rank normalization or z-scoring.

# Combine momentum and volume surge for short-term strength
short_term_strength = momentum * volume_surge

# Combine fundamental factors
fundamental_strength = revenue_growth_factor + roe_factor + inverse_pe

# Overall combined factor - giving more weight to fundamental strength
combined_factor = (short_term_strength * 0.3) + (fundamental_strength * 0.7)


# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
trading_value = data.get('price:成交金額')
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price > 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor
filtered_factor = combined_factor[final_filter]

# Select the top 10 stocks based on the filtered combined factor
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
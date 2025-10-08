# 1. Load data
close = data.get('price:收盤價')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
trading_value = data.get('price:成交金額')
volume = data.get('price:成交股數')

# 2. Calculate factors

# Factor 1: Momentum (60-day returns)
returns_60d = close.pct_change(60)
momentum_factor = returns_60d.shift(1)

# Factor 2: Value (Inverse of P/B ratio, lower P/B is better)
# Cap P/B ratio to avoid extreme outliers and handle potential division by zero
pb_ratio_capped = pb_ratio.clip(lower=0.1, upper=50) # Ensure P/B is positive and not excessively high
value_factor = (1 / pb_ratio_capped).shift(1)
value_factor = value_factor.replace([float('inf'), -float('inf')], float('nan'))
# Fill remaining NaNs with the cross-sectional median to maintain relative ranking
value_factor = value_factor.fillna(value_factor.median(axis=1))

# Factor 3: Foreign Investor Strength
# This factor is already a strength indicator, higher is better.
foreign_strength_factor = foreign_strength.shift(1)
# Fill NaNs in foreign strength with 0 or cross-sectional median if preferred
foreign_strength_factor = foreign_strength_factor.fillna(0) # Assume no strength if data missing

# Factor 4: Volume Trend (Average volume relative to long-term average)
avg_volume_20d = volume.rolling(20).mean()
avg_volume_120d = volume.rolling(120).mean()
volume_trend_factor = (avg_volume_20d / avg_volume_120d).shift(1)
volume_trend_factor = volume_trend_factor.fillna(1) # Assume no trend if data missing

# 3. Combine factors
# We want positive momentum, low P/B (high inverse P/B), high foreign strength, and increasing volume trend.
# Normalize factors to a common scale (e.g., rank) before combining if their scales are very different.
# For simplicity, let's use a weighted average after filling NaNs.
# Give more weight to momentum and foreign strength, some to value and volume trend.
combined_factor = (
    momentum_factor * 0.35 +
    value_factor * 0.20 +
    foreign_strength_factor * 0.35 +
    volume_trend_factor * 0.10
)

# 4. Apply filters
# Liquidity filter: 20-day average trading value > 50 million TWD
avg_trading_value_20d = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value_20d > 50_000_000).shift(1)

# Price filter: Ensure price is above a certain threshold to avoid penny stocks or illiquid ones
price_filter = (close > 15).shift(1) # Minimum price of 15 TWD

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined factor and filters, then select top 10 stocks
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
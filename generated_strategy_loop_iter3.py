# 1. Load data
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
roe = data.get('fundamental_features:ROE稅後')
pb_ratio = data.get('fundamental_features:股價淨值比')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: Momentum (20-day returns)
momentum = close.pct_change(20).shift(1)

# Factor 2: Volume strength (current volume vs. 60-day average)
avg_volume_60d = volume.rolling(60).mean()
volume_strength = (volume / avg_volume_60d).shift(1)

# Factor 3: Revenue Growth (YoY)
# Shift revenue_yoy by 1 to avoid look-ahead bias
revenue_growth = revenue_yoy.shift(1)

# Factor 4: ROE (Return on Equity)
# Shift ROE by 1 to avoid look-ahead bias
roe_shifted = roe.shift(1)

# Factor 5: Value (P/B ratio) - lower is better
pb_ratio_shifted = pb_ratio.shift(1)

# 3. Combine factors
# Normalize factors (optional, but good practice for combining)
# For simplicity, we'll combine directly, assuming relative scales are somewhat compatible or we want to emphasize certain factors.
# Higher momentum, higher volume strength, higher revenue growth, higher ROE are good. Lower P/B is good.

# We'll create a composite score where higher is better for momentum, volume, revenue, ROE, and lower is better for P/B.
# To make P/B contribute positively to a "higher is better" score, we can take its inverse or subtract it from a large number.
# Let's use -pb_ratio_shifted so that lower P/B results in a higher score.

combined_factor = (
    momentum * 0.3 +
    volume_strength * 0.2 +
    revenue_growth * 0.2 +
    roe_shifted * 0.2 -
    pb_ratio_shifted * 0.1 # Negative weight for P/B as lower is better
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over the last 20 days must be greater than 50 million TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Close price must be above 10 TWD to avoid penny stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply the filter to the combined factor and select the top 10 stocks
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)